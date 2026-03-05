# Quiz Blitz V3 — Complete Build Blueprint

## Live Site: https://shadowquizblitz.netlify.app
## Repo: https://github.com/ShadowHunter947/QuizBlitz

---

## PROJECT CONTEXT

Quiz Blitz is a trivia PWA currently deployed as a single `index.html` file.
V2 (current) has: 5 categories × 10 easy + 10 hard questions, 8 unlockable themes,
XP leveling system, sound engine (Web Audio API), animated category backgrounds,
service worker for offline caching.

V3 adds: Expanded questions, Perfect 10 trivia rewards, Snake & Ladder mini-game,
currency system, and improved UI illumination.

**IMPORTANT**: V3 should still be a single index.html (PWA). All code inline.
The current architecture uses React via CDN + Babel transpilation in-browser.
Keep this architecture — don't switch to a build system.

---

## FEATURE 1: ILLUMINATED QUESTION AREA ✅ DONE IN V2.1

Cards now use `linear-gradient` backgrounds with higher opacity (~F0-F8),
`backdropFilter: blur(12px)`, subtle `boxShadow` glow from category color,
and `inset` top highlight for depth.

---

## FEATURE 2: EXPANDED QUESTION BANK

### Structure
Triple the questions: 20 easy + 15 hard per category = 175 total questions.

### Progressive Difficulty
- Levels 1-9: Easy questions only, 12s timer
- Levels 10-19: Mix of easy + some hard, 12s timer
- Levels 20+: Full hard pool mixed in, 10s timer
- Levels 30+: Hard questions only, 8s timer (ultra mode)

### Question Format (same as current)
```javascript
{ q: "Question text?", opts: ["A", "B", "C", "D"], a: 1 } // a = correct index
```

### New Questions to Add (examples per category)

**Science (add 10 easy + 5 hard)**
Easy: periodic table elements, basic anatomy, animal facts, weather, ecosystems
Hard: quantum physics, organic chemistry, astrophysics, genetics, neuroscience

**History (add 10 easy + 5 hard)**
Easy: famous leaders, wars basics, inventions, ancient civilizations
Hard: specific treaties, lesser-known empires, economic history, cultural movements

**Geography (add 10 easy + 5 hard)**
Easy: flags, capitals, famous landmarks, oceans, deserts
Hard: tectonic plates, demographics, geopolitics, obscure borders

**Pop Culture (add 10 easy + 5 hard)**
Easy: recent movies, viral internet, gaming basics, music artists
Hard: film history, literary references, indie games, music theory

**Tech (add 10 easy + 5 hard)**
Easy: social media facts, gadget history, basic programming concepts
Hard: cryptography, networking protocols, compiler theory, ML concepts

---

## FEATURE 3: PERFECT 10 TRIVIA REWARD SYSTEM

### How It Works
1. Player answers all 10 questions correctly in a single round (any category)
2. Celebration screen appears with extra animations
3. A "UNLOCK TRIVIA PAGE" button appears
4. Clicking it shows a beautifully designed 2-page illustrated trivia article
5. Bonus XP: `currentLevel * 20` XP awarded

### Trivia Page Content (per category, 3 topics each, randomly picked)

**Science:**
- "The Double Helix: How DNA Was Discovered" — Watson, Crick, Franklin story
- "Black Holes: Where Even Light Cannot Escape" — Event horizons, Hawking radiation
- "CRISPR: Editing the Code of Life" — Gene editing revolution

**History:**
- "The Colosseum: Rome's Arena of Death" — Gladiators, engineering, politics
- "Silk Road: The Highway That Connected the World" — Trade, culture, Marco Polo
- "The Library of Alexandria: Lost Knowledge" — Ancient scholars, the fire

**Geography:**
- "Ring of Fire: Earth's Most Explosive Belt" — Volcanoes, tectonic plates, Pacific
- "The Mariana Trench: Deepest Place on Earth" — Exploration, creatures, pressure
- "Aurora Borealis: Nature's Light Show" — Solar wind, magnetosphere

**Pop Culture:**
- "Christopher Nolan: The Architect of Dreams" — Inception, Interstellar, filmmaking
- "The Evolution of Video Games" — Pong to VR, industry growth
- "Studio Ghibli: Japan's Animation Treasure" — Miyazaki, storytelling

**Tech:**
- "The Birth of the Internet" — ARPANET, TCP/IP, Tim Berners-Lee
- "How AI Learns: Neural Networks Explained" — Perceptrons to transformers
- "Cryptography: The Art of Secret Messages" — Caesar cipher to RSA

