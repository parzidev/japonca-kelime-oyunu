import json
import os
import random
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
GRID_SIZE_FALLBACK = 12

# Build filler characters from the same script family used by each puzzle.
# This prevents hiragana answers from standing out inside an all-katakana board.
HIRAGANA_FILL_CHARS = tuple(
    "あいうえお"
    "かきくけこがぎぐげご"
    "さしすせそざじずぜぞ"
    "たちつてとだぢづでど"
    "なにぬねの"
    "はひふへほばびぶべぼぱぴぷぺぽ"
    "まみむめも"
    "やゆよ"
    "らりるれろ"
    "わをん"
    "ぁぃぅぇぉゃゅょっ"
)
KATAKANA_FILL_CHARS = tuple(
    "アイウエオ"
    "カキクケコガギグゲゴ"
    "サシスセソザジズゼゾ"
    "タチツテトダヂヅデド"
    "ナニヌネノ"
    "ハヒフヘホバビブベボパピプペポ"
    "マミムメモ"
    "ヤユヨ"
    "ラリルレロ"
    "ワヲン"
    "ァィゥェォャュョッー"
)

DIRECTIONS = [
    (1, 0),    # right
    (-1, 0),   # left
    (0, 1),    # down
    (0, -1),   # up
    (1, 1),    # down-right
    (-1, -1),  # up-left
    (1, -1),   # up-right
    (-1, 1),   # down-left
]

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
    static_url_path="/static",
)
CORS(app)


def normalize_kana(value: str) -> str:
    return (value or "").replace(" ", "").replace("　", "")


def load_puzzle_file(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    puzzle_id = data.get("id") or path.stem.replace("words-ja-", "")
    words = data.get("words", [])
    return {
        "id": puzzle_id,
        "title": data.get("title", puzzle_id.title()),
        "emoji": data.get("emoji", "🌸"),
        "category": data.get("category", puzzle_id),
        "language": data.get("language", "ja"),
        "gridSize": data.get("gridSize", GRID_SIZE_FALLBACK),
        "words": words,
        "source": path.name,
    }


def discover_puzzles():
    puzzles = []
    for path in sorted(DATA_DIR.glob("words-ja-*.json")):
        try:
            puzzles.append(load_puzzle_file(path))
        except Exception as exc:
            print(f"ERROR: Could not load {path.name}: {exc}")
    return puzzles


def get_puzzle(puzzle_id=None):
    puzzles = discover_puzzles()
    if not puzzles:
        return None

    if not puzzle_id or puzzle_id == "random":
        return random.choice(puzzles)

    for puzzle in puzzles:
        if puzzle["id"] == puzzle_id:
            return puzzle

    return None


def create_empty_grid(size):
    return [["" for _ in range(size)] for _ in range(size)]


def try_place_word(grid, word, size, max_tries=350):
    chars = list(word)
    if not chars or len(chars) > size:
        return None

    for _ in range(max_tries):
        dx, dy = random.choice(DIRECTIONS)
        start_x = random.randint(0, size - 1)
        start_y = random.randint(0, size - 1)

        end_x = start_x + dx * (len(chars) - 1)
        end_y = start_y + dy * (len(chars) - 1)
        if not (0 <= end_x < size and 0 <= end_y < size):
            continue

        coords = []
        for index, char in enumerate(chars):
            x = start_x + dx * index
            y = start_y + dy * index
            existing = grid[y][x]
            if existing and existing != char:
                break
            coords.append((x, y))
        else:
            for index, (x, y) in enumerate(coords):
                grid[y][x] = chars[index]
            return coords

    return None


def filler_pool_for_words(words):
    text = "".join(normalize_kana(item.get("kana", "")) for item in words)
    uses_hiragana = any("\u3040" <= char <= "\u309f" for char in text)
    uses_katakana = any("\u30a0" <= char <= "\u30ff" for char in text)

    pool = []
    if uses_hiragana:
        pool.extend(HIRAGANA_FILL_CHARS)
    if uses_katakana:
        pool.extend(KATAKANA_FILL_CHARS)
    return tuple(pool or HIRAGANA_FILL_CHARS)


def fill_empty_cells(grid, size, words):
    filler_pool = filler_pool_for_words(words)
    for y in range(size):
        for x in range(size):
            if not grid[y][x]:
                grid[y][x] = random.choice(filler_pool)


def build_game(puzzle):
    grid_size = int(puzzle.get("gridSize") or GRID_SIZE_FALLBACK)
    grid = create_empty_grid(grid_size)

    # Longer words are harder to place, so place them first for a more reliable board.
    source_words = sorted(
        puzzle.get("words", []),
        key=lambda item: len(normalize_kana(item.get("kana", ""))),
        reverse=True,
    )

    placed_words = []
    for word_entry in source_words:
        kana = normalize_kana(word_entry.get("kana", ""))
        coords = try_place_word(grid, kana, grid_size)
        if coords:
            placed_words.append(word_entry)
        else:
            print(f"WARNING: Could not place '{kana}' in puzzle '{puzzle['id']}'")

    fill_empty_cells(grid, grid_size, placed_words)
    random.shuffle(placed_words)

    return {
        "grid": grid,
        "words": placed_words,
        "gridSize": grid_size,
        "puzzle": {
            "id": puzzle["id"],
            "title": puzzle["title"],
            "emoji": puzzle["emoji"],
            "wordCount": len(placed_words),
        },
    }


@app.get("/api/puzzles")
def puzzles_api():
    puzzles = discover_puzzles()
    return jsonify(
        {
            "puzzles": [
                {
                    "id": puzzle["id"],
                    "title": puzzle["title"],
                    "emoji": puzzle["emoji"],
                    "gridSize": puzzle["gridSize"],
                    "wordCount": len(puzzle["words"]),
                }
                for puzzle in puzzles
            ]
        }
    )


@app.get("/api/new-game")
def new_game():
    puzzle_id = request.args.get("category") or "body"
    puzzle = get_puzzle(puzzle_id)
    if puzzle is None:
        return jsonify({"error": "Bulmaca kategorisi bulunamadı."}), 404
    return jsonify(build_game(puzzle))


@app.get("/")
@app.get("/index.html")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
