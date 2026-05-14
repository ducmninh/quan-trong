"""Enemies & bosses: zombies, thieves, snipers, tigers, bosses with AI."""
from __future__ import annotations
import math
import random
import pygame
from utils import Vec, vec_from_angle, draw_text, clamp
from settings import ENEMY_DEFS
from weapons import Bullet


def _rand_gold(rng):
    return random.randint(rng[0], rng[1])


class Enemy:
    def __init__(self, kind: str, pos: Vec):
        self.kind = kind
        spec = dict(ENEMY_DEFS[kind])
        self.spec = spec
        self.max_hp = spec["hp"]
        self.hp = self.max_hp
        self.pos = Vec(pos)
        self.vel = Vec(0, 0)
        self.speed = spec["speed"]
        self.dmg = spec["dmg"]
        self.attack_range = spec["attack_range"]
        self.attack_cd_max = spec["attack_cd"]
        self.attack_cd = random.uniform(0, self.attack_cd_max)
        self.ranged = spec["ranged"]
        self.bullet_speed = spec.get("bullet_speed", 600)
        self.color = spec.get("color", (200, 80, 80))
        self.size = spec.get("size", 42)
        self.sight = spec.get("sight", 500)
        self.is_boss = spec.get("is_boss", False)
        self.alive = True
        self.hit_flash = 0.0
        self.facing = Vec(1, 0)
        self.gold_drop = spec.get("gold", (0, 0))
        self.phase = 1  # for bosses
        self.burst_left = 0
        self.summon_t = 0.0
        self.slam_cd = 3.0
        self.roar_t = 0.0
        self.knockback_t = 0.0
        self.knockback_v = Vec(0, 0)
        self.bobbing = random.uniform(0, math.tau)

    @property
    def radius(self):
        return self.size // 2

    @property
    def rect(self) -> pygame.Rect:
        r = self.radius
        return pygame.Rect(int(self.pos.x - r), int(self.pos.y - r), 2 * r, 2 * r)

    def take_damage(self, dmg, dir_vec: Vec | None = None):
        self.hp -= dmg
        self.hit_flash = 0.18
        if dir_vec is not None and dir_vec.length() > 0.01:
            kb = 220 if not self.is_boss else 60
            self.knockback_v = dir_vec.normalize() * kb
            self.knockback_t = 0.12
        if self.hp <= 0:
            self.alive = False

    # ==================================================================
    def update(self, dt, player, world, particles, enemies, bullets, t):
        self.bobbing += dt * 4
        if self.hit_flash > 0:
            self.hit_flash = max(0, self.hit_flash - dt)
        if self.knockback_t > 0:
            self.knockback_t -= dt
            mv = self.knockback_v * dt
            self._try_move(mv, world)

        if self.attack_cd > 0:
            self.attack_cd = max(0, self.attack_cd - dt)
        if self.roar_t > 0:
            self.roar_t -= dt

        to_player = player.pos - self.pos
        dist = to_player.length()
        if dist < self.sight:
            if dist > 0.5:
                self.facing = to_player.normalize()

            # Boss behaviour first
            if self.is_boss and self.kind == "boss_final":
                self._boss_final_ai(dt, player, world, particles, enemies, bullets, dist, to_player)
                return
            if self.is_boss and self.kind == "boss2":
                self._boss2_ai(dt, player, world, particles, bullets, dist, to_player)
                return
            if self.is_boss and self.kind == "boss3":
                self._tiger_king_ai(dt, player, world, particles, bullets, dist, to_player)
                return
            if self.kind == "minion_smg":
                self._smg_ai(dt, player, world, particles, bullets, dist, to_player)
                return

            # Generic: ranged keeps distance & fires; melee charges
            if self.ranged:
                preferred = self.attack_range * 0.6
                if dist < self.attack_range * 0.4:
                    # back off
                    dirn = -to_player.normalize() if dist > 0.1 else Vec(0, 1)
                    mv = dirn * self.speed * dt
                    self._try_move(mv, world)
                elif dist > preferred:
                    mv = to_player.normalize() * self.speed * dt
                    self._try_move(mv, world)
                # fire if in range
                if dist <= self.attack_range and self.attack_cd <= 0:
                    self._fire_at(player, particles, bullets)
                    self.attack_cd = self.attack_cd_max
            else:
                # Melee: chase
                if dist > self.attack_range * 0.7:
                    mv = to_player.normalize() * self.speed * dt
                    self._try_move(mv, world)
                # attack
                if dist <= self.attack_range and self.attack_cd <= 0:
                    player.take_damage(self.dmg)
                    particles.blood(player.pos, (220, 60, 60), 8)
                    self.attack_cd = self.attack_cd_max
        else:
            # idle wander tiny bit
            if random.random() < 0.01:
                self.facing = vec_from_angle(random.uniform(0, math.tau))
            mv = self.facing * (self.speed * 0.2) * dt
            self._try_move(mv, world)

    # ==================================================================
    def _try_move(self, mv, world):
        new = self.pos + mv
        r = self.radius
        rx = pygame.Rect(int(new.x - r), int(self.pos.y - r), 2 * r, 2 * r)
        if not world.collides(rx):
            self.pos.x = new.x
        ry = pygame.Rect(int(self.pos.x - r), int(new.y - r), 2 * r, 2 * r)
        if not world.collides(ry):
            self.pos.y = new.y
        ww, wh = world.pixel_size()
        self.pos.x = clamp(self.pos.x, r, ww - r)
        self.pos.y = clamp(self.pos.y, r, wh - r)

    def _fire_at(self, player, particles, bullets):
        ang = math.atan2(player.pos.y - self.pos.y, player.pos.x - self.pos.x)
        pellets = self.spec.get("pellets", 1)
        spread = math.radians(self.spec.get("spread", 4))
        for _ in range(pellets):
            a = ang + random.uniform(-spread, spread)
            bullets.append(Bullet(
                self.pos + vec_from_angle(ang, self.radius + 6),
                a, self.bullet_speed, self.dmg, "enemy",
                color=(255, 200, 80), size=4, life=1.6,
            ))
        muzzle_pos = self.pos + vec_from_angle(ang, self.radius + 4)
        particles.muzzle(muzzle_pos, ang)

    # ==================================================================
    # Specific AIs
    # ==================================================================
    def _smg_ai(self, dt, player, world, particles, bullets, dist, to_player):
        preferred = 360
        if dist > preferred:
            mv = to_player.normalize() * self.speed * dt
            self._try_move(mv, world)
        if dist <= self.attack_range:
            # burst fire
            if self.attack_cd <= 0 and self.burst_left <= 0:
                self.burst_left = self.spec.get("burst", 4)
            if self.attack_cd <= 0 and self.burst_left > 0:
                self._fire_at(player, particles, bullets)
                self.burst_left -= 1
                self.attack_cd = self.attack_cd_max if self.burst_left > 0 else 1.0

    def _boss2_ai(self, dt, player, world, particles, bullets, dist, to_player):
        # Zombie Bự Con: slow chase, slam at close
        self.slam_cd -= dt
        if dist > 64:
            mv = to_player.normalize() * self.speed * dt
            self._try_move(mv, world)
        # melee
        if dist <= self.attack_range and self.attack_cd <= 0:
            player.take_damage(self.dmg)
            particles.blood(player.pos, (220, 60, 60), 10)
            self.attack_cd = self.attack_cd_max
        # slam
        if self.slam_cd <= 0 and dist < 360:
            self.slam_cd = 4.5
            for i in range(12):
                a = i * (math.tau / 12)
                bullets.append(Bullet(
                    self.pos + vec_from_angle(a, self.radius + 4),
                    a, 320, self.dmg * 0.7, "enemy",
                    color=(120, 200, 80), size=6, life=1.0,
                ))
            particles.explosion(self.pos, color=(120, 200, 80), count=24)

    def _tiger_king_ai(self, dt, player, world, particles, bullets, dist, to_player):
        # Hổ Vương: fast chase + occasional roar that does AOE
        if dist > 50:
            mv = to_player.normalize() * self.speed * dt
            self._try_move(mv, world)
        if dist <= self.attack_range and self.attack_cd <= 0:
            player.take_damage(self.dmg)
            particles.blood(player.pos, (220, 60, 60), 12)
            self.attack_cd = self.attack_cd_max
        # roar every 5s
        if self.roar_t <= 0:
            self.roar_t = 5.0
            for i in range(16):
                a = i * (math.tau / 16)
                bullets.append(Bullet(
                    self.pos + vec_from_angle(a, self.radius + 4),
                    a, 380, 12, "enemy",
                    color=(255, 100, 80), size=5, life=0.9,
                ))
            particles.explosion(self.pos, color=(255, 100, 60), count=30)

    def _boss_final_ai(self, dt, player, world, particles, enemies, bullets, dist, to_player):
        # 3 phases based on HP%
        pct = self.hp / self.max_hp
        new_phase = 1
        if pct < 0.66:
            new_phase = 2
        if pct < 0.33:
            new_phase = 3
        if new_phase != self.phase:
            self.phase = new_phase
            self.attack_cd_max = max(0.3, self.attack_cd_max - 0.15)
            particles.explosion(self.pos, color=(255, 80, 80), count=40, big=True)
            # spawn extras at phase transitions
            if new_phase == 2:
                from enemies import Enemy as E
                for _ in range(2):
                    a = random.uniform(0, math.tau)
                    p = self.pos + vec_from_angle(a, 220)
                    enemies.append(E("tiger", p))
            elif new_phase == 3:
                for _ in range(4):
                    a = random.uniform(0, math.tau)
                    p = self.pos + vec_from_angle(a, 240)
                    enemies.append(Enemy("minion_shotgun", p))

        # move toward player
        preferred = 380 if self.phase < 3 else 240
        if dist > preferred + 60:
            mv = to_player.normalize() * self.speed * dt
            self._try_move(mv, world)
        elif dist < preferred - 60:
            mv = -to_player.normalize() * self.speed * dt
            self._try_move(mv, world)

        if self.attack_cd <= 0 and dist < self.attack_range:
            self._fire_at(player, particles, bullets)
            self.attack_cd = self.attack_cd_max

    # ==================================================================
    def draw(self, surf, cam, t):
        p = cam.apply(self.pos)
        sz = self.size
        bob = math.sin(self.bobbing) * 1.5
        # shadow
        shadow = pygame.Surface((sz, sz // 3), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 110), (0, 0, sz, sz // 3))
        surf.blit(shadow, (p[0] - sz // 2, p[1] + sz // 3))

        # main body
        if self.kind in ("zombie", "zombie_fast", "boss2"):
            self._draw_zombie(surf, p, bob)
        elif self.kind in ("tiger", "boss3"):
            self._draw_tiger(surf, p, bob)
        elif self.kind == "wild_dog":
            self._draw_dog(surf, p, bob)
        elif self.kind == "boss_final":
            self._draw_boss_final(surf, p, bob)
        elif self.kind == "boss1":
            self._draw_thief(surf, p, bob, big=True, has_gun=False)
        elif self.kind in ("thief_pistol", "minion_smg", "minion_shotgun", "sniper"):
            has_gun = True
            self._draw_thief(surf, p, bob, big=False, has_gun=has_gun)
        elif self.kind == "thief_knife":
            self._draw_thief(surf, p, bob, big=False, has_gun=False)
        else:
            pygame.draw.circle(surf, self.color, (p[0], int(p[1] + bob)), self.radius)

        # hit flash
        if self.hit_flash > 0:
            s = pygame.Surface((sz + 4, sz + 4), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 255, 255, 180),
                               (sz // 2 + 2, sz // 2 + 2), sz // 2 + 2)
            surf.blit(s, (p[0] - sz // 2 - 2, p[1] - sz // 2 - 2))

        # health bar (only show if damaged or boss)
        if self.is_boss:
            # bosses get a big bar at top of screen handled elsewhere
            pass
        elif self.hp < self.max_hp:
            bar_w = max(28, sz)
            x = p[0] - bar_w // 2
            y = p[1] - sz // 2 - 10
            pygame.draw.rect(surf, (40, 0, 0), (x, y, bar_w, 4))
            pygame.draw.rect(surf, (220, 60, 60),
                             (x, y, int(bar_w * (self.hp / self.max_hp)), 4))

    # ------------------------------------------------------------------
    def _draw_zombie(self, surf, p, bob):
        sz = self.size
        cx, cy = p[0], int(p[1] + bob)
        # body
        body_col = self.color
        pygame.draw.ellipse(surf, body_col,
                            (cx - sz // 2, cy - sz // 3, sz, int(sz * 0.85)))
        # ragged shirt
        pygame.draw.rect(surf, (60, 50, 40),
                         (cx - sz // 3, cy, int(sz * 0.66), sz // 3))
        # head
        head_col = (
            min(255, body_col[0] + 30),
            min(255, body_col[1] + 30),
            min(255, body_col[2] + 30),
        )
        pygame.draw.circle(surf, head_col, (cx, cy - sz // 3), sz // 4)
        # eyes
        pygame.draw.circle(surf, (0, 0, 0), (cx - 5, cy - sz // 3), 3)
        pygame.draw.circle(surf, (0, 0, 0), (cx + 5, cy - sz // 3), 3)
        pygame.draw.circle(surf, (220, 50, 50), (cx - 5, cy - sz // 3), 1)
        pygame.draw.circle(surf, (220, 50, 50), (cx + 5, cy - sz // 3), 1)
        # mouth
        pygame.draw.arc(surf, (60, 0, 0),
                        (cx - 7, cy - sz // 3 + 3, 14, 8), 3.14, 0, 2)
        # arms
        ax = int(math.cos(self.bobbing) * 6)
        pygame.draw.line(surf, body_col, (cx - sz // 3, cy - 2),
                         (cx - sz // 3 - 10 + ax, cy + 6), 5)
        pygame.draw.line(surf, body_col, (cx + sz // 3, cy - 2),
                         (cx + sz // 3 + 10 - ax, cy + 6), 5)
        # outline
        pygame.draw.ellipse(surf, (0, 0, 0),
                            (cx - sz // 2, cy - sz // 3, sz, int(sz * 0.85)), 2)
        pygame.draw.circle(surf, (0, 0, 0), (cx, cy - sz // 3), sz // 4, 2)

    def _draw_thief(self, surf, p, bob, big=False, has_gun=True):
        sz = self.size
        cx, cy = p[0], int(p[1] + bob)
        body_col = self.color
        # body
        pygame.draw.rect(surf, body_col,
                         (cx - sz // 3, cy - sz // 4, int(sz * 0.66), int(sz * 0.6)))
        pygame.draw.rect(surf, (30, 30, 30),
                         (cx - sz // 3, cy + sz // 5, int(sz * 0.66), 8))
        # head with hood (mask)
        pygame.draw.circle(surf, (30, 30, 30),
                           (cx, cy - sz // 3), sz // 4 + 2)
        pygame.draw.rect(surf, (220, 200, 180),
                         (cx - 5, cy - sz // 3 - 1, 10, 6))
        # eyes
        pygame.draw.circle(surf, (0, 0, 0), (cx - 3, cy - sz // 3), 1)
        pygame.draw.circle(surf, (0, 0, 0), (cx + 3, cy - sz // 3), 1)
        # gun or knife in facing direction
        ang = math.atan2(self.facing.y, self.facing.x)
        hx = cx + int(math.cos(ang) * (sz // 2 + 2))
        hy = cy + int(math.sin(ang) * (sz // 2 + 2))
        if has_gun:
            pygame.draw.line(surf, (40, 40, 40), (cx, cy), (hx, hy), 5)
            pygame.draw.circle(surf, (40, 40, 40), (hx, hy), 4)
        else:
            # knife: short silver line
            tx = cx + int(math.cos(ang) * sz // 2)
            ty = cy + int(math.sin(ang) * sz // 2)
            pygame.draw.line(surf, (200, 200, 220), (cx, cy), (tx, ty), 4)
            pygame.draw.line(surf, (40, 40, 40), (cx, cy), (tx, ty), 1)
        # outline
        pygame.draw.rect(surf, (0, 0, 0),
                         (cx - sz // 3, cy - sz // 4, int(sz * 0.66), int(sz * 0.6)), 2)
        if big:
            # bandana for boss1
            pygame.draw.rect(surf, (200, 30, 30),
                             (cx - sz // 4, cy - sz // 3 - 6, sz // 2, 5))

    def _draw_tiger(self, surf, p, bob):
        sz = self.size
        cx, cy = p[0], int(p[1] + bob)
        # body (orange)
        pygame.draw.ellipse(surf, self.color,
                            (cx - sz // 2, cy - sz // 4, sz, int(sz * 0.6)))
        # stripes
        for sx in (-sz // 3, -sz // 6, 0, sz // 6, sz // 3):
            pygame.draw.line(surf, (50, 30, 10),
                             (cx + sx, cy - sz // 4),
                             (cx + sx, cy + sz // 3), 3)
        # head
        pygame.draw.circle(surf, self.color, (cx, cy - sz // 4), sz // 4)
        # ears
        pygame.draw.polygon(surf, self.color, [
            (cx - sz // 5, cy - sz // 3),
            (cx - sz // 6, cy - sz // 2),
            (cx - sz // 9, cy - sz // 3),
        ])
        pygame.draw.polygon(surf, self.color, [
            (cx + sz // 9, cy - sz // 3),
            (cx + sz // 6, cy - sz // 2),
            (cx + sz // 5, cy - sz // 3),
        ])
        # eyes
        pygame.draw.circle(surf, (255, 230, 0), (cx - 5, cy - sz // 4 - 2), 3)
        pygame.draw.circle(surf, (255, 230, 0), (cx + 5, cy - sz // 4 - 2), 3)
        pygame.draw.circle(surf, (0, 0, 0), (cx - 5, cy - sz // 4 - 2), 1)
        pygame.draw.circle(surf, (0, 0, 0), (cx + 5, cy - sz // 4 - 2), 1)
        # mouth (fangs)
        pygame.draw.polygon(surf, (255, 255, 255), [
            (cx - 3, cy - sz // 4 + 4),
            (cx, cy - sz // 4 + 9),
            (cx, cy - sz // 4 + 4),
        ])
        pygame.draw.polygon(surf, (255, 255, 255), [
            (cx + 3, cy - sz // 4 + 4),
            (cx, cy - sz // 4 + 9),
            (cx, cy - sz // 4 + 4),
        ])
        # outline
        pygame.draw.ellipse(surf, (0, 0, 0),
                            (cx - sz // 2, cy - sz // 4, sz, int(sz * 0.6)), 2)
        pygame.draw.circle(surf, (0, 0, 0), (cx, cy - sz // 4), sz // 4, 2)

    def _draw_dog(self, surf, p, bob):
        sz = self.size
        cx, cy = p[0], int(p[1] + bob)
        pygame.draw.ellipse(surf, self.color,
                            (cx - sz // 2, cy - sz // 6, sz, int(sz * 0.5)))
        pygame.draw.circle(surf, self.color, (cx + sz // 3, cy - sz // 8), sz // 5)
        # ears
        pygame.draw.polygon(surf, (90, 60, 40), [
            (cx + sz // 3, cy - sz // 4),
            (cx + sz // 3 + 4, cy - sz // 3),
            (cx + sz // 3 + 8, cy - sz // 5),
        ])
        # tail
        pygame.draw.line(surf, self.color,
                         (cx - sz // 2 + 2, cy),
                         (cx - sz // 2 - 6, cy - 8), 4)
        # eyes
        pygame.draw.circle(surf, (0, 0, 0), (cx + sz // 3 + 4, cy - sz // 8), 1)
        pygame.draw.ellipse(surf, (0, 0, 0),
                            (cx - sz // 2, cy - sz // 6, sz, int(sz * 0.5)), 2)

    def _draw_boss_final(self, surf, p, bob):
        sz = self.size
        cx, cy = p[0], int(p[1] + bob)
        # cape
        cape = pygame.Surface((sz + 16, sz), pygame.SRCALPHA)
        pygame.draw.ellipse(cape, (60, 0, 30, 220),
                            (0, sz // 4, sz + 16, sz * 3 // 4))
        surf.blit(cape, (cx - sz // 2 - 8, cy - sz // 8))
        # body
        pygame.draw.rect(surf, self.color,
                         (cx - sz // 3, cy - sz // 4,
                          int(sz * 0.66), int(sz * 0.6)))
        pygame.draw.rect(surf, (0, 0, 0),
                         (cx - sz // 3, cy - sz // 4,
                          int(sz * 0.66), int(sz * 0.6)), 2)
        # belts
        pygame.draw.line(surf, (0, 0, 0),
                         (cx - sz // 3 + 4, cy - 4),
                         (cx + sz // 3 - 4, cy - 4), 3)
        # head + skull mask
        pygame.draw.circle(surf, (240, 230, 220),
                           (cx, cy - sz // 3), sz // 4)
        pygame.draw.circle(surf, (0, 0, 0),
                           (cx - 6, cy - sz // 3 - 2), 4)
        pygame.draw.circle(surf, (0, 0, 0),
                           (cx + 6, cy - sz // 3 - 2), 4)
        pygame.draw.polygon(surf, (0, 0, 0),
                            [(cx - 4, cy - sz // 3 + 6),
                             (cx, cy - sz // 3 + 11),
                             (cx + 4, cy - sz // 3 + 6)])
        pygame.draw.circle(surf, (0, 0, 0),
                           (cx, cy - sz // 3), sz // 4, 2)
        # crown
        pygame.draw.polygon(surf, (255, 215, 0), [
            (cx - sz // 4, cy - sz // 3 - sz // 5),
            (cx - sz // 5, cy - sz // 3 - sz // 3),
            (cx - sz // 8, cy - sz // 3 - sz // 5),
            (cx, cy - sz // 3 - sz // 3 + 2),
            (cx + sz // 8, cy - sz // 3 - sz // 5),
            (cx + sz // 5, cy - sz // 3 - sz // 3),
            (cx + sz // 4, cy - sz // 3 - sz // 5),
        ])
        pygame.draw.polygon(surf, (0, 0, 0), [
            (cx - sz // 4, cy - sz // 3 - sz // 5),
            (cx - sz // 5, cy - sz // 3 - sz // 3),
            (cx - sz // 8, cy - sz // 3 - sz // 5),
            (cx, cy - sz // 3 - sz // 3 + 2),
            (cx + sz // 8, cy - sz // 3 - sz // 5),
            (cx + sz // 5, cy - sz // 3 - sz // 3),
            (cx + sz // 4, cy - sz // 3 - sz // 5),
        ], 2)
        # gun
        ang = math.atan2(self.facing.y, self.facing.x)
        hx = cx + int(math.cos(ang) * (sz // 2 + 6))
        hy = cy + int(math.sin(ang) * (sz // 2 + 6))
        pygame.draw.line(surf, (40, 40, 40), (cx, cy), (hx, hy), 7)
        pygame.draw.circle(surf, (40, 40, 40), (hx, hy), 6)
