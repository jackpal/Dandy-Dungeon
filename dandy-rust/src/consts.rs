// Game Constants
pub const TILE_SIZE: i32 = 16;
pub const MAP_WIDTH: i32 = 60;
pub const MAP_HEIGHT: i32 = 30;
pub const VIEWPORT_WIDTH: i32 = 20;
pub const VIEWPORT_HEIGHT: i32 = 10;

// Tile Constants
pub const SPACE: u8 = 0;
pub const WALL: u8 = 1;
pub const LOCK: u8 = 2;
pub const UP: u8 = 3;
pub const DOWN: u8 = 4;
pub const KEY: u8 = 5;
pub const FOOD: u8 = 6;
pub const MONEY: u8 = 7;
pub const BOMB: u8 = 8;
pub const GHOST: u8 = 9; // 9, 10, 11
pub const HEART: u8 = 12;
pub const GENERATOR: u8 = 13; // 13, 14, 15
pub const ARROW: u8 = 16; // 16..23
pub const PLAYER: u8 = 24; // 24..27

// Movement Directions: 0 is Up, clockwise (0..7)
pub const DIR_TO_DELTA: [(i32, i32); 8] = [
    (0, -1),  // 0: Up
    (1, -1),  // 1: Up-Right
    (1, 0),   // 2: Right
    (1, 1),   // 3: Down-Right
    (0, 1),   // 4: Down
    (-1, 1),  // 5: Down-Left
    (-1, 0),  // 6: Left
    (-1, -1), // 7: Up-Left
];

// Player spawn directions: P1 (North/Up), P2 (East/Right), P3 (South/Down), P4 (West/Left)
pub const PLAYER_SPAWN_DIRS: [usize; 4] = [0, 2, 4, 6];

// Controls definitions for Players
pub struct PlayerControls {
    pub left: &'static str,
    pub right: &'static str,
    pub up: &'static str,
    pub down: &'static str,
    pub shoot: &'static str,
    pub bomb: &'static str,
}

pub const P1_CONTROLS: PlayerControls = PlayerControls {
    left: "ArrowLeft",
    right: "ArrowRight",
    up: "ArrowUp",
    down: "ArrowDown",
    shoot: " ", // Space
    bomb: "b",
};

pub const P2_CONTROLS: PlayerControls = PlayerControls {
    left: "a",
    right: "d",
    up: "w",
    down: "s",
    shoot: "f",
    bomb: "g",
};
