"""Game-wide constants and per-level configuration."""
from __future__ import annotations

TILE = 32
SCREEN_W = 1024
SCREEN_H = 704
VIEW_W = SCREEN_W
VIEW_H = SCREEN_H
HUD_WIDTH = 0  # HUD is now an overlay
FPS = 60
DFS_RADAR_COOLDOWN = 300  # 5 seconds
DFS_RADAR_DURATION = 120  # 2 seconds visibility

# --- Colors (RGB) ---
BLACK       = (0, 0, 0)
WHITE       = (240, 240, 240)
GREY        = (90, 90, 95)
DARK_GREY   = (40, 40, 45)
WALL_DARK   = (24, 28, 46)
WALL_MID    = (56, 62, 92)
WALL_MORTAR = (38, 42, 64)
WALL_LIGHT  = (96, 106, 148)
WALL_MOSS   = (88, 130, 80)
WALL_SHADOW = (12, 14, 26)
FLOOR_DARK  = (32, 26, 22)
FLOOR_MID   = (60, 48, 38)
FLOOR_LIGHT = (96, 78, 58)
FLOOR_DIRT  = (110, 86, 60)
FLOOR_STONE = (130, 120, 100)
GRASS       = (78, 128, 70)
GRASS_DARK  = (45, 80, 45)
FLOWER_PINK = (245, 130, 180)
FLOWER_YEL  = (250, 220, 100)
PUDDLE      = (60, 90, 120)
LANTERN_GLOW = (255, 210, 120)
BLOOD       = (190, 40, 50)
GOLD        = (240, 200, 70)
GOLD_DARK   = (170, 120, 30)
SKIN        = (240, 200, 170)
HAIR        = (60, 40, 30)
SHIRT       = (50, 110, 200)
PANTS       = (40, 50, 80)
BOOTS       = (35, 25, 20)
DOG_FUR     = (210, 170, 110)
DOG_DARK    = (130, 90, 50)
THIEF_BODY  = (40, 40, 50)
THIEF_MASK  = (180, 30, 30)
TRAP_RED    = (200, 60, 60)
TRAP_DARK   = (90, 20, 20)
CAGE_BAR    = (160, 160, 170)
KEY_GLOW    = (255, 230, 120)
HEART_RED   = (220, 40, 60)
HEART_DARK  = (110, 20, 30)
PHONE_BG    = (18, 22, 32)
BUBBLE_HER  = (220, 100, 140)
BUBBLE_HIM  = (80, 140, 220)
HOUSE_ROOF  = (170, 60, 50)
HOUSE_ROOF_DARK = (110, 30, 30)
HOUSE_WALL  = (210, 180, 130)
HOUSE_WALL_DARK = (140, 100, 60)
HOUSE_DOOR  = (90, 50, 30)
HOUSE_GLOW  = (255, 220, 150)
PUPPY_FUR   = (240, 200, 140)
PUPPY_DARK  = (160, 120, 70)

# --- Player ---
PLAYER_SPEED   = 3.5  # pixels per frame
PLAYER_HP_MAX  = 3
INVULN_FRAMES  = 90    # ~1.5s at 60fps after taking damage

# --- Thief ---
THIEF_PATROL_SPEED = 1.6
THIEF_CHASE_SPEED  = 2.4
THIEF_VISION_RAD   = 5  # tiles; line-of-sight checked through walls
# Thieves stay out of (and cannot see into) the cells within this Manhattan
# distance of the player's spawn — the area near the entrance is "safe".
START_SAFE_ZONE    = 4

# --- Dragon (decorative, outside maze) ---
DRAGON_VISION_RAD  = 8   # tiles
DRAGON_FIRE_RATE   = 90  # frames between shots
DRAGON_FIRE_SPEED  = 3.2 # pixels/frame
DRAGON_FIRE_DAMAGE = 1

# --- Bat (decorative) ---
BAT_FLOAT_RADIUS   = 3   # tiles
BAT_FLOAT_SPEED    = 0.025  # radians/frame

# --- Puppy / Dog names ---
PUPPY_NAMES = ["Milu", "Lucky", "Cún Con", "Gấu Bông", "Bi"]
MOTHER_DOG_NAME = "Bông"

# --- Levels ---
# size must be odd so DFS maze gen has neat walls
# User request: L1=1 thief, L2=1 thief, L3=2, L4=2, L5=3
LEVELS = [
    {
        "name": "Khu vườn vắng",
        "size": 15,
        "thieves": 1,
        "keys": 1,
        "hideouts": 4,
        "bats": 2,
        "coins": 10,
        "dog_name": PUPPY_NAMES[0],
        "is_mother": False,
    },
    {
        "name": "Con hẻm bí ẩn",
        "size": 19,
        "thieves": 1,
        "keys": 2,
        "hideouts": 5,
        "bats": 4,
        "coins": 15,
        "dark": True,
        "dog_name": PUPPY_NAMES[1],
        "is_mother": False,
    },
    {
        "name": "Khu rừng hoang",
        "size": 23,
        "thieves": 2,
        "keys": 2,
        "hideouts": 5,
        "bats": 6,
        "coins": 20,
        "dog_name": PUPPY_NAMES[2],
        "is_mother": False,
    },
    {
        "name": "Hang động cổ đại",
        "size": 27,
        "thieves": 2,
        "keys": 3,
        "hideouts": 6,
        "bats": 8,
        "coins": 25,
        "dark": True,
        "dog_name": PUPPY_NAMES[3],
        "is_mother": False,
    },
    {
        "name": "Sào huyệt cuối cùng",
        "size": 31,
        "thieves": 3,
        "keys": 4,
        "hideouts": 8,
        "bats": 10,
        "coins": 30,
        "dog_name": MOTHER_DOG_NAME,
        "is_mother": True,
    },
]

# Vision radius (in tiles) when the level has dark fog
DARK_VIEW_RADIUS = 5
