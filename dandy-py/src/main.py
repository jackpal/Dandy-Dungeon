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
import os
import os.path

import pygame

TILE_SIZE = 16
SCREENRECT = pygame.Rect(0, 0, 320, 280)
MAPRECT = pygame.Rect(0, 40, 320, 240)
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
GHOST = 9  # 9, 10, 11
HEART = 12
GENERATOR = 13  # 13, 14, 15
ARROW = 16  # .. 23
PLAYER = 24  # 24..27


def get_media_path(path):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../Media", path))


def load_image(file):
    "loads an image, prepares it for play"
    file = get_media_path(file)
    try:
        surface = pygame.image.load(file)
    except pygame.error:
        raise SystemExit('Could not load image "%s" %s' % (file, pygame.get_error()))
    return surface


class Strike:
    def __init__(self, name, tileSize):
        self.image = load_image(name)
        self.tileSize = tileSize
        self.tileStride = self.image.get_width() // tileSize
        self.tileMaxY = self.image.get_height() // tileSize

    def draw(self, surface, offsetX, offsetY, x, y, index):
        ty = index // self.tileStride
        if ty <= self.tileMaxY:
            tx = index - ty * self.tileStride
            surface.blit(
                self.image,
                (offsetX + x * self.tileSize, offsetY + y * self.tileSize),
                pygame.Rect(
                    tx * self.tileSize, ty * self.tileSize, self.tileSize, self.tileSize
                ),
            )


