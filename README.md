# Cellrate

A long-term pygame game development project documenting my journey from learning pygame basics to building a scalable game architecture.

---

# Current Stage
Modular survival game prototype with enemy bots, UI systems, and audio integration

---

# Features
- OOP-based architecture
- Modular project structure
- Player movement system
- Enemy chase bot
- Coin collection gameplay loop
- Dynamic difficulty scaling
- Progressive enemy spawning
- Game states (Menu / Playing / Game Over)
- Audio system (sound + music)
- UI rendering system
- Screen boundary collision
- Resizable window
- Fullscreen support
- Score system
- Reset/restart mechanics

---

# Controls
- WASD / Arrow Keys → Move
- ENTER → Start Game
- F11 → Toggle fullscreen
- ESC → Quit

---

# Project Structure

cellrate/
│
├── core/        # Main game loop and state management
├── entities/    # Player, enemies, collectibles
├── systems/     # UI and audio systems
├── assets/      # Sounds and music
└── config.py    # Shared constants/settings

---

# Development Philosophy

This repository intentionally preserves each stage of development to document the evolution from beginner pygame experiments into a scalable game project.

Rather than jumping directly into advanced architecture, each version reflects the concepts being learned and implemented at that stage.

---

# Learning Goals
This repository will gradually evolve through:
- Better game architecture
- Sprites and animations
- Enemy bots improvements
- Combat systems
- Procedural generation
- Advanced UI systems
- Save/load systems
- Optimization
- Advanced pygame techniques

---

# Version Timeline

## v0.1 — Player Movement Prototype
- Created game window
- Added player movement
- Added fullscreen toggle
- Introduced OOP structure

## v0.2 — First Gameplay Loop
- Added collectible coin system
- Added collision detection
- Added score tracking
- Added speed progression mechanic
- Added game reset system

## v0.3 — Enemy bots and Survival Mechanics
- Added enemy entities
- Added enemy chase bots
- Added game over condition
- Added dynamic difficulty scaling
- Added multiple enemy spawning
- Improved gameplay challenge loop

## v0.4 — Modular Architecture Refactor
- Refactored project into multiple modules
- Added centralized configuration system
- Added UI rendering system
- Added audio management system
- Added scalable entity structure
- Added game state system (Menu / Playing / Game Over)
- Organized assets into dedicated directories

---

Future versions will progressively evolve into a complete game.