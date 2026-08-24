use crate::consts::*;
use crate::entity::Player;

#[derive(Clone, Copy, Debug)]
pub struct ActiveRect {
    pub left: i32,
    pub top: i32,
    pub width: i32,
    pub height: i32,
}

#[derive(Clone, Copy, Debug, PartialEq)]
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

    pub fn update(&mut self, target_x: i32, target_y: i32, num_active_players: usize) {
        let n = num_active_players.clamp(1, 4);
        let alpha = (n as f64) / 4.0;
        
        let tx = target_x as f64;
        let ty = target_y as f64;
        
        self.cog_x = (1.0 - alpha) * self.cog_x + alpha * tx;
        self.cog_y = (1.0 - alpha) * self.cog_y + alpha * ty;
        
        if (tx - self.cog_x).abs() < 0.001 {
            self.cog_x = tx;
        }
        if (ty - self.cog_y).abs() < 0.001 {
            self.cog_y = ty;
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_camera_ema_filter_by_player_count() {
        let mut cam = Camera::new(100.0, 100.0);

        // 1 Player: alpha = 0.25 (C_t = 0.75 * 100 + 0.25 * 200 = 125.0)
        cam.update(200, 100, 1);
        assert!((cam.cog_x - 125.0).abs() < 1e-6);

        // 2 Players: alpha = 0.50 (C_t = 0.50 * 125 + 0.50 * 200 = 162.5)
        cam.update(200, 100, 2);
        assert!((cam.cog_x - 162.5).abs() < 1e-6);

        // 3 Players: alpha = 0.75 (C_t = 0.25 * 162.5 + 0.75 * 200 = 190.625)
        cam.update(200, 100, 3);
        assert!((cam.cog_x - 190.625).abs() < 1e-6);

        // 4 Players: alpha = 1.00 (C_t = 200.0)
        cam.update(200, 100, 4);
        assert_eq!(cam.cog_x, 200.0);
    }

    #[test]
    fn test_camera_viewport_offset_clamping_at_map_edges() {
        // Map: 60 * 16 = 960 width, 30 * 16 = 480 height
        // Screen: 320 width, 160 height
        // Max offset range: X in [-640.0, 0.0], Y in [-320.0, 0.0]

        // Top-left extreme
        let cam_top_left = Camera::new(0.0, 0.0);
        let (ox, oy) = cam_top_left.get_offsets();
        assert_eq!(ox, 0.0);
        assert_eq!(oy, 0.0);

        // Bottom-right extreme
        let cam_bottom_right = Camera::new(1000.0, 600.0);
        let (ox, oy) = cam_bottom_right.get_offsets();
        assert_eq!(ox, -640.0);
        assert_eq!(oy, -320.0);

        // ActiveRect within bounds
        let rect = cam_top_left.get_active_rect();
        assert_eq!(rect.left, 0);
        assert_eq!(rect.top, 0);
        assert!(rect.width >= 20);
        assert!(rect.height >= 10);
    }
}
