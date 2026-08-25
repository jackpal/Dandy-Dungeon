// Rollback netcode and multi-peer prediction buffer for Dandy Dungeon
use crate::consts::*;
use crate::game::{Game, GameSnapshot};

pub const MAX_ROLLBACK_FRAMES: usize = 64;
pub const INPUT_HISTORY_BUFFER_SIZE: usize = 256;

// Packet Types
pub const PKT_HANDSHAKE: u8 = 0x00;
pub const PKT_INPUT: u8 = 0x01;
pub const PKT_PING: u8 = 0x02;
pub const PKT_PONG: u8 = 0x03;
pub const PKT_STATE_SYNC: u8 = 0x04;
pub const PKT_JOIN: u8 = 0x05;
pub const PKT_LEAVE: u8 = 0x06;
pub const PKT_SET_DIFFICULTY: u8 = 0x07;
pub const PKT_CHECKSUM: u8 = 0x08;
pub const PKT_RESYNC_REQ: u8 = 0x09;

// Handshake Magic Bytes ('D', 'D')
pub const HANDSHAKE_MAGIC_0: u8 = 0x44;
pub const HANDSHAKE_MAGIC_1: u8 = 0x44;

#[derive(Clone, Copy, Debug, Default)]
pub struct InputEntry {
    pub frame: u32,
    pub mask: u8,
    pub confirmed: bool,
}

pub struct RollbackManager {
    pub local_player_mask: u8,
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

    // History of emitted sound bitmasks per frame for rollback sound deduplication
    pub sound_history: [u32; INPUT_HISTORY_BUFFER_SIZE],

    // Queue of pending sounds (accumulated bitmask) to be consumed by audio playback
    pub pending_sound_mask: u32,
}

impl RollbackManager {
    pub fn new(local_player_idx: usize, initial_game: &Game) -> Self {
        let mask = if local_player_idx < MAX_PLAYERS {
            1 << local_player_idx
        } else {
            0
        };
        Self::new_with_mask(mask, initial_game)
    }

    pub fn new_with_mask(local_player_mask: u8, initial_game: &Game) -> Self {
        let input_history = [[InputEntry::default(); INPUT_HISTORY_BUFFER_SIZE]; MAX_PLAYERS];

        let mut player_joined = [false; MAX_PLAYERS];
        for (p, joined) in player_joined.iter_mut().enumerate() {
            if (local_player_mask & (1 << p)) != 0 {
                *joined = true;
            }
        }

        let mut manager = Self {
            local_player_mask,
            current_frame: 0,
            confirmed_frame: 0,
            rollback_count: 0,
            resimulated_frames_total: 0,
            snapshot_history: Vec::with_capacity(MAX_ROLLBACK_FRAMES + 4),
            input_history,
            last_known_input: [0; MAX_PLAYERS],
            player_joined,
            sound_history: [0; INPUT_HISTORY_BUFFER_SIZE],
            pending_sound_mask: 0,
        };

        // Record initial state at frame 0
        manager.snapshot_history.push((0, initial_game.save_state()));
        manager
    }

    pub fn primary_local_player(&self) -> usize {
        for p in 0..MAX_PLAYERS {
            if (self.local_player_mask & (1 << p)) != 0 {
                return p;
            }
        }
        0
    }

    pub fn is_local_player(&self, player_idx: usize) -> bool {
        if player_idx < MAX_PLAYERS {
            (self.local_player_mask & (1 << player_idx)) != 0
        } else {
            false
        }
    }

    pub fn set_local_player(&mut self, player_idx: usize, is_local: bool) {
        if player_idx < MAX_PLAYERS {
            if is_local {
                self.local_player_mask |= 1 << player_idx;
                self.player_joined[player_idx] = true;
            } else {
                self.local_player_mask &= !(1 << player_idx);
            }
        }
    }