### UI Design for Trivia Pages
```jsx
// Trivia page component structure
const TriviaReward = ({ topic, category, onClose, theme }) => {
  // Full-screen overlay with scroll
  // Page 1: Title + hero illustration (SVG/CSS art) + intro paragraph
  // Page 2: 3-4 "Did you know?" facts with small illustrations
  // Close button returns to result screen
  // Illustrations should be SVG-drawn (same style as category backgrounds)
  
  return (
    <div style={{position:'fixed',inset:0,background:theme.bg,zIndex:200,overflowY:'auto'}}>
      {/* Header with category icon + "PERFECT 10!" badge */}
      {/* Hero SVG illustration matching the topic */}
      {/* Title in Dela Gothic One font */}
      {/* 2-3 paragraphs of interesting content */}
      {/* "Fun Facts" section with 3-4 bite-sized facts */}
      {/* XP bonus display */}
      {/* Close button */}
    </div>
  );
};
```

### State Changes Needed
```javascript
const [showTrivia, setShowTrivia] = useState(false);
const [triviaContent, setTriviaContent] = useState(null);
const [unlockedTrivia, setUnlockedTrivia] = useState([]); // saved to localStorage

// In result screen: if correct === questions.length (perfect 10)
// Show unlock button, pick random topic for that category
// Award bonus XP: level * 20
```

---

## FEATURE 4: SNAKE & LADDER MINI-GAME

### Core Mechanics
- 10×10 board (100 squares), numbered 1-100
- Classic snakes (slide down) and ladders (climb up)
- Player vs AI opponent
- Dice roll (1-6) with animation
- Turn-based: player rolls, moves, then AI rolls, moves
- First to reach 100 wins

### Board Layout
```javascript
const SNAKES = {
  99: 54, 95: 72, 92: 51, 83: 19, 73: 1, 
  64: 36, 48: 9, 44: 22, 32: 10, 16: 4
};
const LADDERS = {
  2: 38, 7: 14, 8: 31, 15: 26, 21: 42,
  28: 84, 36: 44, 51: 67, 71: 91, 78: 98
};
```

### AI Behavior
AI simply rolls dice and moves. No cheating. Random dice rolls.
Add slight delay (1-2s) between AI actions for dramatic effect.

### UI Design
```
┌──────────────────────────────┐
│  🎲 Snake & Ladder           │
│  ┌─────────────────────────┐ │
│  │ 10x10 grid board        │ │
│  │ Snakes: red gradient    │ │
│  │ Ladders: green/gold     │ │  
│  │ Player: teal token      │ │
│  │ AI: red/orange token    │ │
│  └─────────────────────────┘ │
│                              │
│  You: Square 45  |  AI: 38  │
│  🎲 [ROLL DICE]             │
│  Last roll: 5               │
│                              │
│  💰 Prize: 50-200 coins     │
│  ⏰ Next game in: 45:23     │
└──────────────────────────────┘
```

