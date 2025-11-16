"""Web UI for the chess bot using Flask.

Endpoints:
- GET / -> serves static index.html
- POST /move -> accept user's UCI move, validate/apply, run bot search, return bot move and FEN
- POST /reset -> reset the board
- GET /state -> current FEN

Run with: python -m chess_bot.web
"""
from __future__ import annotations

import os
import time
from typing import Optional

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

import chess
from .alpha_beta import search_root


BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="/static")
CORS(app)

# simple global board for demo; single-user
BOARD: chess.Board = chess.Board()


@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/state")
def state():
    return jsonify({
        "fen": BOARD.fen(),
        "turn": "white" if BOARD.turn == chess.WHITE else "black",
        "game_over": BOARD.is_game_over(),
        "result": BOARD.result() if BOARD.is_game_over() else None,
    })


@app.route("/reset", methods=["POST"])
def reset():
    global BOARD
    BOARD = chess.Board()
    return jsonify({"ok": True, "fen": BOARD.fen()})


@app.route("/move", methods=["POST"])
def move():
    data = request.get_json(force=True)
    if not data or "move" not in data:
        return jsonify({"ok": False, "error": "missing move field"}), 400

    uci = data["move"]
    try:
        mv = chess.Move.from_uci(uci)
    except Exception:
        return jsonify({"ok": False, "error": "invalid uci"}), 400

    if mv not in BOARD.legal_moves:
        return jsonify({"ok": False, "error": "illegal move"}), 400

    # apply user's move
    BOARD.push(mv)

    # If game over now, return
    if BOARD.is_game_over():
        return jsonify({"ok": True, "fen": BOARD.fen(), "bot_move": None, "game_over": True, "result": BOARD.result()})

    # run bot
    max_depth = int(data.get("max_depth", 3))
    time_limit = data.get("time_limit")
    t0 = time.time()
    best_move, info = search_root(BOARD, max_depth=max_depth, time_limit=time_limit)
    elapsed = time.time() - t0

    if best_move is None:
        # no move (shouldn't happen unless game over)
        return jsonify({"ok": True, "fen": BOARD.fen(), "bot_move": None, "info": info})

    BOARD.push(best_move)

    return jsonify({
        "ok": True,
        "fen": BOARD.fen(),
        "bot_move": best_move.uci(),
        "info": info,
        "elapsed": elapsed,
        "game_over": BOARD.is_game_over(),
        "result": BOARD.result() if BOARD.is_game_over() else None,
    })


def main():
    # default host/port (use env CHESS_BOT_PORT or first CLI arg to override)
    import sys

    port = 5000
    env_port = os.environ.get("CHESS_BOT_PORT")
    if env_port:
        try:
            port = int(env_port)
        except Exception:
            pass

    # CLI override
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except Exception:
            pass

    app.run(host="127.0.0.1", port=port, debug=False)


if __name__ == "__main__":
    main()
