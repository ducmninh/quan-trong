"""BFS and A* pathfinding on a Maze grid."""
from __future__ import annotations

import heapq
from collections import deque
from typing import Dict, FrozenSet, Iterable, List, Optional, Set, Tuple

from .maze import Cell, Maze


def _reconstruct(came: Dict[Cell, Cell], goal: Cell) -> List[Cell]:
    path = [goal]
    while goal in came:
        goal = came[goal]
        path.append(goal)
    path.reverse()
    return path


def bfs(maze: Maze, start: Cell, goal: Cell, blocked: Optional[Iterable[Cell]] = None) -> List[Cell]:
    """Return the shortest unweighted path from start to goal (inclusive of both).
    Used by thieves to compute their patrol routes.

    `blocked` is an optional set of cells that cannot be entered (e.g. the safe
    zone around the player's spawn). The start cell is exempt so paths can
    always begin even if the searcher is somehow inside the safe zone."""
    if start == goal:
        return [start]
    if not maze.is_walkable(goal):
        return []
    blocked_set: Set[Cell] = set(blocked or ())
    frontier: deque[Cell] = deque([start])
    came: Dict[Cell, Cell] = {}
    visited = {start}
    while frontier:
        cur = frontier.popleft()
        for nxt in maze.neighbors4(cur):
            if nxt in visited or (nxt in blocked_set and nxt != goal):
                continue
            visited.add(nxt)
            came[nxt] = cur
            if nxt == goal:
                return _reconstruct(came, goal)
            frontier.append(nxt)
    return []


def _h(a: Cell, b: Cell) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(maze: Maze, start: Cell, goal: Cell, blocked: Optional[Iterable[Cell]] = None) -> List[Cell]:
    """A* path with Manhattan heuristic. Used by thieves while chasing."""
    if start == goal:
        return [start]
    if not maze.is_walkable(goal):
        return []
    blocked_set: Set[Cell] = set(blocked or ())
    open_heap: List[Tuple[int, int, Cell]] = []
    counter = 0
    heapq.heappush(open_heap, (_h(start, goal), counter, start))
    came: Dict[Cell, Cell] = {}
    g: Dict[Cell, int] = {start: 0}
    while open_heap:
        _, _, cur = heapq.heappop(open_heap)
        if cur == goal:
            return _reconstruct(came, goal)
        for nxt in maze.neighbors4(cur):
            if nxt in blocked_set and nxt != goal:
                continue
            ng = g[cur] + 1
            if ng < g.get(nxt, 1 << 30):
                g[nxt] = ng
                came[nxt] = cur
                f = ng + _h(nxt, goal)
                counter += 1
                heapq.heappush(open_heap, (f, counter, nxt))
    return []


def line_of_sight(maze: Maze, a: Cell, b: Cell, max_dist: int) -> bool:
    """Bresenham-style line-of-sight in the grid. Returns False if blocked by a
    wall or if the Manhattan distance exceeds max_dist."""
    if abs(a[0] - b[0]) + abs(a[1] - b[1]) > max_dist:
        return False
    x0, y0 = a
    x1, y1 = b
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        if (x0, y0) != a and maze.is_wall((x0, y0)):
            return False
        if (x0, y0) == (x1, y1):
            return True
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
def dfs(maze: Maze, start: Cell, goal: Cell, blocked: Optional[Iterable[Cell]] = None) -> List[Cell]:
    """Return a deep, winding path from start to goal using Depth First Search.
    Used for the player's 'Mystical Radar' ability."""
    if start == goal:
        return [start]
    if not maze.is_walkable(goal):
        return []
    blocked_set = set(blocked or ())
    stack: List[Cell] = [start]
    came: Dict[Cell, Cell] = {}
    visited = {start}
    
    # We shuffle neighbors to make DFS paths feel different each time
    import random
    
    while stack:
        cur = stack.pop()
        if cur == goal:
            return _reconstruct(came, goal)
        
        neighs = list(maze.neighbors4(cur))
        random.shuffle(neighs)
        for nxt in neighs:
            if nxt in visited or (nxt in blocked_set and nxt != goal):
                continue
            visited.add(nxt)
            came[nxt] = cur
            stack.append(nxt)
    return []
