#![allow(dead_code)]
// Network Protocol Version & Application ID
pub const NET_PROTOCOL_VERSION: u16 = 1;
pub const NET_APP_ID: &str = "dandy-dungeon";

// Game Constants
pub const TILE_SIZE: i32 = 16;
pub const MAP_WIDTH: i32 = 60;
pub const MAP_HEIGHT: i32 = 30;
pub const VIEWPORT_WIDTH: i32 = 20;
pub const VIEWPORT_HEIGHT: i32 = 10;

// Retro Screen Size for SM-PIE
pub const SCREEN_WIDTH: usize = 320;
pub const SCREEN_HEIGHT: usize = 160;

// Tile Constants
pub const SPACE: u8 = 0;
pub const WALL: u8 = 1;
pub const LOCK: u8 = 2;
pub const UP: u8 = 3;
pub const DOWN: u8 = 4;
pub const KEY: u8 = 5;
pub const FOOD: u8 = 6;
pub const MONEY: u8 = 7;
pub const BOMB: u8 = 8;
pub const GHOST: u8 = 9; // 9, 10, 11
pub const HEART: u8 = 12;
pub const GENERATOR: u8 = 13; // 13, 14, 15
pub const ARROW: u8 = 16; // 16..23
pub const PLAYER: u8 = 24; // 24..27

// Movement Directions: 0 is Up, clockwise (0..7)
pub const DIR_TO_DELTA: [(i32, i32); 8] = [
    (0, -1),  // 0: Up
    (1, -1),  // 1: Up-Right
    (1, 0),   // 2: Right
    (1, 1),   // 3: Down-Right
    (0, 1),   // 4: Down
    (-1, 1),  // 5: Down-Left
    (-1, 0),  // 6: Left
    (-1, -1), // 7: Up-Left
];

// Player spawn directions: P1 (North/Up), P2 (East/Right), P3 (South/Down), P4 (West/Left)
pub const PLAYER_SPAWN_DIRS: [usize; 4] = [0, 2, 4, 6];

pub const MAX_PLAYERS: usize = 4;
pub const PLAYER_NAMES: [&str; 4] = ["Ruby", "Sapphire", "Topaz", "Emerald"];
pub const PLAYER_COLORS: [&str; 4] = ["#ef5350", "#42a5f5", "#ffca28", "#66bb6a"]; // Red (Ruby), Blue (Sapphire), Yellow (Topaz), Green (Emerald)

// Player logical input actions (Bitmask)
pub const ACTION_UP: u8 = 1 << 0;
pub const ACTION_DOWN: u8 = 1 << 1;
pub const ACTION_LEFT: u8 = 1 << 2;
pub const ACTION_RIGHT: u8 = 1 << 3;
pub const ACTION_SHOOT: u8 = 1 << 4;
pub const ACTION_BOMB: u8 = 1 << 5;

// Speed and Timing Constants (60 Hz Fixed Timestep)
pub const PLAYER_MOVE_INTERVAL: u32 = 8; // 1 tile every 8 frames (7.5 tiles/sec, 6502 fractional $20/256 speed)
pub const ARROW_MOVE_INTERVAL: u32 = 4;  // 1 tile every 4 frames (15.0 tiles/sec, 2.0x player velocity)

// 4-Level Difficulty Delays: Trivial (13), Easy (8), Hard (5), Deadly (2)
pub const DIFFICULTY_DELAYS: [u32; 4] = [13, 8, 5, 2];

// Sound Effect IDs (matching 6502 Atari 8-Bit EFFECTS.TXT)
pub const SOUND_NONE: u8 = 0;
pub const SOUND_HIT_PLAYER: u8 = 1;      // Z.HIT.PLAYER
pub const SOUND_SHOOT: u8 = 2;           // Z.SHOOT
pub const SOUND_EXPLODE_BOMB: u8 = 3;    // Z.EXPLODE.BOMB
pub const SOUND_OPEN_DOOR: u8 = 4;       // Z.OPEN.DOOR
pub const SOUND_PICKUP_OBJECT: u8 = 5;   // Z.PICKUP.OBJECT
pub const SOUND_EAT_FOOD: u8 = 6;        // Z.EAT.FOOD
pub const SOUND_PICK_MONEY: u8 = 7;      // Z.PICK.MONEY
pub const SOUND_HAVE_NONE: u8 = 8;       // Z.HAVE.NONE / hit wall thud
pub const SOUND_HIT_WALL: u8 = 8;        // Backward-compatibility alias
pub const SOUND_HIT_MONSTER_1: u8 = 9;   // Z.HIT.MONSTER.1 (AUDF 193)
pub const SOUND_HIT_MONSTER_2: u8 = 10;  // Z.HIT.MONSTER.2 (AUDF 217)
pub const SOUND_HIT_MONSTER_3: u8 = 11;  // Z.HIT.MONSTER.3 (AUDF 243)
pub const SOUND_MONSTER_BITE: u8 = 12;   // Z.MONSTER.BITE
pub const SOUND_DEAD_PLAYER: u8 = 13;    // Z.DEAD.PLAYER
pub const SOUND_WARP_OUT: u8 = 14;       // Z.WARP.OUT
pub const SOUND_WARP_IN: u8 = 15;        // Z.WARP.IN
pub const SOUND_SPAWNING_1: u8 = 16;     // Z.SPAWNING.1 (AUDF 64)
pub const SOUND_HIT_GENERATOR: u8 = 16;  // Backward-compatibility alias
pub const SOUND_SPAWNING_2: u8 = 17;     // Z.SPAWNING.2 (AUDF 81)
pub const SOUND_SPAWNING_3: u8 = 18;     // Z.SPAWNING.3 (AUDF 96)
pub const SOUND_SPAWNING_4: u8 = 19;     // Z.SPAWNING.4 (AUDF 121)
pub const SOUND_TO_HAND: u8 = 20;        // Z.TO.HAND

