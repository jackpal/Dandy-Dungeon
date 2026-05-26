from constants import STATE_INACTIVE, STATE_ACTIVE, STATE_IN_WARP


class Arrow:
    def __init__(self, x, y, dir):
        self.x = x
        self.y = y
        self.dir = dir


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
