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
pub fn net_get_protocol_version() -> u16 {
    NET_PROTOCOL_VERSION
}

#[wasm_bindgen]
pub fn net_get_app_id() -> String {
    NET_APP_ID.to_string()
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

    pub fn net_get_protocol_version(&self) -> u16 {
        NET_PROTOCOL_VERSION
    }

    pub fn net_get_app_id(&self) -> String {
        NET_APP_ID.to_string()
    }

    pub fn net_encode_handshake_packet(&self) -> Vec<u8> {
        netcode::encode_handshake_packet(NET_PROTOCOL_VERSION).to_vec()
    }

    pub fn net_validate_handshake_packet(&self, bytes: &[u8]) -> bool {
        netcode::validate_handshake_packet(bytes)
    }

    pub fn net_decode_handshake_version(&self, bytes: &[u8]) -> i32 {
        match netcode::decode_handshake_packet(bytes) {
            Some(v) => v as i32,
            None => -1,
        }
    }

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
        let mut parsed = Vec::with_capacity(bytes.len() / 8);
        for chunk in bytes.chunks_exact(8) {
            if let Some((peer_idx, frame, curr_mask, prev_mask)) = netcode::decode_input_packet(chunk) {
                parsed.push((peer_idx as usize, frame, curr_mask, prev_mask));
            }
        }
        if parsed.is_empty() {
            return false;
        }
        let did_rollback = self.rollback.receive_remote_packets(&parsed, &mut self.game);
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

    pub fn net_hot_join(&mut self, player_idx: usize) {
        if player_idx < MAX_PLAYERS {
            self.rollback.set_player_joined(player_idx, true);
            if !self.game.players[player_idx].active {
                self.game.spawn_player(player_idx);
            }
            self.update_stats_buffer();
        }
    }

    pub fn net_is_player_joined(&self, player_idx: usize) -> bool {
        self.rollback.is_player_joined(player_idx)
    }

    pub fn net_load_sync_state(&mut self, frame: u32, bytes: &[u8]) -> bool {
        let success = self.game.load_state_bytes(bytes);
        if success {
            for p in 0..MAX_PLAYERS {
                if (self.rollback.is_local_player(p) || self.rollback.is_player_joined(p)) && !self.game.players[p].active {
                    self.game.spawn_player(p);
                }
            }
            self.rollback.sync_state(frame, &self.game);
            self.render_framebuffer();
            self.update_stats_buffer();
        }
        success
    }

    pub fn get_state_checksum(&self) -> u32 {
        self.game.get_state_checksum()
    }

    pub fn net_get_checksum_at_frame(&self, frame: u32) -> u32 {
        if frame == self.rollback.current_frame {
            return self.game.get_state_checksum();
        }
        self.rollback.get_checksum_at_frame(frame).unwrap_or(0)
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
            for p in 0..MAX_PLAYERS {
                if (self.rollback.is_local_player(p) || self.rollback.is_player_joined(p)) && !self.game.players[p].active {
                    self.game.spawn_player(p);
                }
            }
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

    pub fn get_sound_mask(&self) -> u32 {
        let mut mask = self.rollback.pending_sound_mask;
        for &s in &self.game.sounds {
            if s > 0 && s < 32 {
                mask |= 1 << s;
            }
        }
        mask
    }

    pub fn take_sound_mask(&mut self) -> u32 {
        let mut mask = self.rollback.pending_sound_mask;
        self.rollback.pending_sound_mask = 0;
        // Also include any sounds from standalone / single-player game.sounds if rollback not stepping
        for &s in &self.game.sounds {
            if s > 0 && s < 32 {
                mask |= 1 << s;
            }
        }
        mask
    }

    pub fn get_sound_events_ptr(&self) -> *const u8 {
        self.game.sounds.as_ptr()
    }

    pub fn get_sound_events_len(&self) -> usize {
        self.game.sounds.len()
    }

    pub fn get_sound_events(&self) -> Vec<u8> {
        self.game.sounds.clone()
    }

    pub fn get_audio_channel_sound(&self, ch: usize) -> u8 {
        self.game.audio_scheduler.get_channel_sound(ch)
    }

    pub fn is_audio_channel_active(&self, ch: usize) -> bool {
        self.game.audio_scheduler.is_channel_active(ch)
    }

    pub fn get_sound_priority(sound_id: u8) -> u8 {
        sound_priority(sound_id)
    }

    pub fn get_sound_pokey_channel(sound_id: u8) -> usize {
        sound_pokey_channel(sound_id)
    }

    fn render_framebuffer(&mut self) {
        // Clear to black
        self.framebuffer.clear(0, 0, 0);

        let (offset_x, offset_y) = self.game.get_camera_offsets();
        let active = self.game.get_active_rect();

        let base_x = (offset_x + (active.left * TILE_SIZE) as f64).round() as i32;
        let base_y = (offset_y + (active.top * TILE_SIZE) as f64).round() as i32;
        let tile_size = TILE_SIZE;

        // 1. Render viewport active grid (skipping player tile characters)
        for y in 0..active.height {
            let dy = active.top + y;
            let dest_y = base_y + y * tile_size;
            for x in 0..active.width {
                let dx = active.left + x;
                let tile_val = self.game.map.get(dx, dy);

                // Skip player tile characters in map grid
                if (PLAYER..=PLAYER + 3).contains(&tile_val) {
                    continue;
                }

                // Calculate pixel coordinate on retro screen
                let dest_x = base_x + x * tile_size;

                // Blit tile from spritesheet into framebuffer
                self.framebuffer.blit_tile(&self.spritesheet, tile_val, dest_x, dest_y);
            }
        }

        // 2. Render active players at sub-pixel interpolated positions
        for (i, p) in self.game.players.iter().enumerate() {
            if p.active && p.alive && !p.escaped {
                let delta = DIR_TO_DELTA[p.dir];
                let fraction = (p.move_cooldown as f64) / (PLAYER_MOVE_INTERVAL as f64);
                let visual_x = (p.x * TILE_SIZE) as f64 - (delta.0 as f64) * fraction * (TILE_SIZE as f64);
                let visual_y = (p.y * TILE_SIZE) as f64 - (delta.1 as f64) * fraction * (TILE_SIZE as f64);

                let screen_x = (offset_x + visual_x).round() as i32;
                let screen_y = (offset_y + visual_y).round() as i32;

                let player_tile = PLAYER + (i as u8);
                self.framebuffer.blit_tile(&self.spritesheet, player_tile, screen_x, screen_y);
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_dandy_app_initial_framebuffer_rendered_non_zero_rgb() {
        let app = DandyApp::new();
        assert_eq!(app.get_framebuffer_size(), SCREEN_WIDTH * SCREEN_HEIGHT * 4);
        assert!(!app.get_framebuffer_ptr().is_null());

        let fb_slice = &app.framebuffer.pixels;
        let mut non_zero_pixels = 0;
        for px in fb_slice.chunks_exact(4) {
            if px[0] != 0 || px[1] != 0 || px[2] != 0 {
                non_zero_pixels += 1;
            }
        }

        // Level 1 has active dungeon walls, player, floor features covering thousands of pixels
        let total_pixels = SCREEN_WIDTH * SCREEN_HEIGHT;
        assert!(
            non_zero_pixels > 10000,
            "Initial framebuffer must contain non-zero RGB rendered pixels (found {} / {})",
            non_zero_pixels, total_pixels
        );
    }

    #[test]
    fn test_dandy_app_movement_animates_framebuffer_pixels() {
        let mut app = DandyApp::new();
        let initial_pixels = app.framebuffer.pixels.clone();

        // Move player right across 10 frames
        app.set_action(0, PlayerAction::Right, true);
        for _ in 0..10 {
            app.tick();
        }

        let updated_pixels = &app.framebuffer.pixels;
        let differing_bytes = initial_pixels
            .iter()
            .zip(updated_pixels.iter())
            .filter(|(a, b)| a != b)
            .count();

        assert!(
            differing_bytes > 0,
            "Framebuffer pixel memory must mutate when player moves and scene updates (found {} differing bytes)",
            differing_bytes
        );
    }

    #[test]
    fn test_dandy_app_shooting_renders_arrow_visual_update() {
        let mut app = DandyApp::new();
        let before_shoot = app.framebuffer.pixels.clone();

        // Trigger shoot action
        app.set_action(0, PlayerAction::Shoot, true);
        app.tick();

        let after_shoot = &app.framebuffer.pixels;
        let diff_count = before_shoot
            .iter()
            .zip(after_shoot.iter())
            .filter(|(a, b)| a != b)
            .count();

        assert!(
            diff_count > 0,
            "Framebuffer must visually update when arrow is spawned and rendered"
        );
    }

    #[test]
    fn test_subpixel_player_interpolation_during_stride() {
        let mut app = DandyApp::new();
        // Clear inputs, step to let camera arrive
        for _ in 0..30 {
            app.tick();
        }

        // P1 moves Right: move_cooldown starts at 8
        app.set_action(0, PlayerAction::Right, true);
        app.tick(); // Frame 1: move triggered, move_cooldown decremented to 7

        let mut differing_frames = 0;
        let mut prev_fb = app.framebuffer.pixels.clone();

        // Across frames 2..8, player visually steps sub-pixel towards target tile
        for _ in 0..7 {
            app.tick();
            let curr_fb = &app.framebuffer.pixels;
            if prev_fb.iter().zip(curr_fb.iter()).any(|(a, b)| a != b) {
                differing_frames += 1;
            }
            prev_fb = curr_fb.clone();
        }

        assert_eq!(
            differing_frames, 7,
            "Framebuffer must continuously visually update on every single frame of the 8-frame stride (sub-pixel interpolation)"
        );
    }

    #[test]
    fn test_rapid_direction_oscillation_during_stride() {
        let mut app = DandyApp::new();
        for _ in 0..30 {
            app.tick();
        }

        // P1 begins moving Right
        app.set_action(0, PlayerAction::Right, true);
        app.tick(); // Move starts: move_cooldown = 7, dir = 2 (Right)
        app.set_action(0, PlayerAction::Right, false);

        let p1_orig_x = app.game.players[0].x; // Target tile X

        // Rapidly oscillate directions Up/Down/Left while mid-stride
        let opposing_actions = [
            PlayerAction::Up,
            PlayerAction::Down,
            PlayerAction::Left,
            PlayerAction::Up,
            PlayerAction::Down,
            PlayerAction::Left,
        ];

        for action in opposing_actions {
            app.set_action(0, action, true);
            app.tick();
            app.set_action(0, action, false);
            // Direction should remain locked to the stride (Right = 2) until cooldown finishes
            if app.game.players[0].move_cooldown > 0 {
                assert_eq!(
                    app.game.players[0].dir, 2,
                    "Player facing direction must not jump mid-stride on opposing input"
                );
            }
        }

        // Advance until move_cooldown reaches 0
        while app.game.players[0].move_cooldown > 0 {
            app.tick();
        }

        assert_eq!(app.game.players[0].x, p1_orig_x);
        assert_eq!(app.game.players[0].move_cooldown, 0);
    }
}