### Board Rendering (CSS Grid)
```jsx
const SnakeLadderGame = ({ theme, onClose, onWin }) => {
  const [playerPos, setPlayerPos] = useState(0);
  const [aiPos, setAiPos] = useState(0);
  const [dice, setDice] = useState(null);
  const [isPlayerTurn, setIsPlayerTurn] = useState(true);
  const [rolling, setRolling] = useState(false);
  const [gameOver, setGameOver] = useState(false);
  const [winner, setWinner] = useState(null);
  const [moveLog, setMoveLog] = useState([]);

  const rollDice = () => {
    if (rolling || !isPlayerTurn || gameOver) return;
    setRolling(true);
    sfx.click();
    
    // Dice animation: show random numbers rapidly for 0.8s
    let count = 0;
    const anim = setInterval(() => {
      setDice(Math.ceil(Math.random() * 6));
      count++;
      if (count > 8) {
        clearInterval(anim);
        const final = Math.ceil(Math.random() * 6);
        setDice(final);
        movePlayer(final);
      }
    }, 100);
  };

  const movePlayer = (roll) => {
    let newPos = playerPos + roll;
    if (newPos > 100) { setRolling(false); setIsPlayerTurn(false); doAiTurn(); return; }
    if (newPos === 100) { setPlayerPos(100); endGame('player'); return; }
    
    // Check snakes/ladders
    if (SNAKES[newPos]) { newPos = SNAKES[newPos]; sfx.wrong(); }
    else if (LADDERS[newPos]) { newPos = LADDERS[newPos]; sfx.correct(); }
    
    setPlayerPos(newPos);
    setRolling(false);
    setIsPlayerTurn(false);
    setTimeout(() => doAiTurn(), 1500);
  };

  const doAiTurn = () => {
    // Similar logic for AI
    // Add 1.5s delay for suspense
    // Then switch back to player turn
  };

  const endGame = (who) => {
    setGameOver(true);
    setWinner(who);
    const coins = who === 'player' 
      ? 100 + Math.max(0, (100 - aiPos)) // more coins if AI was far behind
      : 20; // consolation coins even on loss
    onWin(coins);
  };

  // Board rendering: 10x10 grid
  // Row direction alternates (boustrophedon - snake pattern)
  // Row 0 (bottom): left to right (1-10)
  // Row 1: right to left (11-20)
  // etc.
  
  const getSquarePosition = (num) => {
    const row = Math.floor((num - 1) / 10);
    const col = row % 2 === 0 ? (num - 1) % 10 : 9 - (num - 1) % 10;
    return { row: 9 - row, col }; // flip so 1 is at bottom-left
  };

  return (
    <div style={{position:'fixed',inset:0,background:theme.bg,zIndex:200,overflowY:'auto'}}>
      {/* Header: back button + title + coin display */}
      {/* 10x10 grid board */}
      {/* Snakes drawn as SVG curves in red */}
      {/* Ladders drawn as SVG in gold/green */}
      {/* Player tokens as colored circles */}
      {/* Dice display + roll button */}
      {/* Move log showing last 5 moves */}
      {/* Game over overlay with coin reward */}
    </div>
  );
};
```

### 1-Hour Cooldown
```javascript
const COOLDOWN_MS = 60 * 60 * 1000; // 1 hour
// In localStorage: save lastSnakeLadderTime
// On mount: check if Date.now() - lastTime >= COOLDOWN_MS
// If not: show countdown timer "Next game in: MM:SS"
// If yes: show "PLAY" button

const [cooldownLeft, setCooldownLeft] = useState(0);
useEffect(() => {
  const last = parseInt(localStorage.getItem('sl_last_play') || '0');
  const remaining = Math.max(0, COOLDOWN_MS - (Date.now() - last));
  setCooldownLeft(remaining);
  if (remaining > 0) {
    const interval = setInterval(() => {
      const r = Math.max(0, COOLDOWN_MS - (Date.now() - last));
      setCooldownLeft(r);
      if (r <= 0) clearInterval(interval);
    }, 1000);
    return () => clearInterval(interval);
  }
}, []);
```

### Reward Calculation
```javascript
// Win: 100 base + bonus based on how far ahead you are
// coins = 100 + max(0, floor((100 - aiPos) / 2))
// Max possible: ~150 coins per win
// Loss: 20 consolation coins
// Perfect win (AI never passed 50): 200 coins
```

---

## FEATURE 5: CURRENCY SYSTEM

### State
```javascript
const [coins, setCoins] = useState(save?.coins || 0);
// Save to localStorage alongside other save data
```

### Earning Coins
- Snake & Ladder wins: 100-200 coins
- Snake & Ladder losses: 20 coins
- Perfect 10 in trivia: 50 coins bonus

### Spending Coins (Theme Unlock Alternative)
Themes can now be unlocked EITHER by level OR by coins:
```javascript
const THEME_PRICES = {
  ocean: 300,
  aurora: 600,
  sakura: 900,
  golden: 1200,
  neon: 1500,
  matrix: 2000,
};

// In theme shop, show:
// "🔒 Unlock at Level 5 OR 💰 300 coins [BUY]"
```

### UI Changes
- Show coin count in header/menu: `💰 {coins}`
- Theme shop shows coin prices alongside level requirements
- Snake & Ladder accessible from main menu with cooldown timer

---

## FEATURE 6: IMPROVED OFFLINE MODE

### Current Status
Service worker already caches all assets. Since the entire app is one HTML file
with CDN scripts, offline mode requires caching the CDN URLs too.

### Changes Needed
Update `sw.js` ASSETS array:
```javascript
const ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  'https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&family=Dela+Gothic+One&display=swap',
  'https://unpkg.com/react@18/umd/react.production.min.js',
  'https://unpkg.com/react-dom@18/umd/react-dom.production.min.js',
  'https://unpkg.com/@babel/standalone/babel.min.js',
];
```

