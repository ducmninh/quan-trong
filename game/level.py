"""Build a level: maze, keys, traps, hideouts, decor, cage, dog, thieves."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from . import settings as S
from . import entities
from .maze import Cell, HIDE, Maze, FLOOR, TRAP, generate_maze, place_traps


@dataclass
class Level:
    config: dict
    maze: Maze
    player_start: Cell
    cage_cell: Cell
    keys: List[Cell] = field(default_factory=list)
    coins: List[Cell] = field(default_factory=list)
    hideouts: List[Cell] = field(default_factory=list)
    thieves: List[entities.Thief] = field(default_factory=list)
    dragons: List[entities.Dragon] = field(default_factory=list)
    bats: List[entities.Bat] = field(default_factory=list)
    trees: List[Cell] = field(default_factory=list)
    # decor: cell -> overlay index into sprites.DECOR_OVERLAYS
    decor: Dict[Cell, int] = field(default_factory=dict)
    lanterns: List[Cell] = field(default_factory=list)
    # Decorative fire dragons placed outside the maze boundary
    fire_dragons: List[Tuple[float, float, int]] = field(default_factory=list)
    rng: random.Random = field(default_factory=random.Random)


def _farthest_pair(maze: Maze) -> Tuple[Cell, Cell]:
    h, w = maze.height, maze.width
    return (1, 1), (w - 2, h - 2)


def _spread_cells(candidates: List[Cell], n: int, rng: random.Random, min_dist: int = 3) -> List[Cell]:
    rng.shuffle(candidates)
    chosen: List[Cell] = []
    for c in candidates:
        if all(abs(c[0] - p[0]) + abs(c[1] - p[1]) >= min_dist for p in chosen):
            chosen.append(c)
        if len(chosen) >= n:
            break
    if len(chosen) < n:
        for c in candidates:
            if c not in chosen:
                chosen.append(c)
            if len(chosen) >= n:
                break
    return chosen


def _perimeter_loop(maze: Maze, start: Cell, rng: random.Random) -> List[Cell]:
    """Build a clockwise loop of waypoints around the outer ring of the maze."""
    size = maze.width
    walkable = set(maze.floor_cells())
    safe = S.START_SAFE_ZONE + 1
    inset = 1
    far = size - 1 - inset

    def closest(target: Cell) -> Cell:
        return min(walkable, key=lambda c: (c[0] - target[0]) ** 2 + (c[1] - target[1]) ** 2)

    anchors_raw: List[Cell] = []
    for x in (size // 4, size // 2, 3 * size // 4, far):
        anchors_raw.append((x, inset))
    for y in (size // 4, size // 2, 3 * size // 4):
        anchors_raw.append((far, y))
    for x in (far, 3 * size // 4, size // 2, size // 4):
        anchors_raw.append((x, far))
    for y in (3 * size // 4, size // 2):
        anchors_raw.append((inset, y))

    loop: List[Cell] = []
    for a in anchors_raw:
        c = closest(a)
        if abs(c[0] - start[0]) + abs(c[1] - start[1]) < safe:
            continue
        if loop and c == loop[-1]:
            continue
        loop.append(c)

    if len(loop) < 4:
        far_cells = sorted(
            (c for c in walkable
             if abs(c[0] - start[0]) + abs(c[1] - start[1]) >= safe + 2),
            key=lambda c: -(abs(c[0] - start[0]) + abs(c[1] - start[1])),
        )
        loop = far_cells[:4]
    return loop


def _place_fire_dragons_outside(maze: Maze, count: int, rng: random.Random) -> List[Tuple[float, float, int]]:
    """Place decorative fire-breathing dragons outside the maze boundary walls."""
    result: List[Tuple[float, float, int]] = []
    size = maze.width
    positions = []

    # Top edge
    for x in range(2, size - 2, max(3, size // 4)):
        positions.append((x * S.TILE, -S.TILE * 1.5, 0))
    # Bottom edge
    for x in range(2, size - 2, max(3, size // 4)):
        positions.append((x * S.TILE, (size + 0.5) * S.TILE, 2))
    # Left edge
    for y in range(2, size - 2, max(3, size // 4)):
        positions.append((-S.TILE * 1.5, y * S.TILE, 1))
    # Right edge
    for y in range(2, size - 2, max(3, size // 4)):
        positions.append(((size + 0.5) * S.TILE, y * S.TILE, 3))

    rng.shuffle(positions)
    for px, py, facing in positions[:count]:
        result.append((px, py, facing))
    return result


def build_level(index: int, seed: int | None = None) -> Level:
    cfg = S.LEVELS[index]
    rng = random.Random(seed if seed is not None else 100 + index)
    maze = generate_maze(cfg["size"], rng)
    start, cage = _farthest_pair(maze)

    # Ensure start and cage are not "stuck" in a 1-exit corner
    for center in [start, cage]:
        neighs = [n for n in maze.neighbors4(center)]
        if len(neighs) < 2:
            x, y = center
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = x + dx, y + dy
                if maze.in_bounds((nx, ny)) and maze.is_wall((nx, ny)):
                    maze.grid[ny][nx] = FLOOR
                    break

    floor = [c for c in maze.floor_cells() if c not in (start, cage)]

    # ----- keys ------------------------------------------------------------ #
    keys = _spread_cells(list(floor), cfg["keys"], rng, min_dist=max(3, cfg["size"] // 5))

    # ----- hideouts -------------------------------------------------------- #
    forbidden = set(keys) | {start, cage}
    hide_candidates = [
        c for c in floor
        if c not in forbidden
        and abs(c[0] - start[0]) + abs(c[1] - start[1]) >= 3
    ]
    hideouts = _spread_cells(hide_candidates, cfg.get("hideouts", 0), rng,
                              min_dist=max(3, cfg["size"] // 4))
    for hx, hy in hideouts:
        maze.grid[hy][hx] = HIDE

    # ----- coins ----------------------------------------------------------- #
    coin_count = cfg.get("coins", 10)
    walkable_for_coins = [c for c in floor if c not in (set(keys) | set(hideouts) | {start, cage})]
    coins = _spread_cells(walkable_for_coins, coin_count, rng, min_dist=1)

    # ----- traps ----------------------------------------------------------- #
    forbidden = set(keys) | set(coins) | set(hideouts) | {start, cage}
    place_traps(maze, cfg.get("traps", 0), forbidden, rng)

    # ----- thieves --------------------------------------------------------- #
    loop = _perimeter_loop(maze, start, rng)
    n_thieves = cfg["thieves"]
    thieves: List[entities.Thief] = []
    if loop:
        step = max(1, len(loop) // n_thieves)
        for i in range(n_thieves):
            offset = (i * step) % len(loop)
            patrol = loop[offset:] + loop[:offset]
            spawn = patrol[0]
            sx, sy = entities.cell_to_pixel(spawn)
            thieves.append(entities.Thief(
                x=sx, y=sy, patrol=patrol, rng=rng, safe_zone_origin=start,
            ))

    # ----- decorative overlays + lanterns ---------------------------------- #
    decor: Dict[Cell, int] = {}
    walkable = [c for c in maze.floor_cells()
                if maze.grid[c[1]][c[0]] not in (TRAP, HIDE)
                and c not in (start, cage)
                and c not in keys
                and c not in coins]
    rng.shuffle(walkable)
    decor_count = max(6, len(walkable) // 12)
    for c in walkable[:decor_count]:
        decor[c] = rng.randrange(5)

    lantern_candidates = [
        c for c in maze.floor_cells()
        if c not in decor and c not in (start, cage) and c not in keys and c not in coins
        and any(maze.grid[c[1] + dy][c[0] + dx] == 1
                for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1))
                if maze.in_bounds((c[0] + dx, c[1] + dy)))
    ]
    n_lanterns = max(3, cfg["size"] // 4)
    lanterns = _spread_cells(lantern_candidates, n_lanterns, rng,
                             min_dist=max(4, cfg["size"] // 5))

    # ----- dragons (decorative, inside maze from level 3+) ----------------- #
    dragons: List[entities.Dragon] = []
    bats: List[entities.Bat] = []
    trees: List[Cell] = []

    if index >= 2:
        dragon_count = index - 1
        dragon_cells = _spread_cells(list(walkable), dragon_count, rng, min_dist=6)
        for dc in dragon_cells:
            dx, dy = entities.cell_to_pixel(dc)
            dragons.append(entities.Dragon(dx, dy))
            if dc in walkable:
                walkable.remove(dc)

    # Bats (decorative)
    bat_count = cfg.get("bats", index + 1)
    bat_cells = _spread_cells(list(walkable), bat_count, rng, min_dist=4)
    for bc in bat_cells:
        bx, by = entities.cell_to_pixel(bc)
        bats.append(entities.Bat(bx, by, angle=rng.random() * 6.28))
        if bc in walkable:
            walkable.remove(bc)

    # Trees
    tree_count = cfg["size"] // 2
    tree_cells = _spread_cells(list(walkable), tree_count, rng, min_dist=3)
    for tc in tree_cells:
        trees.append(tc)
        if tc in walkable:
            walkable.remove(tc)

    # ----- fire dragons outside the maze (decorative) ---------------------- #
    fire_dragon_count = max(2, index + 2)
    fire_dragons = _place_fire_dragons_outside(maze, fire_dragon_count, rng)

    return Level(config=cfg, maze=maze, player_start=start, cage_cell=cage,
                 keys=keys, coins=coins, hideouts=hideouts, thieves=thieves,
                 dragons=dragons, bats=bats, trees=trees,
                 decor=decor, lanterns=lanterns, fire_dragons=fire_dragons, rng=rng)
