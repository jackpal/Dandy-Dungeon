// Game module for Dandy Dungeon
use crate::consts::*;
use crate::entity::{Player, Arrow};
use crate::map::Map;

#[derive(Clone, Copy, Debug)]
pub struct ActiveRect {
    pub left: i32,
    pub top: i32,
    pub width: i32,
    pub height: i32,
}

pub struct Game {
    pub map: Map,
    pub players: Vec<Player>,
    pub level: usize,
    pub time: u32,
    pub last_move_time: u32,
    pub rotor: u8,
    
    // Camera variables
    pub cog_x: f64,
    pub cog_y: f64,

    // Platform-independent PRNG state
    pub rng_state: u32,
}

impl Game {
    pub fn new() -> Self {
        let mut players = Vec::new();
        for i in 0..4 {
            players.push(Player::new(i));
        }
        // Player 1 starts active
        players[0].active = true;
        players[0].alive = true;

        Self {
            map: Map::new(),
            players,
            level: 0,
            time: 0,
            last_move_time: 0,
            rotor: 0,
            cog_x: 0.0,
            cog_y: 0.0,
            rng_state: 12345, // Default seed
        }
    }

    // Platform-independent pseudo-random number generator (LCG)
    pub fn next_random(&mut self) -> f64 {
        self.rng_state = self.rng_state.wrapping_mul(1103515245).wrapping_add(12345);
        let val = (self.rng_state >> 16) & 0x7fff;
        (val as f64) / 32768.0
    }

    pub fn load(&mut self) {
        self.map.load(self.level);
        self.rotor = 0;

        // Find player spawn (stairs UP)
        let spawn = self.map.find(UP).unwrap_or((2, 2));
        
        // Start active players
        for (i, player) in self.players.iter_mut().enumerate() {
            if player.active {
                if i < PLAYER_SPAWN_DIRS.len() {
                    let dir = PLAYER_SPAWN_DIRS[i];
                    let px = spawn.0 + DIR_TO_DELTA[dir].0;
                    let py = spawn.1 + DIR_TO_DELTA[dir].1;
                    player.start(px, py, dir);
                    self.map.set(px, py, PLAYER + i as u8);
                }
            }
        }

        // Initialize camera position to spawn
        let (target_x, target_y) = self.get_target_cog();
        self.cog_x = target_x as f64;
        self.cog_y = target_y as f64;
    }

