# Dandy Dungeon
# Time Log:
# First two hours:
#  Initialize screen
#  Read tile set
#  Read map data
#  Draw map on screen
#  Smooth scrolling
#  Active area
# 30 minutes - create player, game
#  Initial levelload logic.
# 1 hour
#  Controls, generator for active players
#  can move guy around screen (at 60 steps/second)
#  cam move guy around screen at 15 Hz.
# 3:30-3:45: smooth scrolling for cog
#  get sliding along walls working.
# 4:00 got player movement working, including locks


from __future__ import with_statement
import random, os, os.path

import pygame
from pygame.locals import *

TILE_SIZE = 16
SCREENRECT = Rect(0, 0, 320, 240)
MAPRECT = Rect(0,0, SCREENRECT.width, TILE_SIZE * 10)
MAP_WIDTH = 60
MAP_HEIGHT = 30

# Map content enums
SPACE = 0
WALL = 1
LOCK = 2
UP = 3
DOWN = 4
KEY = 5
FOOD = 6
MONEY = 7
BOMB = 8
GHOST = 9 # 9, 10, 11
HEART = 12
GENERATOR = 13 # 13, 14, 15
ARROW = 16 # .. 23
PLAYER = 24 # 24..27

def get_media_path(path):
    return os.path.join('../Media', path)

def load_image(file):
    "loads an image, prepares it for play"
    file = get_media_path(file)
    try:
        surface = pygame.image.load(file)
    except pygame.error:
        raise SystemExit, 'Could not load image "%s" %s'%(file, pygame.get_error())
    return surface

class Strike:
    def __init__(self, name, tileSize):
        self.image = load_image(name)
        self.tileSize = tileSize
        self.tileStride = self.image.get_width() / tileSize
        self.tileMaxY = self.image.get_height() / tileSize

    def draw(self, surface, offsetX, offsetY, x, y, index):
        ty = index / self.tileStride
        if ty <= self.tileMaxY:
            tx = index - ty * self.tileStride
            surface.blit(self.image,
                        (offsetX + x * self.tileSize,
                         offsetY + y * self.tileSize),
                        Rect(tx * self.tileSize, ty * self.tileSize,
                              self.tileSize, self.tileSize))

class Map:
    def __init__(self, width, height):
        "Takes height and width in tiles"
        self.width = width
        self.height = height
        self.data = [0] * width * height
        self.data = [x % 32 for x in xrange(0, width* height)]

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

    def unlock(self, x, y):
        self.unlock2(x + y * self.width)

    def unlock2(self, index):
        if self.data[index] == LOCK:
            self.data[index] = SPACE
            self.unlock2(index - self.width - 1)
            self.unlock2(index - self.width)
            self.unlock2(index - self.width + 1)
            self.unlock2(index - 1)
            self.unlock2(index + 1)
            self.unlock2(index + self.width - 1)
            self.unlock2(index + self.width)
            self.unlock2(index + self.width + 1)

    def toOffset(self, target, screenLength, mapLength):
        "target, screenLength, mapLength all in pixels"
        offset = -target + screenLength / 2
        return max(min(0, offset) , -(mapLength - screenLength))

    def draw(self, screen, targetX, targetY, tileset):
        "draw map on screen using tileset. Try to put (targetX, targetY) at the center of the screen"
        tileSize = tileset.tileSize
        offsetX = self.toOffset(targetX, screen.get_width(), self.width * tileSize)
        offsetY = self.toOffset(targetY, screen.get_height(), self.height * tileSize)
        active = self.getActive(screen, targetX, targetY, tileset.tileSize)
        for y in xrange(0, active.height):
            dy = y + active.top
            for x in xrange(0, active.width):
                dx = x + active.left
                tileset.draw(screen, offsetX, offsetY, dx, dy, self.data[dy * self.width + dx])
        return active

    def getActive(self, screen, targetX, targetY, tileSize):
        "Returns the active rectangle in tiles for the given target in pixels"
        screenWidth = screen.get_width()
        screenHeight = screen.get_height()
        offsetX = self.toOffset(targetX, screenWidth, self.width * tileSize)
        offsetY = self.toOffset(targetY, screenHeight, self.height * tileSize)
        left = -offsetX / tileSize
        right = (-offsetX + screenWidth + tileSize - 1) / tileSize
        top = -offsetY / tileSize
        bottom = (-offsetY + screenHeight + tileSize - 1) / tileSize
        return Rect(left, top, right - left, bottom - top)

    def load(self, level):
        levelPath = get_media_path("levels/LEVEL." + chr(ord('A') + level))
        with open(levelPath, 'r') as f:
            for x in xrange(0, len(self.data) / 2):
                b = ord(f.read(1))
                self.data[x * 2] = b & 15
                self.data[x * 2 + 1] = (b >> 4) & 15

    def find(self, item):
        for i in xrange(len(self.data)):
            if self.data[i] == item:
                return (i % self.width, i / self.width)
        raise Exception("Didn't find item")

    def bomb(self, rect):
        score = 0
        for y in xrange(rect.top, rect.bottom):
            for x in xrange(rect.left, rect.right):
                offset = x + y * self.width
                v = self.data[offset]
                if GHOST <= v < GHOST + 3:
                    self.data[offset] = SPACE
                    score += 10 * (v - GHOST + 1)
        return score

