"""Maze generation and grid helpers.

Cells:
  0 = floor   (walkable)
  1 = wall    (not walkable)
  2 = trap    (walkable but damages player)
  3 = hideout (walkable; thieves cannot see the player while standing on it)
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable, List, Tuple

Cell = Tuple[int, int]
FLOOR = 0
WALL = 1
TRAP = 2
HIDE = 3


@dataclass
class Maze:
    width: int
    height: int
    grid: List[List[int]]

    def in_bounds(self, c: Cell) -> bool:
        x, y = c
        return 0 <= x < self.width and 0 <= y < self.height

    def is_wall(self, c: Cell) -> bool:
        x, y = c
        return self.grid[y][x] == WALL

    def is_walkable(self, c: Cell) -> bool:
        if not self.in_bounds(c):
            return False
        return self.grid[c[1]][c[0]] != WALL

    def neighbors4(self, c: Cell) -> Iterable[Cell]:
        x, y = c
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height and self.grid[ny][nx] != WALL:
                yield (nx, ny)

    def floor_cells(self) -> List[Cell]:
        return [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
            if self.grid[y][x] != WALL
        ]


def generate_maze(size: int, rng: random.Random | None = None) -> Maze:
    """Generate a perfect maze using recursive backtracking, then knock down a few
    extra walls so the maze has loops (more interesting AI behavior)."""
    if size % 2 == 0:
        size += 1
    rng = rng or random.Random()

    grid = [[WALL for _ in range(size)] for _ in range(size)]

    def carve(x: int, y: int) -> None:
        grid[y][x] = FLOOR
        dirs = [(2, 0), (-2, 0), (0, 2), (0, -2)]
        rng.shuffle(dirs)
        for dx, dy in dirs:
            nx, ny = x + dx, y + dy
            if 1 <= nx < size - 1 and 1 <= ny < size - 1 and grid[ny][nx] == WALL:
                grid[y + dy // 2][x + dx // 2] = FLOOR
                carve(nx, ny)

    # iterative version to avoid recursion depth on big maps
    stack = [(1, 1)]
    grid[1][1] = FLOOR
    while stack:
        x, y = stack[-1]
        dirs = [(2, 0), (-2, 0), (0, 2), (0, -2)]
        rng.shuffle(dirs)
        carved = False
        for dx, dy in dirs:
            nx, ny = x + dx, y + dy
            if 1 <= nx < size - 1 and 1 <= ny < size - 1 and grid[ny][nx] == WALL:
                grid[y + dy // 2][x + dx // 2] = FLOOR
                grid[ny][nx] = FLOOR
                stack.append((nx, ny))
                carved = True
                break
        if not carved:
            stack.pop()

    # add some loops to make the maze less linear
    extra = max(2, size // 3)
    attempts = 0
    while extra > 0 and attempts < 500:
        attempts += 1
        x = rng.randrange(1, size - 1)
        y = rng.randrange(1, size - 1)
        if grid[y][x] != WALL:
            continue
        # only knock down inner walls that bridge two floor tiles on opposite sides
        horizontal = grid[y][x - 1] == FLOOR and grid[y][x + 1] == FLOOR
        vertical = grid[y - 1][x] == FLOOR and grid[y + 1][x] == FLOOR
        if horizontal != vertical:
            grid[y][x] = FLOOR
            extra -= 1

    return Maze(size, size, grid)


def place_traps(maze: Maze, count: int, forbidden: Iterable[Cell], rng: random.Random) -> List[Cell]:
    forbidden_set = set(forbidden)
    candidates = [c for c in maze.floor_cells() if c not in forbidden_set]
    rng.shuffle(candidates)
    placed = []
    for c in candidates:
        if len(placed) >= count:
            break
        # avoid placing traps on the unique path between far corners by simply
        # spreading them out a bit (no two traps within 2 tiles)
        if any(abs(c[0] - p[0]) + abs(c[1] - p[1]) < 2 for p in placed):
            continue
        x, y = c
        maze.grid[y][x] = TRAP
        placed.append(c)
    return placed
