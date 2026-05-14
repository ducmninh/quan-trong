"""Level definitions — 4 beautiful hand-designed maps.

Each level has its own builder function returning (world, enemies, label,
biome). Levels are designed to be played left-to-right (exit on the right
edge), with strategic landmarks: houses, gas station shop, industrial
warehouses, boss arena.
"""
from __future__ import annotations
import random
import pygame
from utils import Vec
from world import (
    World, Solid, Pickup, Decal,
    T_GRASS, T_ROAD_H, T_ROAD_V, T_ROAD_X, T_DIRT, T_CONCRETE, T_SAND,
    T_GRASS_DARK, T_FLOOR_WOOD, T_FLOOR_TILE, T_ASH, T_WATER,
    P_GOLD, P_MEDKIT, P_AMMO, P_KEY,
)
from enemies import Enemy
from settings import TILE


# ============================================================
# Helpers
# ============================================================
def _add_house(world, x, y, w, h, wall=None, roof=None):
    rect = pygame.Rect(x, y, w, h)
    s = Solid(rect, "house")
    if wall is not None:
        s.aux["wall"] = wall
    if roof is not None:
        s.aux["roof"] = roof
    world.add_solid(s)
    return s


def _add_fence(world, x, y, w, h):
    world.add_solid(Solid(pygame.Rect(x, y, w, h), "fence"))


def _add_tree(world, cx, cy, r=24):
    world.add_solid(Solid(pygame.Rect(cx - r, cy - r, 2 * r, 2 * r), "tree"))


def _add_car(world, x, y, w=64, h=36, color=None):
    s = Solid(pygame.Rect(x, y, w, h), "car", color=color)
    world.add_solid(s)


def _add_drum(world, cx, cy):
    world.add_solid(Solid(pygame.Rect(cx - 16, cy - 16, 32, 32), "drum"))


def _add_container(world, x, y, w, h, color=None):
    world.add_solid(Solid(pygame.Rect(x, y, w, h), "container", color=color))


def _scatter_gold(world, rect: pygame.Rect, count: int, amount=15):
    for _ in range(count):
        x = random.randint(rect.left + 20, rect.right - 20)
        y = random.randint(rect.top + 20, rect.bottom - 20)
        world.add_pickup(Pickup(Vec(x, y), P_GOLD, amount))


