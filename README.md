# chess-bot

Small demo of a chess engine + bot using alpha-beta pruning (negamax) on top of python-chess.

See `chess_bot/` for the implementation and `tests/` for a minimal test.

To run:

1. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

2. Start interactive play (human vs bot):

```bash
python -m chess_bot.cli
```

By default the bot searches to depth 3; pass an argument to change color and depth, e.g.: `python -m chess_bot.cli black 4`.
# chess-bot