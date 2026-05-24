// Map module for Dandy Dungeon
use crate::consts::{MAP_WIDTH, MAP_HEIGHT, LOCK, SPACE};

pub struct Map {
    pub data: Vec<u8>,
}

impl Map {
    pub fn new() -> Self {
        Self {
            data: vec![0; (MAP_WIDTH * MAP_HEIGHT) as usize],
        }
    }

    pub fn get(&self, x: i32, y: i32) -> u8 {
        if x >= 0 && x < MAP_WIDTH && y >= 0 && y < MAP_HEIGHT {
            self.data[(x + y * MAP_WIDTH) as usize]
        } else {
            1 // Return Wall (1) as default for out of bounds to prevent entities walking out
        }
    }

    pub fn set(&mut self, x: i32, y: i32, val: u8) {
        if x >= 0 && x < MAP_WIDTH && y >= 0 && y < MAP_HEIGHT {
            self.data[(x + y * MAP_WIDTH) as usize] = val;
        }
    }

    pub fn find(&self, item: u8) -> Option<(i32, i32)> {
        for i in 0..self.data.len() {
            if self.data[i] == item {
                let x = (i as i32) % MAP_WIDTH;
                let y = (i as i32) / MAP_WIDTH;
                return Some((x, y));
            }
        }
        None
    }

    pub fn unlock(&mut self, start_x: i32, start_y: i32) {
        let target = LOCK;
        let replacement = SPACE;
        if self.get(start_x, start_y) != target {
            return;
        }

        let mut stack = Vec::new();
        stack.push((start_x, start_y));

        while let Some((cx, cy)) = stack.pop() {
            if self.get(cx, cy) == target {
                self.set(cx, cy, replacement);
                
                for dy in -1..=1 {
                    for dx in -1..=1 {
                        if dx != 0 || dy != 0 {
                            let nx = cx + dx;
                            let ny = cy + dy;
                            if self.get(nx, ny) == target {
                                stack.push((nx, ny));
                            }
                        }
                    }
                }
            }
        }
    }

    pub fn load(&mut self, level: usize) {
        let bytes = get_level_bytes(level);
        // Parse 4-bit packed level data (2 tiles per byte)
        for i in 0..(self.data.len() / 2) {
            if i < bytes.len() {
                let b = bytes[i];
                self.data[i * 2] = b & 15;
                self.data[i * 2 + 1] = (b >> 4) & 15;
            }
        }
    }
}

const LEVEL_MAPS: [&'static [u8]; 26] = [
    include_bytes!("../assets/levels/LEVEL.A"),
    include_bytes!("../assets/levels/LEVEL.B"),
    include_bytes!("../assets/levels/LEVEL.C"),
    include_bytes!("../assets/levels/LEVEL.D"),
    include_bytes!("../assets/levels/LEVEL.E"),
    include_bytes!("../assets/levels/LEVEL.F"),
    include_bytes!("../assets/levels/LEVEL.G"),
    include_bytes!("../assets/levels/LEVEL.H"),
    include_bytes!("../assets/levels/LEVEL.I"),
    include_bytes!("../assets/levels/LEVEL.J"),
    include_bytes!("../assets/levels/LEVEL.K"),
    include_bytes!("../assets/levels/LEVEL.L"),
    include_bytes!("../assets/levels/LEVEL.M"),
    include_bytes!("../assets/levels/LEVEL.N"),
    include_bytes!("../assets/levels/LEVEL.O"),
    include_bytes!("../assets/levels/LEVEL.P"),
    include_bytes!("../assets/levels/LEVEL.Q"),
    include_bytes!("../assets/levels/LEVEL.R"),
    include_bytes!("../assets/levels/LEVEL.S"),
    include_bytes!("../assets/levels/LEVEL.T"),
    include_bytes!("../assets/levels/LEVEL.U"),
    include_bytes!("../assets/levels/LEVEL.V"),
    include_bytes!("../assets/levels/LEVEL.W"),
    include_bytes!("../assets/levels/LEVEL.X"),
    include_bytes!("../assets/levels/LEVEL.Y"),
    include_bytes!("../assets/levels/LEVEL.Z"),
];

fn get_level_bytes(level: usize) -> &'static [u8] {
    LEVEL_MAPS[level.min(25)]
}
