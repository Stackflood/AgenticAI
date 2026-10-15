
"""
Free MCP server: find EV charging sites for specified networks in a US city.

Data sources:
- Nominatim: city geocoding
- OpenStreetMap Overpass API: charging-station POIs

No Google API key or billing required.

Install:
    pip install mcp httpx

Set a real contact email in PowerShell:
    $env:OSM_CONTACT_EMAIL = "lohum.sales@gmail.com"

Run:
    python osm_charging_mcp_server.py
"""

import json
import os
import re
import time
import threading
from pathlib import Path

import httpx
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("osm-charging")

NOMINATIM = "https://nominatim.openstreetmap.org/search"

OVERPASS_URLS = [
    "https://overpass.openstreetmap.fr/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

# Set OSM_CONTACT_EMAIL to a genuine contact address.
CONTACT_EMAIL = os.getenv("OSM_CONTACT_EMAIL", "").strip()

if not CONTACT_EMAIL or "@" not in CONTACT_EMAIL:
    raise RuntimeError(
        "Set OSM_CONTACT_EMAIL to a real contact email before starting "
        "the server. Example PowerShell command:\n"
        '$env:OSM_CONTACT_EMAIL = "lohum.sales@gmail.com"'
    )

USER_AGENT = (
    f"fleet-charging-map/0.2 (contact: {CONTACT_EMAIL})"
)

NOMINATIM_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json",
}

OVERPASS_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json",
}

HTTP_TIMEOUT = httpx.Timeout(120.0, connect=20.0)
OVERPASS_TIMEOUT = httpx.Timeout(60.0, connect=10.0)

# Enforce at least one second between Nominatim request starts.
_nominatim_lock = threading.Lock()
_last_nominatim_request = 0.0


def _geocode_city(city: str) -> dict:
    """Geocode a US city with Nominatim, respecting its rate limit."""
    global _last_nominatim_request

    city = city.strip()
    if not city:
        raise ValueError("City must not be empty.")

    with _nominatim_lock:
        elapsed = time.monotonic() - _last_nominatim_request
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)

        try:
            response = httpx.get(
                NOMINATIM,
                params={
                    "q": city,
                    "format": "jsonv2",
                    "limit": 1,
                    "countrycodes": "us",
                },
                headers=NOMINATIM_HEADERS,
                timeout=HTTP_TIMEOUT,
            )
        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"Nominatim network request failed for {city!r}: {exc}"
            ) from exc
        finally:
            _last_nominatim_request = time.monotonic()

    if response.status_code == 403:
        raise RuntimeError(
            "Nominatim returned HTTP 403 Forbidden. "
            "The request was denied by the service or an intermediary. "
            "Verify your contact email and User-Agent, inspect the response "
            f"body, and check whether access to your IP is restricted. "
            f"Response: {response.text[:1000]}"
        )

    if response.status_code == 429:
        raise RuntimeError(
            "Nominatim returned HTTP 429 Too Many Requests. "
            "Stop retrying and respect the service's usage limits. "
            f"Response: {response.text[:500]}"
        )

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"Nominatim returned HTTP {response.status_code}: "
            f"{response.text[:1000]}"
        ) from exc

    try:
        hits = response.json()
    except ValueError as exc:
        raise RuntimeError(
            "Nominatim returned invalid JSON."
        ) from exc

    if not hits:
        raise ValueError(
            f"City not found in US OpenStreetMap geocoding: {city!r}"
        )

    return hits[0]


def _overpass(query: str) -> dict:
    """Run an Overpass query, trying the fallback endpoint if needed."""
    errors = []

    for url in OVERPASS_URLS:
        try:
            response = httpx.post(
                url,
                data={"data": query},
                headers=OVERPASS_HEADERS,
                timeout=OVERPASS_TIMEOUT,
            )
            if response.status_code == 429:
                errors.append(f"{url}: HTTP 429 Too Many Requests")
                continue

            response.raise_for_status()
            try:
                return response.json()
            except ValueError as exc:
                errors.append(f"{url}: invalid JSON ({exc})")
        except httpx.HTTPError as exc:
            body = exc.response.text[:500] if isinstance(exc, httpx.HTTPStatusError) else ""
            errors.append(f"{url}: {exc}; response={body}")

    raise RuntimeError("All Overpass endpoints failed:\n" + "\n".join(errors))


