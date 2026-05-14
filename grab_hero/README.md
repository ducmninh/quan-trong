# Grab Hero — Giải Cứu Chú Chó

A complete 4-level top-down pygame action game where you play a Grab driver
turned hero, rescuing a kidnapped dog from a gang of thieves, zombies,
tigers and a final boss.

## Quick start

```bash
pip install pygame
python main.py
```

Tested with **Python 3.12** and **pygame 2.6.1**.

## Controls

| Key | Action |
|-----|--------|
| **WASD** / **Arrow keys** | Move |
| **Mouse** | Aim |
| **Left click (hold)** | Fire |
| **R** | Reload |
| **Shift** | Run (uses stamina) |
| **Space** | Dodge roll (i-frames) |
| **1-7** | Switch to weapon in slot |
| **Q / E** / **Mouse wheel** | Cycle weapon (E also opens shop when nearby) |
| **F** | Get on/off bike (level 1 only — uses parked bike sprite) |
| **Tab** | Big map |
| **ESC** | Pause |

## Game design

- **Level 1 — Khu Dân Cư**: open suburban map with houses, roads, parked
  cars and gold scattered around. Zombies and knife-wielding thieves try
  to stop you. Mini-boss: *Trộm Đầu Sỏ*.
- **Level 2 — Phố Cổ Bỏ Hoang**: ruined downtown with abandoned cars and
  rubble. A gas station serves as the **shop** where you can buy your
  first new weapons (Pistol Mk II, SMG, Shotgun) and upgrade them. Faster
  zombies, pistol thieves, wild dogs. Mini-boss: *Zombie Bự Con* (slam
  AOE attack).
- **Level 3 — Khu Công Nghiệp**: container yard with industrial machines
  and crates that drop loot when shot. A warehouse office hosts the
  **second shop** with the AR, Sniper and Grenade Launcher. SMG minions
  and snipers at long range. Mini-boss: *Hổ Vương* (fast charge + roar
  AOE).
- **Level 4 — Hang Ổ Trùm**: walled mansion compound — outer yard with
  tigers, inner courtyard with the dog cage and the final boss *Trùm
  Trộm* (3 phases — spawns tigers at 66 % HP, shotgun minions at 33 %).

## Weapons

| Weapon | DMG | RPS | Mag | Special | Price |
|--------|----:|----:|----:|---------|------:|
| Pistol | 18 | 4 | 12 | infinite reserve | starter |
| Pistol Mk II | 28 | 6 | 15 | infinite reserve | 200 |
| SMG | 12 | 14 | 30 | spread | 400 |
| Shotgun | 10 | 1.2 | 6 | 7 pellets | 600 |
| Assault Rifle | 24 | 9 | 30 | accurate auto | 900 |
| Sniper | 140 | 0.8 | 5 | one-shot most enemies | 1500 |
| Grenade Launcher | 80 | 0.9 | 4 | 140 px AOE | 2200 |

Each weapon can be upgraded **3 levels** in:
- **Damage** (+30 % per level)
- **Fire rate** (+20 % per level)
- **Magazine size** (+40 % per level)

## Project structure

```
grab_hero/
├── main.py            # Game loop / scene manager
├── settings.py        # All tunables (HP, speeds, weapon stats, …)
├── utils.py           # Helpers: Vec, color, sprite cache, draw_text
├── camera.py          # Smooth follow camera with screen shake
├── world.py           # Tile map + collidable solids + pickups + decals
├── player.py          # Player: walk/run/dodge/bike/shoot
├── enemies.py         # All enemy types & boss AI
├── weapons.py         # Weapon definitions + bullets
├── hud.py             # HP bar, gold, ammo, minimap, boss bar
├── shop.py            # In-game shop overlay
├── levels.py          # 4 hand-designed level builders
├── particles.py       # Blood / muzzle / explosion / floating text
└── assets/sprites/    # Player + bike pixel art (provided)
```

## Credits

- Player & bike sprites: provided by user.
- Everything else: drawn procedurally with pygame primitives.
