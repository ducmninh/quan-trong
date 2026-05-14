"""Global settings and constants for Grab Hero."""
from pathlib import Path

# ============================================================
# WINDOW
# ============================================================
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "GRAB HERO — Giải Cứu Chú Chó"

# ============================================================
# PATHS
# ============================================================
ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
SPRITES = ASSETS / "sprites"

# ============================================================
# COLORS
# ============================================================
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 50, 50)
DARK_RED = (140, 20, 20)
GREEN = (50, 200, 80)
GRAB_GREEN = (0, 175, 81)
DARK_GREEN = (0, 110, 50)
YELLOW = (255, 215, 0)
GOLD = (255, 200, 50)
GRAY = (90, 90, 90)
DARK_GRAY = (45, 45, 45)
LIGHT_GRAY = (170, 170, 170)
BROWN = (110, 70, 40)
DARK_BROWN = (70, 45, 25)
BLUE = (60, 120, 220)
SAND = (215, 195, 145)
ROAD = (55, 55, 60)
ROAD_LINE = (230, 220, 100)
GRASS = (70, 130, 60)
GRASS_DARK = (55, 105, 45)
CONCRETE = (165, 165, 160)
DIRT = (130, 95, 65)
WATER = (60, 110, 180)
ROOF_RED = (165, 60, 50)
ROOF_BLUE = (70, 100, 160)
WALL_TAN = (215, 195, 160)
WALL_WHITE = (245, 240, 230)
NEON_PINK = (255, 80, 170)
NEON_CYAN = (80, 230, 255)

# ============================================================
# WORLD
# ============================================================
TILE = 48                     # tile size px
WORLD_W_TILES = 80            # default world dimensions
WORLD_H_TILES = 60
PLAYER_SCALE = 1.5            # sprite scale on top-down (sprites are 1024px, scale down hugely)
PLAYER_SIZE = 56              # rendered size after downscale
BIKE_SIZE = 72

# ============================================================
# GAMEPLAY
# ============================================================
PLAYER_MAX_HP = 150
PLAYER_WALK_SPEED = 220       # px/s
PLAYER_RUN_SPEED = 360
PLAYER_BIKE_SPEED = 480
PLAYER_BIKE_DAMAGE = 50
DODGE_SPEED = 720
DODGE_DURATION = 0.35
DODGE_COOLDOWN = 1.0
STAMINA_MAX = 100
STAMINA_DRAIN = 30            # per second while running
STAMINA_REGEN = 25            # per second while not running

STARTING_GOLD = 50

# ============================================================
# WEAPONS
# Each weapon: name, damage, fire_rate (shots/sec), bullet_speed,
# mag, reload_time, spread (degrees), pellets, price, color
# ============================================================
WEAPONS = {
    "pistol": dict(
        name="Pistol", damage=18, fire_rate=4.0, bullet_speed=900,
        mag=12, reload_time=1.2, spread=2, pellets=1,
        price=0, ammo_reserve=9999, color=(230, 230, 230),
    ),
    "pistol_mk2": dict(
        name="Pistol Mk II", damage=28, fire_rate=6.0, bullet_speed=1000,
        mag=15, reload_time=1.0, spread=1, pellets=1,
        price=200, ammo_reserve=9999, color=(240, 230, 130),
    ),
    "smg": dict(
        name="SMG", damage=12, fire_rate=14.0, bullet_speed=950,
        mag=30, reload_time=1.4, spread=6, pellets=1,
        price=400, ammo_reserve=120, color=(180, 180, 200),
    ),
    "shotgun": dict(
        name="Shotgun", damage=10, fire_rate=1.2, bullet_speed=820,
        mag=6, reload_time=1.8, spread=14, pellets=7,
        price=600, ammo_reserve=36, color=(200, 140, 80),
    ),
    "ar": dict(
        name="Assault Rifle", damage=24, fire_rate=9.0, bullet_speed=1050,
        mag=30, reload_time=1.6, spread=3, pellets=1,
        price=900, ammo_reserve=180, color=(120, 180, 90),
    ),
    "sniper": dict(
        name="Sniper", damage=140, fire_rate=0.8, bullet_speed=1600,
        mag=5, reload_time=2.0, spread=0, pellets=1,
        price=1500, ammo_reserve=20, color=(80, 110, 180),
    ),
    "grenade": dict(
        name="Grenade Launcher", damage=80, fire_rate=0.9, bullet_speed=600,
        mag=4, reload_time=2.2, spread=0, pellets=1, aoe=140,
        price=2200, ammo_reserve=12, color=(220, 100, 50),
    ),
}

