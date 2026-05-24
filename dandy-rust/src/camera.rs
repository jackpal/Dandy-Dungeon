use crate::consts::*;
use crate::entity::Player;

#[derive(Clone, Copy, Debug)]
pub struct ActiveRect {
    pub left: i32,
    pub top: i32,
    pub width: i32,
    pub height: i32,
}

pub struct Camera {
    pub cog_x: f64,
    pub cog_y: f64,
}

impl Camera {
    pub fn new(initial_x: f64, initial_y: f64) -> Self {
        Self {
            cog_x: initial_x,
            cog_y: initial_y,
        }
    }

    pub fn update(&mut self, target_x: i32, target_y: i32) {
        let max_rate = (TILE_SIZE as f64) / 4.0; // Match 4 pixels per frame
        
        let mut dx = (target_x as f64) - self.cog_x;
        let mut dy = (target_y as f64) - self.cog_y;
        
        if dx != 0.0 || dy != 0.0 {
            dx = dx.clamp(-max_rate, max_rate);
            dy = dy.clamp(-max_rate, max_rate);
            self.cog_x += dx;
            self.cog_y += dy;
        }
    }

    pub fn get_offsets(&self) -> (f64, f64) {
        let screen_width = SCREEN_WIDTH as f64;
        let screen_height = SCREEN_HEIGHT as f64;
        
        let map_width = (MAP_WIDTH * TILE_SIZE) as f64;
        let map_height = (MAP_HEIGHT * TILE_SIZE) as f64;
        
        let offset_x = -self.cog_x + screen_width / 2.0;
        let offset_y = -self.cog_y + screen_height / 2.0;
        
        let clamped_x = offset_x.clamp(-(map_width - screen_width), 0.0);
        let clamped_y = offset_y.clamp(-(map_height - screen_height), 0.0);
        
        (clamped_x, clamped_y)
    }

    pub fn get_active_rect(&self) -> ActiveRect {
        let (offset_x, offset_y) = self.get_offsets();
        
        let left = (-offset_x / (TILE_SIZE as f64)).floor() as i32;
        let right = ((-offset_x + (SCREEN_WIDTH as f64) + (TILE_SIZE as f64) - 1.0) / (TILE_SIZE as f64)).floor() as i32;
        
        let top = (-offset_y / (TILE_SIZE as f64)).floor() as i32;
        let bottom = ((-offset_y + (SCREEN_HEIGHT as f64) + (TILE_SIZE as f64) - 1.0) / (TILE_SIZE as f64)).floor() as i32;
        
        // Bound within map coordinates
        let left = left.clamp(0, MAP_WIDTH);
        let right = right.clamp(0, MAP_WIDTH);
        let top = top.clamp(0, MAP_HEIGHT);
        let bottom = bottom.clamp(0, MAP_HEIGHT);
        
        ActiveRect {
            left,
            top,
            width: right - left,
            height: bottom - top,
        }
    }
}

pub fn calculate_target_cog(players: &[Player]) -> (i32, i32) {
    let mut cog_x = 0;
    let mut cog_y = 0;
    let mut num_active = 0;
    for p in players {
        if p.active && p.alive && !p.escaped {
            cog_x += p.x * TILE_SIZE;
            cog_y += p.y * TILE_SIZE;
            num_active += 1;
        }
    }
    if num_active > 0 {
        cog_x /= num_active;
        cog_y /= num_active;
    } else {
        cog_x = 10 * TILE_SIZE;
        cog_y = 5 * TILE_SIZE;
    }
    (cog_x + TILE_SIZE / 2, cog_y + TILE_SIZE / 2)
}
