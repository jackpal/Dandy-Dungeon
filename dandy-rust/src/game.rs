// Game module for Dandy Dungeon
use crate::consts::*;
use crate::entity::Player;
use crate::map::Map;
use crate::rand::LcgRng;
use crate::camera::{Camera, ActiveRect, calculate_target_cog};

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct GameSnapshot {
    pub map_data: [u8; (MAP_WIDTH * MAP_HEIGHT) as usize],
    pub players: [Player; MAX_PLAYERS],
    pub level: usize,
    pub time: u32,
    pub last_move_time: u32,
    pub rotor: u8,
    pub difficulty: crate::Difficulty,
    pub camera: Camera,
    pub rng_state: u32,
}

impl GameSnapshot {
    pub fn get_checksum(&self) -> u32 {
        let mut hash = 2166136261u32;
        let mut fnv = |b: u8| {
            hash = (hash ^ (b as u32)).wrapping_mul(16777619);
        };

        for &b in &(self.level as u32).to_le_bytes() { fnv(b); }
        for &b in &self.time.to_le_bytes() { fnv(b); }
        for &b in &self.last_move_time.to_le_bytes() { fnv(b); }
        fnv(self.rotor);
        fnv(self.difficulty as u8);
        for &b in &self.rng_state.to_le_bytes() { fnv(b); }
        for &b in &self.camera.cog_x.to_bits().to_le_bytes() { fnv(b); }
        for &b in &self.camera.cog_y.to_bits().to_le_bytes() { fnv(b); }
        for &b in &self.map_data { fnv(b); }

        for p in &self.players {
            fnv(p.index as u8);
            fnv(p.active as u8);
            fnv(p.alive as u8);
            fnv(p.escaped as u8);
            fnv(p.dir as u8);
            fnv(p.input_mask);
            fnv(p.move_cooldown);
            for &b in &p.x.to_le_bytes() { fnv(b); }
            for &b in &p.y.to_le_bytes() { fnv(b); }
            for &b in &p.score.to_le_bytes() { fnv(b); }
            for &b in &p.health.to_le_bytes() { fnv(b); }
            for &b in &p.bombs.to_le_bytes() { fnv(b); }
            for &b in &p.keys.to_le_bytes() { fnv(b); }

            if let Some(ref arrow) = p.arrow {
                fnv(1);
                fnv(arrow.dir as u8);
                fnv(arrow.cooldown);
                for &b in &arrow.x.to_le_bytes() { fnv(b); }
                for &b in &arrow.y.to_le_bytes() { fnv(b); }
            } else {
                for _ in 0..11 { fnv(0); }
            }
        }

        hash
    }
}

pub struct Game {
    pub map: Map,
    pub players: [Player; MAX_PLAYERS],
    pub level: usize,
    pub time: u32,
    pub last_move_time: u32,
    pub rotor: u8,
    pub difficulty: crate::Difficulty,
    
    pub camera: Camera,
    pub rng: LcgRng,
    pub sounds: Vec<u8>,
    pub audio_scheduler: PokeyAudioScheduler,
}

#[inline(always)]
fn read_u32(bytes: &[u8], offset: &mut usize) -> u32 {
    let o = *offset;
    *offset += 4;
    u32::from_le_bytes([bytes[o], bytes[o + 1], bytes[o + 2], bytes[o + 3]])
}

#[inline(always)]
fn read_i32(bytes: &[u8], offset: &mut usize) -> i32 {
    let o = *offset;
    *offset += 4;
    i32::from_le_bytes([bytes[o], bytes[o + 1], bytes[o + 2], bytes[o + 3]])
}

#[inline(always)]
fn read_f64(bytes: &[u8], offset: &mut usize) -> f64 {
    let o = *offset;
    *offset += 8;
    f64::from_le_bytes([
        bytes[o], bytes[o + 1], bytes[o + 2], bytes[o + 3],
        bytes[o + 4], bytes[o + 5], bytes[o + 6], bytes[o + 7],
    ])
}

#[inline(always)]
fn write_u32(buf: &mut Vec<u8>, val: u32) {
    buf.extend_from_slice(&val.to_le_bytes());
}

#[inline(always)]
fn write_i32(buf: &mut Vec<u8>, val: i32) {
    buf.extend_from_slice(&val.to_le_bytes());
}

impl Game {
    pub fn new() -> Self {
        let mut players = [
            Player::new(0),
            Player::new(1),
            Player::new(2),
            Player::new(3),
        ];
        // Player 1 starts active by default in local single-player
        players[0].active = true;
        players[0].alive = true;

        Self {
            map: Map::new(),
            players,
            level: 0,
            time: 0,
            last_move_time: 0,
            rotor: 0,
            difficulty: crate::Difficulty::Easy,
            camera: Camera::new(0.0, 0.0),
            rng: LcgRng::new(12345), // Default seed
            sounds: Vec::with_capacity(16),
            audio_scheduler: PokeyAudioScheduler::new(),
        }
    }

    fn find_spawn_tile(map: &Map, spawn: (i32, i32), preferred_dir: usize, player_idx: usize) -> (i32, i32) {
        let delta = DIR_TO_DELTA[preferred_dir];
        let px = spawn.0 + delta.0;
        let py = spawn.1 + delta.1;

        let curr = map.get(px, py);
        if curr == SPACE || curr == (PLAYER + player_idx as u8) {
            return (px, py);
        }

        // Find first available adjacent space
        for &d in &DIR_TO_DELTA {
            let tx = spawn.0 + d.0;
            let ty = spawn.1 + d.1;
            let v = map.get(tx, ty);
            if v == SPACE || v == (PLAYER + player_idx as u8) {
                return (tx, ty);
            }
        }

        (px, py)
    }

    pub fn spawn_player(&mut self, player_idx: usize) {
        if player_idx >= self.players.len() {
            return;
        }
        if self.players[player_idx].active && self.players[player_idx].alive && !self.players[player_idx].escaped {
            return;
        }

        let spawn = self.map.find(UP).unwrap_or((2, 2));
        let dir = if player_idx < PLAYER_SPAWN_DIRS.len() {
            PLAYER_SPAWN_DIRS[player_idx]
        } else {
            0
        };

        let (px, py) = Self::find_spawn_tile(&self.map, spawn, dir, player_idx);

        self.players[player_idx].start(px, py, dir);
        self.map.set(px, py, PLAYER + player_idx as u8);
    }

    pub fn remove_player(&mut self, player_idx: usize) {
        if player_idx >= self.players.len() {
            return;
        }
        if !self.players[player_idx].active {
            return;
        }

        if self.players[player_idx].alive
            && !self.players[player_idx].escaped
            && self.map.get(self.players[player_idx].x, self.players[player_idx].y) == (PLAYER + player_idx as u8)
        {
            self.map.set(self.players[player_idx].x, self.players[player_idx].y, SPACE);
        }
        if let Some(arrow) = self.players[player_idx].arrow {
            let arrow_val = ARROW + (((arrow.dir + 3) & 7) as u8);
            if self.map.get(arrow.x, arrow.y) == arrow_val {
                self.map.set(arrow.x, arrow.y, SPACE);
            }
            self.players[player_idx].arrow = None;
        }

        self.players[player_idx].active = false;
        self.players[player_idx].alive = false;
        self.players[player_idx].escaped = false;
        self.players[player_idx].input_mask = 0;
    }

    pub fn load(&mut self) {
        self.map.load(self.level);
        self.rotor = 0;

        // Find player spawn (stairs UP)
        let spawn = self.map.find(UP).unwrap_or((2, 2));
        
        // Start all active players
        for (i, player) in self.players.iter_mut().enumerate() {
            if player.active && i < PLAYER_SPAWN_DIRS.len() {
                let dir = PLAYER_SPAWN_DIRS[i];
                let (px, py) = Self::find_spawn_tile(&self.map, spawn, dir, i);
                player.start(px, py, dir);
                self.map.set(px, py, PLAYER + i as u8);
            }
        }

        // Initialize camera position to spawn
        let (target_x, target_y) = calculate_target_cog(&self.players);
        self.camera.cog_x = target_x as f64;
        self.camera.cog_y = target_y as f64;

        // Authentic 6502 Z.WARP.IN emitted on dungeon swap / level load (GAME.TXT lines 74-81)
        self.sounds.push(SOUND_WARP_IN);
        self.audio_scheduler.schedule_sound(SOUND_WARP_IN);
    }

    pub fn load_next_level(&mut self) {
        self.map.load(self.level);
        self.rotor = 0;

        // Find player spawn (stairs UP)
        let spawn = self.map.find(UP).unwrap_or((2, 2));

        // Move surviving players to spawn while preserving health, keys, bombs, and score.
        // If a player died on the previous floor, revive them with default health for the new floor.
        for (i, player) in self.players.iter_mut().enumerate() {
            if player.active && i < PLAYER_SPAWN_DIRS.len() {
                let dir = PLAYER_SPAWN_DIRS[i];
                let (px, py) = Self::find_spawn_tile(&self.map, spawn, dir, i);
                player.x = px;
                player.y = py;
                player.dir = dir;
                player.escaped = false;
                player.arrow = None;
                player.move_cooldown = 0;
                player.input_mask = 0;
                if !player.alive {
                    player.alive = true;
                    player.health = 100;
                    player.bombs = 0;
                    player.keys = 0;
                }
                // health, bombs, keys, and score are preserved for surviving players!
                self.map.set(px, py, PLAYER + i as u8);
            }
        }

        // Initialize camera position to spawn
        let (target_x, target_y) = calculate_target_cog(&self.players);
        self.camera.cog_x = target_x as f64;
        self.camera.cog_y = target_y as f64;

        // Authentic 6502 Z.WARP.IN emitted on dungeon swap / level load (GAME.TXT lines 74-81)
        self.sounds.push(SOUND_WARP_IN);
        self.audio_scheduler.schedule_sound(SOUND_WARP_IN);
    }

    pub fn update_camera(&mut self) {
        let (tx, ty) = calculate_target_cog(&self.players);
        let num_active = self.players.iter().filter(|p| p.active && p.alive && !p.escaped).count();
        self.camera.update(tx, ty, num_active);
    }

    pub fn get_camera_offsets(&self) -> (f64, f64) {
        self.camera.get_offsets()
    }

    pub fn get_active_rect(&self) -> ActiveRect {
        self.camera.get_active_rect()
    }

