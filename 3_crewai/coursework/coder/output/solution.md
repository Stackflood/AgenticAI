I created a clean, dependency-free Python Tic-Tac-Toe (3x3) game and simulated a full match between two automated dummy players.

What I did:
- Wrote `tic_tac_toe_dummy.py` in the sandbox.
- Implemented:
  - a 3x3 board
  - win detection for rows, columns, and diagonals
  - available-move tracking
  - two automated players: `X` and `O`
  - random move selection from remaining empty cells
- Ran the script successfully.

Final result from the simulation:
- Player X won the game.

Complete code used:
```python
import random


def create_board():
    return [" "] * 9


def print_board(board):
    for row in range(3):
        start = row * 3
        print(" | ".join(board[start:start + 3]))
        if row < 2:
            print("-" * 9)


def check_winner(board):
    wins = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6),
    ]
    for a, b, c in wins:
        if board[a] != " " and board[a] == board[b] == board[c]:
            return board[a]
    return None


def available_moves(board):
    return [i for i, cell in enumerate(board) if cell == " "]


def play_game():
    board = create_board()
    current_player = "X"

    print("Initial board:")
    print_board(board)
    print()

    while True:
        moves = available_moves(board)
        move = random.choice(moves)
        board[move] = current_player

        print(f"Player {current_player} chooses cell {move + 1}")
        print_board(board)
        print()

        winner = check_winner(board)
        if winner:
            print(f"Winner: Player {winner}")
            return winner

        if not available_moves(board):
            print("Game result: Draw")
            return None

        current_player = "O" if current_player == "X" else "X"


if __name__ == "__main__":
    play_game()
```