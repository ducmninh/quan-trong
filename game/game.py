"""Main Game class with a simple state machine."""
from __future__ import annotations

import math
import random
from typing import List, Optional

import pygame

from . import audio
from . import fonts
from . import settings as S
from . import sprites
from . import story
from . import ui
from .entities import Player, Thief, Bullet, cell_to_pixel, pixel_to_cell
from .level import Level, build_level
from .maze import Maze, FLOOR, HIDE, TRAP, WALL
from .pathfinding import dfs

# Import entities module for type references
from . import entities

# states
TITLE = "title"
INTRO = "intro"
LEVEL_INTRO = "level_intro"
PLAY = "play"
LEVEL_DONE = "level_done"
OUTRO = "outro"
WIN = "win"
LOSE = "lose"
CHAR_SELECT = "char_select"
SHOP = "shop"
TRANSITION = "transition"  # smooth transition between levels


class Game:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.state = TITLE
        self.level_idx = 0
        self.level: Optional[Level] = None
        self.player: Optional[Player] = None
        self.title = ui.TitleScreen()
        self.char_select = ui.CharSelect()
        self.shop: Optional[ui.ShopScreen] = None
        self.hud = ui.HUD()
        self.intro = story.ChatScene(story.INTRO, "Dog Rescue")
        self.level_intro: Optional[story.ChatScene] = None
        self.outro: Optional[story.ChatScene] = None
        self.end: Optional[ui.EndScreen] = None
        self.anim_t = 0
        self.message = ""
        self.message_timer = 0
        self.cam = (0.0, 0.0)
        self.dog_freed = False
        self.fireballs: List[entities.Fireball] = []
        self.bullets: List[Bullet] = []
        self.fullscreen = False
        self.rescued_dogs: int = 0
        self.player_skin = "Boy"
        self.fire_dragon_anim_t = 0
        # Transition timer for smooth level changes
        self.transition_timer = 0
        self.transition_alpha = 0
        self.level_done_timer = 0  # auto-advance from LEVEL_DONE to SHOP
        self.shop_enter_cooldown = 0  # prevent instant SPACE in shop

    # --------------------- helpers --------------------- #
    def _begin_level(self, idx: int) -> None:
        self.level_idx = idx
        self.level = build_level(self.level_idx)
        old_coins = self.player.coins if self.player else 0
        old_skin = self.player.skin if self.player else self.player_skin
        old_speed = self.player.speed_boost if self.player else False
        old_teleport = self.player.teleport_skill if self.player else False
        old_gun = self.player.has_gun if self.player else False
        old_bullets = self.player.bullets if self.player else 0
        old_stop = self.player.stop_time_skill if self.player else False

        self.player = Player(
            *cell_to_pixel(self.level.player_start),
            hp=S.PLAYER_HP_MAX,
            coins=old_coins,
            skin=old_skin,
            speed_boost=old_speed,
            teleport_skill=old_teleport,
            has_gun=old_gun,
            bullets=old_bullets,
            stop_time_skill=old_stop
        )
        self.bullets = []
        self.fireballs = []
        self.dog_freed = False
        self.cam = (0.0, 0.0)
        self.level_done_timer = 0

        self.level_intro = story.ChatScene(
            [story.Bubble(story.HER, story.LEVEL_INTROS[idx])],
            f"Man {idx + 1}: {self.level.config['name']}",
        )
        self.message = ""
        self.message_timer = 0

        # Transition effect: fade in
        self.state = TRANSITION
        self.transition_timer = 40
        self.transition_alpha = 255

        audio.play_bgm(idx)

    def _finish_transition(self) -> None:
        self.state = LEVEL_INTRO

    def _set_message(self, msg: str, frames: int = 120) -> None:
        self.message = msg
        self.message_timer = frames

    # --------------------- input ----------------------- #
    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.QUIT:
            return False
        if event.type != pygame.KEYDOWN:
            return True
        if event.key == pygame.K_ESCAPE:
            if self.state in (TITLE, WIN, LOSE):
                return False
            audio.stop_bgm()
            self.state = TITLE
            return True

        if event.key == pygame.K_f:
            self.fullscreen = not self.fullscreen
            if self.fullscreen:
                pygame.display.set_mode((S.SCREEN_W, S.SCREEN_H), pygame.FULLSCREEN)
            else:
                pygame.display.set_mode((S.SCREEN_W, S.SCREEN_H))
            return True

        if self.state == TITLE:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.state = CHAR_SELECT
        elif self.state == CHAR_SELECT:
            if event.key == pygame.K_LEFT:
                self.char_select.idx = (self.char_select.idx - 1) % len(self.char_select.skins)
            if event.key == pygame.K_RIGHT:
                self.char_select.idx = (self.char_select.idx + 1) % len(self.char_select.skins)
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                skin = self.char_select.skins[self.char_select.idx]
                self.player_skin = skin
                self.rescued_dogs = 0
                self.intro = story.ChatScene(story.INTRO, "Dog Rescue")
                self.state = INTRO
        elif self.state == SHOP:
            if self.shop_enter_cooldown > 0:
                return True  # ignore all input during cooldown
            if event.key == pygame.K_UP:
                self.shop.idx = (self.shop.idx - 1) % len(self.shop.items)
            if event.key == pygame.K_DOWN:
                self.shop.idx = (self.shop.idx + 1) % len(self.shop.items)
            if event.key == pygame.K_RETURN:
                item = self.shop.items[self.shop.idx]
                if item["id"] not in self.shop.bought and self.shop.coins >= item["cost"]:
                    self.shop.coins -= item["cost"]
                    self.shop.bought.add(item["id"])
                    self.player.coins = self.shop.coins
                    if item["id"] == "speed":
                        self.player.speed_boost = True
                    if item["id"] == "key":
                        self.player.keys += 1
                    if item["id"] == "teleport":
                        self.player.teleport_skill = True
                    if item["id"] == "gun":
                        self.player.has_gun = True
                        self.player.bullets += 10
                    if item["id"] == "stop":
                        self.player.stop_time_skill = True
            if event.key in (pygame.K_SPACE, pygame.K_t):
                # Continue to next level from shop
                self._begin_level(self.level_idx + 1)
        elif self.state == INTRO:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.intro.advance()
                if self.intro.done():
                    self._begin_level(0)
        elif self.state == LEVEL_INTRO:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                if self.level_intro:
                    self.level_intro.advance()
                if not self.level_intro or self.level_intro.done():
                    self.state = PLAY
        elif self.state == PLAY:
            if event.key == pygame.K_e:
                self._try_interact()
            if event.key == pygame.K_r:
                self._begin_level(self.level_idx)
            if event.key == pygame.K_g:
                self._trigger_dfs()
            if event.key == pygame.K_t:
                if self.player.teleport_skill:
                    if self.player.teleport_to_hideout(self.level.maze):
                        self._set_message("Da dich chuyen toi nha tru an!", 60)
            if event.key == pygame.K_q:
                if self.player.stop_time_skill and self.player.stop_time_timer <= 0:
                    self.player.stop_time_timer = 300
                    audio.play_stop()
                    self._set_message("THOI GIAN NGUNG DONG!", 300)
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.player.has_gun and self.player.bullets > 0:
                    self.player.bullets -= 1
                    self._shoot_bullet()
        elif self.state == LEVEL_DONE:
            # Any key press advances to shop or outro
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_t):
                self._advance_from_level_done()
        elif self.state == OUTRO:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.outro.advance()
                if self.outro.done():
                    audio.stop_bgm()
                    self.end = ui.EndScreen(won=True)
                    self.state = WIN
        elif self.state == WIN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_r):
                self.state = TITLE
                self.level_idx = 0
                self.rescued_dogs = 0
        elif self.state == LOSE:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_r):
                self._begin_level(self.level_idx)
        return True

    def _advance_from_level_done(self) -> None:
        if self.level_idx + 1 < len(S.LEVELS):
            self.shop = ui.ShopScreen(self.player.coins, self.level_idx)
            self.state = SHOP
            self.shop_enter_cooldown = 30  # ~0.5s cooldown to prevent instant skip
        else:
            self.outro = story.ChatScene(story.OUTRO, "Dog Rescue")
            self.state = OUTRO

    # --------------------- update ---------------------- #
    def update(self) -> None:
        self.anim_t += 1
        self.fire_dragon_anim_t += 1
        if self.message_timer > 0:
            self.message_timer -= 1
            if self.message_timer == 0:
                self.message = ""

        if self.state == TITLE:
            self.title.update()
        elif self.state == CHAR_SELECT:
            self.char_select.update()
        elif self.state == SHOP:
            if self.shop_enter_cooldown > 0:
                self.shop_enter_cooldown -= 1
            if self.shop:
                self.shop.update()
        elif self.state == INTRO:
            self.intro.update()
        elif self.state == LEVEL_INTRO and self.level_intro:
            self.level_intro.update()
        elif self.state == TRANSITION:
            self._update_transition()
        elif self.state == PLAY:
            self._update_play()
        elif self.state == LEVEL_DONE:
            # Auto-advance to shop after 3 seconds if player doesn't press anything
            self.level_done_timer += 1
            if self.level_done_timer >= 180:  # 3 seconds
                self._advance_from_level_done()
        elif self.state == OUTRO and self.outro:
            self.outro.update()
        elif self.state in (WIN, LOSE) and self.end:
            self.end.update()

    def _update_transition(self) -> None:
        self.transition_timer -= 1
        self.transition_alpha = max(0, int(255 * (self.transition_timer / 40.0)))
        if self.transition_timer <= 0:
            self._finish_transition()

    def _try_interact(self) -> None:
        assert self.level and self.player
        cell = self.player.cell()

        # Interact with cage
        if cell == self.level.cage_cell:
            if self.player.keys >= self.level.config["keys"] and not self.dog_freed:
                self.dog_freed = True
                audio.play_alarm()
                self.level.maze.grid[0][1] = FLOOR
                dog_name = self.level.config.get("dog_name", "cho")
                is_mother = self.level.config.get("is_mother", False)
                if is_mother:
                    self._set_message(f"Da giai cuu {dog_name}! Hay quay ve CONG RA!", 240)
                else:
                    self._set_message(f"Da giai cuu {dog_name}! Hay quay ve CONG RA!", 240)

    def _trigger_dfs(self) -> None:
        assert self.level and self.player
        if self.player.dfs_cooldown > 0:
            return

        targets = self.level.keys if self.level.keys else [self.level.cage_cell]
        if not targets:
            return

        start_cell = self.player.cell()
        goal = min(targets, key=lambda c: abs(c[0] - start_cell[0]) + abs(c[1] - start_cell[1]))

        path = dfs(self.level.maze, start_cell, goal)
        if path:
            self.player.dfs_path = path
            self.player.dfs_timer = S.DFS_RADAR_DURATION
            self.player.dfs_cooldown = S.DFS_RADAR_COOLDOWN
            self._set_message("DFS Radar kich hoat!", 60)

    def _update_play(self) -> None:
        assert self.level and self.player
        keys = pygame.key.get_pressed()
        self.player.update(keys, self.level.maze)

        cell = self.player.cell()

        # auto-pick up keys
        if cell in self.level.keys:
            self.level.keys.remove(cell)
            self.player.keys += 1
            audio.play_pickup()
            self._set_message(f"Nhat duoc chia khoa! ({self.player.keys}/{self.level.config['keys']})", 90)

        # auto-pick up coins
        if cell in self.level.coins:
            self.level.coins.remove(cell)
            self.player.coins += 5
            audio.play_coin()
            self._set_message(f"+5 xu! Tong: {self.player.coins}", 60)

        # footstep sounds
        if any(keys[k] for k in (pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d,
                                  pygame.K_UP, pygame.K_LEFT, pygame.K_DOWN, pygame.K_RIGHT)):
            if self.anim_t % 15 == 0:
                audio.play_foot()

        # hideout message
        if self.level.maze.grid[cell[1]][cell[0]] == HIDE:
            if not self.message:
                self._set_message("Dang tru an — trom khong thay ban", 30)

        # Auto-free dog when at cage with enough keys
        if cell == self.level.cage_cell and self.player.keys >= self.level.config["keys"] and not self.dog_freed:
            self.dog_freed = True
            audio.play_alarm()
            self.level.maze.grid[0][1] = FLOOR
            dog_name = self.level.config.get("dog_name", "cho")
            self._set_message(f"Da giai cuu {dog_name}! Hay quay ve CONG RA!", 240)

        # Auto-complete level when player reaches exit with dog freed
        if cell == self.level.player_start and self.dog_freed:
            audio.play_win()
            self.rescued_dogs += 1
            dog_name = self.level.config.get("dog_name", "cho")
            if self.level_idx + 1 < len(S.LEVELS):
                self.state = LEVEL_DONE
                self.level_done_timer = 0
                self._set_message(f"Da cuu {dog_name}! ({self.rescued_dogs}/6)", 180)
            else:
                self.rescued_dogs = 6
                self.outro = story.ChatScene(story.OUTRO, "Dog Rescue")
                self.state = OUTRO

        # update thieves, dragons, bats
        if self.player.stop_time_timer > 0:
            self.player.stop_time_timer -= 1
        else:
            for t in self.level.thieves:
                t.update(self.level.maze, self.player, self.dog_freed)
                player_in_hide = self.level.maze.grid[cell[1]][cell[0]] == HIDE
                if t.collides_with(self.player) and not player_in_hide:
                    if self.player.take_hit():
                        self._set_message("Bi trom tom roi!", 90)
                        if self.dog_freed:
                            self.dog_freed = False
                            self.level.maze.grid[0][1] = WALL
                            self._set_message("Cho bi bat lai! Tim cach giai cuu lan nua!", 120)
                        self._respawn_player()
                    if self.player.hp <= 0:
                        audio.stop_bgm()
                        self.end = ui.EndScreen(won=False)
                        self.state = LOSE

            for d in self.level.dragons:
                fb = d.update(self.level.maze, self.player)
                if fb:
                    self.fireballs.append(fb)

            for b in self.level.bats:
                b.update()

        # fireballs
        if self.player.stop_time_timer <= 0:
            alive_fireballs = []
            for fb in self.fireballs:
                if fb.update(self.level.maze):
                    if fb.collides_with(self.player):
                        if self.player.take_hit():
                            self._set_message("Dinh hoa cau!", 60)
                            self._respawn_player()
                    alive_fireballs.append(fb)
            self.fireballs = alive_fireballs

        # bullets
        for b in self.bullets:
            b.update()
            for t in self.level.thieves:
                if math.hypot(b.x - t.x, b.y - t.y) < S.TILE * 0.8:
                    t.x, t.y = -2000, -2000
                    b.life = 0
                    self._set_message("Da ban ha ten trom!", 60)
        self.bullets = [b for b in self.bullets if b.life > 0]

        # camera
        self._update_camera()

    def _shoot_bullet(self):
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -1
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = 1
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -1
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = 1
        else:
            dx = 1
        speed = 8
        audio.play_shoot()
        self.bullets.append(Bullet(self.player.x, self.player.y, dx * speed, dy * speed))
        self._set_message(f"Da ban! Con lai {self.player.bullets} vien.", 45)

    def _respawn_player(self) -> None:
        assert self.level and self.player
        sx, sy = cell_to_pixel(self.level.player_start)
        self.player.x, self.player.y = sx, sy
        if self.player.keys > 0:
            self.player.keys -= 1
            floor = [c for c in self.level.maze.floor_cells()
                     if c not in self.level.keys
                     and c != self.level.cage_cell
                     and c != self.level.player_start
                     and self.level.maze.grid[c[1]][c[0]] != TRAP]
            if floor:
                self.level.keys.append(self.level.rng.choice(floor))

    def _update_camera(self) -> None:
        assert self.player
        maze_w = self.level.maze.width * S.TILE
        maze_h = self.level.maze.height * S.TILE
        if maze_w <= S.VIEW_W:
            target_x = -(S.VIEW_W - maze_w) / 2
        else:
            target_x = self.player.x - S.VIEW_W / 2
            target_x = max(0, min(target_x, maze_w - S.VIEW_W))
        if maze_h <= S.VIEW_H:
            target_y = -(S.VIEW_H - maze_h) / 2
        else:
            target_y = self.player.y - S.VIEW_H / 2
            target_y = max(0, min(target_y, maze_h - S.VIEW_H))
        cx = self.cam[0] + (target_x - self.cam[0]) * 0.18
        cy = self.cam[1] + (target_y - self.cam[1]) * 0.18
        self.cam = (cx, cy)

    # --------------------- draw ------------------------ #
    def draw(self) -> None:
        if self.state == TITLE:
            self.title.draw(self.screen)
        elif self.state == CHAR_SELECT:
            self.char_select.draw(self.screen)
        elif self.state == SHOP:
            if self.shop:
                self._draw_play()
                self.shop.draw(self.screen)
        elif self.state == INTRO:
            self.intro.draw(self.screen)
        elif self.state == LEVEL_INTRO and self.level_intro:
            self.level_intro.draw(self.screen)
        elif self.state == TRANSITION:
            self._draw_transition()
        elif self.state == PLAY or self.state == LEVEL_DONE:
            self._draw_play()
        elif self.state == OUTRO and self.outro:
            self.outro.draw(self.screen)
        elif self.state == WIN and self.end:
            self.end.draw(self.screen)
        elif self.state == LOSE and self.end:
            self.end.draw(self.screen)

    def _draw_transition(self) -> None:
        """Draw a fade-in transition when starting a new level."""
        if self.level and self.player:
            self._update_camera()
        self.screen.fill((10, 10, 16))

        # Show level name in center during transition
        font = fonts.get(40, bold=True)
        small = fonts.get(22)
        cfg = S.LEVELS[self.level_idx]
        title = font.render(f"Man {self.level_idx + 1}", True, (250, 220, 100))
        name = small.render(cfg["name"], True, (220, 220, 240))
        dog_name = cfg.get("dog_name", "")
        is_mother = cfg.get("is_mother", False)
        if is_mother:
            rescue_txt = small.render(f"Giai cuu cho me {dog_name}!", True, (255, 150, 150))
        else:
            rescue_txt = small.render(f"Giai cuu cho con {dog_name}!", True, (150, 255, 150))

        self.screen.blit(title, (S.SCREEN_W // 2 - title.get_width() // 2, S.SCREEN_H // 2 - 60))
        self.screen.blit(name, (S.SCREEN_W // 2 - name.get_width() // 2, S.SCREEN_H // 2))
        self.screen.blit(rescue_txt, (S.SCREEN_W // 2 - rescue_txt.get_width() // 2, S.SCREEN_H // 2 + 40))

        # Thief count info
        thief_txt = small.render(f"So ten trom: {cfg['thieves']} | Me cung: {cfg['size']}x{cfg['size']}", True, (200, 200, 220))
        self.screen.blit(thief_txt, (S.SCREEN_W // 2 - thief_txt.get_width() // 2, S.SCREEN_H // 2 + 80))

        # Draw puppy or dog sprite
        if is_mother and sprites.DOG_SPRITE:
            dog = pygame.transform.scale(sprites.DOG_SPRITE, (96, 96))
            self.screen.blit(dog, (S.SCREEN_W // 2 - 48, S.SCREEN_H // 2 - 180))
        elif sprites.PUPPY_SPRITE:
            puppy = pygame.transform.scale(sprites.PUPPY_SPRITE, (72, 72))
            self.screen.blit(puppy, (S.SCREEN_W // 2 - 36, S.SCREEN_H // 2 - 160))

        # Fade overlay
        if self.transition_alpha > 0:
            fade = pygame.Surface((S.SCREEN_W, S.SCREEN_H))
            fade.fill((0, 0, 0))
            fade.set_alpha(self.transition_alpha)
            self.screen.blit(fade, (0, 0))

    def _draw_play(self) -> None:
        assert self.level and self.player
        self.screen.fill((10, 10, 16))
        view = pygame.Rect(0, 0, S.VIEW_W, S.VIEW_H)
        prev = self.screen.get_clip()
        self.screen.set_clip(view)

        cam_x, cam_y = self.cam
        x0 = max(0, int(cam_x // S.TILE))
        y0 = max(0, int(cam_y // S.TILE))
        x1 = min(self.level.maze.width, x0 + S.VIEW_W // S.TILE + 2)
        y1 = min(self.level.maze.height, y0 + S.VIEW_H // S.TILE + 2)
        grid = self.level.maze.grid
        decor = self.level.decor

        for ty in range(y0, y1):
            for tx in range(x0, x1):
                c = grid[ty][tx]
                px = tx * S.TILE - cam_x
                py = ty * S.TILE - cam_y
                if c == WALL:
                    tile = sprites.WALL_TILES[(tx * 3 + ty * 5) % len(sprites.WALL_TILES)]
                else:
                    tile = sprites.FLOOR_TILES[(tx * 7 + ty * 11) % len(sprites.FLOOR_TILES)]
                self.screen.blit(tile, (px, py))
                if (c != WALL and ty > 0 and grid[ty - 1][tx] == WALL):
                    shadow = pygame.Surface((S.TILE, 6), pygame.SRCALPHA)
                    shadow.fill((0, 0, 0, 90))
                    self.screen.blit(shadow, (px, py))
                if c == FLOOR and (tx, ty) in decor:
                    overlay = sprites.DECOR_OVERLAYS[decor[(tx, ty)]]
                    self.screen.blit(overlay, (px, py))
                if c == TRAP and sprites.TRAP_SPRITE:
                    self.screen.blit(sprites.TRAP_SPRITE, (px, py))
                elif c == HIDE and sprites.HOUSE_SPRITE:
                    self.screen.blit(sprites.HOUSE_SPRITE, (px, py))

        # lanterns
        for lx, ly in self.level.lanterns:
            if x0 <= lx < x1 and y0 <= ly < y1 and sprites.LANTERN_SPRITE:
                px = lx * S.TILE - cam_x
                py = ly * S.TILE - cam_y
                self.screen.blit(sprites.LANTERN_SPRITE, (px, py))

        # coins with glow + bob animation
        for cc in self.level.coins:
            px = cc[0] * S.TILE + S.TILE // 2 - cam_x
            py = cc[1] * S.TILE + S.TILE // 2 - cam_y
            if sprites.COIN_SPRITE:
                glow = pygame.Surface((S.TILE * 2, S.TILE * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow, (255, 220, 100, 120), (S.TILE, S.TILE), S.TILE // 2)
                self.screen.blit(glow, (int(px - S.TILE), int(py - S.TILE)))
                bob = math.sin(self.anim_t * 0.1) * 6
                rect = sprites.COIN_SPRITE.get_rect(center=(int(px), int(py + bob)))
                self.screen.blit(sprites.COIN_SPRITE, rect)

        # cage + dog/puppy
        cx, cy = cell_to_pixel(self.level.cage_cell)
        cage_px = (int(cx - cam_x) - S.TILE // 2, int(cy - cam_y) - S.TILE // 2)
        is_mother = self.level.config.get("is_mother", False)
        dog_sprite = sprites.DOG_SPRITE if is_mother else sprites.PUPPY_SPRITE

        if not self.dog_freed and sprites.CAGE_SPRITE:
            if dog_sprite:
                self.screen.blit(dog_sprite, cage_px)
            self.screen.blit(sprites.CAGE_SPRITE, cage_px)
        elif self.dog_freed and dog_sprite:
            dx = self.player.x - S.TILE * 0.9
            dy = self.player.y + 4
            self.screen.blit(dog_sprite,
                             (int(dx - cam_x) - S.TILE // 2, int(dy - cam_y) - S.TILE // 2))

        # keys
        for k in self.level.keys:
            kx, ky = cell_to_pixel(k)
            wob = math.sin((self.anim_t + (k[0] + k[1]) * 7) * 0.1) * 3
            self.screen.blit(sprites.KEY_SPRITE,
                             (int(kx - cam_x) - S.TILE // 2,
                              int(ky - cam_y) - S.TILE // 2 + wob))
            glow = pygame.Surface((S.TILE, S.TILE), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*S.KEY_GLOW, 50), (S.TILE // 2, S.TILE // 2), 12)
            self.screen.blit(glow, (int(kx - cam_x) - S.TILE // 2, int(ky - cam_y) - S.TILE // 2))

        # trees
        for tx_t, ty_t in self.level.trees:
            if x0 <= tx_t < x1 and y0 <= ty_t < y1 and sprites.TREE_SPRITE:
                px = tx_t * S.TILE - cam_x
                py = ty_t * S.TILE - cam_y
                self.screen.blit(sprites.TREE_SPRITE, (px, py))

        # dragons (inside maze)
        for d in self.level.dragons:
            d.draw(self.screen, self.cam)

        # bats
        for b in self.level.bats:
            b.draw(self.screen, self.cam, self.anim_t)

        # decorative fire dragons outside the maze
        self._draw_fire_dragons()

        # fireballs
        for fb in self.fireballs:
            fb.draw(self.screen, self.cam)

        # bullets
        for b in self.bullets:
            b.draw(self.screen, self.cam)

        # thieves
        for t in self.level.thieves:
            t.draw(self.screen, self.cam, self.anim_t)

        # path beams when dog freed
        if self.dog_freed:
            self._draw_path_beams()

        # player
        self.player.draw(self.screen, self.cam)

        # hideout effect
        self._draw_hide_effect()

        # DFS radar
        if self.player.dfs_timer > 0 and self.player.dfs_path:
            self._draw_dfs_path()

        # exit indicator
        exit_cell = self.level.player_start
        ex, ey = cell_to_pixel(exit_cell)
        px_e = int(ex - cam_x)
        py_e = int(ey - cam_y)

        if self.dog_freed:
            pulse = (math.sin(self.anim_t * 0.1) + 1) / 2
            glow_size = int(S.TILE * (1.5 + 0.5 * pulse))
            glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (150, 100, 255, int(100 * pulse)), (glow_size, glow_size), glow_size)
            self.screen.blit(glow_surf, (px_e - glow_size, py_e - glow_size))

            if sprites.EXIT_GATE_SPRITE:
                angle = self.anim_t * 2
                rot_portal = pygame.transform.rotate(sprites.EXIT_GATE_SPRITE, angle)
                rect = rot_portal.get_rect(center=(px_e, py_e))
                self.screen.blit(rot_portal, rect)

            font = fonts.get(18, bold=True)
            txt = font.render(">> CONG RA <<", True, (200, 150, 255))
            self.screen.blit(txt, (px_e - txt.get_width() // 2, py_e - S.TILE * 1.5))
        else:
            if sprites.EXIT_GATE_SPRITE:
                placeholder = sprites.EXIT_GATE_SPRITE.copy()
                placeholder.set_alpha(80)
                rect = placeholder.get_rect(center=(px_e, py_e))
                self.screen.blit(placeholder, rect)

        # darkness
        if self.level.config.get("dark"):
            self._draw_darkness()

        self.screen.set_clip(prev)

        # HUD
        dog_name = self.level.config.get("dog_name", "")
        self.hud.draw(
            self.screen,
            self.level_idx,
            self.level.config["name"],
            self.player.keys,
            self.level.config["keys"],
            self.player.hp,
            S.PLAYER_HP_MAX,
            self.dog_freed,
            self.player.dfs_cooldown,
            self.player.dfs_timer,
            coins=self.player.coins,
            message=self.message,
            dog_name=dog_name,
            rescued_count=self.rescued_dogs,
        )

        # banner message at bottom
        if self.message:
            font = fonts.get(22, bold=True)
            text = font.render(self.message, True, (255, 255, 255))
            bg = pygame.Surface((text.get_width() + 28, text.get_height() + 14), pygame.SRCALPHA)
            bg.fill((30, 30, 40, 200))
            bg.blit(text, (14, 7))
            self.screen.blit(bg, (S.VIEW_W // 2 - bg.get_width() // 2, S.SCREEN_H - 60))

        # level-done overlay
        if self.state == LEVEL_DONE:
            overlay = pygame.Surface((S.VIEW_W, S.VIEW_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            self.screen.blit(overlay, (0, 0))
            font = fonts.get(36, bold=True)
            dog_name = self.level.config.get("dog_name", "")
            t = font.render(f"HOAN THANH MAN {self.level_idx + 1}!", True, (100, 255, 100))
            self.screen.blit(t, (S.VIEW_W // 2 - t.get_width() // 2, S.VIEW_H // 2 - 80))

            small = fonts.get(24)
            rescue_msg = f"Da giai cuu {dog_name}! ({self.rescued_dogs}/6 cho)"
            rm = small.render(rescue_msg, True, (255, 230, 100))
            self.screen.blit(rm, (S.VIEW_W // 2 - rm.get_width() // 2, S.VIEW_H // 2 - 20))

            # Show which dog was rescued with sprite
            is_mother = self.level.config.get("is_mother", False)
            dog_spr = sprites.DOG_SPRITE if is_mother else sprites.PUPPY_SPRITE
            if dog_spr:
                scaled = pygame.transform.scale(dog_spr, (64, 64))
                self.screen.blit(scaled, (S.VIEW_W // 2 - 32, S.VIEW_H // 2 + 20))

            n = small.render("Nhan SPACE de tiep tuc", True, (255, 255, 255))
            if (self.anim_t // 30) % 2 == 0:
                self.screen.blit(n, (S.VIEW_W // 2 - n.get_width() // 2, S.VIEW_H // 2 + 100))

            if self.level_idx + 1 < len(S.LEVELS):
                next_txt = fonts.get(18).render(f"Man tiep theo: {S.LEVELS[self.level_idx + 1]['name']}", True, (200, 200, 220))
                self.screen.blit(next_txt, (S.VIEW_W // 2 - next_txt.get_width() // 2, S.VIEW_H // 2 + 140))

    def _draw_fire_dragons(self) -> None:
        if not self.level or not sprites.FIRE_DRAGON_SPRITE:
            return
        cam_x, cam_y = self.cam
        t = self.fire_dragon_anim_t

        for fx, fy, facing in self.level.fire_dragons:
            sx = int(fx - cam_x)
            sy = int(fy - cam_y)

            if -128 < sx < S.VIEW_W + 128 and -128 < sy < S.VIEW_H + 128:
                bob = math.sin(t * 0.05 + fx * 0.01) * 4
                self.screen.blit(sprites.FIRE_DRAGON_SPRITE, (sx, int(sy + bob)))

                fire_phase = (t + int(fx * 13 + fy * 7)) % 120
                if fire_phase < 40:
                    fire_len = int(20 + fire_phase * 1.5)
                    fire_alpha = int(200 - fire_phase * 4)
                    fire_surf = pygame.Surface((fire_len * 2, 20), pygame.SRCALPHA)

                    for fi in range(fire_len):
                        fr = max(0, fire_alpha - fi * 3)
                        color_r = min(255, 255)
                        color_g = max(0, 200 - fi * 5)
                        color_b = 0
                        pygame.draw.circle(fire_surf, (color_r, color_g, color_b, fr),
                                           (fi + fire_len // 2, 10 + int(math.sin(fi * 0.3) * 3)),
                                           max(1, 6 - fi // 8))

                    center_x = sx + S.TILE
                    center_y = int(sy + bob) + S.TILE
                    if facing == 0:
                        self.screen.blit(pygame.transform.rotate(fire_surf, -90),
                                         (center_x - 10, center_y + S.TILE))
                    elif facing == 2:
                        self.screen.blit(pygame.transform.rotate(fire_surf, 90),
                                         (center_x - 10, center_y - S.TILE - fire_len))
                    elif facing == 1:
                        self.screen.blit(fire_surf, (center_x + S.TILE, center_y - 10))
                    else:
                        self.screen.blit(pygame.transform.flip(fire_surf, True, False),
                                         (center_x - S.TILE - fire_len, center_y - 10))

    def _draw_darkness(self) -> None:
        assert self.player
        overlay = pygame.Surface((S.VIEW_W, S.VIEW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        cx = int(self.player.x - self.cam[0])
        cy = int(self.player.y - self.cam[1])
        r = S.DARK_VIEW_RADIUS * S.TILE
        for i in range(12, 0, -1):
            alpha = int(220 * (i / 12))
            pygame.draw.circle(overlay, (0, 0, 0, alpha), (cx, cy), int(r * (i / 12)))
        pygame.draw.circle(overlay, (0, 0, 0, 0), (cx, cy), int(r * 0.5))

        if self.dog_freed:
            ex, ey = cell_to_pixel(self.level.player_start)
            px = int(ex - self.cam[0])
            py = int(ey - self.cam[1])
            pr = S.TILE * 2
            for i in range(8, 0, -1):
                alpha = int(220 * (i / 8))
                pygame.draw.circle(overlay, (0, 0, 0, alpha), (px, py), int(pr * (i / 8)))

        self.screen.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

    def _draw_path_beams(self) -> None:
        assert self.level and self.player
        cam_x, cam_y = self.cam
        pulse = (math.sin(self.anim_t * 0.12) + 1) / 2

        for t in self.level.thieves:
            path = t.visible_path
            if not path or len(path) < 2:
                continue

            base_color = (255, 30, 30)
            alpha = int(140 + 80 * pulse)

            points = []
            for cell in path:
                px = cell[0] * S.TILE + S.TILE // 2 - cam_x
                py = cell[1] * S.TILE + S.TILE // 2 - cam_y
                points.append((int(px), int(py)))

            for i in range(len(points) - 1):
                p1 = points[i]
                p2 = points[i + 1]
                glow_surf = pygame.Surface((S.VIEW_W, S.VIEW_H), pygame.SRCALPHA)
                pygame.draw.line(glow_surf, (*base_color, max(0, alpha - 60)), p1, p2, 5)
                self.screen.blit(glow_surf, (0, 0))
                pygame.draw.line(self.screen, (*base_color, min(255, alpha + 40)), p1, p2, 2)

            for i, pt in enumerate(points):
                if (i + self.anim_t // 4) % 2 == 0:
                    r = int(3 + 2 * pulse)
                    dot_surf = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
                    pygame.draw.circle(dot_surf, (*base_color, alpha), (r * 2, r * 2), r)
                    self.screen.blit(dot_surf, (pt[0] - r * 2, pt[1] - r * 2))

            if len(points) >= 2:
                tip = points[-1]
                prev_pt = points[-2]
                ddx = tip[0] - prev_pt[0]
                ddy = tip[1] - prev_pt[1]
                dist = math.hypot(ddx, ddy)
                if dist > 0:
                    nx, ny = ddx / dist, ddy / dist
                    perp_x, perp_y = -ny, nx
                    size = int(7 + 3 * pulse)
                    arrow = [
                        (tip[0] + int(nx * size), tip[1] + int(ny * size)),
                        (tip[0] + int(perp_x * size // 2) - int(nx * size // 2),
                         tip[1] + int(perp_y * size // 2) - int(ny * size // 2)),
                        (tip[0] - int(perp_x * size // 2) - int(nx * size // 2),
                         tip[1] - int(perp_y * size // 2) - int(ny * size // 2)),
                    ]
                    pygame.draw.polygon(self.screen, base_color, arrow)

    def _draw_hide_effect(self) -> None:
        assert self.level and self.player
        cell = self.player.cell()
        if self.level.maze.grid[cell[1]][cell[0]] != HIDE:
            return

        cam_x, cam_y = self.cam
        px = int(self.player.x - cam_x)
        py = int(self.player.y - cam_y)
        t = self.anim_t

        cloak = pygame.Surface((S.TILE * 2, S.TILE * 2), pygame.SRCALPHA)
        cloak_alpha = int(80 + 40 * math.sin(t * 0.1))
        pygame.draw.circle(cloak, (160, 220, 255, cloak_alpha),
                           (S.TILE, S.TILE), S.TILE - 2)
        self.screen.blit(cloak, (px - S.TILE, py - S.TILE))

        num_particles = 8
        for i in range(num_particles):
            angle = (t * 0.07 + i * (2 * math.pi / num_particles))
            dist = S.TILE * 0.65 + math.sin(t * 0.15 + i) * 5
            sx = int(px + math.cos(angle) * dist)
            sy = int(py + math.sin(angle) * dist)
            spark_alpha = int(180 + 60 * math.sin(t * 0.1 + i))
            spark_r = int(2 + 2 * math.sin(t * 0.2 + i * 1.3))
            s = pygame.Surface((spark_r * 4, spark_r * 4), pygame.SRCALPHA)
            pygame.draw.circle(s, (200, 240, 255, spark_alpha),
                               (spark_r * 2, spark_r * 2), spark_r)
            self.screen.blit(s, (sx - spark_r * 2, sy - spark_r * 2))

        label_alpha = int(180 + 60 * math.sin(t * 0.12))
        font = fonts.get(13, bold=True)
        lbl = font.render("Tang hinh", True, (180, 230, 255))
        lbl_surf = pygame.Surface((lbl.get_width() + 10, lbl.get_height() + 6),
                                  pygame.SRCALPHA)
        lbl_surf.fill((20, 40, 80, min(200, label_alpha)))
        lbl_surf.blit(lbl, (5, 3))
        self.screen.blit(lbl_surf, (px - lbl_surf.get_width() // 2, py - S.TILE - 10))

    def _draw_dfs_path(self) -> None:
        assert self.player
        path = self.player.dfs_path
        if not path:
            return

        cam_x, cam_y = self.cam
        t = self.anim_t
        alpha_base = min(255, int(255 * (self.player.dfs_timer / 30.0))) if self.player.dfs_timer < 30 else 255

        for i, cell in enumerate(path):
            pulse = (math.sin(t * 0.1 + i * 0.3) + 1) / 2
            color = (200, 100, 255, int(alpha_base * (0.4 + 0.6 * pulse)))

            px = cell[0] * S.TILE + S.TILE // 2 - cam_x
            py = cell[1] * S.TILE + S.TILE // 2 - cam_y

            size = int(4 + 4 * pulse)
            glow = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow, color, (size * 2, size * 2), size)
            self.screen.blit(glow, (int(px - size * 2), int(py - size * 2)))

            if i > 0:
                prev_cell = path[i - 1]
                ppx = prev_cell[0] * S.TILE + S.TILE // 2 - cam_x
                ppy = prev_cell[1] * S.TILE + S.TILE // 2 - cam_y
                pygame.draw.line(self.screen, (150, 50, 255, int(alpha_base * 0.5)),
                                 (int(ppx), int(ppy)), (int(px), int(py)), 2)