    pub fn step(&mut self) {
        self.time += 1;
        self.sounds.clear();
        self.audio_scheduler.tick_frame();

        // Handle any player joining dynamically on non-zero input
        for i in 0..self.players.len() {
            if !self.players[i].active && self.players[i].input_mask != 0 {
                self.spawn_player(i);
            }
        }

        let active_rect = self.get_active_rect();

        // 1. Step arrows in flight for active players (1 tile every 4 frames per arrow cooldown)
        for i in 0..self.players.len() {
            if self.players[i].active {
                crate::physics::step_arrow(i, &mut self.players, &mut self.map, active_rect, &mut self.sounds);
            }
        }

        // 2. Step players (0 ms immediate start on 60 Hz frame with 8-frame move cooldown & immediate arrow spawn)
        for i in 0..self.players.len() {
            if self.players[i].active && self.players[i].alive && !self.players[i].escaped {
                crate::physics::step_player(i, &mut self.players, &mut self.map, active_rect, &mut self.sounds);
            }
        }

        // 3. Step enemies every DELAY frames according to difficulty (Trivial: 13, Easy: 8, Hard: 5, Deadly: 2)
        if self.time.is_multiple_of(self.difficulty.delay()) {
            crate::ai::step_enemies(&mut self.map, &mut self.players, active_rect, &mut self.rotor, &mut self.rng, &mut self.sounds);
        }

        // Update audio scheduler with frame sound events
        if !self.sounds.is_empty() {
            self.audio_scheduler.schedule_frame_events(&self.sounds);
        }

        // 4. Centralized Level Progression / Restart Check
        let mut players_in_dungeon = false;
        let mut any_escaped = false;
        let mut any_joined = false;
        let mut arrows_in_flight = false;

        for p in &self.players {
            if p.active {
                any_joined = true;
                if p.alive && !p.escaped {
                    players_in_dungeon = true;
                }
                if p.escaped {
                    any_escaped = true;
                }
                if p.arrow.is_some() {
                    arrows_in_flight = true;
                }
            }
        }

        if any_joined && !players_in_dungeon && !arrows_in_flight {
            if any_escaped {
                // Progress to next level: surviving players carry over health, keys, bombs, score
                self.level = (self.level + 1).min(25);
                self.load_next_level();
            } else {
                // Everyone died, restart game from Level 0 (Level A)
                self.level = 0;
                for p in &mut self.players {
                    p.score = 0;
                }
                self.load();
            }
        }
    }

    pub fn can_sleep(&self) -> bool {
        // 1. No Player Inputs (for active & alive players)
        if self.players.iter().any(|p| p.active && p.alive && !p.escaped && p.input_mask != 0) {
            return false;
        }

        // 2. No Active Move Cooldowns (active & alive players completing tile steps)
        if self.players.iter().any(|p| p.active && p.alive && !p.escaped && p.move_cooldown > 0) {
            return false;
        }

        // 3. No Arrows in Flight for active players
        if self.players.iter().any(|p| p.active && p.arrow.is_some()) {
            return false;
        }

        // 4. Camera Arrived
        let (tx, ty) = calculate_target_cog(&self.players);
        let dx = (tx as f64) - self.camera.cog_x;
        let dy = (ty as f64) - self.camera.cog_y;
        if dx.abs() >= 0.05 || dy.abs() >= 0.05 {
            return false;
        }

        // Viewport active rect
        let active = self.get_active_rect();

        // Check ghosts and generators inside active viewport
        for y in active.top..(active.top + active.height) {
            for x in active.left..(active.left + active.width) {
                let v = self.map.get(x, y);

                // 5. Ghosts inside visible viewport
                if (GHOST..=GHOST + 2).contains(&v)
                    && !crate::ai::is_ghost_blocked(x, y, &self.map, &self.players)
                {
                    return false;
                }

                // 6. Generators inside visible viewport
                if (GENERATOR..=GENERATOR + 2).contains(&v)
                    && !crate::ai::is_generator_blocked(x, y, &self.map)
                {
                    return false;
                }
            }
        }

        true
    }

    pub fn get_state_checksum(&self) -> u32 {
        self.save_state().get_checksum()
    }

    pub fn save_state(&self) -> GameSnapshot {
        GameSnapshot {
            map_data: self.map.data,
            players: self.players,
            level: self.level,
            time: self.time,
            last_move_time: self.last_move_time,
            rotor: self.rotor,
            difficulty: self.difficulty,
            camera: self.camera,
            rng_state: self.rng.state(),
        }
    }

    pub fn load_state(&mut self, snapshot: &GameSnapshot) {
        self.map.data = snapshot.map_data;
        self.players = snapshot.players;
        self.level = snapshot.level;
        self.time = snapshot.time;
        self.last_move_time = snapshot.last_move_time;
        self.rotor = snapshot.rotor;
        self.difficulty = snapshot.difficulty;
        self.camera = snapshot.camera;
        self.rng.set_state(snapshot.rng_state);
    }

    pub fn save_state_bytes(&self) -> Vec<u8> {
        let mut buf = Vec::with_capacity(1900);
        // Magic
        buf.extend_from_slice(b"DNDY");
        // Version
        buf.push(1);
        // Level
        buf.extend_from_slice(&(self.level as u16).to_le_bytes());
        // Time & Last Move Time
        write_u32(&mut buf, self.time);
        write_u32(&mut buf, self.last_move_time);
        // Rotor
        buf.push(self.rotor);
        // Difficulty
        buf.push(self.difficulty as u8);
        // Rng state
        write_u32(&mut buf, self.rng.state());
        // Camera cog
        buf.extend_from_slice(&self.camera.cog_x.to_le_bytes());
        buf.extend_from_slice(&self.camera.cog_y.to_le_bytes());

        // Players count
        buf.push(self.players.len() as u8);
        for p in &self.players {
            buf.push(p.index as u8);
            write_i32(&mut buf, p.x);
            write_i32(&mut buf, p.y);
            buf.push(p.dir as u8);
            write_i32(&mut buf, p.score);
            write_i32(&mut buf, p.health);
            write_i32(&mut buf, p.bombs);
            write_i32(&mut buf, p.keys);

            let mut flags = 0u8;
            if p.active { flags |= 1 << 0; }
            if p.alive { flags |= 1 << 1; }
            if p.escaped { flags |= 1 << 2; }
            if p.arrow.is_some() { flags |= 1 << 3; }
            buf.push(flags);
            buf.push(p.input_mask);
            buf.push(p.move_cooldown);

            if let Some(arrow) = p.arrow {
                write_i32(&mut buf, arrow.x);
                write_i32(&mut buf, arrow.y);
                buf.push(arrow.dir as u8);
                buf.push(arrow.cooldown);
            }
        }

        // Map data
        write_u32(&mut buf, self.map.data.len() as u32);
        buf.extend_from_slice(&self.map.data);

        buf
    }

