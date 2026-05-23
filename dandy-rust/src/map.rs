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

fn get_level_bytes(level: usize) -> &'static [u8] {
    match level {
        0 => include_bytes!("../assets/levels/LEVEL.A"),
        1 => include_bytes!("../assets/levels/LEVEL.B"),
        2 => include_bytes!("../assets/levels/LEVEL.C"),
        3 => include_bytes!("../assets/levels/LEVEL.D"),
        4 => include_bytes!("../assets/levels/LEVEL.E"),
        5 => include_bytes!("../assets/levels/LEVEL.F"),
        6 => include_bytes!("../assets/levels/LEVEL.G"),
        7 => include_bytes!("../assets/levels/LEVEL.H"),
        8 => include_bytes!("../assets/levels/LEVEL.I"),
        9 => include_bytes!("../assets/levels/LEVEL.J"),
        10 => include_bytes!("../assets/levels/LEVEL.K"),
        11 => include_bytes!("../assets/levels/LEVEL.L"),
        12 => include_bytes!("../assets/levels/LEVEL.M"),
        13 => include_bytes!("../assets/levels/LEVEL.N"),
        14 => include_bytes!("../assets/levels/LEVEL.O"),
        15 => include_bytes!("../assets/levels/LEVEL.P"),
        16 => include_bytes!("../assets/levels/LEVEL.Q"),
        17 => include_bytes!("../assets/levels/LEVEL.R"),
        18 => include_bytes!("../assets/levels/LEVEL.S"),
        19 => include_bytes!("../assets/levels/LEVEL.T"),
        20 => include_bytes!("../assets/levels/LEVEL.U"),
        21 => include_bytes!("../assets/levels/LEVEL.V"),
        22 => include_bytes!("../assets/levels/LEVEL.W"),
        23 => include_bytes!("../assets/levels/LEVEL.X"),
        24 => include_bytes!("../assets/levels/LEVEL.Y"),
        25 => include_bytes!("../assets/levels/LEVEL.Z"),
        _ => include_bytes!("../assets/levels/LEVEL.A"),
    }
}
