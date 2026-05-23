// Entity structures for Dandy Dungeon

#[derive(Clone, Copy, Debug)]
pub struct Arrow {
    pub x: i32,
    pub y: i32,
    pub dir: usize,
}

#[derive(Clone, Debug)]
pub struct Player {
    pub index: usize,
    pub x: i32,
    pub y: i32,
    pub dir: usize,
    pub score: i32,
    pub health: i32,
    pub bombs: i32,
    pub keys: i32,
    pub active: bool,
    pub alive: bool,
    pub arrow: Option<Arrow>,
}

impl Player {
    pub fn new(index: usize) -> Self {
        Self {
            index,
            x: 0,
            y: 0,
            dir: 0,
            score: 0,
            health: 0,
            bombs: 0,
            keys: 0,
            active: false,
            alive: false,
            arrow: None,
        }
    }

    pub fn start(&mut self, x: i32, y: i32, dir: usize) {
        self.x = x;
        self.y = y;
        self.dir = dir;
        self.health = 100; // Standard starting health
        self.bombs = 0;
        self.keys = 0;
        self.active = true;
        self.alive = true;
        self.arrow = None;
    }
}