# ============================================================
# LEVEL 1 — Khu Dân Cư (Suburban)
# Beautiful suburban layout: 2 parallel horizontal roads with a vertical
# cross road, two rows of houses with front gardens, scattered trees,
# parked cars, exit on the right.
# ============================================================
def build_level1():
    W, H = 90, 50
    world = World(W, H, default_tile=T_GRASS)
    # Sidewalks/concrete around houses
    # Horizontal main road (3 tiles tall) at y=12 and y=36
    for y in (11, 12, 13):
        for x in range(W):
            world.set_tile(x, y, T_ROAD_H)
    for y in (35, 36, 37):
        for x in range(W):
            world.set_tile(x, y, T_ROAD_H)
    # Vertical connector road at x=44
    for x in (43, 44, 45):
        for y in range(H):
            world.set_tile(x, y, T_ROAD_V)
    # Intersections
    for y in (11, 12, 13, 35, 36, 37):
        for x in (43, 44, 45):
            world.set_tile(x, y, T_ROAD_X)
    # Sidewalks (concrete) flanking roads
    for x in range(W):
        world.set_tile(x, 10, T_CONCRETE)
        world.set_tile(x, 14, T_CONCRETE)
        world.set_tile(x, 34, T_CONCRETE)
        world.set_tile(x, 38, T_CONCRETE)
    for y in range(H):
        for x in (42, 46):
            world.set_tile(x, y, T_CONCRETE)

    # Front gardens darker grass
    for x in range(W):
        for y in (15, 16, 32, 33):
            world.set_tile(x, y, T_GRASS_DARK)
        for y in (8, 9, 39, 40):
            world.set_tile(x, y, T_GRASS_DARK)

    # House blocks: 6 houses in upper row, 6 in lower row, skipping connector
    house_w, house_h = 90, 100
    upper_y = 6 * TILE - 40
    lower_y = 38 * TILE
    house_positions = []
    for i, gx in enumerate([3, 13, 23, 33, 53, 63, 73, 83]):
        x = gx * TILE
        house_positions.append((x, upper_y))
        # roof varying
        roof = (165, 60, 50) if i % 2 == 0 else (70, 100, 160)
        wall = (245, 240, 220) if i % 3 == 0 else (215, 195, 160)
        _add_house(world, x, upper_y, house_w, house_h, wall=wall, roof=roof)
        # tree in front yard
        _add_tree(world, x + house_w // 2, upper_y - 30, r=20)
    for i, gx in enumerate([3, 13, 23, 33, 53, 63, 73, 83]):
        x = gx * TILE
        roof = (70, 100, 160) if i % 2 == 0 else (165, 60, 50)
        wall = (210, 180, 140) if i % 2 == 0 else (245, 240, 220)
        _add_house(world, x, lower_y, house_w, house_h, wall=wall, roof=roof)
        house_positions.append((x, lower_y))
        _add_tree(world, x + house_w // 2, lower_y + house_h + 30, r=20)

    # Fences along gardens (between houses)
    for x in range(0, W * TILE, 36):
        pass  # skip for cleanliness

    # Parked cars on roadside
    car_colors = [(200, 50, 50), (60, 80, 200), (220, 200, 60),
                  (40, 160, 60), (50, 50, 50)]
    for i, gx in enumerate(range(6, W - 6, 14)):
        _add_car(world, gx * TILE, 9 * TILE + 8,
                 color=car_colors[i % len(car_colors)])
        _add_car(world, gx * TILE + 70, 38 * TILE + 8,
                 color=car_colors[(i + 2) % len(car_colors)])

    # Drums for shooting fun
    _add_drum(world, 32 * TILE, 21 * TILE)
    _add_drum(world, 64 * TILE, 24 * TILE)

    # Decorative flowers
    for _ in range(80):
        x = random.randint(0, W * TILE - 10)
        y = random.randint(0, H * TILE - 10)
        # avoid roads
        ti = x // TILE
        tj = y // TILE
        if not (0 <= ti < W and 0 <= tj < H):
            continue
        if world.tiles[tj][ti] in (T_GRASS, T_GRASS_DARK):
            world.add_decal(Decal(pygame.Rect(x, y, 6, 6), "flower",
                                  random.choice([(240, 80, 80),
                                                 (250, 200, 60),
                                                 (180, 100, 240),
                                                 (255, 255, 255)])))

    # Pickups
    _scatter_gold(world, pygame.Rect(2 * TILE, 16 * TILE,
                                     40 * TILE, 16 * TILE), 6, 10)
    _scatter_gold(world, pygame.Rect(46 * TILE, 16 * TILE,
                                     40 * TILE, 16 * TILE), 8, 12)
    world.add_pickup(Pickup(Vec(28 * TILE, 24 * TILE), P_MEDKIT))
    world.add_pickup(Pickup(Vec(72 * TILE, 22 * TILE), P_MEDKIT))

    # Spawn at left
    world.spawn = Vec(3 * TILE, 24 * TILE)

    # Exit at right edge (small zone)
    world.exit_rect = pygame.Rect((W - 4) * TILE, 22 * TILE,
                                  3 * TILE, 6 * TILE)
    world.exit_locked = True  # unlock after boss

    # Enemies — spread out, ramping right-to-left, kept away from spawn
    enemies = []
    for i in range(6):
        x = random.randint(14 * TILE, 36 * TILE)
        y = random.randint(16 * TILE, 32 * TILE)
        kind = "zombie" if random.random() < 0.7 else "thief_knife"
        enemies.append(Enemy(kind, Vec(x, y)))
    for i in range(7):
        x = random.randint(48 * TILE, 76 * TILE)
        y = random.randint(16 * TILE, 32 * TILE)
        kind = "thief_knife" if random.random() < 0.5 else "zombie"
        enemies.append(Enemy(kind, Vec(x, y)))
    # Mini-boss arena near exit
    boss_pos = Vec((W - 8) * TILE, 24 * TILE)
    boss = Enemy("boss1", boss_pos)
    enemies.append(boss)
    # Two guards near boss
    enemies.append(Enemy("thief_knife", boss_pos + Vec(-90, -40)))
    enemies.append(Enemy("thief_knife", boss_pos + Vec(-90, 40)))

    return world, enemies, "Level 1 — Khu Dân Cư", "suburban"


# ============================================================
# LEVEL 2 — Phố Cổ (Downtown) with gas station shop
# Wider concrete streets, narrow alleys, rubble, abandoned cars and a
# gas station building where the shop is located.
# ============================================================
def build_level2():
    W, H = 100, 55
    world = World(W, H, default_tile=T_CONCRETE)
    # Main street horizontal (5 tiles tall, centered on y=22)
    for y in range(20, 25):
        for x in range(W):
            world.set_tile(x, y, T_ROAD_H)
    # Two perpendicular alleys (5 wide)
    for x in range(28, 33):
        for y in range(H):
            world.set_tile(x, y, T_ROAD_V)
    for x in range(64, 69):
        for y in range(H):
            world.set_tile(x, y, T_ROAD_V)
    for x in range(28, 33):
        for y in range(20, 25):
            world.set_tile(x, y, T_ROAD_X)
    for x in range(64, 69):
        for y in range(20, 25):
            world.set_tile(x, y, T_ROAD_X)
    # Sidewalk concrete (default already concrete)
    # Some dirt patches for visual variety
    for _ in range(40):
        cx = random.randint(0, W - 4)
        cy = random.randint(0, H - 4)
        if world.tiles[cy][cx] == T_CONCRETE:
            for dx in range(3):
                for dy in range(3):
                    if 0 <= cx + dx < W and 0 <= cy + dy < H:
                        if random.random() < 0.6:
                            world.tiles[cy + dy][cx + dx] = T_DIRT

    # Abandoned ruined buildings (multi-block, irregular)
    def add_ruin(gx, gy, w, h, wall=(170, 150, 110), roof=(110, 70, 40)):
        _add_house(world, gx * TILE, gy * TILE, w * TILE, h * TILE,
                   wall=wall, roof=roof)

    # Top row buildings
    add_ruin(2, 4, 10, 13, wall=(180, 150, 110), roof=(120, 60, 40))
    add_ruin(13, 6, 6, 11, wall=(160, 140, 110), roof=(140, 60, 50))
    add_ruin(20, 4, 7, 13, wall=(195, 175, 140), roof=(70, 60, 130))
    add_ruin(34, 6, 11, 11, wall=(200, 180, 150), roof=(140, 80, 60))
    add_ruin(46, 4, 9, 13, wall=(160, 130, 100), roof=(70, 50, 130))
    add_ruin(56, 4, 7, 13, wall=(220, 200, 170), roof=(120, 70, 60))
    # Gas station building (shop)
    shop_x, shop_y = 70, 6
    shop_w, shop_h = 14, 9
    _add_house(world, shop_x * TILE, shop_y * TILE,
               shop_w * TILE, shop_h * TILE,
               wall=(245, 240, 220), roof=(60, 130, 80))
    world.shop_rect = pygame.Rect((shop_x + 5) * TILE, (shop_y + shop_h + 1) * TILE,
                                  4 * TILE, 2 * TILE)
    # Pump pad concrete
    for x in range(shop_x + 1, shop_x + shop_w - 1):
        for y in range(shop_y + shop_h, shop_y + shop_h + 3):
            world.set_tile(x, y, T_CONCRETE)
    # Pumps (drums in front)
    _add_drum(world, (shop_x + 3) * TILE + TILE // 2,
              (shop_y + shop_h + 1) * TILE)
    _add_drum(world, (shop_x + 8) * TILE + TILE // 2,
              (shop_y + shop_h + 1) * TILE)
    _add_drum(world, (shop_x + 11) * TILE + TILE // 2,
              (shop_y + shop_h + 1) * TILE)

    add_ruin(86, 4, 10, 13, wall=(140, 120, 90), roof=(120, 60, 40))

    # Bottom row buildings
    add_ruin(2, 28, 7, 15, wall=(180, 150, 110), roof=(120, 60, 40))
    add_ruin(10, 30, 9, 13, wall=(195, 175, 140), roof=(70, 60, 130))
    add_ruin(20, 28, 7, 15, wall=(160, 140, 110), roof=(140, 60, 50))
    add_ruin(34, 30, 11, 13, wall=(200, 180, 150), roof=(140, 80, 60))
    add_ruin(46, 28, 7, 15, wall=(220, 200, 170), roof=(70, 60, 130))
    add_ruin(54, 30, 9, 13, wall=(160, 130, 100), roof=(120, 70, 60))
    add_ruin(70, 28, 8, 15, wall=(195, 175, 140), roof=(140, 70, 50))
    add_ruin(79, 30, 6, 13, wall=(220, 200, 170), roof=(70, 60, 130))
    add_ruin(86, 28, 10, 15, wall=(160, 130, 100), roof=(120, 70, 50))

    # Rubble piles and crashed cars on the road
    for x in (10, 22, 52, 60, 76, 90):
        _add_car(world, x * TILE, 20 * TILE + 12,
                 color=random.choice([(80, 80, 80), (160, 60, 50),
                                      (60, 80, 160)]))
    for x in (38, 48, 78):
        rect = pygame.Rect(x * TILE, 22 * TILE + 8, 64, 36)
        world.add_solid(Solid(rect, "rubble"))
    for x in (16, 42, 72):
        world.add_solid(Solid(pygame.Rect(x * TILE, 23 * TILE,
                                          40, 24), "rubble"))

    # decorative cracks
    for _ in range(80):
        x = random.randint(0, W * TILE - 6)
        y = random.randint(20 * TILE, 26 * TILE)
        world.add_decal(Decal(pygame.Rect(x, y, 12, 12), "crack"))
    for _ in range(30):
        x = random.randint(0, W * TILE - 12)
        y = random.randint(0, H * TILE - 12)
        ti = x // TILE
        tj = y // TILE
        if 0 <= ti < W and 0 <= tj < H and world.tiles[tj][ti] != T_ROAD_H:
            world.add_decal(Decal(pygame.Rect(x, y, 16, 16), "puddle"))

    # Pickups
    _scatter_gold(world, pygame.Rect(2 * TILE, 18 * TILE,
                                     45 * TILE, 16 * TILE), 10, 15)
    _scatter_gold(world, pygame.Rect(48 * TILE, 18 * TILE,
                                     45 * TILE, 16 * TILE), 12, 18)
    world.add_pickup(Pickup(Vec(32 * TILE, 24 * TILE), P_MEDKIT))
    world.add_pickup(Pickup(Vec(67 * TILE, 24 * TILE), P_MEDKIT))
    world.add_pickup(Pickup(Vec(15 * TILE, 23 * TILE), P_AMMO))
    world.add_pickup(Pickup(Vec(58 * TILE, 23 * TILE), P_AMMO))
    world.add_pickup(Pickup(Vec(82 * TILE, 23 * TILE), P_AMMO))

    world.spawn = Vec(2 * TILE, 22 * TILE + 16)
    world.exit_rect = pygame.Rect((W - 4) * TILE, 22 * TILE,
                                  3 * TILE, 5 * TILE)
    world.exit_locked = True

    enemies = []
    # zombies in groups
    for _ in range(10):
        x = random.randint(6 * TILE, 40 * TILE)
        y = random.randint(18 * TILE, 28 * TILE)
        kind = "zombie_fast" if random.random() < 0.6 else "zombie"
        enemies.append(Enemy(kind, Vec(x, y)))
    # thieves with pistols mid-map
    for _ in range(6):
        x = random.randint(28 * TILE, 60 * TILE)
        y = random.randint(18 * TILE, 28 * TILE)
        enemies.append(Enemy("thief_pistol", Vec(x, y)))
    # wild dogs around alleys
    for _ in range(5):
        x = random.randint(28 * TILE, 70 * TILE)
        y = random.choice([random.randint(2 * TILE, 18 * TILE),
                           random.randint(28 * TILE, 44 * TILE)])
        enemies.append(Enemy("wild_dog", Vec(x, y)))
    # more thieves near boss area
    for _ in range(5):
        x = random.randint(72 * TILE, 92 * TILE)
        y = random.randint(18 * TILE, 28 * TILE)
        enemies.append(Enemy("thief_pistol", Vec(x, y)))

    # Mini-boss: Zombie Bự Con
    boss = Enemy("boss2", Vec((W - 8) * TILE, 22 * TILE + 16))
    enemies.append(boss)

    return world, enemies, "Level 2 — Phố Cổ Bỏ Hoang", "downtown"


# ============================================================
# LEVEL 3 — Khu Công Nghiệp (Industrial)
# Dark concrete/ash floor with stacked containers and warehouses, plus a
# warehouse shop and rooftop sniper perches.
# ============================================================
def build_level3():
    W, H = 100, 56
    world = World(W, H, default_tile=T_ASH)
    # Side roads at top and bottom
    for y in range(2, 6):
        for x in range(W):
            world.set_tile(x, y, T_CONCRETE)
    for y in range(50, 54):
        for x in range(W):
            world.set_tile(x, y, T_CONCRETE)
    # Middle corridor
    for y in range(24, 32):
        for x in range(W):
            world.set_tile(x, y, T_CONCRETE)

    # Stripes of dirt
    for _ in range(80):
        cx = random.randint(0, W - 2)
        cy = random.randint(0, H - 2)
        if world.tiles[cy][cx] == T_ASH:
            world.tiles[cy][cx] = T_DIRT

    # Container stacks (rows)
    def add_stack(gx, gy, w, h, color):
        _add_container(world, gx * TILE, gy * TILE,
                       w * TILE, h * TILE, color=color)

    # Warehouse buildings
    _add_house(world, 4 * TILE, 8 * TILE, 12 * TILE, 14 * TILE,
               wall=(120, 120, 130), roof=(80, 80, 90))
    _add_house(world, 4 * TILE, 32 * TILE, 12 * TILE, 14 * TILE,
               wall=(120, 120, 130), roof=(80, 80, 90))
    _add_house(world, 84 * TILE, 8 * TILE, 12 * TILE, 14 * TILE,
               wall=(140, 100, 80), roof=(120, 60, 40))
    _add_house(world, 84 * TILE, 32 * TILE, 12 * TILE, 14 * TILE,
               wall=(140, 100, 80), roof=(120, 60, 40))

    # Shop (office) — building in center top
    shop_x, shop_y = 44, 8
    _add_house(world, shop_x * TILE, shop_y * TILE,
               12 * TILE, 12 * TILE,
               wall=(240, 230, 210), roof=(60, 140, 90))
    world.shop_rect = pygame.Rect((shop_x + 4) * TILE,
                                  (shop_y + 12 + 1) * TILE,
                                  4 * TILE, 2 * TILE)

    # Container stacks across middle area
    container_colors = [(180, 50, 40), (60, 110, 180), (220, 170, 50),
                        (50, 150, 100), (140, 60, 130)]
    layouts = [
        (18, 10, 3, 4), (18, 14, 3, 4), (22, 12, 3, 6),
        (28, 8, 3, 4), (28, 12, 3, 4), (32, 8, 3, 6),
        (60, 8, 3, 4), (60, 12, 3, 4), (64, 10, 3, 4),
        (68, 12, 3, 6), (72, 8, 3, 4), (76, 12, 3, 4),
        (18, 36, 3, 4), (18, 40, 3, 4), (22, 36, 3, 6),
        (28, 38, 3, 4), (28, 42, 3, 4),
        (60, 36, 3, 6), (64, 38, 3, 4), (64, 42, 3, 4),
        (68, 36, 3, 4), (72, 40, 3, 6), (76, 36, 3, 4),
    ]
    for i, (x, y, w, h) in enumerate(layouts):
        add_stack(x, y, w, h, container_colors[i % len(container_colors)])

    # Machines (large industrial objects)
    for gx, gy in [(36, 16), (52, 16), (36, 38), (52, 38)]:
        world.add_solid(Solid(pygame.Rect(gx * TILE, gy * TILE,
                                          4 * TILE, 4 * TILE), "machine"))

    # Crates around for ammo loot
    for gx, gy in [(20, 28), (30, 28), (45, 27),
                   (60, 28), (75, 28), (88, 27),
                   (12, 26), (8, 28)]:
        world.add_solid(Solid(pygame.Rect(gx * TILE, gy * TILE,
                                          TILE, TILE), "crate"))

    # Drums
    for gx, gy in [(20, 26), (40, 25), (62, 26), (80, 25)]:
        _add_drum(world, gx * TILE, gy * TILE)

    # Pickups
    _scatter_gold(world, pygame.Rect(4 * TILE, 24 * TILE,
                                     90 * TILE, 8 * TILE), 18, 20)
    world.add_pickup(Pickup(Vec(30 * TILE, 28 * TILE), P_MEDKIT))
    world.add_pickup(Pickup(Vec(60 * TILE, 28 * TILE), P_MEDKIT))
    world.add_pickup(Pickup(Vec(86 * TILE, 28 * TILE), P_MEDKIT))
    for x in (16, 32, 50, 70, 88):
        world.add_pickup(Pickup(Vec(x * TILE, 28 * TILE), P_AMMO))

    # Decals
    for _ in range(80):
        x = random.randint(0, W * TILE - 8)
        y = random.randint(0, H * TILE - 8)
        ti = x // TILE
        tj = y // TILE
        if 0 <= ti < W and 0 <= tj < H and world.tiles[tj][ti] in (T_ASH, T_CONCRETE):
            world.add_decal(Decal(pygame.Rect(x, y, 12, 12), "puddle"))

    world.spawn = Vec(3 * TILE, 28 * TILE)
    world.exit_rect = pygame.Rect((W - 4) * TILE, 26 * TILE,
                                  3 * TILE, 5 * TILE)
    world.exit_locked = True

    enemies = []
    # SMG minions in mid area
    for _ in range(8):
        x = random.randint(18 * TILE, 60 * TILE)
        y = random.randint(20 * TILE, 36 * TILE)
        enemies.append(Enemy("minion_smg", Vec(x, y)))
    # snipers on raised positions (right side)
    for _ in range(4):
        x = random.randint(60 * TILE, 88 * TILE)
        y = random.choice([10 * TILE, 42 * TILE])
        enemies.append(Enemy("sniper", Vec(x, y)))
    # wild dogs roaming
    for _ in range(6):
        x = random.randint(20 * TILE, 80 * TILE)
        y = random.randint(20 * TILE, 38 * TILE)
        enemies.append(Enemy("wild_dog", Vec(x, y)))
    # extra mid-range pistol thieves
    for _ in range(6):
        x = random.randint(24 * TILE, 80 * TILE)
        y = random.randint(20 * TILE, 36 * TILE)
        enemies.append(Enemy("thief_pistol", Vec(x, y)))

    # Mini-boss: Hổ Vương near right
    boss = Enemy("boss3", Vec((W - 8) * TILE, 28 * TILE))
    enemies.append(boss)

    return world, enemies, "Level 3 — Khu Công Nghiệp", "industrial"


# ============================================================
# LEVEL 4 — Hang Ổ Trùm (Boss Lair)
# Walled compound: outer yard with hedges + entrance, inner arena with the
# kidnapped dog cage and the boss.
# ============================================================
def build_level4():
    W, H = 90, 55
    world = World(W, H, default_tile=T_GRASS_DARK)
    # Stone paths
    for y in range(26, 30):
        for x in range(W):
            world.set_tile(x, y, T_CONCRETE)
    # Outer entrance gravel
    for x in range(0, 20):
        for y in range(24, 32):
            world.set_tile(x, y, T_DIRT)
    # Inner courtyard tile
    for x in range(50, 86):
        for y in range(14, 42):
            world.set_tile(x, y, T_FLOOR_TILE)

    # Outer wall (compound)
    # left half open, right half is the mansion compound
    # Boundary walls of the compound
    for x in range(48, 49):
        for y in range(12, 44):
            world.add_solid(Solid(pygame.Rect(x * TILE, y * TILE,
                                              TILE, TILE), "wall",
                                  color=(110, 95, 75)))
    for x in range(86, 87):
        for y in range(12, 44):
            world.add_solid(Solid(pygame.Rect(x * TILE, y * TILE,
                                              TILE, TILE), "wall",
                                  color=(110, 95, 75)))
    for y in range(12, 13):
        for x in range(48, 87):
            world.add_solid(Solid(pygame.Rect(x * TILE, y * TILE,
                                              TILE, TILE), "wall",
                                  color=(110, 95, 75)))
    for y in range(43, 44):
        for x in range(48, 87):
            world.add_solid(Solid(pygame.Rect(x * TILE, y * TILE,
                                              TILE, TILE), "wall",
                                  color=(110, 95, 75)))
    # Gate gap in left wall around y=26-30 (mid)
    # already drawn as solid 48 col - leave gap
    # Remove solids at gap rows
    world.solids = [s for s in world.solids if not (
        s.kind == "wall" and s.rect.left == 48 * TILE
        and 26 * TILE <= s.rect.top <= 29 * TILE)]

    # Mansion (huge house at right)
    _add_house(world, 70 * TILE, 16 * TILE, 14 * TILE, 24 * TILE,
               wall=(220, 200, 170), roof=(120, 30, 40))
    # Side pavilions
    _add_house(world, 52 * TILE, 16 * TILE, 8 * TILE, 8 * TILE,
               wall=(200, 180, 150), roof=(80, 50, 40))
    _add_house(world, 52 * TILE, 32 * TILE, 8 * TILE, 8 * TILE,
               wall=(200, 180, 150), roof=(80, 50, 40))

    # Fountain (machine)
    world.add_solid(Solid(pygame.Rect(62 * TILE, 26 * TILE,
                                      6 * TILE, 4 * TILE), "machine"))

    # Outside trees, decorative
    for x in [4, 12, 24, 36, 40]:
        for y in [8, 18, 38, 46]:
            _add_tree(world, x * TILE, y * TILE, r=22)

    # Crates / drums around the compound
    for gx, gy in [(54, 14), (62, 14), (78, 14),
                   (54, 41), (62, 41), (78, 41),
                   (50, 22), (50, 30)]:
        world.add_solid(Solid(pygame.Rect(gx * TILE, gy * TILE,
                                          TILE, TILE), "crate"))
    for gx, gy in [(58, 26), (68, 22), (80, 26)]:
        _add_drum(world, gx * TILE, gy * TILE)

    # DOG cage near boss (inside mansion)
    dog_rect = pygame.Rect(76 * TILE, 22 * TILE, 80, 70)
    world.dog_rect = dog_rect

    # Decals (fancy floor pattern)
    for _ in range(120):
        x = random.randint(50 * TILE, 86 * TILE - 8)
        y = random.randint(14 * TILE, 42 * TILE - 8)
        world.add_decal(Decal(pygame.Rect(x, y, 6, 6), "flower",
                              color=random.choice([(140, 100, 200),
                                                   (240, 80, 80),
                                                   (250, 200, 60),
                                                   (180, 200, 240)])))

    # Pickups
    _scatter_gold(world, pygame.Rect(50 * TILE, 14 * TILE,
                                     36 * TILE, 28 * TILE), 20, 25)
    world.add_pickup(Pickup(Vec(55 * TILE, 22 * TILE), P_MEDKIT))
    world.add_pickup(Pickup(Vec(55 * TILE, 35 * TILE), P_MEDKIT))
    world.add_pickup(Pickup(Vec(82 * TILE, 32 * TILE), P_MEDKIT))
    for x in [56, 64, 74]:
        world.add_pickup(Pickup(Vec(x * TILE, 28 * TILE), P_AMMO))

    world.spawn = Vec(4 * TILE, 28 * TILE)
    # Exit is the dog rescue area itself; "exit" used as victory point.
    world.exit_rect = dog_rect.inflate(40, 40)
    world.exit_locked = True   # unlocked after boss

    enemies = []
    # outer yard tigers + minions
    for _ in range(3):
        x = random.randint(6 * TILE, 40 * TILE)
        y = random.randint(20 * TILE, 36 * TILE)
        enemies.append(Enemy("tiger", Vec(x, y)))
    for _ in range(4):
        x = random.randint(6 * TILE, 40 * TILE)
        y = random.randint(18 * TILE, 38 * TILE)
        enemies.append(Enemy("minion_shotgun", Vec(x, y)))
    for _ in range(4):
        x = random.randint(8 * TILE, 42 * TILE)
        y = random.randint(18 * TILE, 38 * TILE)
        enemies.append(Enemy("minion_smg", Vec(x, y)))
    # inner compound minions
    for _ in range(3):
        x = random.randint(54 * TILE, 80 * TILE)
        y = random.choice([18 * TILE, 38 * TILE])
        enemies.append(Enemy("minion_shotgun", Vec(x, y)))
    # boss
    boss = Enemy("boss_final", Vec(78 * TILE, 28 * TILE))
    enemies.append(boss)

    return world, enemies, "Level 4 — Hang Ổ Trùm", "boss_lair"


# ============================================================
LEVEL_BUILDERS = [build_level1, build_level2, build_level3, build_level4]