    pub fn get_target_cog(&self) -> (i32, i32) {
        let mut cog_x = 0;
        let mut cog_y = 0;
        let mut num_active = 0;
        for p in &self.players {
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

    pub fn update_camera(&mut self) {
        let (tx, ty) = self.get_target_cog();
        let max_rate = (TILE_SIZE as f64) / 4.0; // Match 4 pixels per frame
        
        let mut dx = (tx as f64) - self.cog_x;
        let mut dy = (ty as f64) - self.cog_y;
        
        if dx != 0.0 || dy != 0.0 {
            dx = dx.clamp(-max_rate, max_rate);
            dy = dy.clamp(-max_rate, max_rate);
            self.cog_x += dx;
            self.cog_y += dy;
        }
    }

    pub fn get_camera_offsets(&self) -> (f64, f64) {
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
        let (offset_x, offset_y) = self.get_camera_offsets();
        
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

    pub fn step(&mut self) {
        self.time += 1;

        // Handle Player 2 joining dynamically
        if !self.players[1].active {
            let p2_triggered = self.players[1].input_mask != 0;
            
            if p2_triggered {
                self.players[1].active = true;
                self.players[1].alive = true;
                // Spawn P2 exactly 1 tile East of the UP stairs
                let spawn = self.map.find(UP).unwrap_or((2, 2));
                let dir = PLAYER_SPAWN_DIRS[1]; // East/Right (2)
                let px = spawn.0 + DIR_TO_DELTA[dir].0;
                let py = spawn.1 + DIR_TO_DELTA[dir].1;
                self.players[1].start(px, py, dir);
                self.map.set(px, py, PLAYER + 1);
            }
        }

        // Perform steps every TICKS_PER_MOVE frames (4)
        if self.time - self.last_move_time >= 4 {
            self.last_move_time = self.time;

            // Step each player (optimized using primitive local parameters to satisfy borrow checks)
            for i in 0..self.players.len() {
                if self.players[i].active && self.players[i].alive && !self.players[i].escaped {
                    let px = self.players[i].x;
                    let py = self.players[i].y;
                    self.step_player(i, px, py);
                }
            }

            // Step arrows for all active players unconditionally
            for i in 0..self.players.len() {
                if self.players[i].active {
                    self.step_arrow(i);
                }
            }

            self.step_enemies();

            // Centralized Level Progression / Restart Check
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
    }

    fn step_player(&mut self, index: usize, start_x: i32, start_y: i32) {
        if index >= 4 { return; }
        let input = self.players[index].input_mask;

        // 1. Check Smart Bomb
        if (input & ACTION_BOMB) != 0 {
            if self.players[index].bombs > 0 {
                self.players[index].bombs -= 1;
                self.do_smart_bomb(index);
            }
        }

        // Get direction from input mask
        let mut dx = 0;
        let mut dy = 0;
        if (input & ACTION_LEFT) != 0 { dx -= 1; }
        if (input & ACTION_RIGHT) != 0 { dx += 1; }
        if (input & ACTION_UP) != 0 { dy -= 1; }
        if (input & ACTION_DOWN) != 0 { dy += 1; }

        let dir_opt = match (dx, dy) {
            (0, -1) => Some(0),
            (1, -1) => Some(1),
            (1, 0)  => Some(2),
            (1, 1)  => Some(3),
            (0, 1)  => Some(4),
            (-1, 1) => Some(5),
            (-1, 0) => Some(6),
            (-1, -1)=> Some(7),
            _ => None,
        };

        if let Some(d) = dir_opt {
            self.players[index].dir = d;
        }

        // 2. Check Shoot vs Move
        if (input & ACTION_SHOOT) != 0 {
            if self.players[index].arrow.is_none() {
                let shoot_dir = dir_opt.unwrap_or(self.players[index].dir);
                self.players[index].arrow = Some(Arrow {
                    x: start_x,
                    y: start_y,
                    dir: shoot_dir,
                });
            }
        } else if let Some(d) = dir_opt {
            // Try moving with wall-sliding
            let moved = self.try_move_player(index, d);
            if !moved {
                let moved_left = self.try_move_player(index, (d + 1) & 7);
                if !moved_left {
                    self.try_move_player(index, (d + 7) & 7);
                }
            }
        }

        // Arrow stepping moved to central Game::step
    }

    fn try_move_player(&mut self, index: usize, dir: usize) -> bool {
        self.players[index].dir = dir;
        let delta = DIR_TO_DELTA[dir];
        let nx = self.players[index].x + delta.0;
        let ny = self.players[index].y + delta.1;

        let v = self.map.get(nx, ny);
        let mut moved = false;

        match v {
            SPACE => { moved = true; }
            LOCK => {
                if self.players[index].keys > 0 {
                    self.players[index].keys -= 1;
                    self.map.unlock(nx, ny);
                    moved = true;
                }
            }
            DOWN => {
                // Player Escaped!
                self.map.set(self.players[index].x, self.players[index].y, SPACE);
                self.players[index].escaped = true;
                self.players[index].x = -1;
                self.players[index].y = -1;
                return true;
            }
            KEY => {
                self.players[index].keys += 1;
                moved = true;
            }
            FOOD => {
                self.players[index].health += 100;
                moved = true;
            }
            MONEY => {
                self.players[index].score += 100;
                moved = true;
            }
            BOMB => {
                self.players[index].bombs += 1;
                moved = true;
            }
            _ => {}
        }

        if moved {
            // Erase old position
            self.map.set(self.players[index].x, self.players[index].y, SPACE);
            // Set new position
            self.players[index].x = nx;
            self.players[index].y = ny;
            self.map.set(nx, ny, PLAYER + (index as u8));
        }

        moved
    }

    fn step_arrow(&mut self, index: usize) {
        if let Some(a) = self.players[index].arrow {
            let delta = DIR_TO_DELTA[a.dir];
            let nx = a.x + delta.0;
            let ny = a.y + delta.1;

            // Erase old arrow graphic from map if it matched this arrow
            let current_tile = self.map.get(a.x, a.y);
            let arrow_val = ARROW + (((a.dir + 3) & 7) as u8);
            if current_tile == arrow_val {
                self.map.set(a.x, a.y, SPACE);
            }

            // Check new position
            let v = self.map.get(nx, ny);
            let mut new_v = SPACE;
            let mut kill_arrow = true;

            match v {
                SPACE => {
                    // Arrow moves forward
                    self.players[index].arrow = Some(Arrow {
                        x: nx,
                        y: ny,
                        dir: a.dir,
                    });
                    new_v = arrow_val;
                    kill_arrow = false;
                }
                GHOST..=11 => {
                    // Hit ghost!
                    self.players[index].score += 10;
                    if v > GHOST {
                        new_v = v - 1; // Ghost degrades
                    }
                }
                HEART => {
                    // RESURRECTION!
                    new_v = GHOST + 2; // Heart turns into level-3 ghost if nobody resurrected?
                    for p_idx in 0..self.players.len() {
                        if self.players[p_idx].active && !self.players[p_idx].alive {
                            self.players[p_idx].alive = true;
                            self.players[p_idx].x = nx;
                            self.players[p_idx].y = ny;
                            self.players[p_idx].health = 50; // Resurrect with 50 health
                            new_v = PLAYER + (p_idx as u8);
                            break;
                        }
                    }
                }
                BOMB => {
                    // Hit a smart bomb tile! Trigger smart bomb
                    self.do_smart_bomb(index);
                }
                _ => {
                    // Hit wall / door / player / key / etc. Kill arrow, don't change tile
                    new_v = v;
                }
            }

            self.map.set(nx, ny, new_v);
            if kill_arrow {
                self.players[index].arrow = None;
            }
        }
    }

    fn do_smart_bomb(&mut self, player_idx: usize) {
        let active = self.get_active_rect();
        let mut score_gain = 0;

        for y in active.top..(active.top + active.height) {
            for x in active.left..(active.left + active.width) {
                let v = self.map.get(x, y);
                if v >= GHOST && v <= GHOST + 2 {
                    self.map.set(x, y, SPACE);
                    score_gain += 10 * ((v - GHOST) as i32 + 1);
                }
            }
        }

        self.players[player_idx].score += score_gain;
    }

    fn step_enemies(&mut self) {
        let active = self.get_active_rect();
        
        self.rotor = (self.rotor + 1) & 3;
        
        let rx = (self.rotor & 1) as i32;
        let ry = ((self.rotor >> 1) & 1) as i32;

        let x_start = ((active.left + 1) & !1) + rx;
        let y_start = ((active.top + 1) & !1) + ry;
        let x_end = active.left + active.width;
        let y_end = active.top + active.height;

        let mut y = y_start;
        while y < y_end {
            let mut x = x_start;
            while x < x_end {
                let v = self.map.get(x, y);
                if v >= GHOST && v <= GHOST + 2 {
                    self.step_ghost(x, y, v);
                } else if v >= GENERATOR && v <= GENERATOR + 2 {
                    self.step_generator(x, y, v);
                }
                x += 2;
            }
            y += 2;
        }
    }

    fn step_ghost(&mut self, gx: i32, gy: i32, ghost_val: u8) {
        // Find closest active & alive player
        let mut best_p_idx = None;
        let mut best_dist = None;
        
        for i in 0..self.players.len() {
            if self.players[i].active && self.players[i].alive && !self.players[i].escaped {
                let dist = (self.players[i].x - gx).abs() + (self.players[i].y - gy).abs();
                if best_dist.is_none() || dist < best_dist.unwrap() {
                    best_dist = Some(dist);
                    best_p_idx = Some(i);
                }
            }
        }

        let p_idx = match best_p_idx {
            Some(idx) => idx,
            None => return, // No active/alive players
        };

        let px = self.players[p_idx].x;
        let py = self.players[p_idx].y;
        
        // Target direction
        let dx = px - gx;
        let dy = py - gy;
        
        let m_dir = match (dx.signum(), dy.signum()) {
            (0, -1) => 0,
            (1, -1) => 1,
            (1, 0)  => 2,
            (1, 1)  => 3,
            (0, 1)  => 4,
            (-1, 1) => 5,
            (-1, 0) => 6,
            (-1, -1)=> 7,
            _ => 0,
        };

        // Try direct towards player, then left-steer, then right-steer
        let search_order = [0, 7, 1]; // 0, -1, +1
        for offset in search_order {
            let d = (m_dir + offset) & 7;
            let delta = DIR_TO_DELTA[d];
            let nx = gx + delta.0;
            let ny = gy + delta.1;

            let nv = self.map.get(nx, ny);
            if nv == SPACE {
                self.map.set(gx, gy, SPACE);
                self.map.set(nx, ny, ghost_val);
                break;
            } else if nv >= PLAYER && nv <= PLAYER + 3 {
                // Hurt player!
                let p_index = (nv - PLAYER) as usize;
                let pain = 10 * (ghost_val - GHOST + 1) as i32;
                self.hurt_player(p_index, pain);
                self.map.set(gx, gy, SPACE);
                break;
            } else if nv >= ARROW && nv <= ARROW + 7 {
                // Ghost freezes when walking into an arrow
                break;
            }
        }
    }

    fn hurt_player(&mut self, index: usize, pain: i32) {
        if self.players[index].health > pain {
            self.players[index].health -= pain;
        } else {
            self.players[index].health = 0;
            self.players[index].alive = false;
            
            // If player dies, drop a key if they had keys
            let remains = if self.players[index].keys > 0 {
                self.players[index].keys -= 1;
                KEY
            } else {
                SPACE
            };
            self.map.set(self.players[index].x, self.players[index].y, remains);
        }
    }

    fn step_generator(&mut self, gx: i32, gy: i32, gen_val: u8) {
        // 30% spawn rate
        let ran = self.next_random();
        if ran < 0.3 {
            // Pick random cardinal direction: 0, 2, 4, 6
            let dir = ((self.next_random() * 4.0).floor() as usize) * 2;
            let delta = DIR_TO_DELTA[dir];
            let nx = gx + delta.0;
            let ny = gy + delta.1;

            if self.map.get(nx, ny) == SPACE {
                // Spawn ghost corresponding to generator level
                let new_ghost = GHOST + (gen_val - GENERATOR);
                self.map.set(nx, ny, new_ghost);
            }
        }
    }

    pub fn can_sleep(&self) -> bool {
        // 1. No Player Inputs
        if self.players.iter().any(|p| p.input_mask != 0) {
            return false;
        }

        // 2. No Arrows in Flight for active players
        if self.players.iter().any(|p| p.active && p.arrow.is_some()) {
            return false;
        }

        // 3. Camera Arrived
        let (tx, ty) = self.get_target_cog();
        let dx = (tx as f64) - self.cog_x;
        let dy = (ty as f64) - self.cog_y;
        if dx.abs() >= 0.1 || dy.abs() >= 0.1 {
            return false;
        }

        // Viewport active rect
        let active = self.get_active_rect();

        // Check ghosts and generators inside active viewport
        for y in active.top..(active.top + active.height) {
            for x in active.left..(active.left + active.width) {
                let v = self.map.get(x, y);

                // 4. Ghosts inside visible viewport
                if v >= GHOST && v <= GHOST + 2 {
                    if !self.is_ghost_blocked(x, y) {
                        return false;
                    }
                }

                // 5. Generators inside visible viewport
                if v >= GENERATOR && v <= GENERATOR + 2 {
                    if !self.is_generator_blocked(x, y) {
                        return false;
                    }
                }
            }
        }

        true
    }

    fn is_ghost_blocked(&self, gx: i32, gy: i32) -> bool {
        // Find closest active & alive & non-escaped player
        let mut best_p_idx = None;
        let mut best_dist = None;
        
        for i in 0..self.players.len() {
            if self.players[i].active && self.players[i].alive && !self.players[i].escaped {
                let dist = (self.players[i].x - gx).abs() + (self.players[i].y - gy).abs();
                if best_dist.is_none() || dist < best_dist.unwrap() {
                    best_dist = Some(dist);
                    best_p_idx = Some(i);
                }
            }
        }

        let p_idx = match best_p_idx {
            Some(idx) => idx,
            None => return true, // No active/alive players
        };

        let px = self.players[p_idx].x;
        let py = self.players[p_idx].y;
        
        // Target direction
        let dx = px - gx;
        let dy = py - gy;
        
        let m_dir = match (dx.signum(), dy.signum()) {
            (0, -1) => 0,
            (1, -1) => 1,
            (1, 0)  => 2,
            (1, 1)  => 3,
            (0, 1)  => 4,
            (-1, 1) => 5,
            (-1, 0) => 6,
            (-1, -1)=> 7,
            _ => 0,
        };

        // Try direct towards player, then left-steer, then right-steer
        let search_order = [0, 7, 1]; // 0, -1, +1
        for offset in search_order {
            let d = (m_dir + offset) & 7;
            let delta = DIR_TO_DELTA[d];
            let nx = gx + delta.0;
            let ny = gy + delta.1;

            let nv = self.map.get(nx, ny);
            if nv == SPACE {
                return false;
            } else if nv >= PLAYER && nv <= PLAYER + 3 {
                return false;
            } else if nv >= ARROW && nv <= ARROW + 7 {
                return true; // Frozen arrow stops search immediately and freezes the ghost
            }
        }

        true
    }

    fn is_generator_blocked(&self, gx: i32, gy: i32) -> bool {
        for dir in [0, 2, 4, 6] {
            let delta = DIR_TO_DELTA[dir];
            let nx = gx + delta.0;
            let ny = gy + delta.1;
            if self.map.get(nx, ny) == SPACE {
                return false;
            }
        }
        true
    }
}

#[cfg(test)]
mod tests {
    use super::*;

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
        
        // Step game (4 ticks to trigger move)
        for _ in 0..4 {
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
        for _ in 0..4 {
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
        for _ in 0..4 {
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
        for _ in 0..4 {
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
        for _ in 0..4 {
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
        game.players[0].arrow = Some(Arrow { x: 10, y: 10, dir: 0 });
        assert!(!game.can_sleep());

        // Arrow for dead player SHOULD block sleep
        game.players[0].alive = false;
        let (tx, ty) = game.get_target_cog();
        game.cog_x = tx as f64;
        game.cog_y = ty as f64;
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
        game.cog_x += 1.0;
        assert!(!game.can_sleep());

        game.cog_x = (game.get_target_cog().0 as f64) + 0.05;
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
        
        // Step 4 times to trigger movement tick and fire arrow
        for _ in 0..4 {
            game.step();
        }
        
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

        // Step 4 times to trigger next movement tick (arrow hits HEART at px + 2, py)
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
        let (tx, ty) = game.get_target_cog();
        game.cog_x = tx as f64;
        game.cog_y = ty as f64;

        // Wasm can now sleep
        assert!(game.can_sleep());
    }
}