# Weapons available in each shop
SHOP_LEVEL2 = ["pistol_mk2", "smg", "shotgun"]
SHOP_LEVEL3 = ["ar", "sniper", "grenade"]

# Upgrade prices (per tier 1->3)
UPGRADE_DAMAGE_PRICE = [150, 300, 500]
UPGRADE_FIRERATE_PRICE = [150, 300, 500]
UPGRADE_MAG_PRICE = [120, 240, 400]

# ============================================================
# ENEMIES
# ============================================================
ENEMY_DEFS = {
    "zombie": dict(
        name="Zombie", hp=30, speed=70, dmg=6, attack_range=44, attack_cd=1.1,
        ranged=False, gold=(5, 10), color=(80, 130, 70), size=42, sight=480,
    ),
    "zombie_fast": dict(
        name="Zombie Chạy", hp=28, speed=170, dmg=7, attack_range=44, attack_cd=0.7,
        ranged=False, gold=(8, 14), color=(160, 80, 60), size=40, sight=560,
    ),
    "thief_knife": dict(
        name="Trộm Dao", hp=45, speed=140, dmg=12, attack_range=48, attack_cd=0.8,
        ranged=False, gold=(12, 18), color=(60, 60, 80), size=44, sight=600,
    ),
    "thief_pistol": dict(
        name="Trộm Súng Lục", hp=60, speed=115, dmg=10, attack_range=520, attack_cd=1.2,
        ranged=True, bullet_speed=620, gold=(20, 30), color=(70, 50, 90), size=44, sight=720,
    ),
    "minion_smg": dict(
        name="Đồ Đệ SMG", hp=85, speed=125, dmg=8, attack_range=540, attack_cd=0.18,
        burst=4, ranged=True, bullet_speed=680, gold=(40, 60), color=(120, 30, 30), size=46, sight=780,
    ),
    "sniper": dict(
        name="Trộm Sniper", hp=55, speed=70, dmg=35, attack_range=900, attack_cd=2.2,
        ranged=True, bullet_speed=1400, gold=(50, 80), color=(40, 60, 100), size=44, sight=1100,
    ),
    "wild_dog": dict(
        name="Chó Hoang", hp=22, speed=240, dmg=8, attack_range=40, attack_cd=0.6,
        ranged=False, gold=(4, 8), color=(150, 110, 70), size=34, sight=620,
    ),
    "tiger": dict(
        name="Hổ", hp=160, speed=260, dmg=22, attack_range=52, attack_cd=0.8,
        ranged=False, gold=(70, 110), color=(230, 140, 40), size=64, sight=900,
    ),
    "minion_shotgun": dict(
        name="Đồ Đệ Shotgun", hp=110, speed=120, dmg=14, attack_range=320, attack_cd=1.1,
        ranged=True, bullet_speed=700, pellets=5, spread=20, gold=(55, 85),
        color=(150, 60, 30), size=48, sight=700,
    ),
    # Bosses
    "boss1": dict(
        name="Trộm Đầu Sỏ", hp=180, speed=140, dmg=18, attack_range=480, attack_cd=1.0,
        ranged=True, bullet_speed=620, gold=(120, 160), color=(80, 30, 30), size=64, sight=1000,
        is_boss=True,
    ),
    "boss2": dict(
        name="Zombie Bự Con", hp=420, speed=90, dmg=26, attack_range=80, attack_cd=1.4,
        ranged=False, slam=True, gold=(200, 260), color=(50, 110, 50), size=92, sight=900,
        is_boss=True,
    ),
    "boss3": dict(
        name="Hổ Vương", hp=520, speed=290, dmg=28, attack_range=64, attack_cd=0.7,
        ranged=False, gold=(300, 380), color=(255, 130, 30), size=96, sight=1100,
        is_boss=True,
    ),
    "boss_final": dict(
        name="Trùm Trộm", hp=950, speed=140, dmg=22, attack_range=500, attack_cd=0.6,
        ranged=True, bullet_speed=720, pellets=3, spread=12, gold=(0, 0),
        color=(120, 0, 40), size=100, sight=1300, is_boss=True,
    ),
}

