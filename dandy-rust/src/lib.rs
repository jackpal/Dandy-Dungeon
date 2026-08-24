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
pub mod netcode;

use consts::*;
use game::Game;
use graphics::{Framebuffer, parse_bmp};
use netcode::RollbackManager;
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
#[repr(u8)]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Difficulty {
    Trivial = 0,
    Easy = 1,
    Hard = 2,
    Deadly = 3,
}

impl Difficulty {
    pub fn from_u8(val: u8) -> Self {
        match val {
            0 => Difficulty::Trivial,
            2 => Difficulty::Hard,
            3 => Difficulty::Deadly,
            _ => Difficulty::Easy,
        }
    }

    pub fn delay(self) -> u32 {
        match self {
            Difficulty::Trivial => 13,
            Difficulty::Easy => 8,
            Difficulty::Hard => 5,
            Difficulty::Deadly => 2,
        }
    }
}

#[wasm_bindgen]
pub struct DandyApp {
    game: Game,
    rollback: RollbackManager,
    spritesheet: Vec<u8>,
    framebuffer: Framebuffer,
    stats: [i32; 28],
}

impl Default for DandyApp {
    fn default() -> Self {
        Self::new()
    }
}

#[wasm_bindgen(start)]
pub fn wasm_start() {
    console_error_panic_hook::set_once();
}

#[wasm_bindgen]
impl DandyApp {
    #[wasm_bindgen(constructor)]
    pub fn new() -> Self {
        console_error_panic_hook::set_once();

        let mut game = Game::new();
        game.load();

        let rollback = RollbackManager::new(0, &game);
        let spritesheet = parse_bmp(SPRITESHEET_BYTES);
        let framebuffer = Framebuffer::new();
        
        // 4 players * 7 stats = 28 elements
        let stats = [0i32; 28];

        let mut app = Self {
            game,
            rollback,
            spritesheet,
            framebuffer,
            stats,
        };
        app.update_stats_buffer();
        app.render_framebuffer(); // Initial render
        app
    }

    pub fn get_build_info(&self) -> String {
        "dandy-rust v0.2.0 (wasm32; bulk-memory; zero-copy ABI; rollback-p2p)".to_string()
    }

    pub fn get_route_info(&self) -> String {
        "engine=sm-pie;arch=wasm32;opt=z;panic=abort;boundary=G3-cached-view;blitter=word-fill+bulk-copy;parity=tier-2;netcode=rollback-4p".to_string()
    }

