"""Player and Thief entities."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
import math
from typing import Dict, List, Optional, Tuple

import pygame

from . import audio
from . import sprites
from . import settings as S
from .maze import Cell, HIDE, Maze
from .pathfinding import astar, bfs, line_of_sight


def cell_to_pixel(c: Cell) -> Tuple[float, float]:
    return c[0] * S.TILE + S.TILE / 2, c[1] * S.TILE + S.TILE / 2


def pixel_to_cell(px: float, py: float) -> Cell:
    return int(px // S.TILE), int(py // S.TILE)


@dataclass
class Player:
    x: float
    y: float
    hp: int = S.PLAYER_HP_MAX
    keys: int = 0
    invuln: int = 0
    facing: int = 0  # 0=down 1=up 2=left 3=right
    anim_t: int = 0
    dfs_path: List[Cell] = field(default_factory=list)
    dfs_timer: int = 0
    dfs_cooldown: int = 0
    # New shop features
    skin: str = "Boy"
    coins: int = 0
    speed_boost: bool = False
    teleport_skill: bool = False
    has_gun: bool = False
    bullets: int = 0
    stop_time_skill: bool = False
    stop_time_timer: int = 0 # frames left for time stop

    def cell(self) -> Cell:
        return pixel_to_cell(self.x, self.y)

    def update(self, keys, maze: Maze) -> None:
        if self.invuln > 0:
            self.invuln -= 1
        if self.dfs_timer > 0:
            self.dfs_timer -= 1
        if self.dfs_cooldown > 0:
            self.dfs_cooldown -= 1
        dx = dy = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= S.PLAYER_SPEED
            self.facing = 2
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += S.PLAYER_SPEED
            self.facing = 3
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= S.PLAYER_SPEED
            self.facing = 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += S.PLAYER_SPEED
            self.facing = 0
        speed = S.PLAYER_SPEED * (1.5 if self.speed_boost else 1.0)
        if dx and dy:
            dx *= 0.7071
            dy *= 0.7071
        
        dx *= speed / S.PLAYER_SPEED
        dy *= speed / S.PLAYER_SPEED

        self._move_axis(dx, 0.0, maze)
        self._move_axis(0.0, dy, maze)
        if dx or dy:
            self.anim_t = (self.anim_t + 1) % 30

    def _move_axis(self, dx: float, dy: float, maze: Maze) -> None:
        if dx == 0 and dy == 0:
            return
        # collision: treat the player as a circle of radius r
        r = S.TILE * 0.28  # reduced for smoother movement
        nx, ny = self.x + dx, self.y + dy
        
        # Check collision
        collided = False
        corners = [
            (nx - r, ny - r),
            (nx + r, ny - r),
            (nx - r, ny + r),
            (nx + r, ny + r),
        ]
        for cx, cy in corners:
            if maze.is_wall(pixel_to_cell(cx, cy)):
                collided = True
                break
        
        if not collided:
            self.x, self.y = nx, ny
            return

        # If we collided, try to "nudge" the player to allow sliding around corners
        # This makes it easier to enter 1-tile wide corridors
        if dx != 0:
            # Try nudging up/down
            for nudge in [1, -1, 2, -2, 3, -3, 4, -4]:
                if not self._check_collision(nx, self.y + nudge, r, maze):
                    self.x = nx
                    self.y += nudge * 0.5  # smooth nudge
                    return
        if dy != 0:
            # Try nudging left/right
            for nudge in [1, -1, 2, -2, 3, -3, 4, -4]:
                if not self._check_collision(self.x + nudge, ny, r, maze):
                    self.y = ny
                    self.x += nudge * 0.5
                    return

    def _check_collision(self, x: float, y: float, r: float, maze: Maze) -> bool:
        for cx, cy in [(x-r, y-r), (x+r, y-r), (x-r, y+r), (x+r, y+r)]:
            if maze.is_wall(pixel_to_cell(cx, cy)):
                return True
        return False

    def take_hit(self) -> bool:
        if self.invuln > 0:
            return False
        self.hp -= 1
        audio.play_hurt()
        self.invuln = S.INVULN_FRAMES
        return True

    def draw(self, surf: pygame.Surface, cam: Tuple[float, float]) -> None:
        skin_data = sprites.PLAYER_SKINS.get(self.skin, sprites.PLAYER_SKINS["Boy"])
        frame = skin_data["A" if self.anim_t < 15 else "B"]
        if self.invuln and (self.invuln // 5) % 2 == 0:
            return
        px = int(self.x - cam[0])
        py = int(self.y - cam[1])
        rect = frame.get_rect(center=(px, py))
        surf.blit(frame, rect)

    def teleport_to_hideout(self, maze: Maze) -> bool:
        hideouts = [
            (x, y)
            for y in range(maze.height)
            for x in range(maze.width)
            if maze.grid[y][x] == HIDE
        ]
        if not hideouts: return False
        import random
        target = random.choice(hideouts)
        self.x, self.y = cell_to_pixel(target)
        return True


PATROL = "patrol"
CHASE = "chase"
RETURN = "return"


@dataclass
class Thief:
    x: float
    y: float
    patrol: List[Cell]
    rng: random.Random
    safe_zone_origin: Cell = (0, 0)
    state: str = PATROL
    path: List[Cell] = field(default_factory=list)
    target_idx: int = 0
    chase_timer: int = 0
    label: str = "BFS"  # for debug overlay
    last_seen: Optional[Cell] = None
    # simple movement target in pixel coords
    move_target: Optional[Tuple[float, float]] = None
    # path drawn as beam when dog is freed
    visible_path: List[Cell] = field(default_factory=list)
    # True when player is hidden (for AI logic)
    sees_player: bool = False
    # knife slash animation timer (increments when sees_player)
    slash_t: int = 0
    # current facing direction for sprite selection: "down" | "up" | "left" | "right"
    facing: str = "down"

    def cell(self) -> Cell:
        return pixel_to_cell(self.x, self.y)

    def _in_safe_zone(self, c: Cell) -> bool:
        sx, sy = self.safe_zone_origin
        return abs(c[0] - sx) + abs(c[1] - sy) <= S.START_SAFE_ZONE

    def _safe_cells(self, maze: Maze) -> List[Cell]:
        sx, sy = self.safe_zone_origin
        r = S.START_SAFE_ZONE
        out: List[Cell] = []
        for dy in range(-r, r + 1):
            rem = r - abs(dy)
            for dx in range(-rem, rem + 1):
                c = (sx + dx, sy + dy)
                if maze.in_bounds(c):
                    out.append(c)
        return out

    # ------------------- AI -------------------
    def update(self, maze: Maze, player: Player, dog_freed: bool = False) -> None:
        player_cell = player.cell()
        blocked = self._safe_cells(maze)
        
        # Once dog is freed, thieves always know player's position (high intensity!)
        # UNLESS the player hides in a house
        player_in_hide = maze.grid[player_cell[1]][player_cell[0]] == HIDE
        
        if dog_freed and not player_in_hide:
            self.state = CHASE
            self.sees_player = True
            self.last_seen = player_cell
            self.label = "A*"  # Shortest path mode
            # Use A* to find the shortest path to the player
            self.path = astar(maze, self.cell(), player_cell, blocked=blocked)
            self.visible_path = list(self.path)
            self._step_path(S.THIEF_CHASE_SPEED, maze)
            self.slash_t += 1
            return
        elif dog_freed and player_in_hide:
            # Player is hidden, thief loses interest and goes back to patrol
            if self.state == CHASE:
                self.state = RETURN
                self.path = []
                self.sees_player = False
                self.visible_path = []
        # The player is invisible while standing inside a hideout house, and
        # while inside the safe zone around the entrance.
        in_hideout = maze.grid[player_cell[1]][player_cell[0]] == HIDE
        in_safe = self._in_safe_zone(player_cell)
        sees = (not in_hideout) and (not in_safe) and line_of_sight(
            maze, self.cell(), player_cell, S.THIEF_VISION_RAD
        )
        self.sees_player = sees
        if sees:
            self.slash_t += 1   # advance knife spin while chasing
            self.state = CHASE
            self.chase_timer = 180  # ~3 seconds of pursuit even after losing sight
            self.label = "A*"
            self.last_seen = player_cell
            self.path = astar(maze, self.cell(), player_cell, blocked=blocked)
            self.visible_path = list(self.path)
            self._step_path(S.THIEF_CHASE_SPEED, maze)
            return

        if self.state == CHASE:
            # we lost sight – chase toward last known position only
            self.chase_timer -= 1
            target = self.last_seen or player_cell
            if self.chase_timer <= 0 or self.cell() == target or self._in_safe_zone(target):
                self.last_seen = None
                self.state = RETURN
                self.path = []
                self.visible_path = []
            else:
                if not self.path or len(self.path) < 2:
                    self.path = astar(maze, self.cell(), target, blocked=blocked)
                    self.visible_path = list(self.path)
                self._step_path(S.THIEF_CHASE_SPEED, maze)
                self.label = "A*"
                return

        if self.state == RETURN:
            self.label = "BFS"
            self.visible_path = []
            target = self.patrol[self.target_idx]
            if self.cell() == target:
                self.state = PATROL
                self.path = []
            else:
                if not self.path:
                    self.path = bfs(maze, self.cell(), target, blocked=blocked)
                self._step_path(S.THIEF_PATROL_SPEED, maze)
            return

        # PATROL
        self.label = "BFS"
        self.visible_path = []
        target = self.patrol[self.target_idx]
        if self.cell() == target:
            self.target_idx = (self.target_idx + 1) % len(self.patrol)
            self.path = bfs(maze, self.cell(), self.patrol[self.target_idx], blocked=blocked)
        else:
            if not self.path:
                self.path = bfs(maze, self.cell(), target, blocked=blocked)
            self._step_path(S.THIEF_PATROL_SPEED, maze)

    def _step_path(self, speed: float, maze: Maze) -> None:
        # advance along path
        if not self.path:
            return
        # drop the first cell once we have stepped onto its centre
        if len(self.path) >= 1 and self.path[0] == self.cell():
            self.path.pop(0)
        if not self.path:
            return
        target_cell = self.path[0]
        tx, ty = cell_to_pixel(target_cell)
        ddx = tx - self.x
        ddy = ty - self.y
        dist = math.hypot(ddx, ddy)
        if dist < speed:
            self.x, self.y = tx, ty
        else:
            self.x += speed * ddx / dist
            self.y += speed * ddy / dist
        # update facing based on the dominant movement axis
        if abs(ddx) > abs(ddy):
            self.facing = "right" if ddx > 0 else "left"
        elif abs(ddy) > 0:
            self.facing = "down" if ddy > 0 else "up"

    def collides_with(self, player: Player) -> bool:
        return math.hypot(self.x - player.x, self.y - player.y) < S.TILE * 0.55

    def draw(self, surf: pygame.Surface, cam: Tuple[float, float], anim_t: int) -> None:
        ab = "A" if (anim_t // 12) % 2 == 0 else "B"
        key = f"{self.facing}_{ab}"
        frame = sprites.THIEF_FRAMES.get(key, sprites.THIEF_FRAMES[ab])
        cx = int(self.x - cam[0])
        cy = int(self.y - cam[1])
        rect = frame.get_rect(center=(cx, cy))
        surf.blit(frame, rect)

        # --- Knife animation when thief sees the player ---
        if self.sees_player and sprites.KNIFE_SPRITE:
            # slash_t drives a continuous spinning + slashing arc
            angle = -(self.slash_t * 9) % 360       # fast CCW spin
            # orbit radius pulses to mimic a slashing swipe
            orbit = int(S.TILE * 0.55 + S.TILE * 0.25 * math.sin(math.radians(self.slash_t * 12)))
            rad = math.radians(angle)
            kx = cx + int(math.cos(rad) * orbit)
            ky = cy + int(math.sin(rad) * orbit)

            # rotate the knife sprite to match the swing angle
            rotated = pygame.transform.rotate(sprites.KNIFE_SPRITE, angle)
            krect = rotated.get_rect(center=(kx, ky))
            surf.blit(rotated, krect)

            # white flash arc "slash line" across the thief for impact feel
            slash_phase = self.slash_t % 20   # 20-frame slash cycle
            if slash_phase < 8:               # only show during first half
                alpha = int(255 * (1 - slash_phase / 8.0))
                arc_surf = pygame.Surface((S.TILE * 2, S.TILE * 2), pygame.SRCALPHA)
                sweep_start = math.radians(angle - 40)
                sweep_end   = math.radians(angle + 10)
                num_steps = 12
                prev = None
                for step in range(num_steps + 1):
                    a = sweep_start + (sweep_end - sweep_start) * step / num_steps
                    lx = S.TILE + int(math.cos(a) * (S.TILE - 4))
                    ly = S.TILE + int(math.sin(a) * (S.TILE - 4))
                    if prev:
                        pygame.draw.line(arc_surf, (255, 255, 255, alpha), prev, (lx, ly), 3)
                    prev = (lx, ly)
                surf.blit(arc_surf, (cx - S.TILE, cy - S.TILE))
        else:
            # not chasing — reset timer so animation starts fresh next time
            self.slash_t = 0

        # tiny banner above thief showing which algorithm is active
        font = pygame.font.SysFont("monospace", 10, bold=True)
        color = S.TRAP_RED if self.label == "A*" else S.GOLD
        label = font.render(self.label, True, color)
        bg = pygame.Surface((label.get_width() + 4, label.get_height() + 2), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 160))
        bg.blit(label, (2, 1))
        surf.blit(bg, (rect.centerx - bg.get_width() // 2, rect.top - 14))


@dataclass
class Fireball:
    x: float
    y: float
    vx: float
    vy: float

    def update(self, maze: Maze) -> bool:
        self.x += self.vx
        self.y += self.vy
        cell = pixel_to_cell(self.x, self.y)
        if not maze.in_bounds(cell) or maze.is_wall(cell):
            return False
        return True

    def collides_with(self, player: Player) -> bool:
        return math.hypot(self.x - player.x, self.y - player.y) < S.TILE * 0.4

    def draw(self, surf: pygame.Surface, cam: Tuple[float, float]) -> None:
        if sprites.FIRE_SPRITE:
            rect = sprites.FIRE_SPRITE.get_rect(center=(int(self.x - cam[0]), int(self.y - cam[1])))
            surf.blit(sprites.FIRE_SPRITE, rect)


@dataclass
class Dragon:
    x: float
    y: float
    fire_timer: int = 0

    def cell(self) -> Cell:
        return pixel_to_cell(self.x, self.y)

    def update(self, maze: Maze, player: Player) -> Optional[Fireball]:
        self.fire_timer = max(0, self.fire_timer - 1)
        player_cell = player.cell()
        in_hideout = maze.grid[player_cell[1]][player_cell[0]] == HIDE
        if not in_hideout and line_of_sight(maze, self.cell(), player_cell, S.DRAGON_VISION_RAD):
            if self.fire_timer == 0:
                self.fire_timer = S.DRAGON_FIRE_RATE
                dx = player.x - self.x
                dy = player.y - self.y
                dist = math.hypot(dx, dy)
                if dist > 0:
                    vx = (dx / dist) * S.DRAGON_FIRE_SPEED
                    vy = (dy / dist) * S.DRAGON_FIRE_SPEED
                    return Fireball(self.x, self.y, vx, vy)
        return None

    def draw(self, surf: pygame.Surface, cam: Tuple[float, float]) -> None:
        if sprites.DRAGON_SPRITE:
            rect = sprites.DRAGON_SPRITE.get_rect(center=(int(self.x - cam[0]), int(self.y - cam[1])))
            surf.blit(sprites.DRAGON_SPRITE, rect)


@dataclass
class Bat:
    center_x: float
    center_y: float
    angle: float = 0.0
    x: float = 0.0
    y: float = 0.0

    def __post_init__(self):
        self.x = self.center_x
        self.y = self.center_y

    def update(self) -> None:
        self.angle += S.BAT_FLOAT_SPEED
        self.x = self.center_x + math.cos(self.angle) * S.BAT_FLOAT_RADIUS * S.TILE
        self.y = self.center_y + math.sin(self.angle) * S.BAT_FLOAT_RADIUS * S.TILE

    def collides_with(self, player: Player) -> bool:
        return math.hypot(self.x - player.x, self.y - player.y) < S.TILE * 0.4

    def draw(self, surf: pygame.Surface, cam: Tuple[float, float], anim_t: int) -> None:
        if sprites.BAT_FRAMES:
            frame = "A" if (anim_t // 10) % 2 == 0 else "B"
            img = sprites.BAT_FRAMES.get(frame, list(sprites.BAT_FRAMES.values())[0])
            rect = img.get_rect(center=(int(self.x - cam[0]), int(self.y - cam[1])))
            surf.blit(img, rect)


@dataclass
class Bullet:
    x: float
    y: float
    dx: float
    dy: float
    life: int = 120

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.life -= 1

    def draw(self, surf: pygame.Surface, cam: Tuple[float, float]):
        if sprites.BULLET_SPRITE:
            px = int(self.x - cam[0])
            py = int(self.y - cam[1])
            surf.blit(sprites.BULLET_SPRITE, (px - 5, py - 5))
