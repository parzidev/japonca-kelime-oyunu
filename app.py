import json
import random
import os
from flask import Flask, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__, 
            template_folder=os.path.abspath('templates'),
            static_folder=os.path.abspath('static'),
            static_url_path='/static')
CORS(app)

# Configuration
GRID_SIZE_FALLBACK = 12
FILL_CHARS = "アイウエオカキクケコサシスセソタチツテトナニヌネノマミムメモラリルレロハヒフヘホ"

# Directions for word placement (dx, dy)
DIRECTIONS = [
    (1, 0),   # Right
    (-1, 0),  # Left
    (0, 1),   # Down
    (0, -1),  # Up
    (1, 1),   # Down-Right
    (-1, -1), # Up-Left
    (1, -1),  # Up-Right
    (-1, 1)   # Down-Left
]

def load_words():
    """Load words from the JSON file."""
    try:
        # Path relative to app.py
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(base_dir, 'data', 'words-ja-body.json')
        print(f"DEBUG: Loading words from {data_path}")
        
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            words = data.get('words', [])
            print(f"DEBUG: Loaded {len(words)} words.")
            return words, data.get('gridSize', GRID_SIZE_FALLBACK)
    except FileNotFoundError:
        print(f"ERROR: Data file not found at {data_path}")
        return [], GRID_SIZE_FALLBACK
    except Exception as e:
        print(f"ERROR: Failed to load words: {e}")
        return [], GRID_SIZE_FALLBACK

def create_empty_grid(size):
    """Create a grid of empty strings."""
    return [['' for _ in range(size)] for _ in range(size)]

def try_place_word(grid, word, size):
    """Attempt to place a word on the grid."""
    chars = list(word)
    max_tries = 200
    
    for _ in range(max_tries):
        dx, dy = random.choice(DIRECTIONS)
        start_x = random.randint(0, size - 1)
        start_y = random.randint(0, size - 1)
        
        end_x = start_x + dx * (len(chars) - 1)
        end_y = start_y + dy * (len(chars) - 1)
        
        if not (0 <= end_x < size and 0 <= end_y < size):
            continue
            
        # Check for collisions
        ok = True
        temp_coords = []
        for i, char in enumerate(chars):
            x = start_x + dx * i
            y = start_y + dy * i
            existing = grid[y][x]
            if existing != '' and existing != char:
                ok = False
                break
            temp_coords.append((x, y))
            
        if not ok:
            continue
            
        # Place the word
        for i, (x, y) in enumerate(temp_coords):
            grid[y][x] = chars[i]
        return True
        
    return False

def fill_empty_cells(grid, size):
    """Fill empty cells with random characters."""
    for y in range(size):
        for x in range(size):
            if grid[y][x] == '':
                grid[y][x] = random.choice(FILL_CHARS)

@app.route('/api/new-game', methods=['GET'])
def new_game():
    words, grid_size = load_words()
    grid = create_empty_grid(grid_size)
    
    placed_words = []
    
    for word_entry in words:
        kana = word_entry.get('kana', '').replace(' ', '').replace('　', '') # Remove spaces
        if try_place_word(grid, kana, grid_size):
            placed_words.append(word_entry)
        else:
            print(f"Could not place: {kana}")
            
    fill_empty_cells(grid, grid_size)
    
    return jsonify({
        'grid': grid,
        'words': words,
        'gridSize': grid_size
    })

@app.route('/')
@app.route('/index.html')
def index():
    print("Serving index.html")
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
