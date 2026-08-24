// Rollback netcode and multi-peer prediction buffer for Dandy Dungeon
use crate::consts::*;
use crate::game::{Game, GameSnapshot};

pub const MAX_ROLLBACK_FRAMES: usize = 64;
pub const INPUT_HISTORY_BUFFER_SIZE: usize = 256;

// Packet Types
pub const PKT_INPUT: u8 = 0x01;
pub const PKT_PING: u8 = 0x02;
pub const PKT_PONG: u8 = 0x03;
pub const PKT_STATE_SYNC: u8 = 0x04;
pub const PKT_JOIN: u8 = 0x05;
pub const PKT_LEAVE: u8 = 0x06;

#[derive(Clone, Copy, Debug)]
pub struct InputEntry {
    pub frame: u32,
    pub mask: u8,
    pub confirmed: bool,
}

impl Default for InputEntry {
    fn default() -> Self {
        Self {
            frame: 0,
            mask: 0,
            confirmed: false,
        }
    }
}

pub struct RollbackManager {
    pub local_player_idx: usize,
    pub current_frame: u32,
    pub confirmed_frame: u32,
    pub rollback_count: u32,
    pub resimulated_frames_total: u32,

    // Ring buffer of snapshots: (frame_num, snapshot)
    pub snapshot_history: Vec<(u32, GameSnapshot)>,

    // Per-player input history table: player_inputs[player_idx][frame % INPUT_HISTORY_BUFFER_SIZE]
    pub input_history: [[InputEntry; INPUT_HISTORY_BUFFER_SIZE]; MAX_PLAYERS],

    // Last known confirmed input per player for prediction
    pub last_known_input: [u8; MAX_PLAYERS],

    // Active joined status per player slot
    pub player_joined: [bool; MAX_PLAYERS],
}

impl RollbackManager {
    pub fn new(local_player_idx: usize, initial_game: &Game) -> Self {
        let input_history = [[InputEntry::default(); INPUT_HISTORY_BUFFER_SIZE]; MAX_PLAYERS];

        let mut player_joined = [false; MAX_PLAYERS];
        if local_player_idx < MAX_PLAYERS {
            player_joined[local_player_idx] = true;
        }

        let mut manager = Self {
            local_player_idx,
            current_frame: 0,
            confirmed_frame: 0,
            rollback_count: 0,
            resimulated_frames_total: 0,
            snapshot_history: Vec::with_capacity(MAX_ROLLBACK_FRAMES + 4),
            input_history,
            last_known_input: [0; MAX_PLAYERS],
            player_joined,
        };

        // Record initial state at frame 0
        manager.snapshot_history.push((0, initial_game.save_state()));
        manager
    }

    pub fn reset(&mut self, local_player_idx: usize, initial_game: &Game) {
        self.local_player_idx = local_player_idx;
        self.current_frame = 0;
        self.confirmed_frame = 0;
        self.rollback_count = 0;
        self.resimulated_frames_total = 0;
        self.snapshot_history.clear();
        self.snapshot_history.push((0, initial_game.save_state()));

        for p in 0..MAX_PLAYERS {
            for entry in &mut self.input_history[p] {
                entry.frame = 0;
                entry.mask = 0;
                entry.confirmed = false;
            }
            self.last_known_input[p] = 0;
            self.player_joined[p] = p == local_player_idx;
        }
    }

    pub fn sync_state(&mut self, frame: u32, game: &Game) {
        self.current_frame = frame;
        self.confirmed_frame = frame;
        self.snapshot_history.clear();
        self.snapshot_history.push((frame, game.save_state()));

        for p in 0..MAX_PLAYERS {
            for entry in &mut self.input_history[p] {
                entry.frame = 0;
                entry.mask = 0;
                entry.confirmed = false;
            }
            self.last_known_input[p] = 0;
            self.player_joined[p] = game.players[p].active;
        }

        if self.local_player_idx < MAX_PLAYERS {
            self.player_joined[self.local_player_idx] = true;
        }
    }

    pub fn oldest_snapshot_frame(&self) -> u32 {
        self.snapshot_history.first().map(|(f, _)| *f).unwrap_or(self.current_frame)
    }

    pub fn set_player_joined(&mut self, player_idx: usize, joined: bool) {
        if player_idx < MAX_PLAYERS {
            self.player_joined[player_idx] = joined;
        }
    }

    pub fn is_player_joined(&self, player_idx: usize) -> bool {
        if player_idx < MAX_PLAYERS {
            self.player_joined[player_idx]
        } else {
            false
        }
    }

