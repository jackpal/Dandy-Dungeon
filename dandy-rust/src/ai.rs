use crate::consts::*;
use crate::entity::Player;
use crate::map::Map;
use crate::camera::ActiveRect;
use crate::rand::LcgRng;

pub fn step_enemies(
    map: &mut Map,
    players: &mut [Player],
    active: ActiveRect,
    rotor: &mut u8,
    rng: &mut LcgRng,
) {
    *rotor = (*rotor + 1) & 3;
    
    let rx = (*rotor & 1) as i32;
    let ry = ((*rotor >> 1) & 1) as i32;

    let x_start = ((active.left + 1) & !1) + rx;
    let y_start = ((active.top + 1) & !1) + ry;
    let x_end = active.left + active.width;
    let y_end = active.top + active.height;

    let mut y = y_start;
    while y < y_end {
        let mut x = x_start;
        while x < x_end {
            let v = map.get(x, y);
            if (GHOST..=GHOST + 2).contains(&v) {
                step_ghost(x, y, v, map, players);
            } else if (GENERATOR..=GENERATOR + 2).contains(&v) {
                step_generator(x, y, v, map, rng);
            }
            x += 2;
        }
        y += 2;
    }
}

pub fn step_ghost(
    gx: i32,
    gy: i32,
    ghost_val: u8,
    map: &mut Map,
    players: &mut [Player],
) {
    // Find closest active & alive player
    let mut best_p_idx = None;
    let mut best_dist = None;
    
    for (i, p) in players.iter().enumerate() {
        if p.active && p.alive && !p.escaped {
            let dist = (p.x - gx).abs() + (p.y - gy).abs();
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

    let px = players[p_idx].x;
    let py = players[p_idx].y;
    
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

        let nv = map.get(nx, ny);
        if nv == SPACE {
            map.set(gx, gy, SPACE);
            map.set(nx, ny, ghost_val);
            break;
        } else if (PLAYER..=PLAYER + 3).contains(&nv) {
            // Hurt player!
            let p_index = (nv - PLAYER) as usize;
            let pain = 10 * (ghost_val - GHOST + 1) as i32;
            hurt_player(p_index, pain, map, players);
            map.set(gx, gy, SPACE);
            break;
        } else if (ARROW..=ARROW + 7).contains(&nv) {
            // Ghost freezes when walking into an arrow
            break;
        }
    }
}

pub fn hurt_player(
    index: usize,
    pain: i32,
    map: &mut Map,
    players: &mut [Player],
) {
    if players[index].health > pain {
        players[index].health -= pain;
    } else {
        players[index].health = 0;
        players[index].alive = false;
        
        // If player dies, drop a key if they had keys
        let remains = if players[index].keys > 0 {
            players[index].keys -= 1;
            KEY
        } else {
            SPACE
        };
        map.set(players[index].x, players[index].y, remains);
    }
}

pub fn step_generator(
    gx: i32,
    gy: i32,
    gen_val: u8,
    map: &mut Map,
    rng: &mut LcgRng,
) {
    // 30% spawn rate
    let ran = rng.next();
    if ran < 0.3 {
        // Pick random cardinal direction: 0, 2, 4, 6
        let dir = ((rng.next() * 4.0).floor() as usize) * 2;
        let delta = DIR_TO_DELTA[dir];
        let nx = gx + delta.0;
        let ny = gy + delta.1;

        if map.get(nx, ny) == SPACE {
            // Spawn ghost corresponding to generator level
            let new_ghost = GHOST + (gen_val - GENERATOR);
            map.set(nx, ny, new_ghost);
        }
    }
}

pub fn is_ghost_blocked(
    gx: i32,
    gy: i32,
    map: &Map,
    players: &[Player],
) -> bool {
    // Find closest active & alive & non-escaped player
    let mut best_p_idx = None;
    let mut best_dist = None;
    
    for (i, p) in players.iter().enumerate() {
        if p.active && p.alive && !p.escaped {
            let dist = (p.x - gx).abs() + (p.y - gy).abs();
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

    let px = players[p_idx].x;
    let py = players[p_idx].y;
    
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

        let nv = map.get(nx, ny);
        if nv == SPACE || (PLAYER..=PLAYER + 3).contains(&nv) {
            return false;
        } else if (ARROW..=ARROW + 7).contains(&nv) {
            return true; // Frozen arrow stops search immediately and freezes the ghost
        }
    }

    true
}

pub fn is_generator_blocked(
    gx: i32,
    gy: i32,
    map: &Map,
) -> bool {
    for dir in [0, 2, 4, 6] {
        let delta = DIR_TO_DELTA[dir];
        let nx = gx + delta.0;
        let ny = gy + delta.1;
        if map.get(nx, ny) == SPACE {
            return false;
        }
    }
    true
}