# ============================================================
# UI
# ============================================================
FONT_PATH = None              # use default
HUD_HP_W = 280
HUD_HP_H = 22
HUD_PAD = 16

# ============================================================
# CAMERA / EFFECTS
# ============================================================
SHAKE_HIT = 6
SHAKE_EXPLODE = 18
SHAKE_DECAY = 80              # units/sec

# ============================================================
# HUB / SẢNH — PERSISTENT CHARACTER UPGRADES
# ============================================================
# Each upgrade has 5 levels. Cost rises per level.
# Effects are applied to the player every time they leave the hub.
CHAR_UPGRADES = {
    "speed": dict(
        name="Tốc Độ Chạy",
        desc="+5% tốc độ đi/chạy mỗi cấp",
        max_level=5,
        cost=(80, 160, 260, 380, 520),
        per_level=0.05,           # +5% movement speed per level
        color=(120, 230, 120),
    ),
    "fire_rate": dict(
        name="Tốc Độ Bắn",
        desc="+5% RPS mọi súng / cấp",
        max_level=5,
        cost=(100, 200, 320, 460, 620),
        per_level=0.05,           # +5% fire rate per level
        color=(255, 200, 80),
    ),
    "damage": dict(
        name="Sát Thương",
        desc="+10% damage mọi súng / cấp",
        max_level=5,
        cost=(140, 260, 400, 560, 760),
        per_level=0.10,           # +10% damage per level
        color=(230, 90, 90),
    ),
    "max_hp": dict(
        name="Máu Tối Đa",
        desc="+30 HP tối đa / cấp",
        max_level=5,
        cost=(120, 220, 340, 480, 640),
        per_level=30,             # +30 max HP per level
        color=(220, 110, 110),
    ),
    "stamina": dict(
        name="Thể Lực",
        desc="+20 stamina tối đa / cấp",
        max_level=5,
        cost=(60, 120, 200, 300, 420),
        per_level=20,             # +20 max stamina per level
        color=(120, 200, 255),
    ),
}

# Order shown in the hub upgrade panel
CHAR_UPGRADE_ORDER = ["speed", "fire_rate", "damage", "max_hp", "stamina"]


# ============================================================
# HUB / SẢNH — PETS
# ============================================================
PETS = {
    "dog": dict(
        name="Chó Nhỏ",
        emoji="🐶",
        desc="Đi theo chủ, cắn enemy gần",
        price=500,
        size=24,
        color=(200, 160, 100),
        speed=320,           # px/s (a little faster than walk)
        attack_range=70,     # melee reach
        attack_cd=0.7,
        damage=18,
    ),
    "cat": dict(
        name="Mèo Bắn Laser",
        emoji="🦊",
        desc="Bắn tia laser nhỏ vào kẻ địch",
        price=900,
        size=22,
        color=(240, 160, 70),
        speed=300,
        attack_range=520,    # ranged
        attack_cd=0.55,
        damage=14,
        bullet_speed=950,
        bullet_color=(255, 100, 220),
    ),
    "eagle": dict(
        name="Đại Bàng",
        emoji="🦅",
        desc="Bay quanh, gây sát thương AOE liên tục",
        price=1500,
        size=28,
        color=(120, 90, 60),
        speed=380,
        attack_range=110,    # orbit radius / AOE radius
        attack_cd=0.45,
        damage=22,
        aoe=True,
    ),
}

PET_ORDER = ["dog", "cat", "eagle"]

# Guns that can be bought directly from the hub (in addition to in-level shops)
HUB_GUN_ORDER = ["pistol_mk2", "smg", "shotgun", "ar", "sniper", "grenade"]


# ============================================================
# SAVE
# ============================================================
SAVE_FILE = ROOT / "save.json"
