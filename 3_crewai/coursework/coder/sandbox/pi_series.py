from decimal import Decimal, getcontext

# Calculate 4 * (1 - 1/3 + 1/5 - 1/7 + ...)
# using the first 1,000,000 terms.

def main():
    getcontext().prec = 50
    total = Decimal(0)

    for i in range(1_000_000):
        denominator = Decimal(2 * i + 1)
        term = Decimal(1) / denominator
        if i % 2 == 0:
            total += term
        else:
            total -= term

    result = total * 4
    print(result)


if __name__ == "__main__":
    main()
