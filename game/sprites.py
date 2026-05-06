"""Programmatic pixel-art sprites.

Each sprite is described as a small grid of single-character codes that map to
RGB colors. The grid is rendered into a Surface with crisp square pixels so
the result has a real pixel-art look without needing external image assets.
"""
from __future__ import annotations

from typing import Dict, List, Sequence

import pygame

from . import settings as S

# Each sprite is 16x16 logical pixels rendered into a TILE-sized surface.
SPRITE_RES = 16
PIXEL = S.TILE // SPRITE_RES  # 32 / 16 = 2


def _draw(grid: Sequence[str], palette: Dict[str, tuple]) -> pygame.Surface:
    surf = pygame.Surface((S.TILE, S.TILE), pygame.SRCALPHA)
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch == ' ' or ch == '.':
                continue
            color = palette.get(ch)
            if color is None:
                continue
            pygame.draw.rect(surf, color, (x * PIXEL, y * PIXEL, PIXEL, PIXEL))
    return surf


# ----- Floor / Wall tiles -------------------------------------------------- #
def make_floor_tile(seed: int = 0) -> pygame.Surface:
    """Earthy cobble floor with subtle texture variation per seed."""
    surf = pygame.Surface((S.TILE, S.TILE))
    rng = _seeded(seed)
    # vertical gradient for soft depth
    for yy in range(S.TILE):
        t = yy / (S.TILE - 1)
        r = int(S.FLOOR_LIGHT[0] * (1 - t) + S.FLOOR_DARK[0] * t)
        g = int(S.FLOOR_LIGHT[1] * (1 - t) + S.FLOOR_DARK[1] * t)
        b = int(S.FLOOR_LIGHT[2] * (1 - t) + S.FLOOR_DARK[2] * t)
        pygame.draw.line(surf, (r, g, b), (0, yy), (S.TILE - 1, yy))
    # speckle dirt/stone
    for _ in range(14):
        x = rng() % S.TILE
        y = rng() % S.TILE
        c = S.FLOOR_DARK if (rng() % 3) else S.FLOOR_DIRT
        pygame.draw.rect(surf, c, (x, y, 2, 2))
    # a few stone pebbles
    for _ in range(3):
        x = rng() % (S.TILE - 4) + 2
        y = rng() % (S.TILE - 4) + 2
        pygame.draw.rect(surf, S.FLOOR_STONE, (x, y, 3, 2))
        pygame.draw.rect(surf, S.FLOOR_DARK, (x, y + 2, 3, 1))
    # tile-edge shadow for depth
    pygame.draw.line(surf, S.FLOOR_DARK, (0, 0), (S.TILE - 1, 0))
    pygame.draw.line(surf, S.FLOOR_DARK, (0, 0), (0, S.TILE - 1))
    return surf