    pub fn set_local_input(&mut self, frame: u32, mask: u8) {
        let p = self.local_player_idx;
        if p < MAX_PLAYERS {
            let slot = (frame as usize) % INPUT_HISTORY_BUFFER_SIZE;
            self.input_history[p][slot] = InputEntry {
                frame,
                mask,
                confirmed: true,
            };
            self.last_known_input[p] = mask;
            self.player_joined[p] = true;
        }
    }

    pub fn get_input(&self, player_idx: usize, frame: u32) -> u8 {
        if player_idx >= MAX_PLAYERS {
            return 0;
        }
        let slot = (frame as usize) % INPUT_HISTORY_BUFFER_SIZE;
        let entry = &self.input_history[player_idx][slot];
        if entry.frame == frame {
            entry.mask
        } else {
            // Predicted fallback
            self.last_known_input[player_idx]
        }
    }

    /// Receives confirmed remote input for `(peer_idx, frame, mask)`.
    /// Returns true if a rollback re-simulation was performed.
    pub fn receive_remote_input(
        &mut self,
        peer_idx: usize,
        frame: u32,
        mask: u8,
        game: &mut Game,
    ) -> bool {
        if peer_idx >= MAX_PLAYERS || peer_idx == self.local_player_idx {
            return false;
        }

        self.player_joined[peer_idx] = true;

        // Ignore inputs that are older than our oldest retained snapshot
        if frame < self.oldest_snapshot_frame() {
            return false;
        }

        // Ignore inputs too far in the future
        if frame > self.current_frame + (MAX_ROLLBACK_FRAMES as u32) {
            return false;
        }

        let slot = (frame as usize) % INPUT_HISTORY_BUFFER_SIZE;
        let prev_entry = &self.input_history[peer_idx][slot];
        let was_different = (prev_entry.frame == frame && prev_entry.mask != mask)
            || (prev_entry.frame != frame && self.last_known_input[peer_idx] != mask);

        // Store the confirmed input
        self.input_history[peer_idx][slot] = InputEntry {
            frame,
            mask,
            confirmed: true,
        };
        self.last_known_input[peer_idx] = mask;

        let mut did_rollback = false;

        // If the frame is in the past and our prediction differed, we MUST rollback and resimulate
        if frame < self.current_frame && was_different {
            did_rollback = self.execute_rollback(frame, game);
        }

        self.update_confirmed_frame();
        did_rollback
    }

    /// Receives redundant packet `(peer_idx, frame, curr_mask, prev_mask)` and performs at most ONE rollback.
    pub fn receive_remote_packet(
        &mut self,
        peer_idx: usize,
        frame: u32,
        curr_mask: u8,
        prev_mask: u8,
        game: &mut Game,
    ) -> bool {
        if peer_idx >= MAX_PLAYERS || peer_idx == self.local_player_idx {
            return false;
        }
        self.player_joined[peer_idx] = true;

        let oldest_snap = self.oldest_snapshot_frame();
        let mut min_rollback_frame = None;

        // 1. Process frame - 1 (redundant previous frame input)
        if frame > 0 && (frame - 1) >= oldest_snap && (frame - 1) <= self.current_frame + (MAX_ROLLBACK_FRAMES as u32) {
            let prev_f = frame - 1;
            let slot = (prev_f as usize) % INPUT_HISTORY_BUFFER_SIZE;
            let entry = &self.input_history[peer_idx][slot];
            let diff = (entry.frame == prev_f && entry.mask != prev_mask)
                || (entry.frame != prev_f && self.last_known_input[peer_idx] != prev_mask);

            self.input_history[peer_idx][slot] = InputEntry {
                frame: prev_f,
                mask: prev_mask,
                confirmed: true,
            };

            if prev_f < self.current_frame && diff {
                min_rollback_frame = Some(prev_f);
            }
        }

        // 2. Process current frame input
        if frame >= oldest_snap && frame <= self.current_frame + (MAX_ROLLBACK_FRAMES as u32) {
            let slot = (frame as usize) % INPUT_HISTORY_BUFFER_SIZE;
            let entry = &self.input_history[peer_idx][slot];
            let diff = (entry.frame == frame && entry.mask != curr_mask)
                || (entry.frame != frame && self.last_known_input[peer_idx] != curr_mask);

            self.input_history[peer_idx][slot] = InputEntry {
                frame,
                mask: curr_mask,
                confirmed: true,
            };
            self.last_known_input[peer_idx] = curr_mask;

            if frame < self.current_frame && diff {
                min_rollback_frame = Some(match min_rollback_frame {
                    Some(f) => f.min(frame),
                    None => frame,
                });
            }
        }

        let did_rollback = if let Some(rb_frame) = min_rollback_frame {
            self.execute_rollback(rb_frame, game)
        } else {
            false
        };

        self.update_confirmed_frame();
        did_rollback
    }

