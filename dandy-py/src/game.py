import pygame
from constants import (
    TILE_SIZE,
    MAP_WIDTH,
    MAP_HEIGHT,
    SPACE,
    LOCK,
    UP,
    DOWN,
    KEY,
    FOOD,
    MONEY,
    BOMB,
    GHOST,
    HEART,
    GENERATOR,
    ARROW,
    PLAYER,
    STATE_ACTIVE,
    STATE_DEAD,
    STATE_INACTIVE,
    STATE_IN_WARP,
)
from strike import Strike
from map import Map
from entities import Player, Arrow
from controls import (
    Controls,
    dir_to_delta,
    delta_to_dir,
    steer_left,
    steer_right,
)


class Game:
    def __init__(self):
        self.tiles = Strike("dandy.bmp", TILE_SIZE)
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
            dx, dy = dir_to_delta(dir)
            p.start(x + dx, y + dy, dir)
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
                dx, dy = dir_to_delta(dir)
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
            dx, dy = dir_to_delta(dir)
            p.start(x + dx, y + dy, dir)
            self.map.set(p.x, p.y, PLAYER + p.index)

        self.cogX, self.cogY = self.getCog()

    def step(self, keystate):
        if len(self.players) > 1:
            p2 = self.players[1]
            if p2.state == STATE_INACTIVE:
                p2_control = self.controls[1]
                if p2_control and p2_control.is_any_pressed(keystate):
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
        return not any(p.isAlive() for p in self.players)

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
        active = list(self.active_players())
        if not active:
            return None, None
        best_p = min(active, key=lambda p: abs(p.x - x) + abs(p.y - y))
        dx, dy = best_p.x - x, best_p.y - y
        return best_p, delta_to_dir(dx, dy)

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
            dx, dy = dir_to_delta(dir)
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
        dx, dy = dir_to_delta(dir)
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
        active = list(self.active_players())
        if not active:
            return TILE_SIZE // 2, TILE_SIZE // 2

        cogx = sum(p.x for p in active) * TILE_SIZE // len(active) + TILE_SIZE // 2
        cogy = sum(p.y for p in active) * TILE_SIZE // len(active) + TILE_SIZE // 2
        return cogx, cogy

    def draw_hud(self, screen, window_w, hud_height):
        screen.fill((0, 0, 0), pygame.Rect(0, 0, window_w, hud_height))

        window_h = screen.get_height()
        target_size = max(10, int(16 * (window_h / 560.0)))
        if target_size not in self.hud_fonts:
            self.hud_fonts[target_size] = pygame.font.SysFont(
                "arial,helvetica,sans", target_size, bold=True
            )
        font = self.hud_fonts[target_size]

        x = max(10, int(window_w * (10.0 / 640.0)))

        p1 = self.players[0]
        p1_text = f"P1  SCORE: {p1.score:<6}  HEALTH: {p1.health:<3}  KEYS: {p1.keys}  BOMBS: {p1.bombs}"
        p1_surf = font.render(p1_text, True, (255, 85, 85))
        p1_y = int(hud_height * (15.0 / 80.0))
        screen.blit(p1_surf, (x, p1_y))

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
        self.visibleRect = self.map.draw(
            self.game_surface, self.cogX, self.cogY, self.tiles
        )
        window_w, window_h = screen.get_size()
        hud_height = int(window_h * (80.0 / 560.0))
        scaled_game = pygame.transform.scale(
            self.game_surface, (window_w, window_h - hud_height)
        )
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
            if control and control.is_any_pressed(keystate):
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
