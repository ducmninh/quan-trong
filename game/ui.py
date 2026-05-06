"""Title screen, HUD side-panel, and end screens."""
from __future__ import annotations

from typing import List, Optional

import pygame
import math

from . import fonts
from . import settings as S
from . import sprites


class TitleScreen:
    def __init__(self):
        self.title_font = fonts.get(56, bold=True)
        self.font = fonts.get(22)
        self.small = fonts.get(18)
        self.t = 0

    def update(self):
        self.t += 1

    def draw(self, surf: pygame.Surface):
        surf.fill((20, 24, 36))
        for x in range(0, S.SCREEN_W, 40):
            pygame.draw.line(surf, (28, 32, 50), (x, 0), (x, S.SCREEN_H))
        for y in range(0, S.SCREEN_H, 40):
            pygame.draw.line(surf, (28, 32, 50), (0, y), (S.SCREEN_W, y))

        title = self.title_font.render("GIAI CUU DAN CHO", True, (250, 220, 100))
        sub = self.font.render("Giai cuu 5 cho con va me Bong tu bon trom!", True, (220, 220, 230))
        surf.blit(title, (S.SCREEN_W // 2 - title.get_width() // 2, 100))
        surf.blit(sub, (S.SCREEN_W // 2 - sub.get_width() // 2, 180))

        # Draw dog family
        if sprites.DOG_SPRITE:
            big = pygame.transform.scale(sprites.DOG_SPRITE, (120, 120))
            surf.blit(big, (S.SCREEN_W // 2 - 60, 220))
        if sprites.PUPPY_SPRITE:
            for i in range(5):
                puppy = pygame.transform.scale(sprites.PUPPY_SPRITE, (48, 48))
                x = S.SCREEN_W // 2 - 120 + i * 55
                bounce = abs(math.sin(self.t * 0.08 + i * 0.5)) * 8
                surf.blit(puppy, (x, 340 - bounce))

        if sprites.CAGE_SPRITE:
            cage = pygame.transform.scale(sprites.CAGE_SPRITE, (160, 160))
            cage.set_alpha(140)
            surf.blit(cage, (S.SCREEN_W // 2 - 80, 200))

        lines = [
            "Mui ten hoac WASD de di chuyen",
            "Nhat du chia khoa vang trong me cung",
            f"Giai cuu cho con o moi man — man cuoi giai cuu {S.MOTHER_DOG_NAME}!",
            "Tranh trom — chung dung BFS di tuan va A* duoi anh!",
            "Nhat dong xu de mua do trong Shop sau moi man!",
        ]
        for i, line in enumerate(lines):
            t = self.small.render(line, True, (210, 210, 220))
            surf.blit(t, (S.SCREEN_W // 2 - t.get_width() // 2, 420 + i * 26))

        if (self.t // 30) % 2 == 0:
            prompt = self.font.render("Nhan SPACE de bat dau", True, (255, 240, 150))
            surf.blit(prompt, (S.SCREEN_W // 2 - prompt.get_width() // 2, 580))


class HUD:
    def __init__(self):
        self.font = fonts.get(20, bold=True)
        self.small = fonts.get(16)
        self.micro = fonts.get(12)

    def draw(self, surf: pygame.Surface, level_idx: int, level_name: str,
             keys_have: int, keys_total: int, hp: int, hp_max: int,
             dog_freed: bool, player_dfs_cooldown: int, player_dfs_timer: int,
             coins: int = 0, message: Optional[str] = None,
             dog_name: str = "", rescued_count: int = 0):

        # --- Top-Left: Level Info + Dog Name ---
        dog_label = f" | Giai cuu: {dog_name}" if dog_name else ""
        level_txt = self.font.render(f"Man {level_idx + 1} | {level_name}{dog_label}", True, (250, 220, 100))
        self._draw_overlay_box(surf, (15, 15, level_txt.get_width() + 20, 40), level_txt)

        # --- Top-Right: Stats ---
        stats_w = max(hp_max * 28 + 10, 180)
        stats_surf = pygame.Surface((stats_w, 90), pygame.SRCALPHA)
        stats_surf.fill((20, 20, 30, 160))

        # hearts
        for i in range(hp_max):
            img = sprites.HEART_FULL if i < hp else sprites.HEART_EMPTY
            if img:
                stats_surf.blit(img, (10 + i * 28, 10))

        # keys
        if sprites.KEY_SPRITE:
            stats_surf.blit(sprites.KEY_SPRITE, (10, 40))
        kt = self.font.render(f"{keys_have}/{keys_total}", True, (255, 230, 130))
        stats_surf.blit(kt, (42, 44))

        # coins
        coin_txt = self.font.render(f"Xu: {coins}", True, (255, 230, 100))
        stats_surf.blit(coin_txt, (10, 68))

        surf.blit(stats_surf, (S.SCREEN_W - stats_w - 15, 15))

        # --- Rescued dogs counter ---
        rescued_txt = self.small.render(f"Da cuu: {rescued_count}/6 cho", True, (150, 255, 150))
        rescued_bg = pygame.Surface((rescued_txt.get_width() + 16, rescued_txt.get_height() + 8), pygame.SRCALPHA)
        rescued_bg.fill((20, 20, 30, 160))
        rescued_bg.blit(rescued_txt, (8, 4))
        surf.blit(rescued_bg, (S.SCREEN_W - stats_w - 15, 110))

        # --- Bottom-Left: DFS + Controls ---
        dfs_w = 240
        dfs_h = 80
        dfs_surf = pygame.Surface((dfs_w, dfs_h), pygame.SRCALPHA)
        dfs_surf.fill((20, 20, 30, 160))

        dfs_color = (200, 100, 255) if player_dfs_cooldown == 0 else (100, 100, 120)
        dfs_label = self.small.render("[G] DFS Radar: ", True, (220, 220, 240))
        dfs_status = "SAN SANG" if player_dfs_cooldown == 0 else f"Hoi chieu ({player_dfs_cooldown // 60}s)"
        dfs_val = self.small.render(dfs_status, True, dfs_color)
        dfs_surf.blit(dfs_label, (10, 10))
        dfs_surf.blit(dfs_val, (10, 30))

        hint = self.micro.render("WASD: Di chuyen | G: Radar | T: Dich chuyen", True, (160, 160, 180))
        dfs_surf.blit(hint, (10, 55))

        surf.blit(dfs_surf, (15, S.SCREEN_H - dfs_h - 15))

        # --- Bottom-Right: Algorithm Legend ---
        leg_w = 180
        leg_h = 60
        leg_surf = pygame.Surface((leg_w, leg_h), pygame.SRCALPHA)
        leg_surf.fill((20, 20, 30, 160))

        legend = [
            ("Vang: BFS (Tuan tra)", S.GOLD),
            ("Do: A* (Duoi bat)", S.TRAP_RED),
            ("Tim: DFS (Radar)", (200, 100, 255)),
        ]
        for i, (txt, col) in enumerate(legend):
            t = self.micro.render(txt, True, col)
            leg_surf.blit(t, (10, 5 + i * 18))

        surf.blit(leg_surf, (S.SCREEN_W - leg_w - 15, S.SCREEN_H - leg_h - 15))

        if message:
            self._draw_message(surf, message)

    def _draw_overlay_box(self, surf, rect_coords, text_surf):
        x, y, w, h = rect_coords
        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        bg.fill((20, 20, 30, 160))
        surf.blit(bg, (x, y))
        surf.blit(text_surf, (x + 10, y + (h - text_surf.get_height()) // 2))

    def _draw_message(self, surf, message):
        font = fonts.get(22, bold=True)
        text = font.render(message, True, (255, 255, 255))
        bg = pygame.Surface((text.get_width() + 28, text.get_height() + 14), pygame.SRCALPHA)
        bg.fill((30, 30, 40, 220))
        bg.blit(text, (14, 7))
        surf.blit(bg, (S.SCREEN_W // 2 - bg.get_width() // 2, S.SCREEN_H - 120))


class EndScreen:
    def __init__(self, won: bool):
        self.won = won
        self.title_font = fonts.get(54, bold=True)
        self.font = fonts.get(22)
        self.t = 0

    def update(self):
        self.t += 1

    def draw(self, surf: pygame.Surface):
        surf.fill((18, 22, 32) if self.won else (40, 18, 22))
        if self.won:
            title = self.title_font.render(f"DA CUU DUOC {S.MOTHER_DOG_NAME.upper()} VA CA DAN CHO!", True, (250, 220, 100))
            sub = self.font.render("Ca dan cho an toan tro ve. Cam on anh hung nho!", True, (220, 220, 240))
        else:
            title = self.title_font.render("Bi bat mat roi...", True, (250, 130, 140))
            sub = self.font.render("Nhan R de thu lai, Esc de thoat.", True, (220, 220, 240))
        surf.blit(title, (S.SCREEN_W // 2 - title.get_width() // 2, 140))
        surf.blit(sub, (S.SCREEN_W // 2 - sub.get_width() // 2, 220))

        if self.won:
            # Draw the whole dog family
            if sprites.DOG_SPRITE:
                d = pygame.transform.scale(sprites.DOG_SPRITE, (120, 120))
                surf.blit(d, (S.SCREEN_W // 2 - 60, 280))
            if sprites.PUPPY_SPRITE:
                for i in range(5):
                    p = pygame.transform.scale(sprites.PUPPY_SPRITE, (48, 48))
                    x = S.SCREEN_W // 2 - 120 + i * 55
                    bounce = abs(math.sin(self.t * 0.1 + i * 0.7)) * 10
                    surf.blit(p, (x, 400 - bounce))

        prompt = self.font.render("Nhan SPACE de choi lai tu dau", True, (255, 240, 150))
        if (self.t // 30) % 2 == 0:
            surf.blit(prompt, (S.SCREEN_W // 2 - prompt.get_width() // 2, 500))


class CharSelect:
    def __init__(self):
        self.skins = ["Boy", "Girl", "Ninja"]
        self.idx = 0
        self.font = fonts.get(28, bold=True)
        self.small = fonts.get(18)
        self.t = 0

    def update(self):
        self.t += 1

    def draw(self, surf: pygame.Surface):
        surf.fill((20, 25, 40))
        title = self.font.render("CHON NHAN VAT", True, (255, 255, 255))
        surf.blit(title, (S.SCREEN_W // 2 - title.get_width() // 2, 100))

        for i, skin in enumerate(self.skins):
            color = (255, 230, 100) if i == self.idx else (120, 120, 150)
            txt = self.font.render(skin, True, color)
            x = S.SCREEN_W // 2 - 200 + i * 200
            y = 350

            preview = sprites.PLAYER_SKINS[skin]["A"]
            prev_scaled = pygame.transform.scale(preview, (128, 128))
            if i == self.idx:
                bounce = abs(math.sin(self.t * 0.1)) * 15
                surf.blit(prev_scaled, (x - 64, y - 150 - bounce))
            else:
                surf.blit(prev_scaled, (x - 64, y - 150))

            surf.blit(txt, (x - txt.get_width() // 2, y))

        hint = self.small.render("Dung Mui ten de chon — SPACE de bat dau", True, (200, 200, 220))
        surf.blit(hint, (S.SCREEN_W // 2 - hint.get_width() // 2, 550))


class ShopScreen:
    def __init__(self, coins: int, level_idx: int):
        self.coins = coins
        self.level_idx = level_idx
        self.items = [
            {"id": "speed", "name": "Giay Than Toc", "cost": 100, "desc": "Tang 50% toc do chay"},
            {"id": "key", "name": "Chia Khoa Vang", "cost": 50, "desc": "Bat dau voi 1 chia khoa"},
            {"id": "teleport", "name": "Dich Chuyen", "cost": 150, "desc": "Phim T de ve nha tru an"},
            {"id": "gun", "name": "Sung Luc (10 vien)", "cost": 300, "desc": "Phim ENTER de ban trom"},
            {"id": "stop", "name": "Ngung Dong Thoi Gian", "cost": 250, "desc": "Phim Q: Dung trom 5 giay"},
        ]
        self.idx = 0
        self.font = fonts.get(24, bold=True)
        self.small = fonts.get(18)
        self.bought = set()

    def update(self):
        pass

    def draw(self, surf: pygame.Surface):
        overlay = pygame.Surface((S.SCREEN_W, S.SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surf.blit(overlay, (0, 0))

        shop_w = S.SCREEN_W - 300
        shop_h = S.SCREEN_H - 200
        pygame.draw.rect(surf, (40, 50, 80), (150, 100, shop_w, shop_h))
        pygame.draw.rect(surf, (255, 230, 100), (150, 100, shop_w, shop_h), 3)

        title = self.font.render("CUA HANG NANG CAP", True, (255, 230, 100))
        surf.blit(title, (S.SCREEN_W // 2 - title.get_width() // 2, 120))

        coins_txt = self.font.render(f"Xu cua ban: {self.coins}", True, (255, 215, 0))
        surf.blit(coins_txt, (S.SCREEN_W // 2 - coins_txt.get_width() // 2, 155))

        # Draw shop keeper
        if sprites.SHOP_KEEPER_SPRITE:
            keeper = pygame.transform.scale(sprites.SHOP_KEEPER_SPRITE, (80, 80))
            surf.blit(keeper, (170, 115))

        for i, item in enumerate(self.items):
            y = 200 + i * 75
            selected = i == self.idx
            bought = item["id"] in self.bought
            can_afford = self.coins >= item["cost"]

            bg_color = (60, 80, 120) if selected else (40, 50, 80)
            if bought:
                bg_color = (30, 60, 30)
            pygame.draw.rect(surf, bg_color, (180, y, shop_w - 60, 65))
            if selected:
                pygame.draw.rect(surf, (255, 230, 100), (180, y, shop_w - 60, 65), 2)

            name_color = (150, 150, 150) if bought else ((255, 255, 255) if can_afford else (200, 100, 100))
            name = self.font.render(item["name"], True, name_color)
            cost = self.small.render(f"{item['cost']} xu" if not bought else "DA MUA", True,
                                     (100, 200, 100) if bought else ((255, 215, 0) if can_afford else (200, 100, 100)))
            desc = self.small.render(item["desc"], True, (180, 180, 200))

            surf.blit(name, (200, y + 5))
            surf.blit(cost, (shop_w + 100 - cost.get_width(), y + 5))
            surf.blit(desc, (200, y + 35))

        hint = self.small.render("UP/DOWN: Chon | ENTER: Mua | SPACE: Tiep tuc man tiep theo", True, (200, 200, 220))
        surf.blit(hint, (S.SCREEN_W // 2 - hint.get_width() // 2, S.SCREEN_H - 130))

        next_lvl = self.level_idx + 2
        if next_lvl <= len(S.LEVELS):
            next_cfg = S.LEVELS[self.level_idx + 1]
            next_txt = self.small.render(f"Man tiep theo: {next_cfg['name']} ({next_cfg['thieves']} trom)", True, (180, 220, 255))
            surf.blit(next_txt, (S.SCREEN_W // 2 - next_txt.get_width() // 2, S.SCREEN_H - 100))