    pub fn load_state_bytes(&mut self, bytes: &[u8]) -> bool {
        if bytes.len() < 38 || &bytes[0..4] != b"DNDY" || bytes[4] != 1 {
            return false;
        }

        let mut offset = 5;
        if offset + 2 + 4 + 4 + 1 + 1 + 4 + 8 + 8 + 1 > bytes.len() {
            return false;
        }

        let level = u16::from_le_bytes([bytes[offset], bytes[offset + 1]]) as usize;
        offset += 2;

        let time = read_u32(bytes, &mut offset);
        let last_move_time = read_u32(bytes, &mut offset);
        let rotor = bytes[offset];
        offset += 1;
        let difficulty = crate::Difficulty::from_u8(bytes[offset]);
        offset += 1;
        let rng_state = read_u32(bytes, &mut offset);
        let cog_x = read_f64(bytes, &mut offset);
        let cog_y = read_f64(bytes, &mut offset);
        let num_players = bytes[offset] as usize;
        offset += 1;
        if num_players > MAX_PLAYERS {
            return false;
        }

        let mut new_players = [
            Player::new(0),
            Player::new(1),
            Player::new(2),
            Player::new(3),
        ];

        for player_slot in new_players.iter_mut().take(num_players) {
            if offset + 29 > bytes.len() {
                return false;
            }

            let index = bytes[offset] as usize;
            offset += 1;
            if index >= MAX_PLAYERS {
                return false;
            }
            let x = read_i32(bytes, &mut offset);
            let y = read_i32(bytes, &mut offset);
            let dir = bytes[offset] as usize;
            offset += 1;
            if dir >= 8 {
                return false;
            }
            let score = read_i32(bytes, &mut offset);
            let health = read_i32(bytes, &mut offset);
            let bombs = read_i32(bytes, &mut offset);
            let keys = read_i32(bytes, &mut offset);
            let flags = bytes[offset];
            offset += 1;
            let input_mask = bytes[offset];
            offset += 1;
            let move_cooldown = bytes[offset];
            offset += 1;

            let active = (flags & (1 << 0)) != 0;
            let alive = (flags & (1 << 1)) != 0;
            let escaped = (flags & (1 << 2)) != 0;
            let has_arrow = (flags & (1 << 3)) != 0;

            let arrow = if has_arrow {
                if offset + 10 > bytes.len() {
                    return false;
                }
                let ax = read_i32(bytes, &mut offset);
                let ay = read_i32(bytes, &mut offset);
                let adir = bytes[offset] as usize;
                offset += 1;
                if adir >= 8 {
                    return false;
                }
                let acooldown = bytes[offset];
                offset += 1;
                Some(crate::entity::Arrow { x: ax, y: ay, dir: adir, cooldown: acooldown })
            } else {
                None
            };

            *player_slot = Player {
                index,
                x,
                y,
                dir,
                score,
                health,
                bombs,
                keys,
                active,
                alive,
                escaped,
                arrow,
                input_mask,
                move_cooldown,
            };
        }

        if offset + 4 > bytes.len() {
            return false;
        }
        let map_len = read_u32(bytes, &mut offset) as usize;

        if offset + map_len > bytes.len() || map_len != self.map.data.len() {
            return false;
        }
        let map_bytes = &bytes[offset..offset + map_len];

        self.level = level;
        self.time = time;
        self.last_move_time = last_move_time;
        self.rotor = rotor;
        self.difficulty = difficulty;
        self.rng.set_state(rng_state);
        self.camera.cog_x = cog_x;
        self.camera.cog_y = cog_y;
        self.players = new_players;
        self.map.data.copy_from_slice(map_bytes);

        true
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::entity::Arrow;

    #[test]
    fn test_game_init() {
        let game = Game::new();
        assert_eq!(game.players.len(), 4);
        assert!(game.players[0].active);
        assert!(game.players[0].alive);
        assert!(!game.players[1].active);
        assert!(!game.players[2].active);
        assert!(!game.players[3].active);
    }

    #[test]
    fn test_player_spawning() {
        let mut game = Game::new();
        // Manually activate all players for testing spawn
        for p in &mut game.players {
            p.active = true;
        }
        game.load();

        let spawn = game.map.find(UP).unwrap_or((2, 2));

        // P1: North (0, -1)
        assert_eq!(game.players[0].x, spawn.0);
        assert_eq!(game.players[0].y, spawn.1 - 1);
        assert_eq!(game.players[0].dir, 0);

        // P2: East (1, 0)
        assert_eq!(game.players[1].x, spawn.0 + 1);
        assert_eq!(game.players[1].y, spawn.1);
        assert_eq!(game.players[1].dir, 2);

        // P3: South (0, 1)
        assert_eq!(game.players[2].x, spawn.0);
        assert_eq!(game.players[2].y, spawn.1 + 1);
        assert_eq!(game.players[2].dir, 4);

        // P4: West (-1, 0)
        assert_eq!(game.players[3].x, spawn.0 - 1);
        assert_eq!(game.players[3].y, spawn.1);
        assert_eq!(game.players[3].dir, 6);
    }

    #[test]
    fn test_p2_hot_join() {
        let mut game = Game::new();
        game.load();

        assert!(!game.players[1].active);

        game.players[1].input_mask = ACTION_UP;

        game.step();

        assert!(game.players[1].active);
        assert!(game.players[1].alive);

        let spawn = game.map.find(UP).unwrap_or((2, 2));
        // P2 should spawn 1 tile East of UP stairs
        assert_eq!(game.players[1].x, spawn.0 + 1);
        assert_eq!(game.players[1].y, spawn.1);
        assert_eq!(game.players[1].dir, 2);
    }

    #[test]
    fn test_coop_exit_warp_single_player() {
        let mut game = Game::new();
        game.load();
        // P1 is active and alive. P2 is inactive.
        assert!(game.players[0].active && game.players[0].alive);
        assert!(!game.players[1].active);

        // Find DOWN stairs
        let exit = game.map.find(DOWN).expect("Should have DOWN stairs");
        
        // Teleport P1 to just next to DOWN stairs (say, North of it)
        game.map.set(game.players[0].x, game.players[0].y, SPACE);
        game.players[0].x = exit.0;
        game.players[0].y = exit.1 - 1;
        game.map.set(game.players[0].x, game.players[0].y, PLAYER);

        // Move P1 DOWN (into exit)
        game.players[0].input_mask = ACTION_DOWN;
        
        // Step game (8 ticks to trigger move)
        for _ in 0..8 {
            game.step();
        }

        // P1 should have escaped, and since they were the only player, level should progress.
        assert_eq!(game.level, 1);
        assert!(game.players[0].active);
        assert!(game.players[0].alive);
        assert!(!game.players[0].escaped);
    }

    #[test]
    fn test_coop_exit_warp_two_players_one_escapes_one_alive() {
        let mut game = Game::new();
        // Manually activate P1 and P2
        game.players[0].active = true;
        game.players[0].alive = true;
        game.players[1].active = true;
        game.players[1].alive = true;
        game.load();

        let exit = game.map.find(DOWN).expect("Should have DOWN stairs");

        // Teleport P1 to just North of DOWN stairs
        game.map.set(game.players[0].x, game.players[0].y, SPACE);
        game.players[0].x = exit.0;
        game.players[0].y = exit.1 - 1;
        game.map.set(game.players[0].x, game.players[0].y, PLAYER);
        
        // Move P1 DOWN (into exit)
        game.players[0].input_mask = ACTION_DOWN;

        // Step game
        for _ in 0..8 {
            game.step();
        }

        // P1 should have escaped
        assert!(game.players[0].escaped);
        assert_eq!(game.players[0].x, -1);
        assert_eq!(game.players[0].y, -1);

        // P2 should still be in dungeon
        assert!(game.players[1].alive);
        assert!(!game.players[1].escaped);

        // Level should NOT progress because P2 is still in dungeon
        assert_eq!(game.level, 0);
    }

    #[test]
    fn test_coop_exit_warp_two_players_one_escapes_one_dies() {
        let mut game = Game::new();
        game.players[0].active = true;
        game.players[0].alive = true;
        game.players[1].active = true;
        game.players[1].alive = true;
        game.load();

        let exit = game.map.find(DOWN).expect("Should have DOWN stairs");

        // Teleport P1 to just North of DOWN stairs
        game.map.set(game.players[0].x, game.players[0].y, SPACE);
        game.players[0].x = exit.0;
        game.players[0].y = exit.1 - 1;
        game.map.set(game.players[0].x, game.players[0].y, PLAYER);

        // Move P1 DOWN (into exit)
        game.players[0].input_mask = ACTION_DOWN;

        // Step game to make P1 escape
        for _ in 0..8 {
            game.step();
        }
        assert!(game.players[0].escaped);
        assert_eq!(game.level, 0); // Still level 0

        // Now kill P2
        game.players[1].health = 0;
        game.players[1].alive = false;
        game.map.set(game.players[1].x, game.players[1].y, SPACE);

        // Step game again to trigger check
        game.players[0].input_mask = 0;
        for _ in 0..8 {
            game.step();
        }

        // Level should now progress because P1 escaped and P2 is dead
        assert_eq!(game.level, 1);
        // Both players should be resurrected/reset in new level
        assert!(game.players[0].active && game.players[0].alive && !game.players[0].escaped);
        assert!(game.players[1].active && game.players[1].alive && !game.players[1].escaped);
    }

    #[test]
    fn test_coop_level_restart_death() {
        let mut game = Game::new();
        game.players[0].active = true;
        game.players[0].alive = true;
        game.players[1].active = true;
        game.players[1].alive = true;
        game.load();

        // Kill both players
        game.players[0].health = 0;
        game.players[0].alive = false;
        game.map.set(game.players[0].x, game.players[0].y, SPACE);

        game.players[1].health = 0;
        game.players[1].alive = false;
        game.map.set(game.players[1].x, game.players[1].y, SPACE);

        // Step game to trigger check
        for _ in 0..8 {
            game.step();
        }

        // Level should NOT progress
        assert_eq!(game.level, 0);
        // Level should have restarted, players resurrected on level 0
        assert!(game.players[0].active && game.players[0].alive && !game.players[0].escaped);
        assert!(game.players[1].active && game.players[1].alive && !game.players[1].escaped);
    }

    #[test]
    fn test_can_sleep_basic() {
        let mut game = Game::new();
        game.load();
        // Clear map of ghosts and generators
        for y in 0..MAP_HEIGHT {
            for x in 0..MAP_WIDTH {
                let v = game.map.get(x, y);
                if (GHOST..=GHOST + 2).contains(&v) || (GENERATOR..=GENERATOR + 2).contains(&v) {
                    game.map.set(x, y, SPACE);
                }
            }
        }
        assert!(game.can_sleep());
    }

    #[test]
    fn test_cannot_sleep_with_input() {
        let mut game = Game::new();
        game.load();
        for y in 0..MAP_HEIGHT {
            for x in 0..MAP_WIDTH {
                let v = game.map.get(x, y);
                if (GHOST..=GHOST + 2).contains(&v) || (GENERATOR..=GENERATOR + 2).contains(&v) {
                    game.map.set(x, y, SPACE);
                }
            }
        }
        game.players[0].input_mask = ACTION_UP;
        assert!(!game.can_sleep());
    }

    #[test]
    fn test_cannot_sleep_with_arrow() {
        let mut game = Game::new();
        game.load();
        for y in 0..MAP_HEIGHT {
            for x in 0..MAP_WIDTH {
                let v = game.map.get(x, y);
                if (GHOST..=GHOST + 2).contains(&v) || (GENERATOR..=GENERATOR + 2).contains(&v) {
                    game.map.set(x, y, SPACE);
                }
            }
        }
        game.players[0].arrow = Some(Arrow { x: 10, y: 10, dir: 0, cooldown: 4 });
        assert!(!game.can_sleep());

        // Arrow for dead player SHOULD block sleep
        game.players[0].alive = false;
        let (tx, ty) = calculate_target_cog(&game.players);
        game.camera.cog_x = tx as f64;
        game.camera.cog_y = ty as f64;
        assert!(!game.can_sleep());
    }

    #[test]
    fn test_cannot_sleep_camera_moving() {
        let mut game = Game::new();
        game.load();
        for y in 0..MAP_HEIGHT {
            for x in 0..MAP_WIDTH {
                let v = game.map.get(x, y);
                if (GHOST..=GHOST + 2).contains(&v) || (GENERATOR..=GENERATOR + 2).contains(&v) {
                    game.map.set(x, y, SPACE);
                }
            }
        }
        game.camera.cog_x += 1.0;
        assert!(!game.can_sleep());

        game.camera.cog_x = (calculate_target_cog(&game.players).0 as f64) + 0.06;
        assert!(!game.can_sleep());

        game.camera.cog_x = (calculate_target_cog(&game.players).0 as f64) + 0.04;
        assert!(game.can_sleep());
    }

    #[test]
    fn test_cannot_sleep_unblocked_ghost() {
        let mut game = Game::new();
        game.load();
        for y in 0..MAP_HEIGHT {
            for x in 0..MAP_WIDTH {
                let v = game.map.get(x, y);
                if (GHOST..=GHOST + 2).contains(&v) || (GENERATOR..=GENERATOR + 2).contains(&v) {
                    game.map.set(x, y, SPACE);
                }
            }
        }
        let px = game.players[0].x;
        let py = game.players[0].y;
        
        // Place ghost next to player but with gap
        game.map.set(px + 2, py, GHOST);
        game.map.set(px + 1, py, SPACE);

        // Ghost is unblocked
        assert!(!game.can_sleep());

        // Block candidate paths
        game.map.set(px + 1, py, WALL);
        game.map.set(px + 1, py + 1, WALL);
        game.map.set(px + 1, py - 1, WALL);

        assert!(game.can_sleep());
    }

    #[test]
    fn test_cannot_sleep_unblocked_generator() {
        let mut game = Game::new();
        game.load();
        for y in 0..MAP_HEIGHT {
            for x in 0..MAP_WIDTH {
                let v = game.map.get(x, y);
                if (GHOST..=GHOST + 2).contains(&v) || (GENERATOR..=GENERATOR + 2).contains(&v) {
                    game.map.set(x, y, SPACE);
                }
            }
        }
        
        let active = game.get_active_rect();
        let gx = active.left + 2;
        let gy = active.top + 2;
        game.map.set(gx, gy, GENERATOR);
        game.map.set(gx, gy - 1, SPACE);

        assert!(!game.can_sleep());

        game.map.set(gx, gy - 1, WALL);
        game.map.set(gx + 1, gy, WALL);
        game.map.set(gx, gy + 1, WALL);
        game.map.set(gx - 1, gy, WALL);

        assert!(game.can_sleep());
    }

    #[test]
    fn test_self_resurrection() {
        let mut game = Game::new();
        game.load();
        
        // Clear map of ghosts and generators to avoid interference
        for y in 0..MAP_HEIGHT {
            for x in 0..MAP_WIDTH {
                let v = game.map.get(x, y);
                if (GHOST..=GHOST + 2).contains(&v) || (GENERATOR..=GENERATOR + 2).contains(&v) {
                    game.map.set(x, y, SPACE);
                }
            }
        }

        // Setup Player 1 at (5, 5) facing East (2)
        let p1_idx = 0;
        let px = 5;
        let py = 5;
        game.map.set(game.players[p1_idx].x, game.players[p1_idx].y, SPACE);
        game.players[p1_idx].x = px;
        game.players[p1_idx].y = py;
        game.players[p1_idx].dir = 2;
        game.players[p1_idx].health = 100;
        game.players[p1_idx].alive = true;
        game.map.set(px, py, PLAYER + p1_idx as u8);

        // Center camera on player
        let (tx, ty) = calculate_target_cog(&game.players);
        game.camera.cog_x = tx as f64;
        game.camera.cog_y = ty as f64;

        // Clear path for arrow
        game.map.set(px + 1, py, SPACE);

        // Place HEART at (px + 2, py)
        game.map.set(px + 2, py, HEART);

        // Fire P1's arrow East (input ACTION_SHOOT)
        game.players[p1_idx].input_mask = ACTION_SHOOT;
        
        // Step 1 time: Fires arrow immediately on 60 Hz frame, takes 1st step to px + 1, py
        game.step();
        
        // Arrow should be at (px + 1, py) now (fired and moved 1 tile)
        assert!(game.players[p1_idx].arrow.is_some());
        assert_eq!(game.players[p1_idx].arrow.unwrap().x, px + 1);
        assert_eq!(game.players[p1_idx].arrow.unwrap().y, py);
        
        // Clear input mask
        game.players[p1_idx].input_mask = 0;

        // Kill P1 on subsequent frame (before arrow hits HEART)
        game.players[p1_idx].health = 0;
        game.players[p1_idx].alive = false;
        game.map.set(px, py, SPACE); // Remove player from map

        // Verify Wasm cannot sleep while the arrow is in flight (even though player is dead)
        assert!(!game.can_sleep());

        // Step 4 times to trigger arrow movement tick (arrow hits HEART at px + 2, py)
        for _ in 0..4 {
            game.step();
        }

        // P1 should be resurrected to health = 50 at (px + 2, py)
        assert!(game.players[p1_idx].alive);
        assert_eq!(game.players[p1_idx].health, 50);
        assert_eq!(game.players[p1_idx].x, px + 2);
        assert_eq!(game.players[p1_idx].y, py);
        
        // Arrow should be destroyed
        assert!(game.players[p1_idx].arrow.is_none());
        
        // Map at (px + 2, py) should now be PLAYER + p1_idx
        assert_eq!(game.map.get(px + 2, py), PLAYER + p1_idx as u8);

        // Force camera to target COG to avoid camera movement blocking sleep
        let (tx, ty) = calculate_target_cog(&game.players);
        game.camera.cog_x = tx as f64;
        game.camera.cog_y = ty as f64;

        // Wasm can now sleep
        assert!(game.can_sleep());
    }

    #[test]
    fn test_player_8_frame_cadence() {
        let mut game = Game::new();
        game.load();
        // Clear map obstacles in front of P1
        let px = game.players[0].x;
        let py = game.players[0].y;
        game.map.set(px + 1, py, SPACE);
        game.map.set(px + 2, py, SPACE);
        game.map.set(px + 3, py, SPACE);

        game.players[0].input_mask = ACTION_RIGHT;

        // Frame 1: Immediate Move Start on 60 Hz frame (0 ms input lag)
        game.step();
        assert_eq!(game.players[0].x, px + 1, "P1 must move 1 tile immediately at frame 1");

        // Frames 2..8 (7 frames cooldown duration): P1 stays at px + 1
        for f in 2..=8 {
            game.step();
            assert_eq!(game.players[0].x, px + 1, "P1 must stay at px+1 until frame 9 (at frame {})", f);
        }

        // Frame 9 (8 frames after frame 1): P1 moves to px + 2
        game.step();
        assert_eq!(game.players[0].x, px + 2, "P1 must move to px+2 at frame 9");

        // Frames 10..16 (7 frames cooldown duration): P1 stays at px + 2
        for f in 10..=16 {
            game.step();
            assert_eq!(game.players[0].x, px + 2, "P1 must stay at px+2 until frame 17 (at frame {})", f);
        }

        // Frame 17 (8 frames after frame 9): P1 moves to px + 3
        game.step();
        assert_eq!(game.players[0].x, px + 3, "P1 must move to px+3 at frame 17");
    }

    #[test]
    fn test_arrow_4_frame_cadence_and_velocity_ratio() {
        let mut game = Game::new();
        game.load();
        let px = 10;
        let py = 10;
        game.map.set(game.players[0].x, game.players[0].y, SPACE);
        game.players[0].x = px;
        game.players[0].y = py;
        game.players[0].dir = 2; // East
        game.map.set(px, py, PLAYER);

        // Center camera on player
        let (tx, ty) = calculate_target_cog(&game.players);
        game.camera.cog_x = tx as f64;
        game.camera.cog_y = ty as f64;

        for x in (px + 1)..(px + 10) {
            game.map.set(x, py, SPACE);
        }

        // At frame 1: P1 fires arrow East immediately
        game.players[0].input_mask = ACTION_SHOOT;
        game.step(); // frame 1: arrow created and immediately moves to (11, 10)

        assert!(game.players[0].arrow.is_some());
        assert_eq!(game.players[0].arrow.unwrap().x, px + 1);

        // Frames 2..4 (3 frames): Arrow remains at px + 1
        game.players[0].input_mask = 0;
        for f in 2..=4 {
            game.step();
            assert_eq!(game.players[0].arrow.unwrap().x, px + 1, "Arrow should stay at px+1 at frame {}", f);
        }
        // Frame 5 (4 frames after frame 1): arrow advances to px + 2
        game.step();
        assert_eq!(game.players[0].arrow.unwrap().x, px + 2, "Arrow should advance to px+2 at frame 5");

        // Frames 6..8 (3 frames): Arrow remains at px + 2
        for f in 6..=8 {
            game.step();
            assert_eq!(game.players[0].arrow.unwrap().x, px + 2, "Arrow should stay at px+2 at frame {}", f);
        }
        // Frame 9 (4 frames after frame 5): arrow advances to px + 3
        game.step();
        assert_eq!(game.players[0].arrow.unwrap().x, px + 3, "Arrow should advance to px+3 at frame 9");
    }

    #[test]
    fn test_difficulty_delays_and_scaling() {
        assert_eq!(crate::Difficulty::Trivial.delay(), 13);
        assert_eq!(crate::Difficulty::Easy.delay(), 8);
        assert_eq!(crate::Difficulty::Hard.delay(), 5);
        assert_eq!(crate::Difficulty::Deadly.delay(), 2);

        let mut game = Game::new();
        assert_eq!(game.difficulty, crate::Difficulty::Easy);

        game.difficulty = crate::Difficulty::Deadly;
        let snap = game.save_state();
        assert_eq!(snap.difficulty, crate::Difficulty::Deadly);

        let mut game2 = Game::new();
        game2.load_state(&snap);
        assert_eq!(game2.difficulty, crate::Difficulty::Deadly);

        let bytes = game.save_state_bytes();
        let mut game3 = Game::new();
        let ok = game3.load_state_bytes(&bytes);
        assert!(ok);
        assert_eq!(game3.difficulty, crate::Difficulty::Deadly);
    }

    #[test]
    fn test_4player_hot_join_and_leave() {
        let mut game = Game::new();
        game.load();

        // P1 active, P2-P4 inactive
        assert!(game.players[0].active);
        assert!(!game.players[1].active);
        assert!(!game.players[2].active);
        assert!(!game.players[3].active);

        // P3 (Topaz) joins on input
        game.players[2].input_mask = ACTION_DOWN;
        game.step();
        assert!(game.players[2].active);
        assert!(game.players[2].alive);
        assert_eq!(game.map.get(game.players[2].x, game.players[2].y), PLAYER + 2);

        // P4 (Emerald) joins on input
        game.players[3].input_mask = ACTION_LEFT;
        game.step();
        assert!(game.players[3].active);
        assert!(game.players[3].alive);
        assert_eq!(game.map.get(game.players[3].x, game.players[3].y), PLAYER + 3);

        // Disconnect P3
        let p3_x = game.players[2].x;
        let p3_y = game.players[2].y;
        game.remove_player(2);
        assert!(!game.players[2].active);
        assert!(!game.players[2].alive);
        assert_eq!(game.map.get(p3_x, p3_y), SPACE);
    }

    #[test]
    fn test_snapshot_save_and_load_parity() {
        let mut game = Game::new();
        game.load();
        // Join P2 and simulate 20 frames
        game.players[1].input_mask = ACTION_RIGHT;
        for _ in 0..20 {
            game.step();
            game.update_camera();
        }

        let snap = game.save_state();

        // Modify game further
        for _ in 0..30 {
            game.players[0].input_mask = ACTION_DOWN;
            game.step();
            game.update_camera();
        }

        assert_ne!(game.time, snap.time);

        // Restore snapshot
        game.load_state(&snap);

        assert_eq!(game.time, snap.time);
        assert_eq!(game.last_move_time, snap.last_move_time);
        assert_eq!(game.level, snap.level);
        assert_eq!(game.rotor, snap.rotor);
        assert_eq!(game.difficulty, snap.difficulty);
        assert_eq!(game.rng.state(), snap.rng_state);
        assert_eq!(game.map.data, snap.map_data);
        assert_eq!(game.players, snap.players);
        assert_eq!(game.camera, snap.camera);
    }

    #[test]
    fn test_binary_state_serialization_roundtrip() {
        let mut game_a = Game::new();
        game_a.load();
        game_a.difficulty = crate::Difficulty::Hard;
        // Activate P1, P2, P3, P4
        game_a.spawn_player(1);
        game_a.spawn_player(2);
        game_a.spawn_player(3);

        for _ in 0..16 {
            game_a.players[0].input_mask = ACTION_RIGHT;
            game_a.players[1].input_mask = ACTION_UP;
            game_a.players[2].input_mask = ACTION_DOWN;
            game_a.players[3].input_mask = ACTION_LEFT;
            game_a.step();
            game_a.update_camera();
        }

        let bytes = game_a.save_state_bytes();
        assert!(!bytes.is_empty());

        let mut game_b = Game::new();
        let ok = game_b.load_state_bytes(&bytes);
        assert!(ok, "load_state_bytes must succeed");

        assert_eq!(game_a.time, game_b.time);
        assert_eq!(game_a.level, game_b.level);
        assert_eq!(game_a.rotor, game_b.rotor);
        assert_eq!(game_a.difficulty, game_b.difficulty);
        assert_eq!(game_a.rng.state(), game_b.rng.state());
        assert_eq!(game_a.map.data, game_b.map.data);
        assert_eq!(game_a.players, game_b.players);
        assert_eq!(game_a.camera.cog_x, game_b.camera.cog_x);
        assert_eq!(game_a.camera.cog_y, game_b.camera.cog_y);
    }

    #[test]
    fn test_deterministic_state_checksum() {
        let mut game_a = Game::new();
        game_a.load();
        let mut game_b = Game::new();
        game_b.load();

        assert_eq!(game_a.get_state_checksum(), game_b.get_state_checksum());

        // Step both identically
        for _ in 0..20 {
            game_a.players[0].input_mask = ACTION_RIGHT;
            game_b.players[0].input_mask = ACTION_RIGHT;
            game_a.step();
            game_b.step();
        }
        assert_eq!(game_a.get_state_checksum(), game_b.get_state_checksum());

        // Snapshot roundtrip checksum parity
        let snap = game_a.save_state();
        assert_eq!(snap.get_checksum(), game_a.get_state_checksum());

        let bytes = game_a.save_state_bytes();
        let mut game_c = Game::new();
        let ok = game_c.load_state_bytes(&bytes);
        assert!(ok);
        assert_eq!(game_c.get_state_checksum(), game_a.get_state_checksum());

        // Mutating any player state (health, score, keys, bombs, pos, dir, arrow) changes checksum
        let original_cs = game_a.get_state_checksum();
        game_a.players[0].health -= 1;
        assert_ne!(game_a.get_state_checksum(), original_cs);
        game_a.players[0].health += 1;
        assert_eq!(game_a.get_state_checksum(), original_cs);

        game_a.players[0].score += 10;
        assert_ne!(game_a.get_state_checksum(), original_cs);
        game_a.players[0].score -= 10;
        assert_eq!(game_a.get_state_checksum(), original_cs);

        game_a.players[0].keys += 1;
        assert_ne!(game_a.get_state_checksum(), original_cs);
        game_a.players[0].keys -= 1;
        assert_eq!(game_a.get_state_checksum(), original_cs);

        game_a.players[0].bombs += 1;
        assert_ne!(game_a.get_state_checksum(), original_cs);
        game_a.players[0].bombs -= 1;
        assert_eq!(game_a.get_state_checksum(), original_cs);

        game_a.players[0].move_cooldown += 1;
        assert_ne!(game_a.get_state_checksum(), original_cs);
        game_a.players[0].move_cooldown -= 1;
        assert_eq!(game_a.get_state_checksum(), original_cs);

        game_a.rotor = (game_a.rotor + 1) & 3;
        assert_ne!(game_a.get_state_checksum(), original_cs);
        game_a.rotor = (game_a.rotor + 3) & 3;
        assert_eq!(game_a.get_state_checksum(), original_cs);

        game_a.map.set(10, 10, GHOST);
        assert_ne!(game_a.get_state_checksum(), original_cs);
    }

    #[test]
    fn test_arrow_generator_degradation_and_destruction() {
        let mut game = Game::new();
        game.load();
        let px = 10;
        let py = 10;
        game.map.set(game.players[0].x, game.players[0].y, SPACE);
        game.players[0].x = px;
        game.players[0].y = py;
        game.players[0].dir = 2; // East
        game.map.set(px, py, PLAYER);

        // Center camera on player
        let (tx, ty) = calculate_target_cog(&game.players);
        game.camera.cog_x = tx as f64;
        game.camera.cog_y = ty as f64;

        // Place a Level 3 Generator at (px + 2, py)
        game.map.set(px + 1, py, SPACE);
        game.map.set(px + 2, py, GENERATOR + 2); // 15
        game.players[0].score = 0;

        // Shot 1: Fire arrow East
        game.players[0].input_mask = ACTION_SHOOT;
        game.step(); // Frame 1: arrow spawns at px + 1
        game.players[0].input_mask = 0;

        for _ in 0..4 {
            game.step(); // Frame 5: arrow hits generator at px + 2
        }

        // Generator should degrade from 15 -> 14, player score + 200
        assert_eq!(game.map.get(px + 2, py), GENERATOR + 1);
        assert_eq!(game.players[0].score, 200);
        assert!(game.players[0].arrow.is_none());

        // Shot 2: Fire again
        game.players[0].input_mask = ACTION_SHOOT;
        game.step();
        game.players[0].input_mask = 0;
        for _ in 0..4 {
            game.step();
        }

        // Generator should degrade from 14 -> 13, player score + 200 -> 400
        assert_eq!(game.map.get(px + 2, py), GENERATOR);
        assert_eq!(game.players[0].score, 400);
        assert!(game.players[0].arrow.is_none());

        // Shot 3: Fire again to destroy
        game.players[0].input_mask = ACTION_SHOOT;
        game.step();
        game.players[0].input_mask = 0;
        for _ in 0..4 {
            game.step();
        }

        // Generator should be destroyed to SPACE, player score + 200 -> 600
        assert_eq!(game.map.get(px + 2, py), SPACE);
        assert_eq!(game.players[0].score, 600);
        assert!(game.players[0].arrow.is_none());
    }

    #[test]
    fn test_smart_bomb_clears_generators_and_ghosts() {
        let mut game = Game::new();
        game.load();
        
        // Clear map of existing ghosts and generators
        for y in 0..MAP_HEIGHT {
            for x in 0..MAP_WIDTH {
                let v = game.map.get(x, y);
                if (GHOST..=GHOST + 2).contains(&v) || (GENERATOR..=GENERATOR + 2).contains(&v) {
                    game.map.set(x, y, SPACE);
                }
            }
        }

        let active = game.get_active_rect();

        // Place ghost and generator inside active rect
        let gx = active.left + 2;
        let gy = active.top + 2;
        game.map.set(gx, gy, GHOST + 1); // 20 pts
        game.map.set(gx + 1, gy, GENERATOR + 1); // 200 pts

        game.players[0].score = 0;
        game.players[0].bombs = 1;
        game.players[0].input_mask = ACTION_BOMB;

        game.step();

        // Both should be cleared to SPACE
        assert_eq!(game.map.get(gx, gy), SPACE);
        assert_eq!(game.map.get(gx + 1, gy), SPACE);
        // Score should be 20 + 200 = 220
        assert_eq!(game.players[0].score, 220);
        assert_eq!(game.players[0].bombs, 0);
    }

    #[test]
    fn test_move_cooldown_decrements_while_shooting() {
        let mut game = Game::new();
        game.load();
        let px = 10;
        let py = 10;
        game.map.set(game.players[0].x, game.players[0].y, SPACE);
        game.players[0].x = px;
        game.players[0].y = py;
        game.map.set(px, py, PLAYER);
        game.map.set(px + 1, py, SPACE);
        game.map.set(px + 2, py, SPACE);
        game.map.set(px, py + 1, SPACE);

        // Frame 1: P1 moves Right (move_cooldown set to 8)
        game.players[0].input_mask = ACTION_RIGHT;
        game.step();
        assert_eq!(game.players[0].x, px + 1);
        assert_eq!(game.players[0].move_cooldown, 8);

        // Frames 2..9 (8 frames): P1 holds Shoot
        game.players[0].input_mask = ACTION_SHOOT;
        for _ in 0..8 {
            game.step();
        }

        // move_cooldown should now have fully decremented to 0
        assert_eq!(game.players[0].move_cooldown, 0);

        // Frame 10: P1 releases shoot and presses Down -> must move IMMEDIATELY (0 ms lag)
        game.players[0].input_mask = ACTION_DOWN;
        game.step();
        assert_eq!(game.players[0].y, py + 1, "Player must move immediately without 8-frame freeze");
    }

    #[test]
    fn test_arrow_despawns_at_active_viewport_boundary() {
        let mut game = Game::new();
        game.load();

        // Clear existing ghosts and generators
        for y in 0..MAP_HEIGHT {
            for x in 0..MAP_WIDTH {
                let v = game.map.get(x, y);
                if (GHOST..=GHOST + 2).contains(&v) || (GENERATOR..=GENERATOR + 2).contains(&v) {
                    game.map.set(x, y, SPACE);
                }
            }
        }

        let px = 10;
        let py = 5;
        game.map.set(game.players[0].x, game.players[0].y, SPACE);
        game.players[0].x = px;
        game.players[0].y = py;
        game.players[0].dir = 2; // East
        game.map.set(px, py, PLAYER);

        // Center camera on player
        let (tx, ty) = calculate_target_cog(&game.players);
        game.camera.cog_x = tx as f64;
        game.camera.cog_y = ty as f64;

        let active = game.get_active_rect();
        // Clear line of sight all the way across the map
        for x in 0..MAP_WIDTH {
            game.map.set(x, py, SPACE);
        }
        game.map.set(px, py, PLAYER);

        // Fire arrow East
        game.players[0].input_mask = ACTION_SHOOT;
        game.step();
        game.players[0].input_mask = 0;

        assert!(game.players[0].arrow.is_some());
        assert!(game.sounds.contains(&SOUND_SHOOT));

        // Fly arrow step-by-step until it reaches the edge of active_rect
        let right_edge = active.left + active.width;
        let mut frames = 0;
        while game.players[0].arrow.is_some() && frames < 200 {
            game.step();
            frames += 1;
            if let Some(arrow) = game.players[0].arrow {
                assert!(arrow.x < right_edge, "Arrow must not advance past right edge of visible viewport");
            }
        }

        // Arrow must have despawned cleanly upon reaching the edge
        assert!(game.players[0].arrow.is_none(), "Arrow must despawn when leaving active viewport");
        // Player must be immediately able to shoot again
        game.players[0].input_mask = ACTION_SHOOT;
        game.step();
        assert!(game.players[0].arrow.is_some(), "Player must be able to shoot immediately once arrow despawned");
    }

    #[test]
    fn test_arrow_hit_wall_sound_and_slot_freed() {
        let mut game = Game::new();
        game.load();
        let px = 5;
        let py = 5;
        game.map.set(game.players[0].x, game.players[0].y, SPACE);
        game.players[0].x = px;
        game.players[0].y = py;
        game.players[0].dir = 2; // East
        game.map.set(px, py, PLAYER);

        let (tx, ty) = calculate_target_cog(&game.players);
        game.camera.cog_x = tx as f64;
        game.camera.cog_y = ty as f64;

        // Place wall right in front at px + 1
        game.map.set(px + 1, py, WALL);

        game.players[0].input_mask = ACTION_SHOOT;
        game.step();

        // Arrow immediately hit wall on spawn step, emitted SOUND_HIT_WALL and freed arrow slot
        assert!(game.players[0].arrow.is_none());
        assert_eq!(game.map.get(px + 1, py), WALL, "Wall must remain intact");
        assert!(game.sounds.contains(&SOUND_HIT_WALL), "SOUND_HIT_WALL must be triggered");
    }

    #[test]
    fn test_arrow_hit_monster_sounds_by_tier() {
        let mut game = Game::new();
        game.load();
        let px = 5;
        let py = 5;
        game.map.set(game.players[0].x, game.players[0].y, SPACE);
        game.players[0].x = px;
        game.players[0].y = py;
        game.players[0].dir = 2; // East
        game.map.set(px, py, PLAYER);

        let (tx, ty) = calculate_target_cog(&game.players);
        game.camera.cog_x = tx as f64;
        game.camera.cog_y = ty as f64;

        // Test Tier 1 Ghost (GHOST / 9)
        game.map.set(px + 1, py, GHOST);
        game.players[0].input_mask = ACTION_SHOOT;
        game.step();
        assert!(game.sounds.contains(&SOUND_HIT_MONSTER_1), "SOUND_HIT_MONSTER_1 must be triggered");
        assert_eq!(game.map.get(px + 1, py), SPACE, "Tier 1 ghost destroyed to SPACE");
        assert_eq!(game.players[0].score, 10);
        assert!(game.players[0].arrow.is_none());

        // Test Tier 2 Ghost (GHOST + 1 / 10)
        game.map.set(px + 1, py, GHOST + 1);
        game.step(); // Fire again
        assert!(game.sounds.contains(&SOUND_HIT_MONSTER_2), "SOUND_HIT_MONSTER_2 must be triggered");
        assert_eq!(game.map.get(px + 1, py), GHOST, "Tier 2 ghost degraded to Tier 1");
        assert_eq!(game.players[0].score, 20);
        assert!(game.players[0].arrow.is_none());

        // Test Tier 3 Ghost (GHOST + 2 / 11)
        game.map.set(px + 1, py, GHOST + 2);
        game.step(); // Fire again
        assert!(game.sounds.contains(&SOUND_HIT_MONSTER_3), "SOUND_HIT_MONSTER_3 must be triggered");
        assert_eq!(game.map.get(px + 1, py), GHOST + 1, "Tier 3 ghost degraded to Tier 2");
        assert_eq!(game.players[0].score, 30);
        assert!(game.players[0].arrow.is_none());
    }

    #[test]
    fn test_arrow_friendly_fire_and_bomb_trigger() {
        let mut game = Game::new();
        game.load();
        let px = 5;
        let py = 5;
        game.map.set(game.players[0].x, game.players[0].y, SPACE);
        game.players[0].x = px;
        game.players[0].y = py;
        game.players[0].dir = 2; // East
        game.map.set(px, py, PLAYER);

        // Spawn P2 in front at px + 1
        game.players[1].active = true;
        game.players[1].alive = true;
        game.players[1].x = px + 1;
        game.players[1].y = py;
        game.map.set(px + 1, py, PLAYER + 1);

        let (tx, ty) = calculate_target_cog(&game.players);
        game.camera.cog_x = tx as f64;
        game.camera.cog_y = ty as f64;

        // Shoot towards P2
        game.players[0].input_mask = ACTION_SHOOT;
        game.step();

        assert!(game.sounds.contains(&SOUND_HIT_PLAYER), "SOUND_HIT_PLAYER must trigger on friendly fire");
        assert_eq!(game.map.get(px + 1, py), PLAYER + 1, "Player tile remains intact");
        assert!(game.players[0].arrow.is_none(), "Arrow must despawn on player collision");

        // Now test Arrow hitting a Bomb tile
        game.map.set(px + 1, py, BOMB);
        game.step(); // Fire again
        assert!(game.sounds.contains(&SOUND_EXPLODE_BOMB), "SOUND_EXPLODE_BOMB must trigger on bomb tile hit");
        assert_eq!(game.map.get(px + 1, py), SPACE, "Bomb tile cleared after explosion");
        assert!(game.players[0].arrow.is_none());
    }

    #[test]
    fn test_sound_priority_hierarchy() {
        assert!(sound_priority(SOUND_EXPLODE_BOMB) > sound_priority(SOUND_DEAD_PLAYER));
        assert!(sound_priority(SOUND_DEAD_PLAYER) > sound_priority(SOUND_WARP_OUT));
        assert!(sound_priority(SOUND_WARP_OUT) > sound_priority(SOUND_WARP_IN));
        assert!(sound_priority(SOUND_WARP_IN) > sound_priority(SOUND_MONSTER_BITE));
        assert!(sound_priority(SOUND_MONSTER_BITE) > sound_priority(SOUND_HIT_PLAYER));
        assert!(sound_priority(SOUND_HIT_PLAYER) > sound_priority(SOUND_EAT_FOOD));
        assert!(sound_priority(SOUND_EAT_FOOD) > sound_priority(SOUND_OPEN_DOOR));
        assert!(sound_priority(SOUND_OPEN_DOOR) > sound_priority(SOUND_HIT_GENERATOR));
        assert!(sound_priority(SOUND_HIT_GENERATOR) > sound_priority(SOUND_HIT_MONSTER_3));
        assert!(sound_priority(SOUND_HIT_MONSTER_3) > sound_priority(SOUND_HIT_MONSTER_2));
        assert!(sound_priority(SOUND_HIT_MONSTER_2) > sound_priority(SOUND_HIT_MONSTER_1));
        assert!(sound_priority(SOUND_HIT_MONSTER_1) > sound_priority(SOUND_PICK_MONEY));
        assert!(sound_priority(SOUND_PICK_MONEY) > sound_priority(SOUND_PICKUP_OBJECT));
        assert!(sound_priority(SOUND_PICKUP_OBJECT) > sound_priority(SOUND_HIT_WALL));
        assert!(sound_priority(SOUND_HIT_WALL) > sound_priority(SOUND_SHOOT));
        assert!(sound_priority(SOUND_SHOOT) > sound_priority(SOUND_NONE));
    }

    #[test]
    fn test_sound_pokey_channel_mapping() {
        // Channel 3: Explosions, Death, Warps
        assert_eq!(sound_pokey_channel(SOUND_EXPLODE_BOMB), 3);
        assert_eq!(sound_pokey_channel(SOUND_DEAD_PLAYER), 3);
        assert_eq!(sound_pokey_channel(SOUND_WARP_OUT), 3);
        assert_eq!(sound_pokey_channel(SOUND_WARP_IN), 3);

        // Channel 2: Monster Bite
        assert_eq!(sound_pokey_channel(SOUND_MONSTER_BITE), 2);

        // Channel 1: Monster/Player/Spawner hits
        assert_eq!(sound_pokey_channel(SOUND_HIT_PLAYER), 1);
        assert_eq!(sound_pokey_channel(SOUND_HIT_MONSTER_1), 1);
        assert_eq!(sound_pokey_channel(SOUND_HIT_MONSTER_2), 1);
        assert_eq!(sound_pokey_channel(SOUND_HIT_MONSTER_3), 1);
        assert_eq!(sound_pokey_channel(SOUND_HIT_GENERATOR), 1);

        // Channel 0: Ambient / Items / Actions
        assert_eq!(sound_pokey_channel(SOUND_SHOOT), 0);
        assert_eq!(sound_pokey_channel(SOUND_OPEN_DOOR), 0);
        assert_eq!(sound_pokey_channel(SOUND_PICKUP_OBJECT), 0);
        assert_eq!(sound_pokey_channel(SOUND_EAT_FOOD), 0);
        assert_eq!(sound_pokey_channel(SOUND_PICK_MONEY), 0);
        assert_eq!(sound_pokey_channel(SOUND_HIT_WALL), 0);
    }

    #[test]
    fn test_pokey_audio_scheduler_idle_allocation() {
        let mut scheduler = PokeyAudioScheduler::new();

        // 1. Schedule shoot -> allocates preferred channel 0
        let ch0 = scheduler.schedule_sound(SOUND_SHOOT);
        assert_eq!(ch0, Some(0));
        assert_eq!(scheduler.get_channel_sound(0), SOUND_SHOOT);
        assert!(scheduler.is_channel_active(0));

        // 2. Schedule monster hit 1 -> allocates preferred channel 1
        let ch1 = scheduler.schedule_sound(SOUND_HIT_MONSTER_1);
        assert_eq!(ch1, Some(1));
        assert_eq!(scheduler.get_channel_sound(1), SOUND_HIT_MONSTER_1);

        // 3. Schedule monster bite -> allocates preferred channel 2
        let ch2 = scheduler.schedule_sound(SOUND_MONSTER_BITE);
        assert_eq!(ch2, Some(2));
        assert_eq!(scheduler.get_channel_sound(2), SOUND_MONSTER_BITE);

        // 4. Schedule smart bomb explosion -> allocates preferred channel 3
        let ch3 = scheduler.schedule_sound(SOUND_EXPLODE_BOMB);
        assert_eq!(ch3, Some(3));
        assert_eq!(scheduler.get_channel_sound(3), SOUND_EXPLODE_BOMB);
    }

    #[test]
    fn test_pokey_audio_scheduler_preemption_high_over_low() {
        let mut scheduler = PokeyAudioScheduler::new();

        // Fill all 4 channels with low-priority sounds
        scheduler.schedule_sound(SOUND_SHOOT); // Ch 0, prio 15
        scheduler.schedule_sound(SOUND_HIT_WALL); // Ch 1 (since 0 busy if not matched), prio 20
        scheduler.schedule_sound(SOUND_PICKUP_OBJECT); // Ch 2, prio 35
        scheduler.schedule_sound(SOUND_PICK_MONEY); // Ch 3, prio 40

        for ch in 0..NUM_POKEY_CHANNELS {
            assert!(scheduler.is_channel_active(ch));
        }

        // Now incoming high-priority sound: SOUND_EXPLODE_BOMB (prio 100)
        // Must preempt the lowest priority channel (SOUND_SHOOT, prio 15 on Ch 0)
        let ch = scheduler.schedule_sound(SOUND_EXPLODE_BOMB);
        assert_eq!(ch, Some(0));
        assert_eq!(scheduler.get_channel_sound(0), SOUND_EXPLODE_BOMB);

        // Next incoming high-priority sound: SOUND_DEAD_PLAYER (prio 95)
        // Must preempt next lowest priority channel (SOUND_HIT_WALL, prio 20 on Ch 1)
        let ch2 = scheduler.schedule_sound(SOUND_DEAD_PLAYER);
        assert_eq!(ch2, Some(1));
        assert_eq!(scheduler.get_channel_sound(1), SOUND_DEAD_PLAYER);
    }

    #[test]
    fn test_pokey_audio_scheduler_drop_lower_priority_when_busy() {
        let mut scheduler = PokeyAudioScheduler::new();

        // Fill all 4 channels with major high-priority sounds
        scheduler.schedule_sound(SOUND_EXPLODE_BOMB); // prio 100
        scheduler.schedule_sound(SOUND_DEAD_PLAYER);  // prio 95
        scheduler.schedule_sound(SOUND_WARP_OUT);     // prio 90
        scheduler.schedule_sound(SOUND_WARP_IN);      // prio 85

        for ch in 0..NUM_POKEY_CHANNELS {
            assert!(scheduler.is_channel_active(ch));
        }

        // Incoming low-priority sound: SOUND_SHOOT (prio 15) must be dropped
        let result = scheduler.schedule_sound(SOUND_SHOOT);
        assert_eq!(result, None);

        // Incoming medium sound: SOUND_HIT_MONSTER_1 (prio 45) must be dropped
        let result2 = scheduler.schedule_sound(SOUND_HIT_MONSTER_1);
        assert_eq!(result2, None);

        // All 4 high priority sounds remain intact
        assert_eq!(scheduler.get_channel_sound(3), SOUND_EXPLODE_BOMB);
    }

    #[test]
    fn test_pokey_audio_scheduler_batch_frame_prioritization() {
        let mut scheduler = PokeyAudioScheduler::new();

        // Batch of 6 sounds in one frame: 2 low, 2 medium, 2 critical
        let events = [
            SOUND_SHOOT,         // prio 15
            SOUND_EXPLODE_BOMB,  // prio 100
            SOUND_HIT_WALL,      // prio 20
            SOUND_DEAD_PLAYER,   // prio 95
            SOUND_MONSTER_BITE,  // prio 75
            SOUND_EAT_FOOD,      // prio 65
        ];
        scheduler.schedule_frame_events(&events);

        let mut scheduled_sounds = Vec::new();
        for ch in 0..NUM_POKEY_CHANNELS {
            if scheduler.is_channel_active(ch) {
                scheduled_sounds.push(scheduler.get_channel_sound(ch));
            }
        }
        assert_eq!(scheduled_sounds.len(), 4, "Top 4 priority sounds claim the 4 channels");
        assert!(scheduled_sounds.contains(&SOUND_EXPLODE_BOMB));
        assert!(scheduled_sounds.contains(&SOUND_DEAD_PLAYER));
        assert!(scheduled_sounds.contains(&SOUND_MONSTER_BITE));
        assert!(scheduled_sounds.contains(&SOUND_EAT_FOOD));
        assert!(!scheduled_sounds.contains(&SOUND_SHOOT));
        assert!(!scheduled_sounds.contains(&SOUND_HIT_WALL));
    }

    #[test]
    fn test_pokey_audio_scheduler_duration_and_expiry() {
        let mut scheduler = PokeyAudioScheduler::new();
        // Schedule short sound: SOUND_SHOOT (5 frames duration)
        let ch = scheduler.schedule_sound(SOUND_SHOOT).unwrap();
        assert!(scheduler.is_channel_active(ch));

        // Advance 4 frames -> still active
        for _ in 0..4 {
            scheduler.tick_frame();
            assert!(scheduler.is_channel_active(ch));
        }

        // Advance 5th frame -> expired and freed!
        scheduler.tick_frame();
        assert!(!scheduler.is_channel_active(ch));
        assert_eq!(scheduler.get_channel_sound(ch), SOUND_NONE);
    }

    #[test]
    fn test_monster_bite_and_death_sound_emission() {
        let mut game = Game::new();
        game.load();
        let px = 5;
        let py = 5;
        game.map.set(game.players[0].x, game.players[0].y, SPACE);
        game.players[0].x = px;
        game.players[0].y = py;
        game.players[0].health = 15; // Low health
        game.map.set(px, py, PLAYER);

        // Place Tier 1 Ghost right above player at (5, 4)
        game.map.set(px, py - 1, GHOST);

        let mut sounds = Vec::new();

        // Step ghost -> moves Down (5, 5) and bites player
        crate::ai::step_ghost(px, py - 1, GHOST, &mut game.map, &mut game.players, &mut sounds);

        assert!(sounds.contains(&SOUND_MONSTER_BITE), "Must emit SOUND_MONSTER_BITE on attack");
        assert_eq!(game.players[0].health, 5, "Health reduced by 10 (from 15 to 5)");
        assert!(game.players[0].alive);

        // Ghost attacks again -> kills player!
        sounds.clear();
        game.map.set(px, py - 1, GHOST);
        crate::ai::step_ghost(px, py - 1, GHOST, &mut game.map, &mut game.players, &mut sounds);

        assert!(sounds.contains(&SOUND_MONSTER_BITE));
        assert!(sounds.contains(&SOUND_DEAD_PLAYER), "Must emit SOUND_DEAD_PLAYER when player dies");
        assert_eq!(game.players[0].health, 0);
        assert!(!game.players[0].alive);
        assert_eq!(game.players[0].move_cooldown, 0, "move_cooldown must be reset to 0 upon death");
        assert_eq!(game.players[0].input_mask, 0, "input_mask must be reset to 0 upon death");
    }

    #[test]
    fn test_player_facing_direction_preserved_when_wall_sliding_fails() {
        let mut game = Game::new();
        game.load();

        // Place player at (10, 10) surrounded by walls to the North, North-East, and North-West
        let px = 10;
        let py = 10;
        game.map.set(game.players[0].x, game.players[0].y, SPACE);
        game.players[0].x = px;
        game.players[0].y = py;
        game.players[0].dir = 0; // Up
        game.map.set(px, py, PLAYER);

        // Wall to Up (10, 9), Up-Right (11, 9), Up-Left (9, 9)
        game.map.set(px, py - 1, WALL);
        game.map.set(px + 1, py - 1, WALL);
        game.map.set(px - 1, py - 1, WALL);

        let mut sounds = Vec::new();
        let active = game.get_active_rect();

        // Player inputs UP
        game.players[0].input_mask = ACTION_UP;
        game.players[0].move_cooldown = 0;

        crate::physics::step_player(0, &mut game.players, &mut game.map, active, &mut sounds);

        // Movement should have failed (player stays at 10, 10)
        assert_eq!(game.players[0].x, px);
        assert_eq!(game.players[0].y, py);
        // Player direction must REMAIN 0 (Up), NOT 7 (Up-Left) or 1 (Up-Right)
        assert_eq!(game.players[0].dir, 0, "Facing direction must remain UP (0) when all slide paths fail");
    }

    #[test]
    fn test_dead_player_does_not_block_can_sleep() {
        let mut game = Game::new();
        game.load();
        // Activate P2
        game.players[1].active = true;
        game.players[1].alive = true;
        game.players[1].move_cooldown = 6; // P2 was moving mid-stride

        // Kill P2 directly
        let mut sounds = Vec::new();
        crate::ai::hurt_player(1, 200, &mut game.map, &mut game.players, &mut sounds);

        assert!(!game.players[1].alive);
        assert_eq!(game.players[1].move_cooldown, 0);

        // P1 is alive with 0 input and 0 cooldown
        game.players[0].input_mask = 0;
        game.players[0].move_cooldown = 0;

        // Clear ghosts in viewport to isolate player state
        let active = game.get_active_rect();
        for y in active.top..(active.top + active.height) {
            for x in active.left..(active.left + active.width) {
                let v = game.map.get(x, y);
                if (GHOST..=GHOST + 2).contains(&v) || (GENERATOR..=GENERATOR + 2).contains(&v) {
                    game.map.set(x, y, SPACE);
                }
            }
        }

        // can_sleep should succeed even though P2 is dead in the game
        assert!(game.can_sleep(), "Dead player must not block can_sleep");
    }

    #[test]
    fn test_enemy_scanning_odd_bounds() {
        let mut game = Game::new();
        game.load();

        // Setup active rect with odd left and top bounds: left=1, top=1, width=4, height=4
        let active = ActiveRect { left: 1, top: 1, width: 4, height: 4 };

        // Clear region
        for y in 1..5 {
            for x in 1..5 {
                game.map.set(x, y, SPACE);
            }
        }

        // Place ghost at odd border tile (1, 1)
        game.map.set(1, 1, GHOST);

        // Position alive player at (1, 3)
        game.map.set(game.players[0].x, game.players[0].y, SPACE);
        game.players[0].x = 1;
        game.players[0].y = 3;
        game.map.set(1, 3, PLAYER);

        // Step enemies 4 times to cycle through all 4 rotor phases (0..3)
        let mut sounds = Vec::new();
        for _ in 0..4 {
            crate::ai::step_enemies(&mut game.map, &mut game.players, active, &mut game.rotor, &mut game.rng, &mut sounds);
        }

        // Ghost at (1, 1) should have been scanned and moved towards player at (1, 3)
        assert_ne!(game.map.get(1, 1), GHOST, "Ghost at odd coordinate (1, 1) must be scanned and stepped");
    }

    #[test]
    fn test_load_state_rejects_truncated_player_block() {
        let mut game = Game::new();
        game.load();
        let valid_bytes = game.save_state_bytes();
        assert!(game.load_state_bytes(&valid_bytes), "Valid bytes must load successfully");

        // The header consumes 38 bytes (offset = 38).
        // The first player block starts at offset 38 and requires 29 fixed bytes (up to offset 67).
        // Test all truncated lengths between offset and offset + 28 (i.e. length 38..66):
        for len in 38..67 {
            let truncated = &valid_bytes[..len];
            assert!(
                !game.load_state_bytes(truncated),
                "Truncated state bytes of length {} must be rejected cleanly without panic",
                len
            );
        }
    }

    #[test]
    fn test_load_state_rejects_excess_players() {
        let mut game = Game::new();
        game.load();
        let mut valid_bytes = game.save_state_bytes();
        // Byte 37 is num_players (offset 37 from 0..38 header)
        valid_bytes[37] = 5; // > MAX_PLAYERS (4)
        assert!(!game.load_state_bytes(&valid_bytes), "num_players > MAX_PLAYERS must be rejected");
        valid_bytes[37] = 255;
        assert!(!game.load_state_bytes(&valid_bytes), "num_players = 255 must be rejected");
    }

    #[test]
    fn test_load_state_rejects_corrupted_directions() {
        let mut game = Game::new();
        game.load();
        let mut valid_bytes = game.save_state_bytes();
        // First player block starts at offset 38.
        // Index is offset 38, x is 39..42, y is 43..46, dir is offset 47.
        valid_bytes[47] = 8; // Invalid dir >= 8
        assert!(!game.load_state_bytes(&valid_bytes), "Player dir >= 8 must be rejected to prevent OOB indexing");

        valid_bytes[47] = 255;
        assert!(!game.load_state_bytes(&valid_bytes), "Player dir = 255 must be rejected to prevent OOB indexing");
    }

    #[test]
    fn test_load_state_rejects_corrupted_player_index() {
        let mut game = Game::new();
        game.load();
        let mut valid_bytes = game.save_state_bytes();
        // First player index is at offset 38
        valid_bytes[38] = 4; // index >= MAX_PLAYERS (4)
        assert!(!game.load_state_bytes(&valid_bytes), "Player index >= MAX_PLAYERS must be rejected");
    }

    #[test]
    fn test_hurt_player_idempotent_on_dead_or_escaped_player() {
        let mut game = Game::new();
        game.load();
        game.players[0].keys = 3;
        let px = game.players[0].x;
        let py = game.players[0].y;
        let mut sounds = Vec::new();

        // 1. First lethal attack kills player, emits SOUND_DEAD_PLAYER, and drops 1 key (keys 3 -> 2)
        crate::ai::hurt_player(0, 200, &mut game.map, &mut game.players, &mut sounds);
        assert!(!game.players[0].alive);
        assert_eq!(game.players[0].keys, 2);
        assert_eq!(game.map.get(px, py), KEY);
        assert!(sounds.contains(&SOUND_DEAD_PLAYER));

        // 2. Subsequent attack on already-dead player must be a NO-OP (no sound, keys stay 2, map unchanged)
        sounds.clear();
        game.map.set(px, py, SPACE); // Someone picked up the key
        crate::ai::hurt_player(0, 200, &mut game.map, &mut game.players, &mut sounds);
        assert!(!game.players[0].alive);
        assert_eq!(game.players[0].keys, 2, "Dead player must not drop duplicate keys");
        assert_eq!(game.map.get(px, py), SPACE, "Dead player must not overwrite map tile");
        assert!(sounds.is_empty(), "Dead player must not re-emit death sound");

        // 3. Attack on escaped player must also be a NO-OP
        game.players[1].active = true;
        game.players[1].alive = true;
        game.players[1].escaped = true;
        game.players[1].keys = 5;
        crate::ai::hurt_player(1, 200, &mut game.map, &mut game.players, &mut sounds);
        assert!(sounds.is_empty(), "Escaped player must not be hurt or drop keys");
        assert_eq!(game.players[1].keys, 5);
    }

    #[test]
    fn test_locked_door_have_none_sound_when_no_keys() {
        let mut game = Game::new();
        game.load();
        let px = 5;
        let py = 5;
        game.map.set(game.players[0].x, game.players[0].y, SPACE);
        game.players[0].x = px;
        game.players[0].y = py;
        game.players[0].dir = 2; // East
        game.players[0].keys = 0;
        game.map.set(px, py, PLAYER);

        // Place a locked door directly to the East (6, 5)
        game.map.set(px + 1, py, LOCK);

        let mut sounds = Vec::new();
        let moved = crate::physics::try_move_player(0, &mut game.players[0], &mut game.map, 2, &mut sounds);

        assert!(!moved, "Player cannot move through locked door without keys");
        assert_eq!(game.players[0].x, px, "Player remains in position");
        assert_eq!(game.map.get(px + 1, py), LOCK, "Door remains locked");
        assert!(sounds.contains(&SOUND_HAVE_NONE), "Must emit SOUND_HAVE_NONE when hitting door with 0 keys");
    }

    #[test]
    fn test_bomb_action_have_none_sound_when_no_bombs() {
        let mut game = Game::new();
        game.load();
        game.players[0].bombs = 0;
        game.players[0].input_mask = ACTION_BOMB;
        game.players[0].move_cooldown = 0;

        let mut sounds = Vec::new();
        let active = game.get_active_rect();
        crate::physics::step_player(0, &mut game.players, &mut game.map, active, &mut sounds);

        assert!(sounds.contains(&SOUND_HAVE_NONE), "Must emit SOUND_HAVE_NONE when triggering bomb with 0 bombs");
    }

    #[test]
    fn test_spawner_sound_emissions_and_tiers() {
        let mut game = Game::new();
        game.load();
        let gx = 10;
        let gy = 10;

        // Place generator at (10, 10) surrounded by SPACE
        game.map.set(gx, gy, GENERATOR);
        game.map.set(gx, gy - 1, SPACE); // North
        game.map.set(gx + 1, gy, SPACE); // East
        game.map.set(gx, gy + 1, SPACE); // South
        game.map.set(gx - 1, gy, SPACE); // West

        let mut sounds = Vec::new();
        let mut rng = LcgRng::new(42);

        crate::ai::step_generator(gx, gy, GENERATOR, &mut game.map, &mut rng, &mut sounds);

        assert!(!sounds.is_empty(), "Spawner must emit a sound on ghost spawn");
        let snd = sounds[0];
        assert!(
            (SOUND_SPAWNING_1..=SOUND_SPAWNING_4).contains(&snd),
            "Emitted sound {snd} must be in SOUND_SPAWNING_1..=SOUND_SPAWNING_4"
        );
    }

    #[test]
    fn test_initial_level_load_emits_warp_in_sound() {
        let mut game = Game::new();
        game.load();
        assert!(game.sounds.contains(&SOUND_WARP_IN), "Initial Level 1 load must emit SOUND_WARP_IN");
        assert!(game.audio_scheduler.is_channel_active(3), "SOUND_WARP_IN must be scheduled on channel 3 upon initial level load");
        assert_eq!(game.audio_scheduler.get_channel_sound(3), SOUND_WARP_IN);
    }

    #[test]
    fn test_level_restart_and_progression_warp_in_sound() {
        let mut game = Game::new();
        game.load();

        // 1. Single player escapes with keys, bombs, health, score -> next level preserves them
        game.players[0].health = 250;
        game.players[0].keys = 3;
        game.players[0].bombs = 2;
        game.players[0].score = 1500;
        game.players[0].escaped = true;
        game.players[0].alive = true;
        game.step();

        assert_eq!(game.level, 1);
        assert_eq!(game.players[0].health, 250);
        assert_eq!(game.players[0].keys, 3);
        assert_eq!(game.players[0].bombs, 2);
        assert_eq!(game.players[0].score, 1500);
        assert!(game.sounds.contains(&SOUND_WARP_IN), "Level transition must emit SOUND_WARP_IN");
        assert!(game.audio_scheduler.is_channel_active(3), "SOUND_WARP_IN scheduled on channel 3");

        // 2. Player dies and restarts -> wipes to level 0 with 0 score, 100 health, 0 keys, 0 bombs
        game.players[0].alive = false;
        game.players[0].escaped = false;
        game.step();

        assert_eq!(game.level, 0);
        assert_eq!(game.players[0].health, 100);
        assert_eq!(game.players[0].keys, 0);
        assert_eq!(game.players[0].bombs, 0);
        assert_eq!(game.players[0].score, 0);
        assert!(game.sounds.contains(&SOUND_WARP_IN), "Wipe restart must emit SOUND_WARP_IN");
    }

    #[test]
    fn test_full_sound_table_parity() {
        // Assert all 21 sound constants match 6502 EFFECTS.TXT Z.PRIOR and channel assignments
        assert_eq!(SOUND_NONE, 0);
        assert_eq!(SOUND_HIT_PLAYER, 1);
        assert_eq!(SOUND_SHOOT, 2);
        assert_eq!(SOUND_EXPLODE_BOMB, 3);
        assert_eq!(SOUND_OPEN_DOOR, 4);
        assert_eq!(SOUND_PICKUP_OBJECT, 5);
        assert_eq!(SOUND_EAT_FOOD, 6);
        assert_eq!(SOUND_PICK_MONEY, 7);
        assert_eq!(SOUND_HAVE_NONE, 8);
        assert_eq!(SOUND_HIT_MONSTER_1, 9);
        assert_eq!(SOUND_HIT_MONSTER_2, 10);
        assert_eq!(SOUND_HIT_MONSTER_3, 11);
        assert_eq!(SOUND_MONSTER_BITE, 12);
        assert_eq!(SOUND_DEAD_PLAYER, 13);
        assert_eq!(SOUND_WARP_OUT, 14);
        assert_eq!(SOUND_WARP_IN, 15);
        assert_eq!(SOUND_SPAWNING_1, 16);
        assert_eq!(SOUND_SPAWNING_2, 17);
        assert_eq!(SOUND_SPAWNING_3, 18);
        assert_eq!(SOUND_SPAWNING_4, 19);
        assert_eq!(SOUND_TO_HAND, 20);

        // Verify Pokey Channels
        assert_eq!(sound_pokey_channel(SOUND_SPAWNING_1), 1);
        assert_eq!(sound_pokey_channel(SOUND_SPAWNING_2), 1);
        assert_eq!(sound_pokey_channel(SOUND_SPAWNING_3), 1);
        assert_eq!(sound_pokey_channel(SOUND_SPAWNING_4), 1);
        assert_eq!(sound_pokey_channel(SOUND_TO_HAND), 0);
        assert_eq!(sound_pokey_channel(SOUND_HAVE_NONE), 0);

        // Verify Priorities
        assert_eq!(sound_priority(SOUND_SPAWNING_1), 55);
        assert_eq!(sound_priority(SOUND_SPAWNING_2), 55);
        assert_eq!(sound_priority(SOUND_SPAWNING_3), 55);
        assert_eq!(sound_priority(SOUND_SPAWNING_4), 55);
        assert_eq!(sound_priority(SOUND_TO_HAND), 30);
        assert_eq!(sound_priority(SOUND_HAVE_NONE), 20);
    }

    #[test]
    fn test_movement_followed_by_shoot_sound_emission() {
        let mut game = Game::new();
        game.load();
        let px = 10;
        let py = 10;
        game.map.set(game.players[0].x, game.players[0].y, SPACE);
        game.players[0].x = px;
        game.players[0].y = py;
        game.players[0].dir = 2; // East
        game.map.set(px, py, PLAYER);
        let (tx, ty) = calculate_target_cog(&game.players);
        game.camera.cog_x = tx as f64;
        game.camera.cog_y = ty as f64;
        for x in (px - 5)..=(px + 5) {
            for y in (py - 5)..=(py + 5) {
                if (x, y) != (px, py) {
                    game.map.set(x, y, SPACE);
                }
            }
        }

        // 1. Step player to the right (move action)
        game.players[0].input_mask = ACTION_RIGHT;
        game.step();
        assert_eq!(game.players[0].x, px + 1);
        assert_eq!(game.players[0].move_cooldown, PLAYER_MOVE_INTERVAL as u8);

        // 2. Clear input and let movement cooldown complete
        game.players[0].input_mask = 0;
        for _ in 0..PLAYER_MOVE_INTERVAL {
            game.step();
        }
        assert_eq!(game.players[0].move_cooldown, 0);

        // 3. Fire arrow immediately after moving
        game.players[0].input_mask = ACTION_SHOOT;
        game.step();

        // Must emit SOUND_SHOOT in sounds vector and schedule on channel 0
        assert!(game.players[0].arrow.is_some(), "Arrow must be spawned");
        assert!(game.sounds.contains(&SOUND_SHOOT), "SOUND_SHOOT must be emitted immediately upon shooting after movement");
        assert!(game.audio_scheduler.is_channel_active(0), "Channel 0 must be active for SOUND_SHOOT");
        assert_eq!(game.audio_scheduler.get_channel_sound(0), SOUND_SHOOT);
    }
}

