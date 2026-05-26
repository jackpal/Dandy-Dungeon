import pygame
from constants import SPACE, LOCK, UP, GHOST
from media import get_media_path


class Map:
    def __init__(self, width, height):
        "Takes height and width in tiles"
        self.width = width
        self.height = height
        self.data = [x % 32 for x in range(width * height)]

    def set(self, x, y, val):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.data[x + y * self.width] = val
        else:
            raise Exception("x, y out of range")

    def get(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.data[x + y * self.width]
        else:
            raise Exception("x, y out of range")

    def erase(self, x, y, val):
        offset = x + y * self.width
        if self.data[offset] == val:
            self.data[offset] = SPACE

    def unlock(self, start_x, start_y):
        if not (0 <= start_x < self.width and 0 <= start_y < self.height):
            return

        if self.data[start_x + start_y * self.width] != LOCK:
            return

        self.data[start_x + start_y * self.width] = SPACE
        stack = [(start_x, start_y)]

        while stack:
            cx, cy = stack.pop()
            for nx in range(cx - 1, cx + 2):
                for ny in range(cy - 1, cy + 2):
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        n_idx = nx + ny * self.width
                        if self.data[n_idx] == LOCK:
                            self.data[n_idx] = SPACE
                            stack.append((nx, ny))

    def toOffset(self, target, screenLength, mapLength):
        "target, screenLength, mapLength all in pixels"
        offset = -target + screenLength // 2
        return max(min(0, offset), -(mapLength - screenLength))

    def draw(self, screen, targetX, targetY, tileset):
        "draw map on screen using tileset. Try to put (targetX, targetY) at the center of the screen"
        tileSize = tileset.tileSize
        sw, sh = screen.get_width(), screen.get_height()
        offsetX = self.toOffset(targetX, sw, self.width * tileSize)
        offsetY = self.toOffset(targetY, sh, self.height * tileSize)
        active = self.getActive(sw, sh, offsetX, offsetY, tileSize)
        for dy in range(active.top, active.bottom):
            for dx in range(active.left, active.right):
                tileset.draw(
                    screen, offsetX, offsetY, dx, dy, self.data[dy * self.width + dx]
                )
        return active

    def getActive(self, screen_width, screen_height, offsetX, offsetY, tileSize):
        "Returns the active rectangle in tiles for the given offsets"
        left = max(0, -offsetX // tileSize)
        right = min(self.width, (-offsetX + screen_width + tileSize - 1) // tileSize)
        top = max(0, -offsetY // tileSize)
        bottom = min(self.height, (-offsetY + screen_height + tileSize - 1) // tileSize)
        return pygame.Rect(left, top, right - left, bottom - top)

    def load(self, level):
        levelPath = get_media_path(f"levels/LEVEL.{chr(ord('A') + level)}")
        with open(levelPath, "rb") as f:
            block = f.read(len(self.data) // 2)
            for i, b in enumerate(block):
                self.data[i * 2] = b & 15
                self.data[i * 2 + 1] = (b >> 4) & 15

    def find(self, item):
        for i, val in enumerate(self.data):
            if val == item:
                return (i % self.width, i // self.width)
        raise Exception("Did not find item")

    def bomb(self, rect):
        score = 0
        for y in range(rect.top, rect.bottom):
            for x in range(rect.left, rect.right):
                offset = x + y * self.width
                v = self.data[offset]
                if GHOST <= v < GHOST + 3:
                    self.data[offset] = SPACE
                    score += 10 * (v - GHOST + 1)
        return score