// Sound Priority Ranking (Higher value = Higher Priority)
pub fn sound_priority(sound_id: u8) -> u8 {
    match sound_id {
        SOUND_EXPLODE_BOMB => 100,
        SOUND_DEAD_PLAYER => 95,
        SOUND_WARP_OUT => 90,
        SOUND_WARP_IN => 85,
        SOUND_MONSTER_BITE => 75,
        SOUND_HIT_PLAYER => 70,
        SOUND_EAT_FOOD => 65,
        SOUND_OPEN_DOOR => 60,
        SOUND_SPAWNING_1 | SOUND_SPAWNING_2 | SOUND_SPAWNING_3 | SOUND_SPAWNING_4 => 55,
        SOUND_HIT_MONSTER_3 => 50,
        SOUND_HIT_MONSTER_2 => 48,
        SOUND_HIT_MONSTER_1 => 45,
        SOUND_PICK_MONEY => 40,
        SOUND_PICKUP_OBJECT => 35,
        SOUND_TO_HAND => 30,
        SOUND_HAVE_NONE => 20,
        SOUND_SHOOT => 15,
        _ => 0,
    }
}

// Preferred Hardware POKEY Channel (0..3) matching 6502 Atari 8-Bit EFFECTS.TXT Z.PRIOR
pub fn sound_pokey_channel(sound_id: u8) -> usize {
    match sound_id {
        // Channel 3: Explosions, Death, Warp in/out
        SOUND_EXPLODE_BOMB | SOUND_DEAD_PLAYER | SOUND_WARP_OUT | SOUND_WARP_IN => 3,
        // Channel 2: Monster Bite
        SOUND_MONSTER_BITE => 2,
        // Channel 1: Impacts, monster hits, player hits, generator spawning
        SOUND_HIT_PLAYER
        | SOUND_HIT_MONSTER_1
        | SOUND_HIT_MONSTER_2
        | SOUND_HIT_MONSTER_3
        | SOUND_SPAWNING_1
        | SOUND_SPAWNING_2
        | SOUND_SPAWNING_3
        | SOUND_SPAWNING_4 => 1,
        // Channel 0: Ambient / Items / Shooting / Doors / Walls / To Hand
        SOUND_SHOOT
        | SOUND_OPEN_DOOR
        | SOUND_PICKUP_OBJECT
        | SOUND_EAT_FOOD
        | SOUND_PICK_MONEY
        | SOUND_HAVE_NONE
        | SOUND_TO_HAND => 0,
        _ => 0,
    }
}

// Sound duration in 60 Hz frames
pub fn sound_duration_frames(sound_id: u8) -> u32 {
    match sound_id {
        SOUND_EXPLODE_BOMB => 25, // ~416ms
        SOUND_DEAD_PLAYER => 60,  // ~1000ms
        SOUND_WARP_OUT => 30,     // ~500ms
        SOUND_WARP_IN => 30,      // ~500ms
        SOUND_MONSTER_BITE => 15, // ~250ms
        SOUND_HIT_PLAYER => 3,    // ~50ms
        SOUND_EAT_FOOD => 30,     // ~500ms
        SOUND_OPEN_DOOR => 10,    // ~166ms
        SOUND_SPAWNING_1 | SOUND_SPAWNING_2 | SOUND_SPAWNING_3 | SOUND_SPAWNING_4 => 5, // ~83ms
        SOUND_HIT_MONSTER_1 | SOUND_HIT_MONSTER_2 | SOUND_HIT_MONSTER_3 => 10, // ~166ms
        SOUND_PICK_MONEY => 15,   // ~250ms
        SOUND_PICKUP_OBJECT => 10,// ~166ms
        SOUND_TO_HAND => 30,      // ~500ms
        SOUND_HAVE_NONE => 5,     // ~83ms
        SOUND_SHOOT => 5,         // ~83ms
        _ => 0,
    }
}