    pub fn bench_tick(&mut self, frames: u32) {
        for _ in 0..frames {
            self.tick();
        }
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

    pub fn set_player_input_mask(&mut self, player_idx: usize, mask: u8) {
        if player_idx < self.game.players.len() {
            self.game.players[player_idx].input_mask = mask;
        }
    }

    pub fn spawn_player(&mut self, player_idx: usize) {
        self.game.spawn_player(player_idx);
        self.rollback.set_player_joined(player_idx, true);
        self.update_stats_buffer();
    }

    pub fn remove_player(&mut self, player_idx: usize) {
        self.game.remove_player(player_idx);
        self.rollback.set_player_joined(player_idx, false);
        self.update_stats_buffer();
    }

    pub fn is_player_active(&self, player_idx: usize) -> bool {
        if player_idx < self.game.players.len() {
            self.game.players[player_idx].active
        } else {
            false
        }
    }

    pub fn get_player_class_name(&self, player_idx: usize) -> String {
        if player_idx < PLAYER_NAMES.len() {
            PLAYER_NAMES[player_idx].to_string()
        } else {
            "Adventurer".to_string()
        }
    }

    pub fn get_player_color(&self, player_idx: usize) -> String {
        if player_idx < PLAYER_COLORS.len() {
            PLAYER_COLORS[player_idx].to_string()
        } else {
            "#ffffff".to_string()
        }
    }

    // -------------------------------------------------------------------------
    // Rollback Netcode Engine APIs
    // -------------------------------------------------------------------------

    pub fn net_init(&mut self, local_player_idx: usize) {
        let mask = if local_player_idx < MAX_PLAYERS { 1 << local_player_idx } else { 0 };
        self.net_init_mask(mask);
    }

    pub fn net_init_mask(&mut self, local_player_mask: u8) {
        for p in 0..MAX_PLAYERS {
            if (local_player_mask & (1 << p)) != 0 {
                if !self.game.players[p].active {
                    self.game.spawn_player(p);
                }
            } else if self.game.players[p].active {
                self.game.remove_player(p);
            }
        }
        self.rollback.reset_mask(local_player_mask, &self.game);
        self.render_framebuffer();
        self.update_stats_buffer();
    }

    pub fn net_set_is_local_player(&mut self, player_idx: usize, is_local: bool) {
        self.rollback.set_local_player(player_idx, is_local);
        if is_local {
            self.game.spawn_player(player_idx);
        }
        self.update_stats_buffer();
    }

    pub fn net_is_local_player(&self, player_idx: usize) -> bool {
        self.rollback.is_local_player(player_idx)
    }

    pub fn net_get_local_player_mask(&self) -> u8 {
        self.rollback.local_player_mask
    }

    pub fn net_set_local_action(&mut self, action: PlayerAction, pressed: bool) {
        let p = self.rollback.primary_local_player();
        self.net_set_player_local_action(p, action, pressed);
    }

    pub fn net_set_player_local_action(&mut self, player_idx: usize, action: PlayerAction, pressed: bool) {
        if player_idx < MAX_PLAYERS {
            let bit = 1 << (action as u8);
            let mut mask = self.rollback.last_known_input[player_idx];
            if pressed {
                mask |= bit;
            } else {
                mask &= !bit;
            }
            let frame = self.rollback.current_frame;
            self.rollback.set_player_local_input(player_idx, frame, mask);
        }
    }

    pub fn net_set_local_input_mask(&mut self, mask: u8) {
        let p = self.rollback.primary_local_player();
        self.net_set_player_local_input_mask(p, mask);
    }

    pub fn net_set_player_local_input_mask(&mut self, player_idx: usize, mask: u8) {
        let frame = self.rollback.current_frame;
        self.rollback.set_player_local_input(player_idx, frame, mask);
    }

    pub fn net_get_local_input_mask(&self, frame: u32) -> u8 {
        self.net_get_player_input_mask(self.rollback.primary_local_player(), frame)
    }

    pub fn net_get_player_input_mask(&self, player_idx: usize, frame: u32) -> u8 {
        self.rollback.get_input(player_idx, frame)
    }

    pub fn net_encode_local_input_packet(&self, frame: u32) -> Vec<u8> {
        self.net_encode_player_input_packet(self.rollback.primary_local_player(), frame)
    }

    pub fn net_encode_player_input_packet(&self, player_idx: usize, frame: u32) -> Vec<u8> {
        let p = player_idx as u8;
        let curr_mask = self.rollback.get_input(player_idx, frame);
        let prev_frame = if frame > 0 { frame - 1 } else { 0 };
        let prev_mask = self.rollback.get_input(player_idx, prev_frame);
        netcode::encode_input_packet(p, frame, curr_mask, prev_mask).to_vec()
    }

    pub fn net_encode_all_local_input_packets(&self, frame: u32) -> Vec<u8> {
        let mut buf = Vec::with_capacity(32);
        for p in 0..MAX_PLAYERS {
            if self.rollback.is_local_player(p) && self.rollback.is_player_joined(p) {
                let curr_mask = self.rollback.get_input(p, frame);
                let prev_frame = if frame > 0 { frame - 1 } else { 0 };
                let prev_mask = self.rollback.get_input(p, prev_frame);
                let pkt = netcode::encode_input_packet(p as u8, frame, curr_mask, prev_mask);
                buf.extend_from_slice(&pkt);
            }
        }
        buf
    }

    pub fn net_receive_remote_input(&mut self, peer_idx: usize, frame: u32, mask: u8) -> bool {
        let did_rollback = self.rollback.receive_remote_input(peer_idx, frame, mask, &mut self.game);
        if did_rollback {
            self.render_framebuffer();
            self.update_stats_buffer();
        }
        did_rollback
    }

    pub fn net_receive_remote_packet(&mut self, bytes: &[u8]) -> bool {
        let mut parsed = [(0usize, 0u32, 0u8, 0u8); 4];
        let mut count = 0;
        for chunk in bytes.chunks_exact(8) {
            if let Some((peer_idx, frame, curr_mask, prev_mask)) = netcode::decode_input_packet(chunk) {
                if count < 4 {
                    parsed[count] = (peer_idx as usize, frame, curr_mask, prev_mask);
                    count += 1;
                }
            }
        }
        if count == 0 {
            return false;
        }
        let did_rollback = self.rollback.receive_remote_packets(&parsed[..count], &mut self.game);
        if did_rollback {
            self.render_framebuffer();
            self.update_stats_buffer();
        }
        did_rollback
    }

    pub fn net_step(&mut self) -> u32 {
        let new_frame = self.rollback.step_frame(&mut self.game);
        self.render_framebuffer();
        self.update_stats_buffer();
        new_frame
    }

    pub fn net_get_current_frame(&self) -> u32 {
        self.rollback.current_frame
    }

    pub fn net_get_confirmed_frame(&self) -> u32 {
        self.rollback.confirmed_frame
    }

    pub fn net_get_rollback_count(&self) -> u32 {
        self.rollback.rollback_count
    }

    pub fn net_get_resimulated_frames(&self) -> u32 {
        self.rollback.resimulated_frames_total
    }

    pub fn net_set_player_joined(&mut self, player_idx: usize, joined: bool) {
        self.rollback.set_player_joined(player_idx, joined);
        if joined {
            self.game.spawn_player(player_idx);
        } else {
            self.game.remove_player(player_idx);
        }
        self.update_stats_buffer();
    }

    pub fn net_is_player_joined(&self, player_idx: usize) -> bool {
        self.rollback.is_player_joined(player_idx)
    }

    pub fn net_load_sync_state(&mut self, frame: u32, bytes: &[u8]) -> bool {
        let success = self.game.load_state_bytes(bytes);
        if success {
            for p in 0..MAX_PLAYERS {
                if self.rollback.is_local_player(p) && !self.game.players[p].active {
                    self.game.spawn_player(p);
                }
            }
            self.rollback.sync_state(frame, &self.game);
            self.render_framebuffer();
            self.update_stats_buffer();
        }
        success
    }

    pub fn get_player_x(&self, player_idx: usize) -> i32 {
        if player_idx < self.game.players.len() {
            self.game.players[player_idx].x
        } else {
            -1
        }
    }

    pub fn get_player_y(&self, player_idx: usize) -> i32 {
        if player_idx < self.game.players.len() {
            self.game.players[player_idx].y
        } else {
            -1
        }
    }

    pub fn get_player_dir(&self, player_idx: usize) -> usize {
        if player_idx < self.game.players.len() {
            self.game.players[player_idx].dir
        } else {
            0
        }
    }

    // -------------------------------------------------------------------------
    // State Snapshotting & Buffer Access
    // -------------------------------------------------------------------------

    pub fn save_state_bytes(&self) -> Vec<u8> {
        self.game.save_state_bytes()
    }

    pub fn load_state_bytes(&mut self, bytes: &[u8]) -> bool {
        let success = self.game.load_state_bytes(bytes);
        if success {
            self.rollback.snapshot_history.clear();
            self.rollback.snapshot_history.push((self.rollback.current_frame, self.game.save_state()));
            self.render_framebuffer();
            self.update_stats_buffer();
        }
        success
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

    pub fn get_difficulty(&self) -> u8 {
        self.game.difficulty as u8
    }

    pub fn set_difficulty(&mut self, val: u8) {
        self.game.difficulty = Difficulty::from_u8(val);
    }

    fn render_framebuffer(&mut self) {
        // Clear to black
        self.framebuffer.clear(0, 0, 0);

        let (offset_x, offset_y) = self.game.get_camera_offsets();
        let active = self.game.get_active_rect();

        let base_x = (offset_x + (active.left * TILE_SIZE) as f64) as i32;
        let base_y = (offset_y + (active.top * TILE_SIZE) as f64) as i32;
        let tile_size = TILE_SIZE;

        // Render viewport active grid
        for y in 0..active.height {
            let dy = active.top + y;
            let dest_y = base_y + y * tile_size;
            for x in 0..active.width {
                let dx = active.left + x;
                let tile_val = self.game.map.get(dx, dy);

                // Calculate pixel coordinate on retro screen
                let dest_x = base_x + x * tile_size;

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