def _build_query(networks: list[str], hit: dict) -> str:
    if not networks:
        raise ValueError("Provide at least one charging network.")

    if hit.get("osm_type") == "relation":
        scope_head = f"area({3600000000 + int(hit['osm_id'])})->.a;"
        scope = "(area.a)"
    else:
        s, n, w, e = hit["boundingbox"]
        scope_head = ""
        scope = f"({s},{w},{n},{e})"

    # Combine network names into one regex instead of repeating
    # a separate query clause for every network.
    pattern = "|".join(re.escape(net) for net in networks)

    lines = [
        f'  nwr["amenity"="charging_station"]["{key}"~"{pattern}",i]{scope};'
        for key in ("operator", "network", "brand")
    ]

    return (
        "[out:json][timeout:45];\n"
        f"{scope_head}\n"
        "(\n" + "\n".join(lines) + "\n);\n"
        "out center tags;"
    )


def _match_network(tags: dict, networks: list[str]) -> str | None:
    """Match an OSM element to one of the requested networks."""
    fields = ("operator", "network", "brand")
    blob = " ".join(
        str(tags.get(key, "")) for key in fields
    ).casefold()

    for network in networks:
        if network.casefold() in blob:
            return network

    return None


@mcp.tool()
def find_charging_sites(
    networks: list[str],
    city: str,
    output_prefix: str = "charging_sites",
) -> dict:
    """
    Find OpenStreetMap charging sites for specified networks in a US city.

    Saves results to JSON and GeoJSON files.

    networks: e.g. ["Electrify America", "ChargePoint"]
    city: e.g. "Houston, TX"
    output_prefix: output filename prefix, without extension
    """
    if not networks:
        raise ValueError("Provide at least one charging network.")

    hit = _geocode_city(city)
    query = _build_query(networks, hit)
    data = _overpass(query)

    sites = []
    seen = set()

    for element in data.get("elements", []):
        tags = element.get("tags", {})
        center = element.get("center", {})

        lat = element.get("lat", center.get("lat"))
        lng = element.get("lon", center.get("lon"))

        network = _match_network(tags, networks)
        key = (element.get("type"), element.get("id"))

        if (
            lat is None
            or lng is None
            or network is None
            or key in seen
        ):
            continue

        seen.add(key)

        street = " ".join(
            filter(
                None,
                [
                    tags.get("addr:housenumber"),
                    tags.get("addr:street"),
                ],
            )
        )

        address = ", ".join(
            filter(
                None,
                [
                    street,
                    tags.get("addr:city"),
                    tags.get("addr:state"),
                    tags.get("addr:postcode"),
                ],
            )
        )

        sites.append(
            {
                "network": network,
                "name": tags.get("name") or tags.get("operator") or network,
                "address": address or None,
                "lat": lat,
                "lng": lng,
                "stalls": tags.get("capacity"),
                "osm_id": f"{element['type']}/{element['id']}",
            }
        )

    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [site["lng"], site["lat"]],
                },
                "properties": {
                    key: value
                    for key, value in site.items()
                    if key not in ("lat", "lng")
                },
            }
            for site in sites
        ],
    }

    # Write outputs in the current working directory.
    prefix = Path(output_prefix)
    json_path = prefix.with_suffix(".json")
    geojson_path = prefix.with_suffix(".geojson")

    json_path.write_text(
        json.dumps(sites, indent=2),
        encoding="utf-8",
    )
    geojson_path.write_text(
        json.dumps(geojson, indent=2),
        encoding="utf-8",
    )

    counts = {
        network: sum(
            1 for site in sites if site["network"] == network
        )
        for network in networks
    }

    return {
        "city": hit.get("display_name"),
        "counts_by_network": counts,
        "total_sites": len(sites),
        "files": [
            str(json_path.resolve()),
            str(geojson_path.resolve()),
        ],
        "sample": sites[:5],
        "note": (
            "OpenStreetMap coverage varies. These results are not "
            "guaranteed to represent every real-world charging site. "
            "A zero count does not prove that a network has no sites "
            "in the city."
        ),
    }


if __name__ == "__main__":
    mcp.run()
