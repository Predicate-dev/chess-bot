"""Engine wrapper around python-chess to provide simple move application and queries.

This is intentionally small: move generation and legality are delegated to python-chess.
"""
from __future__ import annotations

import chess
from typing import Iterable, Optional


class ChessEngine:
    """Wrapper around a `chess.Board`.

    Simple contract:
    - Inputs: moves as UCI strings (e.g. 'e2e4') or chess.Move objects
    - Outputs: updates board state, provides legal moves, and game status
    - Error modes: raises ValueError for illegal moves
    """

    def __init__(self, fen: Optional[str] = None):
        self.board = chess.Board() if fen is None else chess.Board(fen)

    def set_fen(self, fen: str) -> None:
        self.board.set_fen(fen)

    def legal_moves(self) -> Iterable[chess.Move]:
        return list(self.board.legal_moves)

    def push(self, move) -> None:
        """Apply a move. Accepts UCI string or chess.Move."""
        if isinstance(move, str):
            m = chess.Move.from_uci(move)
        else:
            m = move
        if m not in self.board.legal_moves:
            raise ValueError(f"Illegal move: {m}")
        self.board.push(m)

    def pop(self) -> chess.Move:
        return self.board.pop()

    def is_game_over(self) -> bool:
        return self.board.is_game_over()

    def result(self) -> str:
        return self.board.result()

    def fen(self) -> str:
        return self.board.fen()

    def copy(self) -> "ChessEngine":
        e = ChessEngine(self.board.fen())
        return e
