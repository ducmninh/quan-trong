# Dog Rescue Game - Giai Cuu Dan Cho

A pixel-art maze game built with Python and Pygame where you rescue a family of dogs from thieves!

## Story
Bong (mother dog) and her 5 puppies have been stolen by dog thieves and locked in cages across 5 increasingly difficult maze levels. Navigate each maze, collect keys to unlock cages, avoid thieves, and bring the dogs home safely!

## Features
- **5 Levels** with increasing difficulty (maze size, thief count, complexity)
- **5 Puppies + Mother Dog (Bong)** — rescue one dog per level
- **Shop System** — buy upgrades between levels: speed boost, gun, time freeze, teleportation
- **Gold Coins** scattered across maps for currency
- **Thief AI** using BFS patrol and A* chase pathfinding
- **DFS Radar** ability to find keys
- **Decorative Animals** — fire-breathing dragons and bats outside/inside mazes
- **Background Music** — unique synthesized tracks per level
- **Dark Levels** with limited visibility
- **3 Playable Characters** — Boy, Girl, Ninja

## Controls
- **WASD / Arrow Keys** — Move
- **E** — Interact (open cage)
- **G** — DFS Radar (find nearest key)
- **T** — Teleport to hideout (if purchased)
- **Q** — Time freeze 5 seconds (if purchased)
- **Enter** — Shoot (if gun purchased)
- **F** — Toggle fullscreen
- **Esc** — Back to title

## Level Difficulty
| Level | Maze Size | Thieves | Dog to Rescue |
|-------|-----------|---------|---------------|
| 1     | 15x15     | 1       | Milu (puppy)  |
| 2     | 19x19     | 1       | Lucky (puppy) |
| 3     | 23x23     | 2       | Cun Con (puppy)|
| 4     | 27x27     | 2       | Gau Bong (puppy)|
| 5     | 31x31     | 3       | Bong (mother) |

## Installation
```bash
pip install pygame
python main.py
```

## Requirements
- Python >= 3.10
- Pygame >= 2.5
