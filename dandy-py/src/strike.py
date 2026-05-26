import pygame
from media import load_image


class Strike:
    def __init__(self, name, tileSize):
        self.image = load_image(name)
        self.tileSize = tileSize
        self.tileStride = self.image.get_width() // tileSize
        self.tileMaxY = self.image.get_height() // tileSize

    def draw(self, surface, offsetX, offsetY, x, y, index):
        ty = index // self.tileStride
        if ty <= self.tileMaxY:
            tx = index % self.tileStride
            surface.blit(
                self.image,
                (offsetX + x * self.tileSize, offsetY + y * self.tileSize),
                (tx * self.tileSize, ty * self.tileSize, self.tileSize, self.tileSize),
            )