pub const NUM_POKEY_CHANNELS: usize = 4;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct PokeyVoice {
    pub sound_id: u8,
    pub priority: u8,
    pub remaining_frames: u32,
    pub age: u32,
}

impl PokeyVoice {
    pub const fn empty() -> Self {
        Self {
            sound_id: SOUND_NONE,
            priority: 0,
            remaining_frames: 0,
            age: 0,
        }
    }

    pub fn is_active(&self) -> bool {
        self.sound_id != SOUND_NONE && self.remaining_frames > 0
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct PokeyAudioScheduler {
    pub channels: [PokeyVoice; NUM_POKEY_CHANNELS],
}

impl Default for PokeyAudioScheduler {
    fn default() -> Self {
        Self::new()
    }
}

impl PokeyAudioScheduler {
    pub fn new() -> Self {
        Self {
            channels: [PokeyVoice::empty(); NUM_POKEY_CHANNELS],
        }
    }

    pub fn is_channel_active(&self, ch: usize) -> bool {
        if ch < NUM_POKEY_CHANNELS {
            self.channels[ch].is_active()
        } else {
            false
        }
    }

    pub fn get_channel_sound(&self, ch: usize) -> u8 {
        if ch < NUM_POKEY_CHANNELS && self.channels[ch].is_active() {
            self.channels[ch].sound_id
        } else {
            SOUND_NONE
        }
    }

    pub fn tick_frame(&mut self) {
        for voice in &mut self.channels {
            if voice.is_active() {
                voice.age += 1;
                if voice.remaining_frames > 0 {
                    voice.remaining_frames -= 1;
                }
                if voice.remaining_frames == 0 {
                    *voice = PokeyVoice::empty();
                }
            }
        }
    }

    /// Schedule a sound event.
    /// Allocates an idle channel (preferring hardware POKEY channel if idle, then any idle channel).
    /// If all channels are busy:
    ///   - Finds the channel playing the lowest-priority sound (breaking ties by oldest playing sound).
    ///   - If incoming sound priority >= that channel's priority, PREEMPTS that channel.
    ///   - Otherwise, drops the sound (returns None).
    ///
    /// Returns Some(channel_index) if allocated/preempted, or None if dropped.
    pub fn schedule_sound(&mut self, sound_id: u8) -> Option<usize> {
        if sound_id == SOUND_NONE {
            return None;
        }

        let priority = sound_priority(sound_id);
        let duration = sound_duration_frames(sound_id);

        // 1. Try preferred POKEY channel first if it is idle
        let preferred_ch = sound_pokey_channel(sound_id);
        if !self.channels[preferred_ch].is_active() {
            self.channels[preferred_ch] = PokeyVoice {
                sound_id,
                priority,
                remaining_frames: duration,
                age: 0,
            };
            return Some(preferred_ch);
        }

        // 2. Try any idle channel
        for ch in 0..NUM_POKEY_CHANNELS {
            if !self.channels[ch].is_active() {
                self.channels[ch] = PokeyVoice {
                    sound_id,
                    priority,
                    remaining_frames: duration,
                    age: 0,
                };
                return Some(ch);
            }
        }

        // 3. All channels busy -> Find channel with lowest priority
        let mut lowest_priority_idx = 0;
        let mut min_priority = self.channels[0].priority;
        let mut oldest_age = self.channels[0].age;

        for ch in 1..NUM_POKEY_CHANNELS {
            let ch_prio = self.channels[ch].priority;
            let ch_age = self.channels[ch].age;
            if ch_prio < min_priority || (ch_prio == min_priority && ch_age > oldest_age) {
                min_priority = ch_prio;
                lowest_priority_idx = ch;
                oldest_age = ch_age;
            }
        }

        // 4. Preempt if incoming priority >= lowest active priority
        if priority >= min_priority {
            self.channels[lowest_priority_idx] = PokeyVoice {
                sound_id,
                priority,
                remaining_frames: duration,
                age: 0,
            };
            Some(lowest_priority_idx)
        } else {
            // Lower priority than all playing sounds -> dropped
            None
        }
    }

    /// Schedule a batch of sound events emitted in a single frame.
    /// Sorts them by priority (highest first) on the stack so highest priority sounds claim channels first.
    pub fn schedule_frame_events(&mut self, events: &[u8]) {
        if events.is_empty() {
            return;
        }
        let mut buf = [0u8; 32];
        let mut len = 0;
        for &s in events {
            if s != SOUND_NONE && len < 32 {
                buf[len] = s;
                len += 1;
            }
        }
        // Tiny in-place insertion sort by descending priority
        for i in 1..len {
            let mut j = i;
            while j > 0 && sound_priority(buf[j]) > sound_priority(buf[j - 1]) {
                buf.swap(j, j - 1);
                j -= 1;
            }
        }
        for &s in &buf[..len] {
            self.schedule_sound(s);
        }
    }
}