    pub fn reset(&mut self, local_player_idx: usize, initial_game: &Game) {
        let mask = if local_player_idx < MAX_PLAYERS {
            1 << local_player_idx
        } else {
            0
        };
        self.reset_mask(mask, initial_game);
    }

    pub fn reset_mask(&mut self, local_player_mask: u8, initial_game: &Game) {
        self.local_player_mask = local_player_mask;
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
            self.player_joined[p] = (local_player_mask & (1 << p)) != 0;
        }
        self.sound_history = [0; INPUT_HISTORY_BUFFER_SIZE];
        self.pending_sound_mask = 0;
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
            self.player_joined[p] = game.players[p].active || self.is_local_player(p) || self.player_joined[p];
        }
        self.sound_history = [0; INPUT_HISTORY_BUFFER_SIZE];
        self.pending_sound_mask = 0;
    }

    pub fn oldest_snapshot_frame(&self) -> u32 {
        self.snapshot_history.first().map(|(f, _)| *f).unwrap_or(self.current_frame)
    }

    pub fn get_checksum_at_frame(&self, frame: u32) -> Option<u32> {
        for (f, snap) in self.snapshot_history.iter().rev() {
            if *f == frame {
                return Some(snap.get_checksum());
            }
        }
        None
    }

    pub fn set_player_joined(&mut self, player_idx: usize, joined: bool) {
        if player_idx < MAX_PLAYERS {
            self.player_joined[player_idx] = joined;
            if !joined && self.is_local_player(player_idx) {
                self.local_player_mask &= !(1 << player_idx);
            }
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
        let p = self.primary_local_player();
        self.set_player_local_input(p, frame, mask);
    }

    pub fn set_player_local_input(&mut self, player_idx: usize, frame: u32, mask: u8) {
        if player_idx < MAX_PLAYERS {
            let slot = (frame as usize) % INPUT_HISTORY_BUFFER_SIZE;
            self.input_history[player_idx][slot] = InputEntry {
                frame,
                mask,
                confirmed: true,
            };
            self.last_known_input[player_idx] = mask;
            self.player_joined[player_idx] = true;
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
        } else if self.is_local_player(player_idx) {
            // Local player unconfirmed frame: fallback to last known local input
            self.last_known_input[player_idx]
        } else {
            // Remote player unconfirmed frame: predict Neutral (0 / No Action)
            // Retro grid-based pacing avoids false tile advances & snap-backs on key release
            0
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
        let prev_mask = if frame > 0 {
            let slot = ((frame - 1) as usize) % INPUT_HISTORY_BUFFER_SIZE;
            let entry = &self.input_history[peer_idx][slot];
            if entry.frame == frame - 1 {
                entry.mask
            } else {
                0
            }
        } else {
            mask
        };
        self.receive_remote_packet(peer_idx, frame, mask, prev_mask, game)
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
        self.receive_remote_packets(&[(peer_idx, frame, curr_mask, prev_mask)], game)
    }

    /// Receives a batch of remote inputs and executes at most ONE rollback across all of them.
    pub fn receive_remote_packets(
        &mut self,
        packets: &[(usize, u32, u8, u8)],
        game: &mut Game,
    ) -> bool {
        let oldest_snap = self.oldest_snapshot_frame();
        let max_f = self.current_frame + (MAX_ROLLBACK_FRAMES as u32);
        let mut min_rollback_frame: Option<u32> = None;

        for &(peer_idx, frame, curr_mask, prev_mask) in packets {
            if peer_idx >= MAX_PLAYERS || self.is_local_player(peer_idx) {
                continue;
            }
            self.player_joined[peer_idx] = true;

            let ingest = |f: u32, mask: u8, min_rb: &mut Option<u32>, history: &mut [[InputEntry; INPUT_HISTORY_BUFFER_SIZE]; MAX_PLAYERS], cur_f: u32| {
                if f >= oldest_snap && f <= max_f {
                    let slot = (f as usize) % INPUT_HISTORY_BUFFER_SIZE;
                    let entry = &history[peer_idx][slot];
                    let diff = (entry.frame == f && entry.mask != mask)
                        || (entry.frame != f && mask != 0);

                    history[peer_idx][slot] = InputEntry {
                        frame: f,
                        mask,
                        confirmed: true,
                    };

                    if f < cur_f && diff {
                        *min_rb = Some(match *min_rb {
                            Some(c) => c.min(f),
                            None => f,
                        });
                    }
                }
            };

            if frame > 0 {
                ingest(frame - 1, prev_mask, &mut min_rollback_frame, &mut self.input_history, self.current_frame);
            }
            ingest(frame, curr_mask, &mut min_rollback_frame, &mut self.input_history, self.current_frame);
            self.last_known_input[peer_idx] = curr_mask;
        }

        let did_rollback = if let Some(rb_frame) = min_rollback_frame {
            self.execute_rollback(rb_frame, game)
        } else {
            false
        };

        self.update_confirmed_frame();
        did_rollback
    }

    fn apply_inputs_and_step(&mut self, game: &mut Game, frame: u32) {
        for p in 0..MAX_PLAYERS {
            if self.player_joined[p] {
                if !game.players[p].active {
                    game.spawn_player(p);
                }
                let slot = (frame as usize) % INPUT_HISTORY_BUFFER_SIZE;
                let mask = if self.input_history[p][slot].frame == frame {
                    self.input_history[p][slot].mask
                } else {
                    let pred = if self.is_local_player(p) {
                        self.last_known_input[p]
                    } else {
                        // Remote player prediction: 0 (Neutral / No Action)
                        // Prevents overshooting into subsequent tiles on key release
                        0
                    };
                    self.input_history[p][slot] = InputEntry {
                        frame,
                        mask: pred,
                        confirmed: false,
                    };
                    pred
                };
                game.players[p].input_mask = mask;
            } else {
                game.players[p].input_mask = 0;
            }
        }
        game.step();
        game.update_camera();
    }

    /// Rollback the game to snapshot at `rollback_to_frame` and re-simulate to `self.current_frame`.
    fn execute_rollback(&mut self, rollback_to_frame: u32, game: &mut Game) -> bool {
        // Find snapshot at or before rollback_to_frame
        let snap_idx = match self
            .snapshot_history
            .iter()
            .rposition(|(f, _)| *f <= rollback_to_frame)
        {
            Some(i) => i,
            None => return false,
        };

        let (snap_frame, ref snapshot) = self.snapshot_history[snap_idx];
        game.load_state(snapshot);
        self.rollback_count += 1;

        // Truncate future snapshots after snap_frame
        self.snapshot_history.truncate(snap_idx + 1);

        // Re-simulate ticks from snap_frame to current_frame
        let end_frame = self.current_frame;
        for f in snap_frame..end_frame {
            self.apply_inputs_and_step(game, f);
            self.resimulated_frames_total += 1;

            let mut sound_mask = 0u32;
            for &s in &game.sounds {
                if s > 0 && s < 32 {
                    sound_mask |= 1 << s;
                }
            }
            let slot = (f as usize) % INPUT_HISTORY_BUFFER_SIZE;
            let old_mask = self.sound_history[slot];
            let diff_mask = sound_mask & (!old_mask);
            self.pending_sound_mask |= diff_mask;
            self.sound_history[slot] = sound_mask;

            self.snapshot_history.push((f + 1, game.save_state()));
        }

        true
    }

    /// Steps one frame forward in time, applying local and predicted remote inputs.
    pub fn step_frame(&mut self, game: &mut Game) -> u32 {
        let frame = self.current_frame;
        self.apply_inputs_and_step(game, frame);

        let mut sound_mask = 0u32;
        for &s in &game.sounds {
            if s > 0 && s < 32 {
                sound_mask |= 1 << s;
            }
        }
        self.sound_history[(frame as usize) % INPUT_HISTORY_BUFFER_SIZE] = sound_mask;
        self.pending_sound_mask |= sound_mask;

        self.current_frame += 1;

        self.snapshot_history.push((self.current_frame, game.save_state()));
        if self.snapshot_history.len() > MAX_ROLLBACK_FRAMES {
            self.snapshot_history.remove(0);
        }

        self.current_frame
    }

    fn update_confirmed_frame(&mut self) {
        let mut min_confirmed = self.current_frame;
        let mut any_peer = false;

        for p in 0..MAX_PLAYERS {
            if !self.is_local_player(p) && self.player_joined[p] {
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

/// Encodes a checksum verification packet:
/// [PKT_CHECKSUM(1), frame(4, BE), checksum(4, BE)] = 9 bytes
pub fn encode_checksum_packet(frame: u32, checksum: u32) -> [u8; 9] {
    let f_bytes = frame.to_be_bytes();
    let c_bytes = checksum.to_be_bytes();
    [
        PKT_CHECKSUM,
        f_bytes[0], f_bytes[1], f_bytes[2], f_bytes[3],
        c_bytes[0], c_bytes[1], c_bytes[2], c_bytes[3],
    ]
}

/// Decodes a checksum verification packet: returns (frame, checksum)
pub fn decode_checksum_packet(bytes: &[u8]) -> Option<(u32, u32)> {
    if bytes.len() < 9 || bytes[0] != PKT_CHECKSUM {
        return None;
    }
    let frame = u32::from_be_bytes([bytes[1], bytes[2], bytes[3], bytes[4]]);
    let checksum = u32::from_be_bytes([bytes[5], bytes[6], bytes[7], bytes[8]]);
    Some((frame, checksum))
}

/// Encodes a resync request packet:
/// [PKT_RESYNC_REQ(1), peer_idx(1), frame(4, BE)] = 6 bytes
pub fn encode_resync_req_packet(peer_idx: u8, frame: u32) -> [u8; 6] {
    let f_bytes = frame.to_be_bytes();
    [
        PKT_RESYNC_REQ,
        peer_idx,
        f_bytes[0], f_bytes[1], f_bytes[2], f_bytes[3],
    ]
}

/// Decodes a resync request packet: returns (peer_idx, frame)
pub fn decode_resync_req_packet(bytes: &[u8]) -> Option<(u8, u32)> {
    if bytes.len() < 6 || bytes[0] != PKT_RESYNC_REQ {
        return None;
    }
    let peer_idx = bytes[1];
    let frame = u32::from_be_bytes([bytes[2], bytes[3], bytes[4], bytes[5]]);
    Some((peer_idx, frame))
}

/// Encodes a binary DataChannel handshake packet:
/// [PKT_HANDSHAKE(1), MAGIC_0(1), MAGIC_1(1), VERSION_HI(1), VERSION_LO(1)] = 5 bytes
pub fn encode_handshake_packet(protocol_version: u16) -> [u8; 5] {
    let v_bytes = protocol_version.to_be_bytes();
    [
        PKT_HANDSHAKE,
        HANDSHAKE_MAGIC_0,
        HANDSHAKE_MAGIC_1,
        v_bytes[0],
        v_bytes[1],
    ]
}

/// Decodes a handshake packet: returns Some(protocol_version) if valid format and magic, or None
pub fn decode_handshake_packet(bytes: &[u8]) -> Option<u16> {
    if bytes.len() < 5 || bytes[0] != PKT_HANDSHAKE || bytes[1] != HANDSHAKE_MAGIC_0 || bytes[2] != HANDSHAKE_MAGIC_1 {
        return None;
    }
    let version = u16::from_be_bytes([bytes[3], bytes[4]]);
    Some(version)
}

/// Validates whether a packet is a valid handshake matching NET_PROTOCOL_VERSION
pub fn validate_handshake_packet(bytes: &[u8]) -> bool {
    decode_handshake_packet(bytes) == Some(NET_PROTOCOL_VERSION)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_handshake_packet_encode_decode() {
        let pkt = encode_handshake_packet(NET_PROTOCOL_VERSION);
        assert_eq!(pkt.len(), 5);
        assert_eq!(pkt[0], PKT_HANDSHAKE);
        assert_eq!(pkt[1], HANDSHAKE_MAGIC_0);
        assert_eq!(pkt[2], HANDSHAKE_MAGIC_1);
        assert_eq!(u16::from_be_bytes([pkt[3], pkt[4]]), NET_PROTOCOL_VERSION);

        let decoded = decode_handshake_packet(&pkt).expect("Should decode valid handshake");
        assert_eq!(decoded, NET_PROTOCOL_VERSION);
        assert!(validate_handshake_packet(&pkt), "Should validate matching protocol version");

        // Version mismatch packet
        let v99_pkt = encode_handshake_packet(99);
        assert_eq!(decode_handshake_packet(&v99_pkt), Some(99));
        assert!(!validate_handshake_packet(&v99_pkt), "v99 must fail validation against current version");

        // Corrupt magic
        let mut corrupt_magic = pkt;
        corrupt_magic[1] = 0x58; // 'X'
        assert_eq!(decode_handshake_packet(&corrupt_magic), None);
        assert!(!validate_handshake_packet(&corrupt_magic));

        // Wrong packet type
        let mut wrong_type = pkt;
        wrong_type[0] = PKT_INPUT;
        assert_eq!(decode_handshake_packet(&wrong_type), None);

        // Short buffer
        assert_eq!(decode_handshake_packet(&pkt[..4]), None);
        assert_eq!(decode_handshake_packet(&[]), None);
    }

    #[test]
    fn test_packet_encode_decode() {
        let pkt = encode_input_packet(2, 1024, ACTION_UP | ACTION_SHOOT, ACTION_LEFT);
        let decoded = decode_input_packet(&pkt).expect("Should decode");
        assert_eq!(decoded.0, 2);
        assert_eq!(decoded.1, 1024);
        assert_eq!(decoded.2, ACTION_UP | ACTION_SHOOT);
        assert_eq!(decoded.3, ACTION_LEFT);

        let cs_pkt = encode_checksum_packet(120, 0x12345678);
        let (f, cs) = decode_checksum_packet(&cs_pkt).expect("Should decode checksum pkt");
        assert_eq!(f, 120);
        assert_eq!(cs, 0x12345678);

        let resync_pkt = encode_resync_req_packet(1, 120);
        let (p, f_resync) = decode_resync_req_packet(&resync_pkt).expect("Should decode resync pkt");
        assert_eq!(p, 1);
        assert_eq!(f_resync, 120);
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

        // Ground truth: create second game where P2 had ACTION_UP tap at frame 3 (0 for all other frames)
        let mut game_b = Game::new();
        game_b.load();
        for f in 0..10 {
            game_b.players[0].input_mask = ACTION_RIGHT;
            if f == 3 {
                game_b.players[1].input_mask = ACTION_UP;
            } else {
                game_b.players[1].input_mask = 0;
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
    fn test_remote_neutral_prediction_no_overshoot_on_key_release() {
        let mut host_game = Game::new();
        host_game.load();
        host_game.spawn_player(1);
        let mut host_rollback = RollbackManager::new(0, &host_game);
        host_rollback.set_player_joined(1, true);

        let initial_p2_y = host_game.players[1].y;

        // P2 presses Down for 8 frames (frames 0..7) to complete exactly 1 tile movement,
        // then releases key (0) for frames 8..15.
        // Deliver frames 0..7 to host:
        for f in 0..8 {
            host_rollback.set_local_input(f, 0);
            host_rollback.receive_remote_input(1, f, ACTION_DOWN, &mut host_game);
            host_rollback.step_frame(&mut host_game);
        }

        // At frame 8, P2 has moved exactly 1 tile Down (y = initial_p2_y + 1)
        assert_eq!(host_game.players[1].y, initial_p2_y + 1);

        // Now host steps ahead 5 unconfirmed frames (frames 8..12) while P2 release packets are in flight.
        // Under Neutral prediction (0), host should NOT predict ACTION_DOWN and NOT advance P2 into tile + 2.
        for f in 8..13 {
            host_rollback.set_local_input(f, 0);
            host_rollback.step_frame(&mut host_game);
        }
        assert_eq!(host_rollback.current_frame, 13);
        // Player 2 must remain firmly on initial_p2_y + 1 without overshooting
        assert_eq!(host_game.players[1].y, initial_p2_y + 1, "P2 must not overshoot into next tile under neutral prediction");

        // When the release packet for frame 8 (mask = 0) arrives at frame 13:
        let did_rollback = host_rollback.receive_remote_input(1, 8, 0, &mut host_game);
        // Since prediction was already 0, NO rollback occurs!
        assert!(!did_rollback, "Packet matching neutral prediction 0 should not trigger rollback");
        assert_eq!(host_game.players[1].y, initial_p2_y + 1, "P2 position must remain stable with zero visual jump-back");
    }

    #[test]
    fn test_action_shoot_and_bomb_not_repeated_during_prediction() {
        let mut host_game = Game::new();
        host_game.load();
        host_game.spawn_player(1);
        let mut host_rollback = RollbackManager::new(0, &host_game);
        host_rollback.set_player_joined(1, true);

        // Deliver frame 0 with ACTION_SHOOT
        host_rollback.set_local_input(0, 0);
        host_rollback.receive_remote_input(1, 0, ACTION_SHOOT, &mut host_game);
        host_rollback.step_frame(&mut host_game);

        // Step 10 frames under prediction (unconfirmed frames 1..10)
        for f in 1..11 {
            host_rollback.set_local_input(f, 0);
            host_rollback.step_frame(&mut host_game);
            // Verify that for all predicted frames, P2 input_mask was 0 (never repeating SHOOT)
            assert_eq!(host_rollback.get_input(1, f), 0, "Remote SHOOT must not be repeated during prediction");
        }
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

    #[test]
    fn test_hybrid_multi_local_rollback() {
        let mut game_a = Game::new();
        game_a.load();
        game_a.spawn_player(1);
        game_a.spawn_player(2);
        game_a.spawn_player(3);

        // Host controls P1 (slot 0) and P2 (slot 1) locally
        let mut host_rollback = RollbackManager::new_with_mask(0b0011, &game_a);
        host_rollback.set_player_joined(2, true);
        host_rollback.set_player_joined(3, true);

        // Step 10 frames on Host: P1 moves Right, P2 moves Down
        for f in 0..10 {
            host_rollback.set_player_local_input(0, f, ACTION_RIGHT);
            host_rollback.set_player_local_input(1, f, ACTION_DOWN);
            host_rollback.step_frame(&mut game_a);
        }
        assert_eq!(host_rollback.current_frame, 10);
        assert_eq!(host_rollback.rollback_count, 0);

        // Remote peer (controlling P3 slot 2 and P4 slot 3) sends delayed inputs for frame 4
        let rb_p3 = host_rollback.receive_remote_input(2, 4, ACTION_LEFT, &mut game_a);
        assert!(rb_p3, "Delayed remote P3 input must trigger rollback on Host");
        assert_eq!(host_rollback.rollback_count, 1);

        let rb_p4 = host_rollback.receive_remote_input(3, 4, ACTION_UP, &mut game_a);
        assert!(rb_p4, "Delayed remote P4 input must trigger rollback on Host");
        assert_eq!(host_rollback.rollback_count, 2);

        // Ensure host local slots (0 and 1) were not overridden by remote receive
        assert!(!host_rollback.receive_remote_input(0, 4, ACTION_UP, &mut game_a), "Host cannot receive remote input for local slot 0");
        assert!(!host_rollback.receive_remote_input(1, 4, ACTION_UP, &mut game_a), "Host cannot receive remote input for local slot 1");
    }

    #[test]
    fn test_multi_local_host_p1_p3_with_remote_p2_resimulation_and_parity() {
        let mut host_game = Game::new();
        host_game.load();
        host_game.spawn_player(2); // Spawn P3 (slot 2)

        // Host has P1 (slot 0) and P3 (slot 2) local
        let mut host_rollback = RollbackManager::new_with_mask(0b0101, &host_game);
        assert!(host_rollback.is_local_player(0));
        assert!(!host_rollback.is_local_player(1));
        assert!(host_rollback.is_local_player(2));
        assert!(!host_rollback.is_local_player(3));

        // Step 5 frames on Host before remote P2 connects
        for f in 0..5 {
            host_rollback.set_player_local_input(0, f, ACTION_RIGHT);
            host_rollback.set_player_local_input(2, f, ACTION_LEFT);
            host_rollback.step_frame(&mut host_game);
        }
        assert_eq!(host_rollback.current_frame, 5);
        assert!(host_game.players[0].active);
        assert!(!host_game.players[1].active);
        assert!(host_game.players[2].active);

        // Now remote P2 joins! Host receives remote input for P2 starting at frame 2
        let did_rb = host_rollback.receive_remote_input(1, 2, ACTION_DOWN, &mut host_game);
        assert!(did_rb, "Receiving remote P2 input for frame 2 must trigger rollback");

        // Verify that after rollback re-simulation, all 3 players (0, 1, 2) are active on Host!
        assert!(host_game.players[0].active, "P1 must remain active on Host");
        assert!(host_game.players[1].active, "P2 must be active after remote join/rollback");
        assert!(host_game.players[2].active, "P3 must remain active on Host");
        assert_eq!(host_rollback.current_frame, 5);
    }

    #[test]
    fn test_delayed_remote_shoot_sound_emitted_in_rollback_without_duplication() {
        let mut host_game = Game::new();
        host_game.load();
        host_game.spawn_player(1); // Spawn P2 (slot 1)

        let mut host_rollback = RollbackManager::new(0, &host_game);
        host_rollback.set_player_joined(1, true);

        // Step 5 frames on Host (frames 0..5)
        for f in 0..5 {
            host_rollback.set_local_input(f, ACTION_RIGHT);
            host_rollback.step_frame(&mut host_game);
        }
        assert_eq!(host_rollback.current_frame, 5);

        // Drain any pending sounds from forward steps
        host_rollback.pending_sound_mask = 0;

        // Remote P2's ACTION_SHOOT arrives for frame 0 with 5 frames of latency
        let did_rb = host_rollback.receive_remote_input(1, 0, ACTION_SHOOT, &mut host_game);
        assert!(did_rb, "Delayed shoot packet must trigger rollback");

        // Verify that SOUND_SHOOT is present in pending_sound_mask
        let shoot_bit = 1 << SOUND_SHOOT;
        assert_ne!(
            host_rollback.pending_sound_mask & shoot_bit,
            0,
            "SOUND_SHOOT bit must be queued in pending_sound_mask during rollback resimulation"
        );

        // Step another frame forward (frame 5) and ensure sound mask is tracked in history
        let frame_after = host_rollback.step_frame(&mut host_game);
        assert_eq!(frame_after, 6);

        // An identical redundant packet for frame 0 arriving later must NOT re-trigger rollback or duplicate sound
        let did_rb_again = host_rollback.receive_remote_input(1, 0, ACTION_SHOOT, &mut host_game);
        assert!(!did_rb_again, "Redundant confirmed shoot packet must not trigger rollback again");
    }
}