class Arrow:
    def __init__(self, x, y, dir):
        self.x = x
        self.y = y
        self.dir = dir

STATE_DEAD = 0
STATE_ACTIVE = 1
STATE_IN_WARP = 2

class Player:
    def __init__(self, index):
        self.index = index
        self.score = 0
        self.health = 100
        self.bombs = 0
        self.keys = 0
        self.state = STATE_DEAD

    def isAlive(self):
        return self.state != STATE_DEAD

    def start(self, x, y, dir):
        self.x = x
        self.y = y
        self.dir = dir
        self.arrow = None
        self.state = STATE_ACTIVE

# Direction, up is 0, clockwise

DIR_TO_DELTA_X = [ 0,  1, 1, 1, 0, -1, -1, -1]
DIR_TO_DELTA_Y = [-1, -1, 0, 1, 1,  1,  0, -1]
DELTA_TO_DIR = [[7, 0, 1], [6, None, 2], [5, 4, 3]]

def sign(x):
    if x > 0: return 1
    elif x == 0: return 0
    else: return -1

def dir_to_delta(dir):
    return DIR_TO_DELTA_X[dir], DIR_TO_DELTA_Y[dir]

def delta_to_dir(dx, dy):
    return DELTA_TO_DIR[sign(dy) + 1][sign(dx) + 1]

def steer_left(dir):
    return (dir - 1) & 7

def steer_right(dir):
    return (dir + 1) & 7

def getDelta(dir):
    return (DIR_TO_DELTA_X[dir], DIR_TO_DELTA_Y[dir])

class Controls:
    def __init__(self, left, right, up, down, shoot, bomb):
        self.left = left
        self.right = right
        self.up = up
        self.down = down
        self.shoot = shoot
        self.bomb = bomb

    def getDir(self, keystate):
        dx = 0
        dy = 0
        if keystate[self.left]: dx -= 1
        if keystate[self.right]: dx += 1
        if keystate[self.up]: dy -= 1
        if keystate[self.down]: dy += 1
        return DELTA_TO_DIR[dy + 1][dx + 1]