### Strategy
Use stale-while-revalidate for CDN resources:
```javascript
self.addEventListener('fetch', e => {
  if (e.request.url.includes('unpkg.com') || e.request.url.includes('fonts.googleapis.com')) {
    // Cache-first for CDN resources
    e.respondWith(caches.match(e.request).then(r => r || fetch(e.request).then(res => {
      const clone = res.clone();
      caches.open(CACHE_NAME).then(c => c.put(e.request, clone));
      return res;
    })));
  } else {
    // Network-first for app files
    e.respondWith(fetch(e.request).then(res => {
      const clone = res.clone();
      caches.open(CACHE_NAME).then(c => c.put(e.request, clone));
      return res;
    }).catch(() => caches.match(e.request)));
  }
});
```

---

## FEATURE 7: UNIQUE LOGO ✅ DONE

New logo generated with Pillow: lightning bolt with teal glow ring on dark background.
Files: icon-192.png, icon-512.png, logo-1024.png
Can be improved with a proper design tool if needed.

---

## MAIN MENU RESTRUCTURE

The main menu needs a new layout to accommodate Snake & Ladder:

```
┌──────────────────────────┐
│     ⚡ QUIZ BLITZ        │
│                          │
│  [Level Bar + XP]  💰245 │
│                          │
│  ┌────────┐ ┌──────────┐│
│  │ 🎨     │ │ 🎲 Snake │ │
│  │ Themes │ │ & Ladder │ │
│  │        │ │ ⏰ 34:21 │ │
│  └────────┘ └──────────┘ │
│                          │
│  🧬 Science    → PLAY    │
│  🏛️ History    → PLAY    │
│  🌍 Geography  → PLAY    │
│  🎬 Pop Culture→ PLAY    │
│  💻 Tech       → PLAY    │
│                          │
│  [🔀 MIXED BLITZ]       │
└──────────────────────────┘
```

---

## APP SCREENS FLOW

```
MENU ──→ CATEGORY GAME ──→ RESULT ──→ TRIVIA REWARD (if perfect 10)
  │                                       │
  ├──→ THEME SHOP (buy with coins/level)  │
  │                                       │
  └──→ SNAKE & LADDER ──→ REWARD SCREEN ──┘
         (1hr cooldown)    (coins awarded)
```

---

## LOCALSTORAGE SAVE STRUCTURE

```javascript
{
  hs: 2450,           // high score
  tp: 15,             // total played
  tid: "midnight",    // theme id
  lvl: 8,             // level
  xp: 45,             // current xp
  soundOn: true,
  coins: 340,         // currency
  unlockedTrivia: ["science_dna", "history_colosseum"],  // seen trivia
  unlockedThemes: ["ocean"],  // themes bought with coins
  slLastPlay: 1709900000000,  // snake & ladder last play timestamp
  slWins: 3,          // snake & ladder total wins
  slLosses: 1,
  perfectTens: { Science: 2, History: 1 },  // perfect 10 counts
}
```

---

## IMPLEMENTATION ORDER (for Claude Code)

1. **Expand question bank** (add 50+ new questions across categories)
2. **Add currency state** (coins in save, display in UI)
3. **Update theme shop** (add coin purchase option)
4. **Build Snake & Ladder** (board, dice, AI, animations, cooldown)
5. **Build Perfect 10 reward** (detection, trivia content, display)
6. **Update service worker** (better offline caching)
7. **Polish** (transitions between screens, sound effects for new features)

---

## PROMPT TO GIVE CLAUDE CODE

Copy this entire file, then say:

"I have a trivia PWA game called Quiz Blitz. Here is the current deployed code
at /path/to/index.html and the V3 blueprint. Please implement all features
described in the blueprint. Keep it as a single index.html PWA file. 
Use the existing architecture (React via CDN + Babel, Web Audio API for sounds,
localStorage for saves). Start with the question bank expansion, then Snake & 
Ladder, then Perfect 10 rewards, then currency system."

---

## KEY TECHNICAL NOTES

- All React uses `React.createElement` or JSX via Babel in-browser transpilation
- Sounds use the `SoundEngine` class (Web Audio API oscillators, no files)
- Themes are objects with color values, applied via inline styles
- Category backgrounds are React components returning SVG/HTML
- All state lives in the main `App` component
- localStorage used for persistence (check for errors, key: "quiz_blitz_save")
- Service worker at /sw.js handles offline caching
- Deployed on Netlify with auto-deploy from GitHub
