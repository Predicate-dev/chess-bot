"""CLI to play vs the alpha-beta bot or run a demo game.

Run `python -m chess_bot.cli` to start an interactive session.
"""
from __future__ import annotations

import sys
import time
from typing import Optional

import chess

from .alpha_beta import search_root


def print_board(board: chess.Board) -> None:
    print(board)
    print()


def ask_move(board: chess.Board) -> chess.Move:
    while True:
        user = input("Your move (UCI, e.g. e2e4): ").strip()
        try:
            if user == 'quit':
                print('Exiting')
                sys.exit(0)
            # try UCI first
            mv = chess.Move.from_uci(user)
            if mv in board.legal_moves:
                return mv
        except Exception:
            pass

        # try SAN
        try:
            mv = board.parse_san(user)
            if mv in board.legal_moves:
                return mv
        except Exception:
            pass

        print("Illegal or invalid move, try again (or type 'quit' to exit).")


def play_vs_bot(max_depth: int = 3, human_color: str = 'white') -> None:
    board = chess.Board()
    human_is_white = human_color.lower().startswith('w')

    while not board.is_game_over():
        print_board(board)
        if board.turn == chess.WHITE and human_is_white or board.turn == chess.BLACK and not human_is_white:
            # human to move
            mv = ask_move(board)
            board.push(mv)
        else:
            # bot to move
            print('Bot thinking... (depth:', max_depth, ')')
            start = time.time()
            best_move, info = search_root(board, max_depth)
            took = time.time() - start
            if best_move is None:
                print('Bot found no move')
                break
            print(f"Bot selects {best_move.uci()} eval={info['eval']} nodes={info['nodes']} time={took:.2f}s pv={info['pv']}")
            board.push(best_move)

    print_board(board)
    print('Game over:', board.result())


def main(argv=None):
    argv = argv or sys.argv[1:]
    color = 'white'
    depth = 3
    if len(argv) >= 1:
        color = argv[0]
    if len(argv) >= 2:
        try:
            depth = int(argv[1])
        except Exception:
            pass

    print(f"You are playing as {color}. Bot search depth {depth}.")
    play_vs_bot(depth, human_color=color)


if __name__ == '__main__':
    main()