class Game:
    def __init__(self):
        self.tiles = Strike('dandy.bmp', TILE_SIZE)
        # Change xrange for 1..4 players
        self.players = [Player(i) for i in xrange(0,1)]
        self.players[0].state = STATE_ACTIVE
        self.controls = [Controls(K_LEFT, K_RIGHT, K_UP, K_DOWN, K_SPACE, K_z),
                         None, None, None]
        self.level = 0
        self.map = Map(MAP_WIDTH, MAP_HEIGHT)
        self.load()
        self.time = 0
        self.last_move_time = 0
        self.TICKS_PER_MOVE = 4
        self.rotor = 0

    def active_players(self):
        for p in self.players:
            if p.state == STATE_ACTIVE:
                yield p

    def live_players(self):
        for p in self.players:
            if p.isAlive():
                yield p
                
    def dead_players(self):
        for p in self.players:
            if not p.isAlive():
                yield p
                
    def load(self):
        self.map.load(self.level)
        self.rotor = 0
        try:
            x, y = self.map.find(UP)
        except Exception:
            x, y = 2, 2
        for p in self.live_players():
            dir = p.index * 2
            p.start(x + DIR_TO_DELTA_X[dir], y + DIR_TO_DELTA_Y[dir], dir)
            self.map.set(p.x, p.y, PLAYER + p.index)
        self.cogX, self.cogY = self.getCog()

    def move_player(self, p, x, y):
        self.map.set(p.x, p.y, SPACE)
        p.x = x
        p.y = y
        self.map.set(x, y, PLAYER + p.index)

    def step(self, keystate):
        self.time += 1
        if self.time - self.last_move_time >= self.TICKS_PER_MOVE:
            self.last_move_time = self.time
            playersActive = False
            for p in self.active_players():
                playersActive = True
                self.step_player(p, keystate)
            self.step_enemies()
            if not playersActive:
                self.nextLevel()

    def nextLevel(self):
        if self.allDead():
            return
        self.level = min(self.level + 1, 25)
        self.load()

    def allDead(self):
        for p in self.players:
            if p.isAlive():
                return False
        return True

    def step_enemies(self):
        vr = self.visibleRect
        if vr == None:
            return
        self.rotor = (self.rotor + 1) & 3
        xStart = ((vr.left + 1) & ~1) + (self.rotor & 1)
        yStart = ((vr.top + 1) & ~1) + ((self.rotor >> 1) & 1)
        for y in xrange(yStart, vr.bottom, 2):
            for x in xrange(xStart, vr.right, 2):
                v = self.map.get(x, y)
                if GHOST <= v <= GHOST + 2:
                    self.step_ghost(x, y)
                elif GENERATOR <= v <= GENERATOR + 2:
                    self.step_generator(x, y)
    
    def step_ghost(self, x, y):
        p, dir = self.closest_player(x, y)
        if dir == None:
            return
        self.move_ghost(x, y, dir) or self.move_ghost(x, y, steer_left(dir)) \
            or self.move_ghost(x, y, steer_right(dir))
    
    def closest_player(self, x, y):
        best_p, best_dist, best_dir = None, None, None
        for p in self.active_players():
            dx, dy = p.x - x, p.y - y
            distance = abs(dx) + abs(dy)
            if best_dist == None or best_dist > distance:
                best_dist, best_p, best_dx, best_dy = distance, p, dx, dy
        if best_dist != None:
            best_dir = delta_to_dir(best_dx, best_dy)
        return best_p, best_dir
    
    def move_ghost(self, x, y, dir):
        dx, dy = dir_to_delta(dir)
        nx, ny = x + dx, y + dy
        mv = self.map.get(x, y)
        v = self.map.get(nx, ny)
        if v == SPACE:
            self.map.set(x, y, SPACE)
            self.map.set(nx, ny, mv)
            return True
        elif PLAYER <= v <= PLAYER + 3:
            self.map.set(x, y, SPACE)
            self.hurt_player(self.players[v-PLAYER], 10 * (mv - GHOST))
            return True
        elif ARROW <= v <= ARROW + 7:
            # monsters freeze when about to move into an arrow
            return True
        return False
    
    def hurt_player(self, p, pain):
        if p.health > pain:
            p.health -= pain
        else:
            p.health = 0
            p.state = STATE_DEAD
            v = SPACE
            if p.keys > 0:
                v = KEY
                p.keys -= 1
            self.map.set(p.x, p.y, v)

    def step_generator(self, x, y):
        pass
    def step_player(self, p, keystate):
        control = self.controls[p.index]
        dir = control.getDir(keystate)
        if dir != None:
            p.dir = dir

        if keystate[control.bomb]:
            if p.bombs > 0:
                p.bombs -= 1
                self.do_bomb(p)
        if keystate[control.shoot]:
            if p.arrow == None:
                if dir == None:
                    dir = p.dir
                if dir == None:
                    dir = 0
                p.arrow = Arrow(p.x, p.y, dir)
        else:
            if dir != None:
                self.try_move(p, dir) or self.try_move(p, (dir + 1) & 7) or self.try_move(p, (dir - 1) & 7)
        self.move_arrow(p)

    def move_arrow(self, p):
        a = p.arrow
        if a != None:
            dir = a.dir
            arrowVal = ARROW + ((dir + 3) & 7)
            dx, dy = getDelta(dir)
            x, y =  a.x + dx, a.y + dy
            self.map.erase(a.x, a.y, arrowVal)
            v = self.map.get(x, y)
            newV = SPACE
            kill = True
            if v == SPACE:
                a.x, a.y = x, y
                newV = arrowVal
                kill = False
            elif GHOST <= v <= GHOST + 2:
                p.score += 10
                if v > GHOST:
                    newV = v - 1
            elif v == HEART:
                newV = GHOST + 2
                for p2 in self.dead_players():
                    # pick the first one.
				    p2.state = STATE_ACTIVE
				    p2.x = x
				    p2.y = y
				    newV = PLAYER + p2.index
				    break
            elif v == BOMB:
                self.do_bomb(p)
            else:
                newV = v
            self.map.set(x, y, newV)
            if kill:
                p.arrow = None

    def do_bomb(self, p):
        p.score += self.map.bomb(self.visibleRect)

    def try_move(self, p, dir):
        p.dir = dir
        dx, dy = getDelta(dir)
        x = p.x + dx
        y = p.y + dy
        v = self.map.get(x, y)
        moved = False
        if v == SPACE:
            moved = True
        elif v == LOCK:
            if p.keys > 0:
                p.keys -= 1
                self.map.unlock(x, y)
                moved = True
        elif v == DOWN:
            p.state = STATE_IN_WARP
            self.map.set(p.x, p.y, SPACE)
            return True
        elif v == KEY:
            p.keys += 1
            moved = True
        elif v == FOOD:
            p.health += 100
            moved = True
        elif v == MONEY:
            p.score += 100
            moved = True
        elif v == BOMB:
            p.bombs += 1
            moved = True
        if moved:
            self.move_player(p, x, y)
        return moved

    def getCog(self):
        cogx = 0
        cogy = 0
        numActive = 0
        for p in self.active_players():
            cogx += TILE_SIZE * p.x
            cogy += TILE_SIZE * p.y
            numActive += 1
        if numActive > 0:
            cogx /= numActive
            cogy /= numActive
        cogx += TILE_SIZE / 2
        cogy += TILE_SIZE / 2
        return (cogx, cogy)

    def draw(self, screen, mapScreen):
        x, y = self.getCog()
        maxRate = TILE_SIZE / self.TICKS_PER_MOVE
        dx = x - self.cogX
        dy = y - self.cogY
        if dx != 0 or dy != 0:
            dx = max(-maxRate, min(dx, maxRate))
            dy = max(-maxRate, min(dy, maxRate))
            self.cogX += dx
            self.cogY += dy

        self.visibleRect = self.map.draw(mapScreen, self.cogX, self.cogY, self.tiles)


def main():
    # Initialize pygame
    pygame.init()
    if pygame.mixer and not pygame.mixer.get_init():
        print 'Warning, no sound'
        pygame.mixer = None

    # Set the display mode
    winstyle = 0  # |FULLSCREEN
    bestdepth = pygame.display.mode_ok(SCREENRECT.size, winstyle, 32)
    screen = pygame.display.set_mode(SCREENRECT.size, winstyle, bestdepth)
    mapScreen = screen.subsurface(MAPRECT)

    pygame.display.set_caption('Dandy Dungeon')
    pygame.mouse.set_visible(0)

    game = Game()

    while 1:
        for event in pygame.event.get():
            if event.type == QUIT or \
                (event.type == KEYDOWN and event.key == K_ESCAPE):
                    return
        keystate = pygame.key.get_pressed()
        game.step(keystate)
        game.draw(screen, mapScreen)
        pygame.display.flip()

if __name__ == '__main__':
     main()
