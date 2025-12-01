// Basit word-search motoru
const GRID_SIZE_FALLBACK = 12;
const GRID_ELEMENT = document.getElementById("grid");
const WORD_LIST_ELEMENT = document.getElementById("wordList");
const TIMER_ELEMENT = document.getElementById("timer");
const SCORE_ELEMENT = document.getElementById("score");
const NEW_GAME_BUTTON = document.getElementById("newGameBtn");
const TOGGLE_HINTS_BTN = document.getElementById("toggleHintsBtn");
let hintsVisible = false;

let words = [];
let gridSize = GRID_SIZE_FALLBACK;
let grid = [];
let timerSeconds = 180;
let timerInterval = null;
let score = 0;

let isMouseDown = false;
let selectedCells = new Set();
let cellElements = [];
let wordStatus = new Map(); // kana -> found? boolean

// Grid ve kelime listesi backend'den gelecek


// DOM'da grid'i çiz
function renderGrid() {
  GRID_ELEMENT.innerHTML = "";
  GRID_ELEMENT.style.gridTemplateColumns = `repeat(${gridSize}, 50px)`;
  GRID_ELEMENT.style.gridTemplateRows = `repeat(${gridSize}, 50px)`;
  cellElements = [];

  for (let y = 0; y < gridSize; y++) {
    for (let x = 0; x < gridSize; x++) {
      const cell = document.createElement("div");
      cell.className = "cell";
      cell.textContent = grid[y][x];
      cell.dataset.x = x;
      cell.dataset.y = y;

      cell.addEventListener("mousedown", onCellMouseDown);
      cell.addEventListener("mouseenter", onCellMouseEnter);
      cell.addEventListener("mouseup", onCellMouseUp);

      GRID_ELEMENT.appendChild(cell);
      cellElements.push(cell);
    }
  }

  // Mouse bırakıldığında temizle
  document.addEventListener("mouseup", clearSelection);
}

// Word list paneli
function renderWordList() {
  WORD_LIST_ELEMENT.innerHTML = "";
  wordStatus.clear();

  words.forEach((w) => {
    const kana = w.kana;
    wordStatus.set(kana, false);

    const li = document.createElement("li");
    li.dataset.kana = kana;

    const kanaSpan = document.createElement("span");
    kanaSpan.textContent = kana;
    kanaSpan.className = "kana blur-text";

    const romajiSpan = document.createElement("span");
    romajiSpan.textContent = w.romaji;
    romajiSpan.className = "romaji";

    const trSpan = document.createElement("span");
    trSpan.textContent = w.meaning_tr;

    li.appendChild(kanaSpan);
    li.appendChild(romajiSpan);
    li.appendChild(trSpan);
    WORD_LIST_ELEMENT.appendChild(li);
  });
}

// SVG Overlay Logic
const SVG_OVERLAY = document.getElementById("grid-overlay");
let currentLine = null;
let startCell = null;

function getCellCenter(cell) {
  const rect = cell.getBoundingClientRect();
  const svgRect = SVG_OVERLAY.getBoundingClientRect();
  return {
    x: rect.left - svgRect.left + rect.width / 2,
    y: rect.top - svgRect.top + rect.height / 2,
  };
}

function createLine(x1, y1, x2, y2, className) {
  const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
  line.setAttribute("x1", x1);
  line.setAttribute("y1", y1);
  line.setAttribute("x2", x2);
  line.setAttribute("y2", y2);
  line.setAttribute("class", className);
  SVG_OVERLAY.appendChild(line);
  return line;
}

// Seçimi yönetme
function onCellMouseDown(e) {
  clearSelection();
  isMouseDown = true;
  startCell = e.currentTarget;

  const center = getCellCenter(startCell);
  currentLine = createLine(center.x, center.y, center.x, center.y, "selection-line");

  addCellToSelection(startCell);

  // Add global mouse move/up listeners to handle dragging outside cells
  document.addEventListener("mousemove", onGlobalMouseMove);
}

function onGlobalMouseMove(e) {
  if (!isMouseDown || !currentLine) return;

  // Calculate mouse position relative to SVG
  const svgRect = SVG_OVERLAY.getBoundingClientRect();
  const x = e.clientX - svgRect.left;
  const y = e.clientY - svgRect.top;

  currentLine.setAttribute("x2", x);
  currentLine.setAttribute("y2", y);

  // Optional: Highlight cell under mouse if needed, 
  // but for now we rely on the line visual.
  // To detect cell under mouse:
  // const el = document.elementFromPoint(e.clientX, e.clientY);
  // if (el && el.classList.contains('cell')) { ... }
}

function onCellMouseEnter(e) {
  if (!isMouseDown) return;
  addCellToSelection(e.currentTarget);

  // Snap line to current cell center
  const center = getCellCenter(e.currentTarget);
  if (currentLine) {
    currentLine.setAttribute("x2", center.x);
    currentLine.setAttribute("y2", center.y);
  }
}

