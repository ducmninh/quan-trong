"""Entry point for the Dog Rescue game.

Run with:
    python main.py
"""
from __future__ import annotations

import os
import sys

import pygame

from game import settings as S
from game import sprites
from game import audio
from game.game import Game


def main() -> int:
    pygame.init()
    pygame.display.set_caption("Giải cứu chú chó — Dog Rescue")
    flags = 0
    screen = pygame.display.set_mode((S.SCREEN_W, S.SCREEN_H), flags)
    sprites.init()
    audio.init()

    game = Game(screen)
    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if not game.handle_event(event):
                running = False
                break
        if not running:
            break
        game.update()
        game.draw()
        pygame.display.flip()
        clock.tick(S.FPS)

    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
