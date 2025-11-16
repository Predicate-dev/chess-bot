"""Alpha-beta (negamax) search with iterative deepening and thought reporting.

This module uses python-chess for board representation. The search is implemented
as a negamax with alpha-beta pruning and basic move ordering (captures first).
"""
from __future__ import annotations

import time
from typing import Dict, List, Optional, Tuple

import chess

# piece values (centipawns)
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000,
}


def evaluate(board: chess.Board) -> int:
    """Simple evaluation: material + small mobility bonus.

    Positive values favor White. We return centipawns from the side to move's
    perspective in the negamax framework (caller will negate as needed).
    """
    material = 0
    for piece_type in PIECE_VALUES:
        material += PIECE_VALUES[piece_type] * (
            len(board.pieces(piece_type, chess.WHITE)) - len(board.pieces(piece_type, chess.BLACK))
        )

    # mobility
    mobility = 10 * (board.legal_moves.count() if hasattr(board.legal_moves, 'count') else len(list(board.legal_moves)))

    score = material + (mobility if board.turn == chess.WHITE else -mobility)
    return score


class SearchInfo:
    def __init__(self):
        self.nodes = 0
        self.start_time = 0.0
        self.best_line: List[chess.Move] = []


class TTEntry:
    def __init__(self, depth: int, value: int, flag: str, move: Optional[chess.Move]):
        # flag: 'EXACT', 'LOWER', 'UPPER'
        self.depth = depth
        self.value = value
        self.flag = flag
        self.move = move


class TranspositionTable:
    def __init__(self):
        self.table: Dict[object, TTEntry] = {}

    def get(self, key: object) -> Optional[TTEntry]:
        return self.table.get(key)

    def store(self, key: object, entry: TTEntry) -> None:
        # store or replace; could add replacement heuristics
        self.table[key] = entry


def quiescence(board: chess.Board, alpha: int, beta: int, info: SearchInfo, tt: TranspositionTable, max_q_depth: int = 4) -> int:
    """Quiescence search that only explores captures to avoid the horizon effect.

    Returns evaluation in centipawns.
    """
    info.nodes += 1

    # probe TT for quiet positions (use board key)
    key = board.transposition_key() if hasattr(board, "transposition_key") else board.fen()
    tt_entry = tt.get(key)
    if tt_entry is not None and tt_entry.depth >= 0 and tt_entry.flag == 'EXACT':
        return tt_entry.value

    stand_pat = evaluate(board)
    if stand_pat >= beta:
        return stand_pat
    if alpha < stand_pat:
        alpha = stand_pat

    # limit quiescence depth to avoid runaway
    if max_q_depth <= 0:
        return stand_pat

    # consider captures only
    moves = [m for m in board.legal_moves if board.is_capture(m)]
    # simple MVV-LVA like ordering: capture value (victim - attacker)
    def mvvlva(m: chess.Move) -> int:
        victim = board.piece_type_at(m.to_square)
        attacker = board.piece_type_at(m.from_square)
        v_val = PIECE_VALUES.get(victim, 0) if victim is not None else 0
        a_val = PIECE_VALUES.get(attacker, 0) if attacker is not None else 0
        return (v_val - a_val)

    moves.sort(key=mvvlva, reverse=True)

    for mv in moves:
        board.push(mv)
        score = -quiescence(board, -beta, -alpha, info, tt, max_q_depth - 1)
        board.pop()

        if score >= beta:
            return score
        if score > alpha:
            alpha = score

    return alpha


def negamax(board: chess.Board, depth: int, alpha: int, beta: int, info: SearchInfo, tt: TranspositionTable) -> Tuple[int, Optional[chess.Move]]:
    """Negamax with alpha-beta pruning. Returns evaluation in centipawns.

    This function mutates `info.nodes` and uses board.push/pop to explore moves.
    """
    if board.is_game_over():
        return evaluate(board), None

    info.nodes += 1

    # TT probe
    key = board.transposition_key() if hasattr(board, "transposition_key") else board.fen()
    tt_entry = tt.get(key)
    if tt_entry is not None and tt_entry.depth >= depth:
        if tt_entry.flag == 'EXACT':
            return tt_entry.value, tt_entry.move
        elif tt_entry.flag == 'LOWER':
            alpha = max(alpha, tt_entry.value)
        elif tt_entry.flag == 'UPPER':
            beta = min(beta, tt_entry.value)
        if alpha >= beta:
            return tt_entry.value, tt_entry.move

    if depth == 0:
        # at leaf, do quiescence search
        val = quiescence(board, alpha, beta, info, tt)
        return val, None

    best_value = -10_000_000
    best_move: Optional[chess.Move] = None

    # move ordering: prefer TT move first, then captures
    moves = list(board.legal_moves)
    if tt_entry is not None and tt_entry.move in moves:
        moves.remove(tt_entry.move)
        moves.insert(0, tt_entry.move)

    moves.sort(key=lambda m: 0 if board.is_capture(m) else 1)

    for mv in moves:
        board.push(mv)
        val, _ = negamax(board, depth - 1, -beta, -alpha, info, tt)
        val = -val
        board.pop()

        if val > best_value:
            best_value = val
            best_move = mv

        alpha = max(alpha, val)
        if alpha >= beta:
            # store as lower bound in TT
            tt.store(key, TTEntry(depth, best_value, 'LOWER', best_move))
            return best_value, best_move

    # store result in TT
    flag = 'EXACT'
    if best_value <= alpha:
        flag = 'UPPER'
    elif best_value >= beta:
        flag = 'LOWER'

    tt.store(key, TTEntry(depth, best_value, flag, best_move))
    return best_value, best_move


def search_root(board: chess.Board, max_depth: int, time_limit: Optional[float] = None) -> Tuple[Optional[chess.Move], Dict]:
    """Iterative deepening wrapper. Returns best move and info dict.

    info dict contains: nodes, depth_reached, time, best_move (uci), eval, pv (as list of ucis)
    """
    info = SearchInfo()
    info.start_time = time.time()

    best_move = None
    best_eval = 0
    pv: List[chess.Move] = []

    tt = TranspositionTable()

    for depth in range(1, max_depth + 1):
        # Respect time limit
        if time_limit is not None and (time.time() - info.start_time) > time_limit:
            break

        info.nodes = 0
        val, move = negamax(board, depth, -10_000_000, 10_000_000, info, tt)
        best_eval = val

        if move is not None:
            best_move = move
            pv = [move]

    elapsed = time.time() - info.start_time
    info_dict = {
        "nodes": info.nodes,
        "time": elapsed,
        "depth_reached": depth if 'depth' in locals() else 0,
        "best_move": best_move.uci() if best_move is not None else None,
        "eval": best_eval,
        "pv": [m.uci() for m in pv],
    }
    return best_move, info_dict