    /// Rollback the game to snapshot at `rollback_to_frame` and re-simulate to `self.current_frame`.
    fn execute_rollback(&mut self, rollback_to_frame: u32, game: &mut Game) -> bool {
        // Find snapshot at or before rollback_to_frame
        let mut target_idx = None;
        for (i, (f, _)) in self.snapshot_history.iter().enumerate() {
            if *f == rollback_to_frame {
                target_idx = Some(i);
                break;
            }
        }

        let snap_idx = match target_idx {
            Some(i) => i,
            None => {
                let mut best_i = None;
                for (i, (f, _)) in self.snapshot_history.iter().enumerate() {
                    if *f <= rollback_to_frame {
                        best_i = Some(i);
                    } else {
                        break;
                    }
                }
                match best_i {
                    Some(i) => i,
                    None => return false,
                }
            }
        };

        let (snap_frame, ref snapshot) = self.snapshot_history[snap_idx];
        game.load_state(snapshot);
        self.rollback_count += 1;

        // Truncate future snapshots after snap_frame
        self.snapshot_history.truncate(snap_idx + 1);

        // Re-simulate ticks from snap_frame to current_frame
        let end_frame = self.current_frame;
        for f in snap_frame..end_frame {
            // Apply inputs for each player at frame f
            for p in 0..MAX_PLAYERS {
                if self.player_joined[p] {
                    let slot = (f as usize) % INPUT_HISTORY_BUFFER_SIZE;
                    let input_to_apply = if self.input_history[p][slot].frame == f {
                        self.input_history[p][slot].mask
                    } else {
                        let pred = self.last_known_input[p];
                        self.input_history[p][slot] = InputEntry {
                            frame: f,
                            mask: pred,
                            confirmed: false,
                        };
                        pred
                    };
                    game.players[p].input_mask = input_to_apply;
                }
            }

            // Step game simulation
            game.step();
            game.update_camera();
            self.resimulated_frames_total += 1;

            // Record updated snapshot for f + 1
            self.snapshot_history.push((f + 1, game.save_state()));
        }

        true
    }

    /// Steps one frame forward in time, applying local and predicted remote inputs.
    pub fn step_frame(&mut self, game: &mut Game) -> u32 {
        let frame = self.current_frame;

        // Apply inputs for all players, recording predicted inputs in history
        for p in 0..MAX_PLAYERS {
            if self.player_joined[p] {
                let slot = (frame as usize) % INPUT_HISTORY_BUFFER_SIZE;
                let mask = if self.input_history[p][slot].frame == frame {
                    self.input_history[p][slot].mask
                } else {
                    let pred = self.last_known_input[p];
                    self.input_history[p][slot] = InputEntry {
                        frame,
                        mask: pred,
                        confirmed: false,
                    };
                    pred
                };
                game.players[p].input_mask = mask;
            }
        }

        // Step simulation and camera
        game.step();
        game.update_camera();

        self.current_frame += 1;

        // Store snapshot for the new frame
        self.snapshot_history.push((self.current_frame, game.save_state()));

        // Prune oldest snapshots beyond MAX_ROLLBACK_FRAMES
        if self.snapshot_history.len() > MAX_ROLLBACK_FRAMES {
            let overflow = self.snapshot_history.len() - MAX_ROLLBACK_FRAMES;
            self.snapshot_history.drain(0..overflow);
        }

        self.current_frame
    }

    fn update_confirmed_frame(&mut self) {
        let mut min_confirmed = self.current_frame;
        let mut any_peer = false;

        for p in 0..MAX_PLAYERS {
            if p != self.local_player_idx && self.player_joined[p] {
                any_peer = true;
                let mut peer_confirmed = 0;
                let oldest = self.oldest_snapshot_frame();
                for f in oldest..=self.current_frame {
                    let slot = (f as usize) % INPUT_HISTORY_BUFFER_SIZE;
                    let entry = &self.input_history[p][slot];
                    if entry.frame == f && entry.confirmed {
                        peer_confirmed = f;
                    } else {
                        break;
                    }
                }
                if peer_confirmed < min_confirmed {
                    min_confirmed = peer_confirmed;
                }
            }
        }

        if any_peer {
            self.confirmed_frame = min_confirmed;
        } else {
            self.confirmed_frame = self.current_frame;
        }
    }
}

// -----------------------------------------------------------------------------
// Network Packet Encoding / Decoding with Redundant Inputs
// -----------------------------------------------------------------------------

