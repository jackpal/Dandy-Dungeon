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
        }
    }

    fn find_spawn_tile(&self, spawn: (i32, i32), preferred_dir: usize, player_idx: usize) -> (i32, i32) {
        let delta = DIR_TO_DELTA[preferred_dir];
        let px = spawn.0 + delta.0;
        let py = spawn.1 + delta.1;

        let curr = self.map.get(px, py);
        if curr == SPACE || curr == (PLAYER + player_idx as u8) {
            return (px, py);
        }

        // Find first available adjacent space
        for test_dir in 0..8 {
            let d = DIR_TO_DELTA[test_dir];
            let tx = spawn.0 + d.0;
            let ty = spawn.1 + d.1;
            let v = self.map.get(tx, ty);
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

        let (px, py) = self.find_spawn_tile(spawn, dir, player_idx);

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

        if self.players[player_idx].alive && !self.players[player_idx].escaped {
            if self.map.get(self.players[player_idx].x, self.players[player_idx].y) == (PLAYER + player_idx as u8) {
                self.map.set(self.players[player_idx].x, self.players[player_idx].y, SPACE);
            }
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
                let (px, py) = {
                    let delta = DIR_TO_DELTA[dir];
                    let mut tx = spawn.0 + delta.0;
                    let mut ty = spawn.1 + delta.1;
                    let curr = self.map.get(tx, ty);
                    if curr != SPACE && curr != (PLAYER + i as u8) {
                        for test_dir in 0..8 {
                            let d = DIR_TO_DELTA[test_dir];
                            let candidate_x = spawn.0 + d.0;
                            let candidate_y = spawn.1 + d.1;
                            let v = self.map.get(candidate_x, candidate_y);
                            if v == SPACE || v == (PLAYER + i as u8) {
                                tx = candidate_x;
                                ty = candidate_y;
                                break;
                            }
                        }
                    }
                    (tx, ty)
                };

                player.start(px, py, dir);
                self.map.set(px, py, PLAYER + i as u8);
            }
        }

        // Initialize camera position to spawn
        let (target_x, target_y) = calculate_target_cog(&self.players);
        self.camera.cog_x = target_x as f64;
        self.camera.cog_y = target_y as f64;
    }

    pub fn update_camera(&mut self) {
        let (tx, ty) = calculate_target_cog(&self.players);
        self.camera.update(tx, ty);
    }

    pub fn get_camera_offsets(&self) -> (f64, f64) {
        self.camera.get_offsets()
    }

    pub fn get_active_rect(&self) -> ActiveRect {
        self.camera.get_active_rect()
    }

    pub fn step(&mut self) {
        self.time += 1;

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
                crate::physics::step_arrow(i, &mut self.players, &mut self.map, active_rect);
            }
        }

        // 2. Step players (0 ms immediate start on 60 Hz frame with 8-frame move cooldown & immediate arrow spawn)
        for i in 0..self.players.len() {
            if self.players[i].active && self.players[i].alive && !self.players[i].escaped {
                crate::physics::step_player(i, &mut self.players, &mut self.map, active_rect);
            }
        }

        // 3. Step enemies every DELAY frames according to difficulty (Trivial: 13, Easy: 8, Hard: 5, Deadly: 2)
        if self.time % self.difficulty.delay() == 0 {
            crate::ai::step_enemies(&mut self.map, &mut self.players, active_rect, &mut self.rotor, &mut self.rng);
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
                // Progress to next level
                self.level = (self.level + 1).min(25);
                self.load();
            } else {
                // Everyone died, restart
                self.load();
            }
        }
    }

    pub fn can_sleep(&self) -> bool {
        // 1. No Player Inputs
        if self.players.iter().any(|p| p.input_mask != 0) {
            return false;
        }

        // 2. No Active Move Cooldowns (players completing tile steps)
        if self.players.iter().any(|p| p.active && p.move_cooldown > 0) {
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
        if dx.abs() >= 0.1 || dy.abs() >= 0.1 {
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
        if bytes.len() < 37 || &bytes[0..4] != b"DNDY" || bytes[4] != 1 {
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

        let mut new_players = [
            Player::new(0),
            Player::new(1),
            Player::new(2),
            Player::new(3),
        ];

        for p_idx in 0..num_players.min(MAX_PLAYERS) {
            if offset + 24 > bytes.len() {
                return false;
            }

            let index = bytes[offset] as usize;
            offset += 1;
            let x = read_i32(bytes, &mut offset);
            let y = read_i32(bytes, &mut offset);
            let dir = bytes[offset] as usize;
            offset += 1;
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
                let acooldown = bytes[offset];
                offset += 1;
                Some(crate::entity::Arrow { x: ax, y: ay, dir: adir, cooldown: acooldown })
            } else {
                None
            };

            new_players[p_idx] = Player {
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
                if (v >= GHOST && v <= GHOST + 2) || (v >= GENERATOR && v <= GENERATOR + 2) {
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
                if (v >= GHOST && v <= GHOST + 2) || (v >= GENERATOR && v <= GENERATOR + 2) {
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
                if (v >= GHOST && v <= GHOST + 2) || (v >= GENERATOR && v <= GENERATOR + 2) {
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
                if (v >= GHOST && v <= GHOST + 2) || (v >= GENERATOR && v <= GENERATOR + 2) {
                    game.map.set(x, y, SPACE);
                }
            }
        }
        game.camera.cog_x += 1.0;
        assert!(!game.can_sleep());

        game.camera.cog_x = (calculate_target_cog(&game.players).0 as f64) + 0.05;
        assert!(game.can_sleep());
    }

    #[test]
    fn test_cannot_sleep_unblocked_ghost() {
        let mut game = Game::new();
        game.load();
        for y in 0..MAP_HEIGHT {
            for x in 0..MAP_WIDTH {
                let v = game.map.get(x, y);
                if (v >= GHOST && v <= GHOST + 2) || (v >= GENERATOR && v <= GENERATOR + 2) {
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
                if (v >= GHOST && v <= GHOST + 2) || (v >= GENERATOR && v <= GENERATOR + 2) {
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
                if (v >= GHOST && v <= GHOST + 2) || (v >= GENERATOR && v <= GENERATOR + 2) {
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
}
