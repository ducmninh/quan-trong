"""Grab Hero — main game entry point.

Run:  python main.py
"""
from __future__ import annotations
import os
import sys
import math
import random
import pygame
from pathlib import Path

# Allow `python main.py` from inside this folder
sys.path.insert(0, str(Path(__file__).resolve().parent))

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE,
    PLAYER_BIKE_DAMAGE, SHAKE_HIT, SHAKE_EXPLODE,
    STARTING_GOLD,
)
from utils import Vec, draw_text, draw_panel, lerp_color, clamp
from camera import Camera
from particles import ParticleSystem
from player import Player
from enemies import Enemy
from weapons import Bullet, Weapon
from hud import HUD
from shop import Shop
from world import World, Pickup, P_GOLD, P_MEDKIT, P_AMMO
from levels import LEVEL_BUILDERS
from saveload import load_save, write_save
from hub import Hub, apply_upgrades_to_player
from pets import Pet


# ============================================================
SCENE_MENU = "menu"
SCENE_HUB = "hub"
SCENE_INTRO = "intro"
SCENE_PLAY = "play"
SCENE_PAUSE = "pause"
SCENE_GAMEOVER = "gameover"
SCENE_LEVEL_DONE = "level_done"
SCENE_VICTORY = "victory"
SCENE_MAP = "map"


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.t = 0.0

        self.scene = SCENE_MENU
        self.intro_t = 0.0
        self.menu_blink = 0.0

        self.level_idx = 0
        self.world: World | None = None
        self.enemies: list[Enemy] = []
        self.bullets: list[Bullet] = []
        self.player: Player | None = None
        self.camera: Camera | None = None
        self.particles = ParticleSystem()
        self.hud = HUD()
        self.shop: Shop | None = None
        self.level_name = ""
        self.biome = ""
        self.boss_ref: Enemy | None = None
        self.intro_lines: list[str] = []
        self.outro_t = 0.0
        self.victory_t = 0.0
        self.gameover_t = 0.0
        self.objective_pos: Vec | None = None

        # Persistent save (gold/upgrades/owned guns + pets)
        self.save = load_save()
        self.hub: Hub | None = None
        self.active_pet: Pet | None = None

    # ==================================================================
    def open_hub(self):
        """Bank the player's current run-gold into the save, then open the
        hub overlay. Resets level progress so the next run starts fresh."""
        if self.player is not None:
            # Bank whatever gold the player ended with into the persistent save
            self.save["gold"] += int(getattr(self.player, "gold", 0))
        write_save(self.save)
        self.level_idx = 0
        self.hub = Hub(self.save)
        self.scene = SCENE_HUB

    def start_run_from_hub(self):
        """Launch a new run from the hub: rebuild the player with hub
        upgrades/owned guns, spawn the equipped pet, load level 0."""
        write_save(self.save)
        self.player = Player(Vec(0, 0))
        self.player.gold = STARTING_GOLD  # run-only gold
        # apply unlocked guns from save
        for key in self.save.get("owned_guns", ["pistol"]):
            if key not in self.player.weapons:
                self.player.add_weapon(key)
        # apply persistent upgrades
        apply_upgrades_to_player(self.player, self.save)
        # spawn pet
        eq = self.save.get("equipped_pet")
        self.active_pet = Pet(eq, Vec(0, 0)) if eq else None
        self.level_idx = 0
        self.load_level(0)
        if self.active_pet is not None:
            self.active_pet.pos = Vec(self.player.pos)
        self.scene = SCENE_INTRO
        self.intro_t = 0.0
        self.intro_lines = [
            "Chú chó cưng của bạn vừa bị một băng trộm bắt cóc...",
            "Bạn lao ra phố, cầm súng — sẵn sàng giải cứu!",
            "Mục tiêu: Đi tới cuối mỗi khu vực, hạ trùm, cứu chú chó.",
        ]

    def start_new_game(self):
        """Legacy entry: jump to the hub instead of straight into level 1."""
        self.open_hub()

    def load_level(self, idx):
        builder = LEVEL_BUILDERS[idx]
        world, enemies, name, biome = builder()
        self.world = world
        self.enemies = enemies
        self.level_name = name
        self.biome = biome
        self.bullets = []
        self.particles = ParticleSystem()
        # find boss
        self.boss_ref = next((e for e in enemies if e.is_boss), None)
        self.hud.clear_boss()
        # set player pos
        if self.player is None:
            self.player = Player(world.spawn)
            # apply hub upgrades + guns to fresh player
            for key in self.save.get("owned_guns", ["pistol"]):
                if key not in self.player.weapons:
                    self.player.add_weapon(key)
            apply_upgrades_to_player(self.player, self.save)
        else:
            self.player.pos = Vec(world.spawn)
            self.player.alive = True
            self.player.hp = max(self.player.hp, int(self.player.max_hp * 0.8))
            self.player.invuln_t = 5.0
            self.player.on_bike = False
            self.player.weapon.reloading = False
            self.player.weapon.ammo_in_mag = self.player.weapon.mag_size
        # Move pet to spawn area
        if self.active_pet is not None:
            self.active_pet.pos = Vec(self.player.pos) + Vec(-40, 30)
            self.active_pet.alive = True
        ww, wh = world.pixel_size()
        self.camera = Camera(ww, wh)
        self.camera.offset = Vec(self.player.pos.x - SCREEN_WIDTH // 2,
                                 self.player.pos.y - SCREEN_HEIGHT // 2)
        # set shop per level
        if idx == 1:
            self.shop = Shop(2)
        elif idx == 2:
            self.shop = Shop(3)
        else:
            self.shop = None
        # Objective marker (boss pos)
        if self.boss_ref:
            self.objective_pos = Vec(self.boss_ref.pos)
        else:
            self.objective_pos = None
        self.hud.set_message(name, 3.0)

    # ==================================================================
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 1 / 30)  # avoid huge dt
            self.t += dt
            self.handle_events()

            if self.scene == SCENE_PLAY:
                self.update_play(dt)
            elif self.scene == SCENE_MENU:
                self.menu_blink += dt
            elif self.scene == SCENE_HUB:
                if self.hub is not None:
                    self.hub.update(dt)
                    if self.hub.exit_to_play:
                        # Launch a run with applied upgrades + pet
                        self.start_run_from_hub()
            elif self.scene == SCENE_INTRO:
                self.intro_t += dt
                if self.intro_t > 6.0:
                    self.scene = SCENE_PLAY
            elif self.scene == SCENE_PAUSE:
                pass
            elif self.scene == SCENE_GAMEOVER:
                self.gameover_t += dt
            elif self.scene == SCENE_LEVEL_DONE:
                self.outro_t += dt
            elif self.scene == SCENE_VICTORY:
                self.victory_t += dt
            elif self.scene == SCENE_MAP:
                pass

            self.draw()
            pygame.display.flip()
        pygame.quit()

    # ==================================================================
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if self.scene == SCENE_MENU:
                if event.type == pygame.KEYDOWN and event.key in (
                        pygame.K_RETURN, pygame.K_SPACE):
                    self.start_new_game()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running = False
                continue

            if self.scene == SCENE_HUB:
                if event.type == pygame.KEYDOWN:
                    # Escape from hub returns to menu (keeps progress saved)
                    if event.key == pygame.K_ESCAPE:
                        write_save(self.save)
                        self.scene = SCENE_MENU
                        continue
                if self.hub is not None:
                    self.hub.handle(event)
                continue

            if self.scene == SCENE_INTRO:
                if event.type == pygame.KEYDOWN:
                    self.scene = SCENE_PLAY
                continue

            if self.scene == SCENE_GAMEOVER:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        # Go back to hub so upgrades + carried gold persist
                        self.open_hub()
                        self.gameover_t = 0
                    elif event.key == pygame.K_ESCAPE:
                        self.scene = SCENE_MENU
                        self.gameover_t = 0
                continue

            if self.scene == SCENE_LEVEL_DONE:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.next_level()
                    elif event.key == pygame.K_h:
                        # Optional: jump back to hub after clearing a level
                        self.open_hub()
                continue

            if self.scene == SCENE_VICTORY:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE,
                                     pygame.K_ESCAPE):
                        # Bank earned gold + clear progress, return to hub
                        self.open_hub()
                continue

            if self.scene == SCENE_PAUSE:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.scene = SCENE_PLAY
                    elif event.key == pygame.K_q:
                        self.scene = SCENE_MENU
                continue

            if self.scene == SCENE_MAP:
                if event.type == pygame.KEYDOWN and event.key in (
                        pygame.K_TAB, pygame.K_ESCAPE):
                    self.scene = SCENE_PLAY
                continue

            # PLAY
            if self.scene != SCENE_PLAY:
                continue

            if self.shop and self.shop.open:
                self.shop.handle(event, self.player)
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.scene = SCENE_PAUSE
                elif event.key == pygame.K_TAB:
                    self.scene = SCENE_MAP
                elif event.key == pygame.K_r:
                    self.player.reload()
                elif event.key == pygame.K_SPACE:
                    keys = pygame.key.get_pressed()
                    dx = (1 if keys[pygame.K_d] else 0) - (1 if keys[pygame.K_a] else 0)
                    dy = (1 if keys[pygame.K_s] else 0) - (1 if keys[pygame.K_w] else 0)
                    self.player.start_dodge(dx, dy)
                elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3,
                                   pygame.K_4, pygame.K_5, pygame.K_6,
                                   pygame.K_7):
                    idx = event.key - pygame.K_1
                    if idx < len(self.player.weapon_order):
                        self.player.switch_weapon(self.player.weapon_order[idx])
                elif event.key == pygame.K_q:
                    self.player.cycle_weapon(-1)
                elif event.key == pygame.K_e:
                    # interact: shop trigger
                    if self.shop and self.world.shop_rect and \
                            self.world.shop_rect.colliderect(self.player.rect.inflate(40, 40)):
                        self.shop.show()
                    else:
                        self.player.cycle_weapon(1)
                elif event.key == pygame.K_f:
                    nearest = None
                    best = 9999
                    for s in self.world.solids:
                        if s.kind == "parked_bike" and s.alive:
                            d = (Vec(s.rect.center) - self.player.pos).length()
                            if d < best:
                                best = d
                                nearest = s
                    self.player.toggle_bike(nearest)
            elif event.type == pygame.MOUSEWHEEL:
                self.player.cycle_weapon(-event.y)

    # ==================================================================
    def update_play(self, dt):
        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        mouse_world = self.camera.screen_to_world(*mouse_pos)
        mouse_buttons = pygame.mouse.get_pressed()

        # Shop overlay handling: still update HUD, freeze world
        if self.shop and self.shop.open:
            self.shop.update(dt)
            self.hud.update(dt)
            return

        # Player update
        self.player.update(dt, keys, mouse_world, self.world, self.particles)

        # Pet update (follows player, attacks enemies)
        if self.active_pet is not None and self.active_pet.alive:
            self.active_pet.update(dt, self.player, self.enemies,
                                   self.world, self.bullets,
                                   self.particles, self.t)

        # Firing (auto if button held)
        if mouse_buttons[0] and not self.player.on_bike:
            bullets = self.player.try_fire(self.world)
            if bullets:
                self.bullets.extend(bullets)
                muzzle = self.player.pos + Vec(
                    math.cos(self.player.aim_angle),
                    math.sin(self.player.aim_angle)) * 26
                self.particles.muzzle(muzzle, self.player.aim_angle)
                self.camera.add_shake(2)

        # Bike runover damage
        if self.player.on_bike:
            for e in self.enemies:
                if e.alive and self.player.rect.inflate(8, 8).colliderect(e.rect):
                    if not e.is_boss and e.kind in ("zombie", "zombie_fast",
                                                    "wild_dog"):
                        e.take_damage(PLAYER_BIKE_DAMAGE,
                                      self.player.aim)
                        self.particles.blood(e.pos)
                        self.player.take_damage(2)

        # Bullets
        new_bullets = []
        for b in self.bullets:
            if not b.update(dt):
                # AOE on expire if grenade
                if b.aoe:
                    self.aoe_explode(b)
                continue
            # collide world solids
            hit_solid = None
            for s in self.world.solids:
                if s.alive and s.kind in ("wall", "house", "container",
                                          "machine", "rubble", "fence",
                                          "crate"):
                    if s.rect.collidepoint(b.pos):
                        hit_solid = s
                        break
            if hit_solid:
                # If crate -> drop loot
                if hit_solid.kind == "crate":
                    hit_solid.alive = False
                    self.particles.explosion(Vec(hit_solid.rect.center),
                                             color=(180, 130, 60), count=12)
                    if random.random() < 0.5:
                        self.world.add_pickup(Pickup(
                            Vec(hit_solid.rect.center), P_GOLD, 25))
                    else:
                        self.world.add_pickup(Pickup(
                            Vec(hit_solid.rect.center), P_AMMO))
                if b.aoe:
                    self.aoe_explode(b)
                continue
            # collide drums (explode chain)
            drum_hit = None
            for s in self.world.solids:
                if s.alive and s.kind == "drum" and s.rect.collidepoint(b.pos):
                    drum_hit = s
                    break
            if drum_hit:
                self.drum_explode(drum_hit)
                continue
            # collide enemies (player bullets) / player (enemy bullets)
            consumed = False
            if b.owner == "player":
                for e in self.enemies:
                    if e.alive and e.rect.collidepoint(b.pos):
                        dirv = b.vel.normalize() if b.vel.length() > 0 else Vec(1, 0)
                        e.take_damage(b.damage, dirv)
                        self.particles.blood(b.pos, count=8)
                        if b.aoe:
                            self.aoe_explode(b)
                        consumed = True
                        break
                if consumed:
                    continue
            else:
                if not self.player.dodging and self.player.invuln_t <= 0:
                    if self.player.rect.collidepoint(b.pos):
                        self.player.take_damage(b.damage)
                        self.particles.blood(b.pos, (220, 60, 60), 6)
                        if b.aoe:
                            self.aoe_explode(b)
                        continue
            new_bullets.append(b)
        self.bullets = new_bullets

        # Enemies update
        for e in self.enemies:
            if e.alive:
                e.update(dt, self.player, self.world, self.particles,
                         self.enemies, self.bullets, self.t)

        # Drop gold/medkit on death
        for e in list(self.enemies):
            if not e.alive and not getattr(e, "_dropped", False):
                e._dropped = True
                self.camera.add_shake(SHAKE_HIT if not e.is_boss else SHAKE_EXPLODE)
                self.particles.blood(e.pos, count=20)
                gold = random.randint(*e.gold_drop) if e.gold_drop[1] > 0 else 0
                if gold > 0:
                    self.world.add_pickup(Pickup(Vec(e.pos), P_GOLD, gold))
                    self.particles.text(e.pos + Vec(0, -16),
                                        f"+{gold}", color=(255, 215, 0))
                if random.random() < 0.18 or e.is_boss:
                    self.world.add_pickup(Pickup(Vec(e.pos + Vec(20, 10)),
                                                 P_MEDKIT))
                if random.random() < 0.22:
                    self.world.add_pickup(Pickup(Vec(e.pos + Vec(-20, 10)),
                                                 P_AMMO))
                # Boss death unlocks exit
                if e.is_boss:
                    self.world.exit_locked = False
                    self.hud.set_message("CỔNG ĐÃ MỞ — đi tới cuối map!",
                                         duration=4.0)

        # Boss bar
        if self.boss_ref and self.boss_ref.alive:
            self.hud.set_boss(self.boss_ref, self.boss_ref.spec["name"])
        else:
            self.hud.clear_boss()

        # Pickups
        for p in self.world.pickups:
            if not p.alive:
                continue
            p.update(dt, self.t)
            if (Vec(p.pos) - self.player.pos).length() < 28:
                if p.kind == P_GOLD:
                    self.player.add_gold(p.amount)
                    self.particles.text(p.pos, f"+{p.amount}$",
                                        color=(255, 215, 0))
                    self.particles.pickup(p.pos)
                elif p.kind == P_MEDKIT:
                    self.player.heal(40)
                    self.particles.text(p.pos, "+40 HP",
                                        color=(80, 220, 80))
                    self.particles.pickup(p.pos, color=(100, 230, 100))
                elif p.kind == P_AMMO:
                    # add ammo to non-pistol weapons
                    for k, w in self.player.weapons.items():
                        if w.spec.get("ammo_reserve", 9999) < 9999:
                            w.ammo_reserve = min(
                                w.ammo_reserve + 30,
                                int(w.spec.get("ammo_reserve", 30) * 1.5))
                    self.particles.text(p.pos, "+AMMO",
                                        color=(255, 220, 90))
                    self.particles.pickup(p.pos, color=(255, 220, 90))
                p.alive = False

        # Camera follow
        self.camera.follow(self.player.pos, dt, lerp=8)

        # Particles
        self.particles.update(dt)

        # HUD update
        self.hud.update(dt)

        # Death check
        if not self.player.alive:
            self.scene = SCENE_GAMEOVER
            self.gameover_t = 0
            return

        # Exit -> next level
        if not self.world.exit_locked and self.world.exit_rect:
            if self.world.exit_rect.colliderect(self.player.rect.inflate(8, 8)):
                if self.level_idx == len(LEVEL_BUILDERS) - 1:
                    self.scene = SCENE_VICTORY
                    self.victory_t = 0
                else:
                    self.scene = SCENE_LEVEL_DONE
                    self.outro_t = 0

    # ==================================================================
    def aoe_explode(self, b: Bullet):
        r = b.aoe or 100
        self.particles.explosion(b.pos, count=40, big=True)
        self.camera.add_shake(SHAKE_EXPLODE)
        for e in self.enemies:
            if e.alive and (Vec(e.pos) - b.pos).length() < r:
                dirv = (Vec(e.pos) - b.pos).normalize() \
                    if (Vec(e.pos) - b.pos).length() > 0.1 else Vec(1, 0)
                e.take_damage(b.damage, dirv)
                self.particles.blood(e.pos, count=8)
        # chain drums
        for s in self.world.solids:
            if s.alive and s.kind == "drum" and \
                    (Vec(s.rect.center) - b.pos).length() < r:
                s.alive = False
                self.particles.explosion(Vec(s.rect.center),
                                         color=(255, 140, 40), count=30, big=True)

    def drum_explode(self, drum):
        drum.alive = False
        self.camera.add_shake(SHAKE_EXPLODE)
        self.particles.explosion(Vec(drum.rect.center),
                                 color=(255, 140, 40), count=40, big=True)
        # damage enemies in radius
        r = 140
        for e in self.enemies:
            if e.alive and (Vec(e.pos) - Vec(drum.rect.center)).length() < r:
                dirv = (Vec(e.pos) - Vec(drum.rect.center))
                if dirv.length() > 0.1:
                    dirv = dirv.normalize()
                else:
                    dirv = Vec(1, 0)
                e.take_damage(80, dirv)
                self.particles.blood(e.pos, count=6)
        # damage player if close
        if (self.player.pos - Vec(drum.rect.center)).length() < r:
            self.player.take_damage(30)

    # ==================================================================
    def next_level(self):
        self.level_idx += 1
        if self.level_idx >= len(LEVEL_BUILDERS):
            self.scene = SCENE_VICTORY
            return
        self.load_level(self.level_idx)
        self.scene = SCENE_PLAY
        self.intro_t = 0

    # ==================================================================
    def draw(self):
        if self.scene == SCENE_MENU:
            self.draw_menu()
        elif self.scene == SCENE_HUB:
            if self.hub is not None:
                self.hub.draw(self.screen)
            else:
                self.screen.fill((10, 16, 14))
        elif self.scene == SCENE_INTRO:
            self.draw_play()
            self.draw_intro_overlay()
        elif self.scene in (SCENE_PLAY, SCENE_PAUSE, SCENE_MAP):
            self.draw_play()
            if self.scene == SCENE_PAUSE:
                self.draw_pause_overlay()
            if self.scene == SCENE_MAP:
                self.draw_big_map()
            if self.shop and self.shop.open:
                self.shop.draw(self.screen, self.player)
        elif self.scene == SCENE_GAMEOVER:
            self.draw_play()
            self.draw_gameover_overlay()
        elif self.scene == SCENE_LEVEL_DONE:
            self.draw_play()
            self.draw_level_done_overlay()
        elif self.scene == SCENE_VICTORY:
            self.draw_victory()

    # ==================================================================
    def draw_play(self):
        self.world.draw_bg(self.screen, self.camera)
        # decals and pickups under entities
        self.world.draw_pickups(self.screen, self.camera)
        # solids and entities sorted by y to give depth
        items = []
        for s in self.world.solids:
            if s.alive:
                items.append((s.rect.bottom, "solid", s))
        for e in self.enemies:
            if e.alive:
                items.append((e.pos.y, "enemy", e))
        items.append((self.player.pos.y, "player", self.player))
        if self.active_pet is not None and self.active_pet.alive:
            items.append((self.active_pet.pos.y, "pet", self.active_pet))
        items.sort(key=lambda x: x[0])
        for _, kind, obj in items:
            if kind == "solid":
                obj.draw(self.screen, self.camera)
            elif kind == "enemy":
                obj.draw(self.screen, self.camera, self.t)
            elif kind == "player":
                obj.draw(self.screen, self.camera, self.t)
            elif kind == "pet":
                obj.draw(self.screen, self.camera, self.t)

        # bullets above sprites
        for b in self.bullets:
            b.draw(self.screen, self.camera)

        # particles
        self.particles.draw(self.screen, self.camera)

        # exit
        self.world.draw_exit_marker(self.screen, self.camera, self.t)

        # dog (visible target in level 4)
        if self.world.dog_rect is not None and self.level_idx == 3:
            self.draw_dog_cage()

        # shop area hint
        if self.shop and self.world.shop_rect:
            if (Vec(self.world.shop_rect.center) - self.player.pos).length() < 90:
                rect = self.camera.apply_rect(self.world.shop_rect)
                pygame.draw.rect(self.screen, (255, 215, 0),
                                 rect.inflate(10, 10), 3)
                draw_text(self.screen, "[E] SHOP NÂNG CẤP",
                          (rect.centerx, rect.top - 16), size=18,
                          color=(255, 215, 0), bold=True, center=True)

        # objective arrow
        self.draw_objective_arrow()

        # crosshair
        if self.scene == SCENE_PLAY and not (self.shop and self.shop.open):
            mx, my = pygame.mouse.get_pos()
            pygame.draw.circle(self.screen, (255, 255, 255), (mx, my), 8, 1)
            pygame.draw.line(self.screen, (255, 255, 255),
                             (mx - 12, my), (mx - 4, my), 1)
            pygame.draw.line(self.screen, (255, 255, 255),
                             (mx + 4, my), (mx + 12, my), 1)
            pygame.draw.line(self.screen, (255, 255, 255),
                             (mx, my - 12), (mx, my - 4), 1)
            pygame.draw.line(self.screen, (255, 255, 255),
                             (mx, my + 4), (mx, my + 12), 1)

        # HUD
        self.hud.draw(self.screen, self.player, self.level_name,
                      self.world, self.enemies, self.t)

    # ==================================================================
    def draw_objective_arrow(self):
        target = None
        if self.world.exit_locked and self.boss_ref and self.boss_ref.alive:
            target = self.boss_ref.pos
        elif self.world.exit_rect and not self.world.exit_locked:
            target = Vec(self.world.exit_rect.center)
        if target is None:
            return
        sp = self.camera.apply(target)
        # if on screen, skip arrow
        if 60 < sp[0] < SCREEN_WIDTH - 60 and 90 < sp[1] < SCREEN_HEIGHT - 90:
            return
        # clamp to screen edge
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        dx, dy = sp[0] - cx, sp[1] - cy
        # find intersection with screen rect
        max_dx = SCREEN_WIDTH / 2 - 80
        max_dy = SCREEN_HEIGHT / 2 - 80
        scale = max(abs(dx) / max_dx, abs(dy) / max_dy)
        if scale == 0:
            return
        ax = cx + dx / scale
        ay = cy + dy / scale
        angle = math.atan2(dy, dx)
        col = (255, 80, 80) if self.world.exit_locked else (90, 220, 100)
        pts = []
        for a in (0, 2.5, -2.5):
            pts.append((ax + math.cos(angle + a) * 18,
                        ay + math.sin(angle + a) * 18))
        pygame.draw.polygon(self.screen, col, pts)
        pygame.draw.polygon(self.screen, (0, 0, 0), pts, 2)

    # ==================================================================
    def draw_dog_cage(self):
        r = self.camera.apply_rect(self.world.dog_rect)
        # cage frame
        pygame.draw.rect(self.screen, (90, 70, 50), r)
        pygame.draw.rect(self.screen, (40, 30, 20), r, 3)
        # bars
        for x in range(r.left + 6, r.right - 4, 8):
            pygame.draw.line(self.screen, (60, 50, 40),
                             (x, r.top), (x, r.bottom), 2)
        # dog inside (simple cute pixel dog)
        cx, cy = r.center
        bob = math.sin(self.t * 4) * 2
        pygame.draw.ellipse(self.screen, (190, 140, 90),
                            (cx - 22, cy - 8 + bob, 44, 24))
        pygame.draw.circle(self.screen, (190, 140, 90),
                           (cx + 18, cy - 6 + int(bob)), 12)
        pygame.draw.polygon(self.screen, (140, 100, 60), [
            (cx + 22, cy - 16 + int(bob)),
            (cx + 30, cy - 22 + int(bob)),
            (cx + 28, cy - 8 + int(bob)),
        ])
        pygame.draw.circle(self.screen, (0, 0, 0),
                           (cx + 22, cy - 6 + int(bob)), 1)
        # tail wag
        wag = math.sin(self.t * 8) * 6
        pygame.draw.line(self.screen, (190, 140, 90),
                         (cx - 22, cy), (cx - 30, cy - 10 + int(wag)), 4)
        # "?" while locked, "!" when freed (boss dead)
        if self.boss_ref and not self.boss_ref.alive:
            draw_text(self.screen, "FREE!", (cx, r.top - 14),
                      size=20, color=(80, 220, 80),
                      bold=True, center=True)
        else:
            draw_text(self.screen, "HELP!", (cx, r.top - 14),
                      size=20, color=(255, 180, 60),
                      bold=True, center=True)

    # ==================================================================
    def draw_menu(self):
        # animated background
        self.screen.fill((22, 30, 22))
        # scrolling stars / leaves
        for i in range(60):
            x = (i * 73 + int(self.t * 30)) % SCREEN_WIDTH
            y = (i * 53 + int(self.t * 20)) % SCREEN_HEIGHT
            r = (i % 3) + 1
            c = (40, 80, 50) if (i % 4) else (60, 110, 70)
            pygame.draw.circle(self.screen, c, (x, y), r)

        # title
        title = "GRAB HERO"
        font = pygame.font.SysFont("arial", 96, bold=True)
        glow = (math.sin(self.t * 2) + 1) / 2
        col = lerp_color((0, 175, 81), (90, 230, 130), glow)
        sh = font.render(title, True, (0, 0, 0))
        img = font.render(title, True, col)
        rect = img.get_rect(center=(SCREEN_WIDTH // 2, 200))
        self.screen.blit(sh, rect.move(4, 4))
        self.screen.blit(img, rect)
        draw_text(self.screen, "Giải Cứu Chú Chó",
                  (SCREEN_WIDTH // 2, 280), size=36,
                  color=(240, 230, 180), bold=True, center=True)

        # start prompt blink
        if int(self.menu_blink * 2) % 2 == 0:
            draw_text(self.screen, "Nhấn ENTER hoặc SPACE để bắt đầu",
                      (SCREEN_WIDTH // 2, 460), size=26,
                      color=(255, 255, 255), bold=True, center=True)
        draw_text(self.screen, "ESC để thoát", (SCREEN_WIDTH // 2, 500),
                  size=18, color=(200, 200, 200), center=True)

        # controls
        controls = [
            "WASD: di chuyển | Chuột: ngắm/bắn | Shift: chạy",
            "Space: né | R: nạp đạn | 1-7: đổi súng",
            "F: lên/xuống xe | E: shop | Tab: bản đồ",
        ]
        for i, c in enumerate(controls):
            draw_text(self.screen, c, (SCREEN_WIDTH // 2, 560 + i * 24),
                      size=15, color=(180, 220, 180), center=True)

        draw_text(self.screen, "Đồ hoạ: Pygame  |  Tài xế Grab vào vai anh hùng",
                  (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30),
                  size=14, color=(150, 150, 150), center=True)

    # ==================================================================
    def draw_intro_overlay(self):
        # darkening overlay with intro text typing
        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 200))
        self.screen.blit(dim, (0, 0))
        title = self.level_name
        draw_text(self.screen, title, (SCREEN_WIDTH // 2, 200),
                  size=48, color=(255, 215, 0), bold=True, center=True)
        for i, line in enumerate(self.intro_lines):
            # type effect
            tt = self.intro_t - i * 1.0
            if tt < 0:
                continue
            chars = int(tt * 28)
            shown = line[:chars]
            draw_text(self.screen, shown,
                      (SCREEN_WIDTH // 2, 320 + i * 50),
                      size=24, color=(240, 240, 240), bold=True, center=True)
        draw_text(self.screen, "[ Nhấn phím bất kỳ để bỏ qua ]",
                  (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60),
                  size=16, color=(200, 200, 200), center=True)

    # ==================================================================
    def draw_pause_overlay(self):
        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 180))
        self.screen.blit(dim, (0, 0))
        draw_text(self.screen, "TẠM DỪNG", (SCREEN_WIDTH // 2, 240),
                  size=64, color=(255, 215, 0), bold=True, center=True)
        draw_text(self.screen, "ESC để tiếp tục   |   Q để về menu",
                  (SCREEN_WIDTH // 2, 340), size=24,
                  color=(220, 220, 220), bold=True, center=True)

    # ==================================================================
    def draw_gameover_overlay(self):
        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        a = min(220, int(self.gameover_t * 200))
        dim.fill((0, 0, 0, a))
        self.screen.blit(dim, (0, 0))
        draw_text(self.screen, "BẠN ĐÃ NGÃ XUỐNG",
                  (SCREEN_WIDTH // 2, 260), size=64,
                  color=(220, 50, 50), bold=True, center=True)
        draw_text(self.screen, "Chú chó vẫn đang chờ bạn quay lại...",
                  (SCREEN_WIDTH // 2, 340), size=24,
                  color=(220, 200, 200), center=True)
        if int(self.t * 2) % 2 == 0:
            draw_text(self.screen, "ENTER để chơi lại    ESC về menu",
                      (SCREEN_WIDTH // 2, 440), size=20,
                      color=(255, 255, 255), bold=True, center=True)

    # ==================================================================
    def draw_level_done_overlay(self):
        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 40, 0, 200))
        self.screen.blit(dim, (0, 0))
        draw_text(self.screen, "HOÀN THÀNH LEVEL!",
                  (SCREEN_WIDTH // 2, 220), size=58,
                  color=(90, 230, 110), bold=True, center=True)
        draw_text(self.screen, self.level_name, (SCREEN_WIDTH // 2, 290),
                  size=28, color=(255, 215, 0), bold=True, center=True)
        draw_text(self.screen, f"Vàng tích luỹ: {self.player.gold}",
                  (SCREEN_WIDTH // 2, 350), size=22,
                  color=(255, 230, 90), bold=True, center=True)
        draw_text(self.screen, f"HP còn: {int(self.player.hp)}/{self.player.max_hp}",
                  (SCREEN_WIDTH // 2, 380), size=22,
                  color=(255, 255, 255), center=True)
        if int(self.t * 2) % 2 == 0:
            draw_text(self.screen, "ENTER để qua Level tiếp theo",
                      (SCREEN_WIDTH // 2, 460), size=22,
                      color=(255, 255, 255), bold=True, center=True)

    # ==================================================================
    def draw_victory(self):
        self.screen.fill((20, 8, 30))
        # fireworks
        for i in range(20):
            t = self.victory_t + i * 0.3
            r = int(10 + (t * 200) % 180)
            cx = (i * 73 + 200) % SCREEN_WIDTH
            cy = (i * 53 + 200) % (SCREEN_HEIGHT - 200) + 100
            col = [(255, 100, 150), (100, 200, 255),
                   (250, 220, 100), (180, 240, 120)][i % 4]
            pygame.draw.circle(self.screen, col, (cx, cy), r, 2)

        draw_text(self.screen, "CHIẾN THẮNG!",
                  (SCREEN_WIDTH // 2, 180), size=88,
                  color=(255, 215, 0), bold=True, center=True)
        draw_text(self.screen, "Bạn đã giải cứu được chú chó!",
                  (SCREEN_WIDTH // 2, 290), size=32,
                  color=(255, 255, 255), bold=True, center=True)
        # Big happy dog
        cx, cy = SCREEN_WIDTH // 2, 440
        bob = math.sin(self.victory_t * 4) * 8
        pygame.draw.ellipse(self.screen, (200, 150, 100),
                            (cx - 60, cy - 20 + bob, 120, 70))
        pygame.draw.circle(self.screen, (200, 150, 100),
                           (cx + 50, cy - 10 + int(bob)), 36)
        pygame.draw.polygon(self.screen, (140, 100, 60), [
            (cx + 60, cy - 40 + int(bob)),
            (cx + 80, cy - 60 + int(bob)),
            (cx + 76, cy - 22 + int(bob)),
        ])
        pygame.draw.circle(self.screen, (0, 0, 0),
                           (cx + 60, cy - 10 + int(bob)), 4)
        pygame.draw.circle(self.screen, (255, 255, 255),
                           (cx + 62, cy - 12 + int(bob)), 2)
        wag = math.sin(self.victory_t * 10) * 14
        pygame.draw.line(self.screen, (200, 150, 100),
                         (cx - 60, cy + bob),
                         (cx - 80, cy - 18 + int(wag)), 8)

        draw_text(self.screen, f"Vàng cuối: {self.player.gold} $",
                  (SCREEN_WIDTH // 2, 570), size=26,
                  color=(255, 220, 90), bold=True, center=True)
        if int(self.t * 2) % 2 == 0:
            draw_text(self.screen, "ENTER để về menu",
                      (SCREEN_WIDTH // 2, 640), size=22,
                      color=(255, 255, 255), bold=True, center=True)

    # ==================================================================
    def draw_big_map(self):
        # full screen minimap
        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 200))
        self.screen.blit(dim, (0, 0))
        ww, wh = self.world.pixel_size()
        size_w = SCREEN_WIDTH - 160
        size_h = SCREEN_HEIGHT - 160
        sx = size_w / ww
        sy = size_h / wh
        s = pygame.Surface((size_w, size_h)).convert()
        s.fill((30, 30, 40))
        # tiles
        from world import (T_ROAD_H, T_ROAD_V, T_ROAD_X,
                           T_CONCRETE, T_DIRT, T_ASH, T_GRASS_DARK,
                           T_FLOOR_TILE)
        for j in range(self.world.h):
            for i in range(self.world.w):
                t = self.world.tiles[j][i]
                col = None
                if t in (T_ROAD_H, T_ROAD_V, T_ROAD_X):
                    col = (95, 95, 100)
                elif t == T_CONCRETE:
                    col = (140, 140, 140)
                elif t == T_DIRT:
                    col = (120, 90, 60)
                elif t == T_ASH:
                    col = (60, 60, 65)
                elif t == T_GRASS_DARK:
                    col = (50, 90, 50)
                elif t == T_FLOOR_TILE:
                    col = (200, 200, 210)
                if col:
                    pygame.draw.rect(s, col,
                                     (int(i * self.world.tile_size * sx),
                                      int(j * self.world.tile_size * sy),
                                      max(2, int(self.world.tile_size * sx)),
                                      max(2, int(self.world.tile_size * sy))))
        # solids
        for sol in self.world.solids:
            if not sol.alive:
                continue
            if sol.kind in ("house", "wall", "container", "machine", "rubble"):
                r = sol.rect
                pygame.draw.rect(s, (180, 140, 90),
                                 (int(r.left * sx), int(r.top * sy),
                                  max(2, int(r.w * sx)),
                                  max(2, int(r.h * sy))))
        # enemies
        for e in self.enemies:
            if not e.alive:
                continue
            col = (255, 80, 80) if not e.is_boss else (255, 30, 180)
            r = 5 if e.is_boss else 3
            pygame.draw.circle(s, col,
                               (int(e.pos.x * sx),
                                int(e.pos.y * sy)), r)
        # exit
        if self.world.exit_rect:
            r = self.world.exit_rect
            col = (220, 220, 220) if self.world.exit_locked else (60, 220, 100)
            pygame.draw.rect(s, col,
                             (int(r.left * sx), int(r.top * sy),
                              max(3, int(r.w * sx)),
                              max(3, int(r.h * sy))), 2)
        # player
        pygame.draw.circle(s, (90, 220, 90),
                           (int(self.player.pos.x * sx),
                            int(self.player.pos.y * sy)), 6)
        self.screen.blit(s, (80, 80))
        pygame.draw.rect(self.screen, (255, 215, 0),
                         (80, 80, size_w, size_h), 4)
        draw_text(self.screen, f"BẢN ĐỒ — {self.level_name}",
                  (SCREEN_WIDTH // 2, 50), size=28,
                  color=(255, 215, 0), bold=True, center=True)
        draw_text(self.screen, "TAB / ESC để đóng",
                  (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 40),
                  size=18, color=(220, 220, 220), bold=True, center=True)


# ============================================================
if __name__ == "__main__":
    # On VMs/CI without audio device avoid initialising mixer
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    Game().run()
