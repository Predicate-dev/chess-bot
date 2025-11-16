import chess

from chess_bot.alpha_beta import search_root


def test_bot_returns_legal_move_from_start():
    board = chess.Board()
    best_move, info = search_root(board, max_depth=2)
    assert best_move is not None
    assert isinstance(best_move, chess.Move)
    assert best_move in board.legal_moves