/// Encodes an input packet with 2 frames of redundancy:
/// [PKT_INPUT(1), player_idx(1), frame(4, BE), current_mask(1), prev_mask(1)] = 8 bytes
pub fn encode_input_packet(player_idx: u8, frame: u32, current_mask: u8, prev_mask: u8) -> [u8; 8] {
    let f_bytes = frame.to_be_bytes();
    [
        PKT_INPUT,
        player_idx,
        f_bytes[0],
        f_bytes[1],
        f_bytes[2],
        f_bytes[3],
        current_mask,
        prev_mask,
    ]
}

/// Decodes an input packet: returns (player_idx, frame, current_mask, prev_mask)
pub fn decode_input_packet(bytes: &[u8]) -> Option<(u8, u32, u8, u8)> {
    if bytes.len() < 8 || bytes[0] != PKT_INPUT {
        return None;
    }
    let player_idx = bytes[1];
    let frame = u32::from_be_bytes([bytes[2], bytes[3], bytes[4], bytes[5]]);
    let current_mask = bytes[6];
    let prev_mask = bytes[7];
    Some((player_idx, frame, current_mask, prev_mask))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_packet_encode_decode() {
        let pkt = encode_input_packet(2, 1024, ACTION_UP | ACTION_SHOOT, ACTION_LEFT);
        let decoded = decode_input_packet(&pkt).expect("Should decode");
        assert_eq!(decoded.0, 2);
        assert_eq!(decoded.1, 1024);
        assert_eq!(decoded.2, ACTION_UP | ACTION_SHOOT);
        assert_eq!(decoded.3, ACTION_LEFT);
    }

    #[test]
    fn test_rollback_prediction_and_recovery() {
        let mut game_a = Game::new();
        game_a.load();
        let mut rollback = RollbackManager::new(0, &game_a);

        // Step 10 frames with local inputs only (P2 predicted as 0)
        for f in 0..10 {
            rollback.set_local_input(f, ACTION_RIGHT);
            rollback.step_frame(&mut game_a);
        }
        assert_eq!(rollback.current_frame, 10);
        assert_eq!(rollback.rollback_count, 0);

        // Ground truth: create second game where P2 had ACTION_UP at frame 3
        let mut game_b = Game::new();
        game_b.load();
        for f in 0..10 {
            game_b.players[0].input_mask = ACTION_RIGHT;
            if f == 3 {
                game_b.players[1].input_mask = ACTION_UP;
            } else if f > 3 {
                game_b.players[1].input_mask = ACTION_UP; // Held
            }
            game_b.step();
            game_b.update_camera();
        }

        // Now send delayed P2 input for frame 3 to game_a (which is at frame 10)
        let did_rollback = rollback.receive_remote_input(1, 3, ACTION_UP, &mut game_a);
        assert!(did_rollback, "Should execute rollback upon receiving past input");
        assert_eq!(rollback.rollback_count, 1);

        // Verify that after rollback and resimulation, game_a matches game_b state!
        assert_eq!(game_a.level, game_b.level);
        assert_eq!(game_a.time, game_b.time);
        assert_eq!(game_a.map.data, game_b.map.data);
        assert_eq!(game_a.players[0].x, game_b.players[0].x);
        assert_eq!(game_a.players[0].y, game_b.players[0].y);
        assert_eq!(game_a.players[1].x, game_b.players[1].x);
        assert_eq!(game_a.players[1].y, game_b.players[1].y);
    }

    #[test]
    fn test_out_of_order_packet_recovery() {
        let mut game = Game::new();
        game.load();
        let mut rollback = RollbackManager::new(0, &game);

        // Step 12 frames
        for f in 0..12 {
            rollback.set_local_input(f, ACTION_RIGHT);
            rollback.step_frame(&mut game);
        }
        assert_eq!(rollback.current_frame, 12);

        // Frame 8 arrives first
        let rb1 = rollback.receive_remote_input(1, 8, ACTION_UP, &mut game);
        assert!(rb1);

        // Frame 6 arrives AFTER frame 8 (out-of-order delivery)
        let rb2 = rollback.receive_remote_input(1, 6, ACTION_LEFT, &mut game);
        assert!(rb2, "Out of order frame 6 must trigger rollback even though frame 8 arrived earlier");
        assert_eq!(rollback.rollback_count, 2);
    }

    #[test]
    fn test_batch_packet_single_rollback() {
        let mut game = Game::new();
        game.load();
        let mut rollback = RollbackManager::new(0, &game);

        for f in 0..10 {
            rollback.set_local_input(f, ACTION_RIGHT);
            rollback.step_frame(&mut game);
        }

        // Packet with frame 5 (curr: ACTION_UP, prev: ACTION_LEFT for frame 4)
        let did_rb = rollback.receive_remote_packet(1, 5, ACTION_UP, ACTION_LEFT, &mut game);
        assert!(did_rb);
        assert_eq!(rollback.rollback_count, 1, "Should execute exactly one rollback for both redundant frames");
    }
}