class Map:
    def __init__(self, width, height):
        "Takes height and width in tiles"
        self.width = width
        self.height = height
        self.data = [0] * width * height
        self.data = [x % 32 for x in range(0, width * height)]

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
        offset = -target + screenLength // 2
        return max(min(0, offset), -(mapLength - screenLength))

    def draw(self, screen, targetX, targetY, tileset):
        "draw map on screen using tileset. Try to put (targetX, targetY) at the center of the screen"
        tileSize = tileset.tileSize
        offsetX = self.toOffset(targetX, screen.get_width(), self.width * tileSize)
        offsetY = self.toOffset(targetY, screen.get_height(), self.height * tileSize)
        active = self.getActive(screen, targetX, targetY, tileset.tileSize)
        for y in range(0, active.height):
            dy = y + active.top
            for x in range(0, active.width):
                dx = x + active.left
                tileset.draw(
                    screen, offsetX, offsetY, dx, dy, self.data[dy * self.width + dx]
                )
        return active

    def getActive(self, screen, targetX, targetY, tileSize):
        "Returns the active rectangle in tiles for the given target in pixels"
        screenWidth = screen.get_width()
        screenHeight = screen.get_height()
        offsetX = self.toOffset(targetX, screenWidth, self.width * tileSize)
        offsetY = self.toOffset(targetY, screenHeight, self.height * tileSize)
        left = -offsetX // tileSize
        right = (-offsetX + screenWidth + tileSize - 1) // tileSize
        top = -offsetY // tileSize
        bottom = (-offsetY + screenHeight + tileSize - 1) // tileSize
        return pygame.Rect(left, top, right - left, bottom - top)

    def load(self, level):
        levelPath = get_media_path("levels/LEVEL." + chr(ord("A") + level))
        with open(levelPath, "rb") as f:
            block = f.read(len(self.data) // 2)
            for i, b in enumerate(block):
                self.data[i * 2] = b & 15
                self.data[i * 2 + 1] = (b >> 4) & 15

    def find(self, item):
        for i in range(len(self.data)):
            if self.data[i] == item:
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


class Arrow:
    def __init__(self, x, y, dir):
        self.x = x
        self.y = y
        self.dir = dir


STATE_DEAD = 0
STATE_ACTIVE = 1
STATE_IN_WARP = 2
STATE_INACTIVE = 3


class Player:
    def __init__(self, index):
        self.index = index
        self.score = 0
        self.health = 100
        self.bombs = 0
        self.keys = 0
        self.state = STATE_INACTIVE if index > 0 else STATE_ACTIVE
        self.arrow = None

    def isAlive(self):
        return self.state in (STATE_ACTIVE, STATE_IN_WARP)

    def start(self, x, y, dir):
        self.x = x
        self.y = y
        self.dir = dir
        self.arrow = None
        self.state = STATE_ACTIVE


# Direction, up is 0, clockwise

DIR_TO_DELTA_X = [0, 1, 1, 1, 0, -1, -1, -1]
DIR_TO_DELTA_Y = [-1, -1, 0, 1, 1, 1, 0, -1]
DELTA_TO_DIR = [[7, 0, 1], [6, None, 2], [5, 4, 3]]


def sign(x):
    if x > 0:
        return 1
    elif x == 0:
        return 0
    else:
        return -1


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
        if keystate[self.left]:
            dx -= 1
        if keystate[self.right]:
            dx += 1
        if keystate[self.up]:
            dy -= 1
        if keystate[self.down]:
            dy += 1
        return DELTA_TO_DIR[dy + 1][dx + 1]


class Game:
    def __init__(self):
        self.tiles = Strike("dandy.bmp", TILE_SIZE)
        # Two players: P1 active, P2 inactive (handled by Player.__init__)
        self.players = [Player(0), Player(1)]
        self.controls = [
            Controls(
                pygame.K_LEFT,
                pygame.K_RIGHT,
                pygame.K_UP,
                pygame.K_DOWN,
                pygame.K_SPACE,
                pygame.K_z,
            ),
            Controls(
                pygame.K_a,
                pygame.K_d,
                pygame.K_w,
                pygame.K_s,
                pygame.K_f,
                pygame.K_g,
            ),
            None,
            None,
        ]
        pygame.font.init()
        self.hud_fonts = {}
        self.game_surface = pygame.Surface((320, 240))
        self.level = 0
        self.map = Map(MAP_WIDTH, MAP_HEIGHT)
        self.load()
        self.time = 0
        self.last_move_time = 0
        self.TICKS_PER_MOVE = 4
        self.rotor = 0
        self.visibleRect = None

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
            if p.state == STATE_DEAD:
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

    def join_player(self, p):
        p1 = self.players[0]
        spawned = False
        if p1.isAlive():
            # Try to find empty space adjacent to P1
            for dir in range(8):
                dx, dy = getDelta(dir)
                nx, ny = p1.x + dx, p1.y + dy
                if 0 <= nx < self.map.width and 0 <= ny < self.map.height:
                    if self.map.get(nx, ny) == SPACE:
                        p.start(nx, ny, dir)
                        self.map.set(nx, ny, PLAYER + p.index)
                        spawned = True
                        break
        if not spawned:
            # Fallback to UP stairs
            try:
                x, y = self.map.find(UP)
            except Exception:
                x, y = 2, 2
            dir = p.index * 2
            p.start(x + DIR_TO_DELTA_X[dir], y + DIR_TO_DELTA_Y[dir], dir)
            self.map.set(p.x, p.y, PLAYER + p.index)
            
        # Trigger camera update to center on both
        self.cogX, self.cogY = self.getCog()

    def step(self, keystate):
        # Check P2 hot-join
        if len(self.players) > 1:
            p2 = self.players[1]
            if p2.state == STATE_INACTIVE:
                p2_control = self.controls[1]
                if any(keystate[key] for key in [p2_control.left, p2_control.right, p2_control.up, p2_control.down, p2_control.shoot, p2_control.bomb]):
                    self.join_player(p2)

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
        if vr is None:
            return
        self.rotor = (self.rotor + 1) & 3
        xStart = ((vr.left + 1) & ~1) + (self.rotor & 1)
        yStart = ((vr.top + 1) & ~1) + ((self.rotor >> 1) & 1)
        for y in range(yStart, vr.bottom, 2):
            for x in range(xStart, vr.right, 2):
                v = self.map.get(x, y)
                if GHOST <= v <= GHOST + 2:
                    self.step_ghost(x, y)
                elif GENERATOR <= v <= GENERATOR + 2:
                    self.step_generator(x, y)

    def step_ghost(self, x, y):
        p, dir = self.closest_player(x, y)
        if dir is None:
            return
        self.move_ghost(x, y, dir) or self.move_ghost(
            x, y, steer_left(dir)
        ) or self.move_ghost(x, y, steer_right(dir))

    def closest_player(self, x, y):
        best_p, best_dist, best_dir = None, None, None
        for p in self.active_players():
            dx, dy = p.x - x, p.y - y
            distance = abs(dx) + abs(dy)
            if best_dist is None or best_dist > distance:
                best_dist, best_p, best_dx, best_dy = distance, p, dx, dy
        if best_dist is not None:
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
            self.hurt_player(self.players[v - PLAYER], 10 * (mv - GHOST))
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
        if dir is not None:
            p.dir = dir

        if keystate[control.bomb]:
            if p.bombs > 0:
                p.bombs -= 1
                self.do_bomb(p)
        if keystate[control.shoot]:
            if p.arrow is None:
                if dir is None:
                    dir = p.dir
                if dir is None:
                    dir = 0
                p.arrow = Arrow(p.x, p.y, dir)
        else:
            if dir is not None:
                self.try_move(p, dir) or self.try_move(
                    p, (dir + 1) & 7
                ) or self.try_move(p, (dir - 1) & 7)
        self.move_arrow(p)

    def move_arrow(self, p):
        a = p.arrow
        if a is not None:
            dir = a.dir
            arrowVal = ARROW + ((dir + 3) & 7)
            dx, dy = getDelta(dir)
            x, y = a.x + dx, a.y + dy
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
        if self.visibleRect is not None:
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
            cogx //= numActive
            cogy //= numActive
        cogx += TILE_SIZE // 2
        cogy += TILE_SIZE // 2
        return (cogx, cogy)

    def draw_hud(self, screen, window_w, hud_height):
        # Clear HUD area
        screen.fill((0, 0, 0), pygame.Rect(0, 0, window_w, hud_height))
        
        window_h = screen.get_height()
        target_size = max(10, int(16 * (window_h / 560.0)))
        if target_size not in self.hud_fonts:
            self.hud_fonts[target_size] = pygame.font.SysFont("arial,helvetica,sans", target_size, bold=True)
        font = self.hud_fonts[target_size]
        
        x = max(10, int(window_w * (10.0 / 640.0)))
        
        # P1 (Red)
        p1 = self.players[0]
        p1_text = f"P1  SCORE: {p1.score:<6}  HEALTH: {p1.health:<3}  KEYS: {p1.keys}  BOMBS: {p1.bombs}"
        p1_surf = font.render(p1_text, True, (255, 85, 85))
        p1_y = int(hud_height * (15.0 / 80.0))
        screen.blit(p1_surf, (x, p1_y))
        
        # P2 (Green or Gray)
        if len(self.players) > 1:
            p2 = self.players[1]
            if p2.state == STATE_INACTIVE:
                p2_text = "P2: Press W/A/S/D to Join"
                p2_surf = font.render(p2_text, True, (128, 128, 128))
            else:
                p2_text = f"P2  SCORE: {p2.score:<6}  HEALTH: {p2.health:<3}  KEYS: {p2.keys}  BOMBS: {p2.bombs}"
                p2_surf = font.render(p2_text, True, (85, 255, 85))
            p2_y = int(hud_height * (45.0 / 80.0))
            screen.blit(p2_surf, (x, p2_y))

    def draw(self, screen):
        x, y = self.getCog()
        maxRate = TILE_SIZE // self.TICKS_PER_MOVE
        dx = x - self.cogX
        dy = y - self.cogY
        if dx != 0 or dy != 0:
            dx = max(-maxRate, min(dx, maxRate))
            dy = max(-maxRate, min(dy, maxRate))
            self.cogX += dx
            self.cogY += dy

        self.game_surface.fill((0, 0, 0))
        self.visibleRect = self.map.draw(self.game_surface, self.cogX, self.cogY, self.tiles)
        window_w, window_h = screen.get_size()
        hud_height = int(window_h * (80.0 / 560.0))
        scaled_game = pygame.transform.scale(self.game_surface, (window_w, window_h - hud_height))
        screen.blit(scaled_game, (0, hud_height))
        self.draw_hud(screen, window_w, hud_height)

    def can_ghost_move_dir(self, x, y, dir):
        dx, dy = dir_to_delta(dir)
        nx, ny = x + dx, y + dy
        if 0 <= nx < self.map.width and 0 <= ny < self.map.height:
            v = self.map.get(nx, ny)
            if v == SPACE or (PLAYER <= v <= PLAYER + 3):
                return True
        return False

    def is_ghost_blocked(self, x, y):
        p, dir = self.closest_player(x, y)
        if dir is None:
            return True
        return not (
            self.can_ghost_move_dir(x, y, dir)
            or self.can_ghost_move_dir(x, y, steer_left(dir))
            or self.can_ghost_move_dir(x, y, steer_right(dir))
        )

    def can_sleep(self, keystate):
        for p in self.players:
            if p.arrow is not None:
                return False
            if p.state == STATE_IN_WARP:
                return False

        x, y = self.getCog()
        if x != self.cogX or y != self.cogY:
            return False

        for p in self.active_players():
            control = self.controls[p.index]
            if control:
                if (
                    keystate[control.left]
                    or keystate[control.right]
                    or keystate[control.up]
                    or keystate[control.down]
                    or keystate[control.shoot]
                    or keystate[control.bomb]
                ):
                    return False

        vr = self.visibleRect
        if vr is not None:
            left = max(0, vr.left)
            right = min(self.map.width, vr.right)
            top = max(0, vr.top)
            bottom = min(self.map.height, vr.bottom)
            for y in range(top, bottom):
                for x in range(left, right):
                    v = self.map.get(x, y)
                    if GHOST <= v <= GHOST + 2:
                        if not self.is_ghost_blocked(x, y):
                            return False
        return True


# Dynamically compile WINDOW_EVENTS from dir(pygame)
num_events = getattr(pygame, "NUMEVENTS", 65535)
WINDOW_EVENTS = [
    getattr(pygame, name)
    for name in dir(pygame)
    if name.startswith("WINDOW")
    and not name.startswith("WINDOWPOS")
    and isinstance(getattr(pygame, name), int)
    and 0 <= getattr(pygame, name) < num_events
]
if hasattr(pygame, "ACTIVEEVENT"):
    WINDOW_EVENTS.append(pygame.ACTIVEEVENT)


def is_significant_event(event):
    if event.type in (
        pygame.QUIT,
        pygame.KEYDOWN,
        pygame.KEYUP,
        pygame.VIDEORESIZE,
        pygame.VIDEOEXPOSE,
    ):
        return True

    if hasattr(pygame, "JOYAXISMOTION") and event.type == pygame.JOYAXISMOTION:
        return abs(event.value) > 0.15

    # All other joystick events (buttons, hats, device updates, etc.) are significant
    joy_types = []
    for name in (
        "JOYBUTTONDOWN",
        "JOYBUTTONUP",
        "JOYHATMOTION",
        "JOYBALLMOTION",
        "JOYDEVICEADDED",
        "JOYDEVICEREMOVED",
    ):
        if hasattr(pygame, name):
            joy_types.append(getattr(pygame, name))
    if event.type in joy_types:
        return True

    if event.type in WINDOW_EVENTS:
        return True

    return False


def main():
    # Initialize pygame
    pygame.init()

    # Layer 1: OS/SDL Event Whitelisting
    pygame.event.set_blocked(None)
    allowed_events = [
        pygame.QUIT,
        pygame.KEYDOWN,
        pygame.KEYUP,
        pygame.VIDEORESIZE,
        pygame.VIDEOEXPOSE,
    ]
    # Dynamically add all joystick events
    for name in (
        "JOYAXISMOTION",
        "JOYBALLMOTION",
        "JOYHATMOTION",
        "JOYBUTTONDOWN",
        "JOYBUTTONUP",
        "JOYDEVICEADDED",
        "JOYDEVICEREMOVED",
    ):
        if hasattr(pygame, name):
            allowed_events.append(getattr(pygame, name))
    allowed_events.extend(WINDOW_EVENTS)
    pygame.event.set_allowed(allowed_events)

    if pygame.mixer and not pygame.mixer.get_init():
        print("Warning, no sound")
        pygame.mixer = None

    # Set the display mode
    screen = pygame.display.set_mode((640, 560), pygame.RESIZABLE)

    pygame.display.set_caption("Dandy Dungeon")
    pygame.mouse.set_visible(0)

    game = Game()
    clock = pygame.time.Clock()
    sleeping = False

    while True:
        if sleeping:
            # Layer 3: Hardened Sleep Loop
            while True:
                event = pygame.event.wait()
                if is_significant_event(event):
                    sleeping = False
                    events = [event] + pygame.event.get()
                    break
        else:
            events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            ):
                return

        keystate = pygame.key.get_pressed()
        game.step(keystate)
        game.draw(screen)
        pygame.display.flip()

        if game.can_sleep(keystate):
            sleeping = True
        else:
            clock.tick(60)


if __name__ == "__main__":
    main()