function onCellMouseUp() {
  if (isMouseDown) {
    checkSelection();
    clearSelection(); // This clears the temp line
  }
}

function addCellToSelection(cell) {
  const key = `${cell.dataset.x},${cell.dataset.y}`;
  if (!selectedCells.has(key)) {
    selectedCells.add(key);
    // cell.classList.add("highlight-temp"); // No longer needed
  }
}

function clearSelection() {
  isMouseDown = false;
  selectedCells.clear();
  // cellElements.forEach((c) => c.classList.remove("highlight-temp"));

  if (currentLine) {
    currentLine.remove();
    currentLine = null;
  }
  startCell = null;
  document.removeEventListener("mousemove", onGlobalMouseMove);
}

// Seçilen harflerden kelime oluştur
function checkSelection() {
  if (selectedCells.size === 0) return;

  const coords = Array.from(selectedCells).map((s) => {
    const [x, y] = s.split(",").map(Number);
    return { x, y };
  });

  // Sıralama: önce y, sonra x
  coords.sort((a, b) => (a.y - b.y) || (a.x - b.x));

  let selectedChars = "";
  coords.forEach(({ x, y }) => {
    selectedChars += grid[y][x];
  });

  // Sağdan sola veya tersten de olabilir
  const reversed = Array.from(selectedChars).reverse().join("");

  let foundKana = null;
  for (const w of words) {
    const kana = w.kana;
    if (kana === selectedChars || kana === reversed) {
      foundKana = kana;
      break;
    }
  }

  if (!foundKana) return;

  if (wordStatus.get(foundKana)) {
    return; // zaten bulunmuş
  }

  // Skor + işaretleme
  wordStatus.set(foundKana, true);
  score += 10;
  SCORE_ELEMENT.textContent = score.toString();

  // Word list'te işaretle
  const li = WORD_LIST_ELEMENT.querySelector(`li[data-kana="${foundKana}"]`);
  if (li) li.classList.add("found");

  // Draw permanent line
  // We need start and end cells of the found word
  // Assuming coords are sorted, first and last might be start/end
  // But user might have dragged backwards.
  // We can use the startCell and the last hovered cell if we tracked it,
  // or just use the first and last from sorted coords (which works for straight lines).

  if (coords.length > 0) {
    const first = coords[0];
    const last = coords[coords.length - 1];

    // Find DOM elements
    const startEl = cellElements.find(c => Number(c.dataset.x) === first.x && Number(c.dataset.y) === first.y);
    const endEl = cellElements.find(c => Number(c.dataset.x) === last.x && Number(c.dataset.y) === last.y);

    if (startEl && endEl) {
      const startCenter = getCellCenter(startEl);
      const endCenter = getCellCenter(endEl);
      createLine(startCenter.x, startCenter.y, endCenter.x, endCenter.y, "found-line");
    }
  }
}

// Timer
function startTimer() {
  clearInterval(timerInterval);
  timerSeconds = 180;
  updateTimerText();
  timerInterval = setInterval(() => {
    timerSeconds--;
    if (timerSeconds <= 0) {
      timerSeconds = 0;
      clearInterval(timerInterval);
    }
    updateTimerText();
  }, 1000);
}

function updateTimerText() {
  const m = String(Math.floor(timerSeconds / 60)).padStart(2, "0");
  const s = String(timerSeconds % 60).padStart(2, "0");
  TIMER_ELEMENT.textContent = `${m}:${s}`;
}

// Yeni oyun
// Yeni oyun
async function newGame() {
  score = 0;
  SCORE_ELEMENT.textContent = "0";

  try {
    const res = await fetch("/api/new-game");
    if (!res.ok) throw new Error("API hatası");

    const data = await res.json();
    grid = data.grid;
    words = data.words;
    gridSize = data.gridSize;

    renderGrid();
    renderWordList();
    startTimer();
  } catch (e) {
    console.error("Oyun başlatılamadı:", e);
    alert("Backend'e bağlanılamadı. Lütfen Flask sunucusunu çalıştırın (python app.py).");
  }
}

NEW_GAME_BUTTON.addEventListener("click", () => {
  newGame();
});

TOGGLE_HINTS_BTN.addEventListener("click", () => {
  console.log("Toggle hints clicked");
  hintsVisible = !hintsVisible;
  const elements = document.querySelectorAll(".word-list .kana");
  elements.forEach(el => {
    // If parent is found, keep it revealed (handled by CSS .found .blur-text)
    // But we toggle the class anyway so it works for non-found
    if (hintsVisible) {
      el.classList.remove("blur-text");
    } else {
      el.classList.add("blur-text");
    }
  });
});

// İlk yükleme
newGame();
