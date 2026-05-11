# Cellrate

Cellrate is a long-term pygame game development project that documents the journey from basic movement experiments into a scalable arcade survival game.

The repository intentionally preserves the progression of ideas: each version adds a new layer of design, architecture, mechanics, or polish instead of hiding the learning path behind a single final code dump.

---

## Current Stage

**v0.5 - Round-Based Arcade Survival Refresh**

Cellrate has moved beyond the original single-loop prototype into a round-based survival game with level phases, smarter enemy behavior, richer collectibles, persistent run history, improved UI overlays, bot-controlled play, and a more production-ready package layout.

---

## Features

- Modular package architecture under `game/`
- Resizable pygame window with fullscreen support
- Menu, playing, bot, pause, transition, and game-over states
- Keyboard and mouse-driven UI interactions
- Round phases: intro, active collection, gemstone rush, and level transition
- Level rule system with progressive mechanics
- Player acceleration, drag, counter-braking, trails, slow effects, and invulnerability
- Coin collection with level-based scoring
- Gemstone bonus phase after round objectives
- Trap coins, magnetic coins, and invincibility pickups
- Wraparound movement on later levels
- Speed and slow zones for player and enemy movement
- Multiple enemy classes: standard, interceptor, and warden
- Enemy steering, separation, spawn spacing, and delayed reinforcements
- Smart bot mode with route scoring and hazard avoidance
- Persistent best score and top-run history
- In-game scoring details, shortcuts, and high-score overlays
- Audio system with music, sound toggles, volume controls, and silent fallbacks
- Cached background image rendering for resized windows
- Automated gameplay regression tests
- JavaScript bot simulation tool for experimentation

---

## Controls

- `WASD` / arrow keys: Move
- `Enter`: Select menu option
- `P`: Pause during a run
- `C`: Continue from pause
- `H`: Toggle shortcuts overlay
- `M`: Toggle music
- `N`: Toggle sound effects
- `[` / `]`: Adjust volume
- `F11`: Toggle fullscreen
- `Esc`: Back, close overlay, or quit depending on context

---

## Project Structure

```text
cellrate/
|-- assets/
|   |-- backgrounds/   # Background images
|   |-- music/         # Music tracks
|   `-- sounds/        # Sound effects
|-- game/
|   |-- bots/          # Smart bot decision-making
|   |-- core/          # Game loop, rounds, rules, scoring history
|   |-- entities/      # Player, enemies, collectibles, zones
|   |-- rendering/     # Background and scene rendering helpers
|   |-- systems/       # Audio and UI helpers
|   `-- config.py      # Shared constants/settings
|-- tests/             # Gameplay regression tests
|-- tools/             # Simulation and analysis utilities
|-- main.py            # Entry point
|-- requirements.txt   # Python dependencies
`-- README.md
```

Runtime score files such as `best_score.json` and `high_score_log.json` are generated locally and ignored by git.

---

## Running the Game

```bash
pip install -r requirements.txt
python main.py
```

To run the gameplay regression tests:

```bash
python -m unittest discover -s tests -v
```

---

## Development Philosophy

Cellrate is built as a game development journey. Earlier stages remain visible in the timeline so the project shows how simple pygame concepts evolved into more advanced systems.

The goal is not only to build a playable game, but also to document how movement, game loops, enemy behavior, UI, audio, architecture, AI, persistence, testing, and content systems mature over time.

---

## Learning Goals

This repository will continue to evolve through:

- Better game architecture
- Sprites and animation systems
- Enemy AI improvements
- Combat or defensive mechanics
- Procedural level generation
- Stronger UI and menu flows
- Save/load systems
- Content balancing
- Performance profiling and optimization
- Advanced pygame techniques
- Packaging and release workflows

---

## Version Timeline

### v0.1 - Player Movement Prototype

- Created the game window
- Added player movement
- Added fullscreen toggle
- Introduced an object-oriented structure

### v0.2 - First Gameplay Loop

- Added collectible coin system
- Added collision detection
- Added score tracking
- Added speed progression mechanic
- Added game reset system

### v0.3 - Enemy Bots and Survival Mechanics

- Added enemy entities
- Added enemy chase bots
- Added game over condition
- Added dynamic difficulty scaling
- Added multiple enemy spawning
- Improved the survival challenge loop

### v0.4 - Modular Architecture Refactor

- Refactored the project into multiple modules
- Added centralized configuration
- Added UI rendering helpers
- Added audio management
- Added scalable entity structure
- Added game states: menu, playing, and game over
- Organized assets into dedicated directories

### v1.0 - First Playable Arcade Prototype

This version marks the transition from a pygame learning project into a fully playable arcade survival prototype with scalable architecture, multiple gameplay systems, persistence, testing, and polished progression mechanics.

- Promoted the project into a package-based `game/` architecture
- Added level rules, round phases, and objective-based progression
- Added gemstone rush phases and level-scaled scoring
- Added trap coins, magnetic coins, invincibility pickups, and speed zones
- Added enemy classes with steering, separation, interception, and warden behavior
- Added delayed enemy reinforcements and safer spawn logic
- Added smart bot mode with tactical route scoring
- Added persistent best-score and run-history systems
- Added in-game overlays for shortcuts, scoring rules, pause controls, and top scores
- Added background image rendering, player trails, collectible glow effects, and fade transitions
- Added automated gameplay tests and a bot simulation utility

---

Future versions will continue evolving Cellrate from a strong prototype into a more complete arcade game.
