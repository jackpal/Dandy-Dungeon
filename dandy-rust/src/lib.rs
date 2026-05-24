// Main entry point for Dandy Dungeon in Rust Wasm (SM-PIE architecture)
mod consts;
mod entity;
mod map;
mod game;
mod graphics;
mod rand;
mod camera;
mod physics;
mod ai;

use consts::*;
use game::Game;
use graphics::{Framebuffer, parse_bmp};
use wasm_bindgen::prelude::*;

const SPRITESHEET_BYTES: &[u8] = include_bytes!("../assets/dandy.bmp");

#[wasm_bindgen]
#[repr(u8)]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum PlayerAction {
    Up = 0,
    Down = 1,
    Left = 2,
    Right = 3,
    Shoot = 4,
    Bomb = 5,
}

#[wasm_bindgen]
pub struct DandyApp {
    game: Game,
    spritesheet: Vec<u8>,
    framebuffer: Framebuffer,
    stats: Vec<i32>,
}

impl Default for DandyApp {
    fn default() -> Self {
        Self::new()
    }
}

#[wasm_bindgen]
impl DandyApp {
    #[wasm_bindgen(constructor)]
    pub fn new() -> Self {
        console_error_panic_hook::set_once();

        let mut game = Game::new();
        game.load();

        let spritesheet = parse_bmp(SPRITESHEET_BYTES);
        let framebuffer = Framebuffer::new();
        
        // 4 players * 7 stats = 28 elements
        let stats = vec![0i32; 28];

        let mut app = Self {
            game,
            spritesheet,
            framebuffer,
            stats,
        };
        app.update_stats_buffer();
        app.render_framebuffer(); // Initial render
        app
    }

    pub fn tick(&mut self) {
        // 1. Step the game physics
        self.game.step();

        // 2. Update camera offsets
        self.game.update_camera();

        // 3. Render scene to flat software framebuffer
        self.render_framebuffer();

        // 4. Update stats flat buffer
        self.update_stats_buffer();
    }

    pub fn can_sleep(&self) -> bool {
        self.game.can_sleep()
    }

    pub fn set_action(&mut self, player_idx: usize, action: PlayerAction, pressed: bool) {
        if player_idx < self.game.players.len() {
            let bit = 1 << (action as u8);
            if pressed {
                self.game.players[player_idx].input_mask |= bit;
            } else {
                self.game.players[player_idx].input_mask &= !bit;
            }
        }
    }

    pub fn get_framebuffer_ptr(&self) -> *const u8 {
        self.framebuffer.pixels.as_ptr()
    }

    pub fn get_framebuffer_size(&self) -> usize {
        self.framebuffer.pixels.len()
    }

    pub fn get_stats_ptr(&self) -> *const i32 {
        self.stats.as_ptr()
    }

    pub fn get_stats_len(&self) -> usize {
        self.stats.len()
    }

    pub fn get_level(&self) -> usize {
        self.game.level
    }

    fn render_framebuffer(&mut self) {
        // Clear to black
        self.framebuffer.clear(0, 0, 0);

        let (offset_x, offset_y) = self.game.get_camera_offsets();
        let active = self.game.get_active_rect();

        // Render viewport active grid
        for y in 0..active.height {
            let dy = active.top + y;
            for x in 0..active.width {
                let dx = active.left + x;
                let tile_val = self.game.map.get(dx, dy);

                // Calculate pixel coordinate on retro screen
                let dest_x = (offset_x + (dx * TILE_SIZE) as f64) as i32;
                let dest_y = (offset_y + (dy * TILE_SIZE) as f64) as i32;

                // Blit tile from spritesheet into framebuffer
                self.framebuffer.blit_tile(&self.spritesheet, tile_val, dest_x, dest_y);
            }
        }
    }

    fn update_stats_buffer(&mut self) {
        let mut idx = 0;
        for p in &self.game.players {
            self.stats[idx] = if p.active { 1 } else { 0 };
            self.stats[idx + 1] = if p.alive { 1 } else { 0 };
            self.stats[idx + 2] = if p.escaped { 1 } else { 0 };
            self.stats[idx + 3] = p.score;
            self.stats[idx + 4] = p.health;
            self.stats[idx + 5] = p.keys;
            self.stats[idx + 6] = p.bombs;
            idx += 7;
        }
    }
}