def make_wall_tile(seed: int = 0) -> pygame.Surface:
    """Stone-block wall with mortar lines and occasional moss patches."""
    surf = pygame.Surface((S.TILE, S.TILE))
    surf.fill(S.WALL_MORTAR)
    rng = _seeded(seed + 99)
    # 2 rows of staggered stones, mortar visible between them
    brick_h = 16
    for row, y in enumerate(range(0, S.TILE, brick_h)):
        offset = (row % 2) * (S.TILE // 2)
        for x in range(-S.TILE // 2, S.TILE + 1, S.TILE // 2):
            bx = x + offset + 1
            by = y + 1
            bw = S.TILE // 2 - 2
            bh = brick_h - 2
            # stone fill with slight gradient
            pygame.draw.rect(surf, S.WALL_MID, (bx, by, bw, bh))
            pygame.draw.rect(surf, S.WALL_LIGHT, (bx, by, bw, 2))  # top highlight
            pygame.draw.rect(surf, S.WALL_DARK, (bx, by + bh - 2, bw, 2))  # bottom shadow
            # side highlights for 3D look
            pygame.draw.line(surf, S.WALL_LIGHT, (bx, by), (bx, by + bh - 1))
            pygame.draw.line(surf, S.WALL_DARK, (bx + bw - 1, by), (bx + bw - 1, by + bh - 1))
            # speckle inside the stone
            for _ in range(5):
                sx = bx + rng() % bw
                sy = by + rng() % bh
                pygame.draw.rect(surf, S.WALL_DARK, (sx, sy, 1, 1))
    # occasional moss patch
    if rng() % 2 == 0:
        mx = rng() % (S.TILE - 8)
        my = rng() % (S.TILE - 8)
        for _ in range(10):
            dx = rng() % 8
            dy = rng() % 8
            pygame.draw.rect(surf, S.WALL_MOSS, (mx + dx, my + dy, 1, 1))
    return surf


# Decorative overlays drawn on top of floor for variety.
def make_grass_overlay() -> pygame.Surface:
    surf = pygame.Surface((S.TILE, S.TILE), pygame.SRCALPHA)
    base = S.TILE - 10
    for i, x in enumerate((6, 11, 16, 22)):
        h = 4 + (i % 3)
        pygame.draw.line(surf, S.GRASS_DARK, (x, base), (x, base - h))
        pygame.draw.line(surf, S.GRASS, (x + 1, base), (x + 1, base - h + 1))
    return surf


def make_flower_overlay(color: tuple) -> pygame.Surface:
    surf = pygame.Surface((S.TILE, S.TILE), pygame.SRCALPHA)
    cx, cy = S.TILE // 2 + 2, S.TILE - 8
    # stem
    pygame.draw.line(surf, S.GRASS_DARK, (cx, cy), (cx, cy + 6))
    # petals
    pygame.draw.rect(surf, color, (cx - 3, cy - 2, 6, 4))
    pygame.draw.rect(surf, color, (cx - 1, cy - 4, 3, 8))
    pygame.draw.rect(surf, S.FLOWER_YEL, (cx - 1, cy - 1, 2, 2))
    return surf


def make_pebble_overlay() -> pygame.Surface:
    surf = pygame.Surface((S.TILE, S.TILE), pygame.SRCALPHA)
    pygame.draw.rect(surf, S.FLOOR_STONE, (8, 18, 5, 3))
    pygame.draw.rect(surf, S.FLOOR_DARK, (8, 21, 5, 1))
    pygame.draw.rect(surf, S.FLOOR_STONE, (18, 22, 4, 2))
    pygame.draw.rect(surf, S.FLOOR_DARK, (18, 24, 4, 1))
    return surf


def make_puddle_overlay() -> pygame.Surface:
    surf = pygame.Surface((S.TILE, S.TILE), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, S.PUDDLE, (6, 14, 20, 10))
    pygame.draw.ellipse(surf, (110, 150, 180), (10, 16, 12, 4))
    return surf


def make_lantern_overlay() -> pygame.Surface:
    surf = pygame.Surface((S.TILE, S.TILE), pygame.SRCALPHA)
    # glow
    glow = pygame.Surface((S.TILE, S.TILE), pygame.SRCALPHA)
    for r in range(14, 4, -2):
        a = max(0, 30 - r)
        pygame.draw.circle(glow, (*S.LANTERN_GLOW, a + 25), (S.TILE // 2, 8), r)
    surf.blit(glow, (0, 0))
    # post
    pygame.draw.rect(surf, (60, 50, 35), (S.TILE // 2 - 1, 10, 3, S.TILE - 12))
    # lamp box
    pygame.draw.rect(surf, (40, 30, 20), (S.TILE // 2 - 4, 4, 9, 8))
    pygame.draw.rect(surf, S.LANTERN_GLOW, (S.TILE // 2 - 3, 5, 7, 6))
    pygame.draw.rect(surf, (255, 255, 200), (S.TILE // 2 - 2, 6, 5, 4))
    return surf


DECOR_OVERLAYS: List[pygame.Surface] = []  # populated by init()


def _seeded(seed: int):
    state = [seed | 1]

    def nxt() -> int:
        state[0] = (state[0] * 1103515245 + 12345) & 0x7FFFFFFF
        return state[0]

    return nxt


# ----- Entity sprites ------------------------------------------------------ #
PLAYER_SKINS: Dict[str, Dict[str, pygame.Surface]] = {}
COIN_SPRITE: pygame.Surface | None = None
BULLET_SPRITE: pygame.Surface | None = None
SHOP_KEEPER_SPRITE: pygame.Surface | None = None
THIEF_FRAMES: Dict[str, pygame.Surface] = {}
DOG_SPRITE: pygame.Surface | None = None
PUPPY_SPRITE: pygame.Surface | None = None
KEY_SPRITE: pygame.Surface | None = None
CAGE_SPRITE: pygame.Surface | None = None
TRAP_SPRITE: pygame.Surface | None = None
HOUSE_SPRITE: pygame.Surface | None = None
LANTERN_SPRITE: pygame.Surface | None = None
HEART_FULL: pygame.Surface | None = None
HEART_EMPTY: pygame.Surface | None = None
GIRL_PORTRAIT: pygame.Surface | None = None
BOY_PORTRAIT: pygame.Surface | None = None
KNIFE_SPRITE: pygame.Surface | None = None
TREE_SPRITE: pygame.Surface | None = None
BAT_FRAMES: Dict[str, pygame.Surface] = {}
DRAGON_SPRITE: pygame.Surface | None = None
FIRE_SPRITE: pygame.Surface | None = None
FIRE_DRAGON_SPRITE: pygame.Surface | None = None
EXIT_GATE_SPRITE: pygame.Surface | None = None
FLOOR_TILES: List[pygame.Surface] = []
WALL_TILES: List[pygame.Surface] = []


# Hero (boy) facing down — arms slightly different per frame for animation
_BOY_DOWN_A = [
    "................",
    ".....22222......",
    "....2333332.....",
    "....2333332.....",
    "....23ww332.....",  # hair/face
    "....28888332....",  # forehead/face
    "....28ee882.....",  # face with eyes
    "....288888......",
    "...4488884......",  # neck/shirt
    "..444488844.....",  # shoulders + shirt
    "..554488455.....",  # arms
    "..55448855......",
    "...554485.......",
    "...55..55.......",  # pants
    "...66..66.......",
    "..6666..6666....",  # boots
]

_BOY_DOWN_B = [
    "................",
    ".....22222......",
    "....2333332.....",
    "....2333332.....",
    "....23ww332.....",
    "....28888332....",
    "....28ee882.....",
    "....288888......",
    "...4488884......",
    "..444488844.....",
    "...44488844.....",
    "...44488844.....",
    "....55485.......",
    "...55..55.......",
    "...66..66.......",
    "..6666..6666....",
]

_BOY_PALETTE = {
    '2': S.HAIR,        # hair
    '3': S.HAIR,
    'w': (255, 255, 255),  # eye highlight (unused but safe)
    '8': S.SKIN,        # face
    'e': (40, 30, 30),  # eyes
    '4': S.SHIRT,       # shirt
    '5': S.PANTS,       # pants
    '6': S.BOOTS,       # boots
}


_THIEF_A = [
    "................",
    "....11111111....",
    "....1ggggg11....",  # hood
    "....1g999g11....",  # face area
    "....1g9R9g1.....",  # red mask band
    "....1ggggg1.....",
    "....11111111....",
    "...111111111....",
    "..1111R1R111....",  # belt highlights
    "..11111111111...",
    "..111111R1111...",
    "..1111111111....",
    "...111111111....",
    "...11.....11....",
    "...11.....11....",
    "..222.....222...",
]

_THIEF_B = [
    "................",
    "....11111111....",
    "....1ggggg11....",
    "....1g999g11....",
    "....1g9R9g1.....",
    "....1ggggg1.....",
    "....11111111....",
    "...111111111....",
    "..111R111R111...",
    "..11111111111...",
    "..1111R11R111...",
    "..11111111111...",
    "...111111111....",
    "...11.....11....",
    "...11.....11....",
    "..222.....222...",
]

_THIEF_PALETTE = {
    '1': S.THIEF_BODY,
    'g': (60, 60, 70),
    '9': S.SKIN,
    'R': S.THIEF_MASK,
    '2': (20, 20, 25),
}


_DOG = [
    "................",
    "................",
    "...DDDDD........",
    "..DddddddD......",
    "..DdEdEddD......",
    "..DdddddDD..DD..",
    "..DDDDdDDDDDDD..",
    "...DDDdDDDDDDD..",
    "....DDDdddddD...",
    "....DDDdddddD...",
    "....DD..DD......",
    "....DD..DD......",
    "................",
    "................",
    "................",
    "................",
]
_DOG_PAL = {
    'D': S.DOG_DARK,
    'd': S.DOG_FUR,
    'E': (30, 20, 15),
}


_KEY = [
    "................",
    "................",
    "....KKKK........",
    "...K....K.......",
    "...K.kk.K.......",  # ring
    "...K....K.......",
    "....KKKKK.......",
    "........KKK.....",
    "........KKKK....",
    "........K..K....",  # tooth
    "........KK.K....",
    "........K..K....",
    "........KKKK....",
    "................",
    "................",
    "................",
]
_KEY_PAL = {'K': S.GOLD, 'k': S.GOLD_DARK}


_CAGE = [
    "................",
    "..CCCCCCCCCCCC..",
    "..C..........C..",
    "..C.C..C..C..C..",
    "..C.C..C..C..C..",
    "..C.C..C..C..C..",
    "..C.C..C..C..C..",
    "..C.C..C..C..C..",
    "..C.C..C..C..C..",
    "..C.C..C..C..C..",
    "..C.C..C..C..C..",
    "..C.C..C..C..C..",
    "..C..........C..",
    "..CCCCCCCCCCCC..",
    "................",
    "................",
]
_CAGE_PAL = {'C': S.CAGE_BAR}


_TRAP = [
    "................",
    "................",
    "....TTTTTTTT....",
    "...TttttttttT...",
    "...TtBtBtBttT...",  # spikes
    "...TttBtBtBtT...",
    "...TtBtBtBttT...",
    "...TttttttttT...",
    "....TTTTTTTT....",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
]
_TRAP_PAL = {'T': S.TRAP_DARK, 't': S.TRAP_RED, 'B': (255, 240, 240)}


# Hideout house: red roof + warm wood walls + small lit window
_HOUSE = [
    "................",
    ".......RR.......",
    "......RrrR......",
    ".....RrrrrR.....",
    "....RrrrrrrR....",
    "...RRRRRRRRR....",
    "...DRRRRRRRR....",  # roof eave
    "...WWWWWWWW.....",
    "...WyyWWWyW.....",  # window with light
    "...WyyWWWyW.....",
    "...WWWWdWWW.....",  # door top
    "...WWWWdWWW.....",  # door
    "...WWWWdWWW.....",
    "...WWWWWWW......",
    "................",
    "................",
]
_HOUSE_PAL = {
    'R': S.HOUSE_ROOF,
    'r': S.HOUSE_ROOF,
    'D': S.HOUSE_ROOF_DARK,
    'W': S.HOUSE_WALL,
    'y': S.HOUSE_GLOW,
    'd': S.HOUSE_DOOR,
}


# Hearts for HUD
_HEART_FULL = [
    "................",
    "................",
    "..HH......HH....",
    ".HhhH....HhhH...",
    ".HhhhH..HhhhH...",
    ".HhhhhHHhhhhH...",
    ".HhhhhhhhhhhH...",
    "..HhhhhhhhhH....",
    "...HhhhhhhH.....",
    "....HhhhhH......",
    ".....HhhH.......",
    "......HH........",
    "................",
    "................",
    "................",
    "................",
]
_HEART_EMPTY = [r.replace('h', '.').replace('H', 'g') for r in _HEART_FULL]
_HEART_FULL_PAL = {'H': S.HEART_DARK, 'h': S.HEART_RED}
_HEART_EMPTY_PAL = {'g': (90, 90, 95)}


# Portraits (for chat-style story)
_GIRL = [
    "................",
    "....HHHHHH......",
    "...HpppppHH.....",  # pink hair
    "..HppppppppH....",
    "..HpSSSSSSpH....",
    "..HSffffffSH....",
    "..HSfeeeeeSH....",  # eyes
    "..HSffffffS.....",
    "..HSff..ffS.....",  # mouth
    "..HSffmmffS.....",
    "..HSSSSSSSS.....",
    "..PPPPPPPPP.....",  # shirt
    "..PPbbbbPPP.....",
    "..PPbbbbbPP.....",
    "..PPPPPPPPP.....",
    "................",
]
_GIRL_PAL = {
    'H': (140, 70, 100),
    'p': (220, 130, 170),
    'S': S.SKIN,
    'f': S.SKIN,
    'e': (50, 30, 30),
    'm': (180, 80, 100),
    'P': (220, 100, 140),
    'b': (255, 220, 230),
}


_BOY_PORTRAIT = [
    "................",
    "....22222.......",
    "...2333332......",
    "..23333333......",
    "..2388888.......",
    "..2388e88.......",
    "..2388888.......",
    "..23eeeee.......",
    "...28888........",
    "..444488444.....",
    "..44488844......",
    "..44488844......",
    "..44488844......",
    "..44444444......",
    "................",
    "................",
]
_BOY_PORTRAIT_PAL = {
    '2': S.HAIR,
    '3': S.HAIR,
    '8': S.SKIN,
    'e': (40, 30, 30),
    '4': S.SHIRT,
}

# Knife / dagger sprite — 16x16 logical pixels (blade points up-right)
_KNIFE = [
    "................",
    "...........Wk...",  # blade tip highlight
    "..........kBB...",
    ".........kBBB...",
    "........kBBBk...",
    ".......kBBBk....",
    "......kBBBk.....",
    ".....kBBBk......",
    "....HHBBk.......",  # guard
    "...HHHHk........",
    "....HHH.........",
    "....Nnn.........",  # handle
    "....Nnn.........",
    "....NnN.........",
    "....NNN.........",
    "................",
]
_KNIFE_PAL = {
    'B': (210, 215, 225),   # blade silver
    'k': (170, 175, 185),   # blade shadow
    'W': (255, 255, 255),   # blade highlight/shine
    'H': (190, 140, 40),    # guard gold
    'N': (90, 55, 30),      # handle dark
    'n': (130, 85, 50),     # handle mid
}

_TREE = [
    "......GGGG......",
    "....GGGGGGGG....",
    "...GGGGGGGGGG...",
    "..GGGGGGGGGGGG..",
    "..GGGGGGGGGGGG..",
    "..GGGGGGGGGGGG..",
    "..GGGGGGGGGGGG..",
    "...GGGGGGGGGG...",
    "....GGGGGGGG....",
    "......TTTT......",
    "......TTTT......",
    "......TTTT......",
    "......TTTT......",
    "......TTTT......",
    "......TTTT......",
    "................",
]
_TREE_PAL = {'G': (34, 139, 34), 'T': (139, 69, 19)}

_BAT_A = [
    "................",
    "................",
    "................",
    "...BB......BB...",
    "...BBB....BBB...",
    "....BBBBBBBB....",
    ".....BBBBBB.....",
    "......BBBB......",
    ".......BB.......",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
]
_BAT_B = [
    "................",
    "................",
    "...B........B...",
    "..BB........BB..",
    ".BBB........BBB.",
    ".BBBBBBBBBBBBBB.",
    "..BBBBBBBBBBBB..",
    "....BBBBBBBB....",
    "......BBBB......",
    ".......BB.......",
    "................",
    "................",
    "................",
    "................",
    "................",
    "................",
]
_BAT_PAL = {'B': (50, 50, 50)}

_DRAGON = [
    "................",
    "......RRRR......",
    ".....RRRRRR.....",
    "....RRRRRRRR....",
    "...RRRRRRRRRR...",
    "...RR..RR..RR...",
    "...RRRRRRRRRR...",
    "....RRRRRRRR....",
    ".....RRRRRR.....",
    "....RRRRRRRR....",
    "...RRRRRRRRRR...",
    "..RRRRRRRRRRRR..",
    "..RR........RR..",
    "..RR........RR..",
    "................",
    "................",
]
_DRAGON_PAL = {'R': (200, 0, 0)}

_FIRE = [
    "................",
    ".......OO.......",
    "......OOOO......",
    ".....OOOOOO.....",
    "....OOOOOOOO....",
    ".....OOOOOO.....",
    "......OOOO......",
    ".......OO.......",
    "................",
    "................",
    "................",
    "................",
]
_FIRE_PAL = {'O': (255, 69, 0)}
_DRAGON_PAL = {'G': (50, 180, 50), 'R': (255, 50, 50), 'Y': (255, 220, 50), 'W': (255, 255, 255), '.': (0,0,0,0)}

_THIEF_A = [
    "....BBBBBB......",
    "...BssssssB.....",
    "..BssssssssB....",
    "..BssssssssB....",
    "..BssWWWWssB....",
    "..BssWBBWssB....",
    "...ssWBBWss.....",
    "....ssssss......",
    "....GGGGGG......",
    "...GGGGGGGG.....",
    "..GGGGGGGGGG....",
    "..GGGGGGGGGG....",
    "..ss......ss....",
]
_THIEF_B = _THIEF_A
_THIEF_PAL = {
    'B': (30, 30, 30),
    's': (230, 190, 150),
    'W': (255, 255, 255),
    'G': (60, 60, 60),
}

_PLAYER_BOY_A = [
    "....hhhhhh......",
    "...hssssssh.....",
    "..hssssssssh....",
    "..hssssssssh....",
    "..hssssssssh....",
    "..hssssssssh....",
    "..hssssssssh....",
    "..hssWWWWssh....",
    "..hssWBBWssh....",
    "...ssWBBWss.....",
    "....ssssss......",
    "....JJJJJJ......",
    "...JJJJJJJJ.....",
    "..JJJJJJJJJJ....",
    "..JJJJJJJJJJ....",
    "..ss......ss....",
]
_PLAYER_GIRL_A = [
    "....pppppp......",
    "...pppppppp.....",
    "..pppppppppp....",
    "..pppppppppp....",
    "..pppppppppp....",
    "..pppppppppp....",
    "..ppWWWWpppp....",
    "..ppWBBWpppp....",
    "...pWBBWp.......",
    "....pppp........",
    "....DDDD........",
    "...DDDDDD.......",
    "..DDDDDDDD......",
    "..DDDDDDDD......",
    "..pp....pp......",
    "..pp....pp......",
]
_PLAYER_NINJA_A = [
    "....NNNNNN......",
    "...NNNNNNNN.....",
    "..NNNNNNNNNN....",
    "..NNRRRRRRNN....",
    "..NRWWWWWWRN....",
    "..NRWBBWBBWRN...",
    "..NRWBBWBBWRN...",
    "..NRWWWWWWWRN...",
    "..NNRRRRRRNN....",
    "....NNNNNN......",
    "....NNNNNN......",
    "...NNNNNNNN.....",
    "..NNNNNNNNNN....",
    "..NNNNNNNNNN....",
    "..NN......NN....",
    "..NN......NN....",
]
_PLAYER_PAL = {
    'h': (80, 50, 30),   # Brown hair
    's': (255, 210, 170), # Skin
    'W': (255, 255, 255), # White eyes
    'B': (0, 0, 0),      # Black pupils
    'J': (30, 80, 200),  # Blue jacket
    'p': (255, 100, 150), # Pink hair
    'D': (255, 230, 100), # Yellow dress
    'N': (30, 30, 40),    # Ninja black
    'R': (200, 30, 30),   # Ninja red
}

_COIN = [
    "....YYYYYYYY....",
    "..YYyyyyyyyyYY..",
    ".YyyyyyyyyyyyyY.",
    "YyyyyyYYYYyyyyyY",
    "YyyyyYYyyYYyyyyY",
    "YyyyyYYyyYYyyyyY",
    "YyyyyYYyyYYyyyyY",
    "YyyyyyYYYYyyyyyY",
    ".YyyyyyyyyyyyyY.",
    "..YYyyyyyyyyYY..",
    "....YYYYYYYY....",
]
_COIN_PAL = {
    'Y': (255, 215, 0),    # Bright Gold
    'y': (255, 255, 150),  # Very Bright Yellow
}

_BULLET = [
    "....WW....",
    "...WYYW...",
    "..WYYYYW..",
    "...WYYW...",
    "....WW....",
]
_BULLET_PAL = {'W': (255, 255, 255), 'Y': (255, 200, 0)}

_SHOP_KEEPER = [
    "....hhhhhh......",
    "...hssssssh.....",
    "..hssssssssh....",
    "..hssssssssh....",
    "..hssWWWWssh....",
    "..hssWBBWssh....",
    "...ssWBBWss.....",
    "....ssssss......",
    "....RRRRRR......",
    "...RRRRRRRR.....",
    "..RRRRRRRRRR....",
    "..RRRRRRRRRR....",
    "..ss......ss....",
]
_SHOP_KEEPER_PAL = {
    'h': (50, 30, 10),
    's': (230, 180, 140),
    'W': (255, 255, 255),
    'B': (0,0,0),
    'R': (150, 50, 50), # Red shop uniform
}
# Puppy (smaller dog sprite)
_PUPPY = [
    "................",
    "................",
    "................",
    "....PPP.........",
    "...PppppP.......",
    "...PpEpEpP......",
    "...PpppppPP..PP.",
    "....PPpPPPPPPP..",
    ".....PPppppP....",
    ".....PPppppP....",
    ".....PP..PP.....",
    ".....PP..PP.....",
    "................",
    "................",
    "................",
    "................",
]
_PUPPY_PAL = {
    'P': S.PUPPY_DARK,
    'p': S.PUPPY_FUR,
    'E': (30, 20, 15),
}

# Decorative fire-breathing dragon (bigger, outside maze wall)
_FIRE_DRAGON = [
    "..GG........GG..",
    ".GRRG......GRRG.",
    ".GRRG......GRRG.",
    "..GRRGGGGGGRRG..",
    "...GRRRRRRRRG...",
    "..GRRWWRRWWRRG..",
    "..GRRBBRRBBRRG..",
    "...GRRRRRRRRG...",
    "....GRRRRRG.....",
    "...GRYYYYYYRG...",
    "..GRYYYYYYYRRRG.",
    ".GRRRRRRRRRRRRG.",
    ".GRRG....GRRRG..",
    ".GRG......GRG...",
    "..GG.......GG...",
    "................",
]
_FIRE_DRAGON_PAL = {
    'G': (50, 180, 50),    # Green body
    'R': (200, 50, 50),    # Red accents
    'W': (255, 255, 255),  # White eyes
    'B': (0, 0, 0),        # Black pupils
    'Y': (255, 200, 50),   # Yellow belly/fire
}

_PORTAL = [
    "TTTTTTTTTTTTTTTT",
    "TBBBBBBBBBBBBBBT",
    "TBGGGGGGGGGGGGBT",
    "TBG..........GBT",
    "TBG...pppp...GBT",
    "TBG..pppppp..GBT",
    "TBG.pppppppp.GBT",
    "TBG.pppppppp.GBT",
    "TBG.pppppppp.GBT",
    "TBG.pppppppp.GBT",
    "TBG..pppppp..GBT",
    "TBG...pppp...GBT",
    "TBG..........GBT",
    "TBGGGGGGGGGGGGBT",
    "TBBBBBBBBBBBBBBT",
    "TTTTTTTTTTTTTTTT",
]
_PORTAL_PAL = {
    'T': (40, 40, 50),    # Dark stone
    'B': (80, 80, 90),    # Light stone
    'G': (250, 220, 100), # Gold trim
    'p': (150, 50, 255),  # Purple magic core
    '.': (20, 20, 30),    # Void
}


def init() -> None:
    """Render all sprite surfaces once after pygame.display is ready."""
    global DOG_SPRITE, PUPPY_SPRITE, KEY_SPRITE, CAGE_SPRITE, TRAP_SPRITE, HOUSE_SPRITE
    global LANTERN_SPRITE
    global HEART_FULL, HEART_EMPTY, GIRL_PORTRAIT, BOY_PORTRAIT
    global KNIFE_SPRITE
    global COIN_SPRITE, BULLET_SPRITE, SHOP_KEEPER_SPRITE
    global BAT_FRAMES, DRAGON_SPRITE, FIRE_SPRITE, FIRE_DRAGON_SPRITE, EXIT_GATE_SPRITE
    global TREE_SPRITE

    PLAYER_SKINS["Boy"] = {"A": _draw(_PLAYER_BOY_A, _PLAYER_PAL), "B": _draw(_PLAYER_BOY_A, _PLAYER_PAL)}
    PLAYER_SKINS["Girl"] = {"A": _draw(_PLAYER_GIRL_A, _PLAYER_PAL), "B": _draw(_PLAYER_GIRL_A, _PLAYER_PAL)}
    PLAYER_SKINS["Ninja"] = {"A": _draw(_PLAYER_NINJA_A, _PLAYER_PAL), "B": _draw(_PLAYER_NINJA_A, _PLAYER_PAL)}
    
    COIN_SPRITE = pygame.transform.scale(_draw(_COIN, _COIN_PAL), (24, 24))
    BULLET_SPRITE = _draw(_BULLET, _BULLET_PAL)
    SHOP_KEEPER_SPRITE = _draw(_SHOP_KEEPER, _SHOP_KEEPER_PAL)
    
    THIEF_FRAMES["A"] = _draw(_THIEF_A, _THIEF_PAL)
    THIEF_FRAMES["B"] = _draw(_THIEF_B, _THIEF_PAL)
    DOG_SPRITE = _draw(_DOG, _DOG_PAL)
    PUPPY_SPRITE = _draw(_PUPPY, _PUPPY_PAL)
    FIRE_DRAGON_SPRITE = pygame.transform.scale(_draw(_FIRE_DRAGON, _FIRE_DRAGON_PAL), (S.TILE * 2, S.TILE * 2))
    KEY_SPRITE = _draw(_KEY, _KEY_PAL)
    CAGE_SPRITE = _draw(_CAGE, _CAGE_PAL)
    TRAP_SPRITE = _draw(_TRAP, _TRAP_PAL)
    HOUSE_SPRITE = _draw(_HOUSE, _HOUSE_PAL)
    LANTERN_SPRITE = make_lantern_overlay()
    HEART_FULL = _draw(_HEART_FULL, _HEART_FULL_PAL)
    HEART_EMPTY = _draw(_HEART_EMPTY, _HEART_EMPTY_PAL)
    GIRL_PORTRAIT = pygame.transform.scale(_draw(_GIRL, _GIRL_PAL), (96, 96))
    BOY_PORTRAIT = pygame.transform.scale(_draw(_BOY_PORTRAIT, _BOY_PORTRAIT_PAL), (96, 96))
    KNIFE_SPRITE = pygame.transform.scale(_draw(_KNIFE, _KNIFE_PAL), (S.TILE, S.TILE))
    TREE_SPRITE = _draw(_TREE, _TREE_PAL)
    BAT_FRAMES["A"] = _draw(_BAT_A, _BAT_PAL)
    BAT_FRAMES["B"] = _draw(_BAT_B, _BAT_PAL)
    DRAGON_SPRITE = _draw(_DRAGON, _DRAGON_PAL)
    FIRE_SPRITE = _draw(_FIRE, _FIRE_PAL)
    # A grand 2x2 gate
    EXIT_GATE_SPRITE = pygame.transform.scale(_draw(_PORTAL, _PORTAL_PAL), (S.TILE * 2, S.TILE * 2))

    for i in range(6):
        FLOOR_TILES.append(make_floor_tile(seed=i))
    for i in range(6):
        WALL_TILES.append(make_wall_tile(seed=i))

    DECOR_OVERLAYS.append(make_grass_overlay())
    DECOR_OVERLAYS.append(make_flower_overlay(S.FLOWER_PINK))
    DECOR_OVERLAYS.append(make_flower_overlay(S.FLOWER_YEL))
    DECOR_OVERLAYS.append(make_pebble_overlay())
    DECOR_OVERLAYS.append(make_puddle_overlay())
