import pygame

# Direction deltas: up is 0, clockwise
DIR_TO_DELTA = [
    (0, -1),  # 0: Up
    (1, -1),  # 1: Up-Right
    (1, 0),  # 2: Right
    (1, 1),  # 3: Down-Right
    (0, 1),  # 4: Down
    (-1, 1),  # 5: Down-Left
    (-1, 0),  # 6: Left
    (-1, -1),  # 7: Up-Left
]
DELTA_TO_DIR = [[7, 0, 1], [6, None, 2], [5, 4, 3]]


def sign(x):
    if x > 0:
        return 1
    elif x == 0:
        return 0
    else:
        return -1


def dir_to_delta(dir):
    return DIR_TO_DELTA[dir]


def delta_to_dir(dx, dy):
    return DELTA_TO_DIR[sign(dy) + 1][sign(dx) + 1]


def steer_left(dir):
    return (dir - 1) & 7


def steer_right(dir):
    return (dir + 1) & 7


class Controls:
    def __init__(self, left, right, up, down, shoot, bomb):
        self.left = left
        self.right = right
        self.up = up
        self.down = down
        self.shoot = shoot
        self.bomb = bomb

    def is_any_pressed(self, keystate) -> bool:
        return any(
            keystate[k]
            for k in (self.left, self.right, self.up, self.down, self.shoot, self.bomb)
        )

    def getDir(self, keystate):
        dx = 0
        dy = 0
        if keystate[self.left]:
            dx -= 1
        if keystate[self.right]:
            dx += 1
        if keystate[self.up]:
            dy -= 1
        if keystate[self.down]:
            dy += 1
        return DELTA_TO_DIR[dy + 1][dx + 1]
