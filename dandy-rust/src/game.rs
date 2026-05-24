// Game module for Dandy Dungeon
use crate::consts::*;
use crate::entity::Player;
use crate::map::Map;
use crate::rand::LcgRng;
use crate::camera::{Camera, ActiveRect, calculate_target_cog};

pub struct Game {
    pub map: Map,
    pub players: Vec<Player>,
    pub level: usize,
    pub time: u32,
    pub last_move_time: u32,
    pub rotor: u8,
    
    pub camera: Camera,
    pub rng: LcgRng,
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
            camera: Camera::new(0.0, 0.0),
            rng: LcgRng::new(12345), // Default seed
        }
    }

    pub fn load(&mut self) {
        self.map.load(self.level);
        self.rotor = 0;

        // Find player spawn (stairs UP)
        let spawn = self.map.find(UP).unwrap_or((2, 2));
        
        // Start active players
        for (i, player) in self.players.iter_mut().enumerate() {
            if player.active && i < PLAYER_SPAWN_DIRS.len() {
                let dir = PLAYER_SPAWN_DIRS[i];
                let px = spawn.0 + DIR_TO_DELTA[dir].0;
                let py = spawn.1 + DIR_TO_DELTA[dir].1;
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

            let active_rect = self.get_active_rect();

            // Step each player
            for i in 0..self.players.len() {
                if self.players[i].active && self.players[i].alive && !self.players[i].escaped {
                    // Borrow only the single player mutably to satisfy borrow checker and API cleanliness
                    let player = &mut self.players[i];
                    crate::physics::step_player(i, player, &mut self.map, active_rect);
                }
            }

            // Step arrows for all active players unconditionally
            for i in 0..self.players.len() {
                if self.players[i].active {
                    crate::physics::step_arrow(i, &mut self.players, &mut self.map, active_rect);
                }
            }

            crate::ai::step_enemies(&mut self.map, &mut self.players, active_rect, &mut self.rotor, &mut self.rng);

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

                // 4. Ghosts inside visible viewport
                if (GHOST..=GHOST + 2).contains(&v)
                    && !crate::ai::is_ghost_blocked(x, y, &self.map, &self.players)
                {
                    return false;
                }

                // 5. Generators inside visible viewport
                if (GENERATOR..=GENERATOR + 2).contains(&v)
                    && !crate::ai::is_generator_blocked(x, y, &self.map)
                {
                    return false;
                }
            }
        }

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
        let (tx, ty) = calculate_target_cog(&game.players);
        game.camera.cog_x = tx as f64;
        game.camera.cog_y = ty as f64;

        // Wasm can now sleep
        assert!(game.can_sleep());
    }
}
