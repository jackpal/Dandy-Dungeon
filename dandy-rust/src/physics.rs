use crate::consts::*;
use crate::entity::{Player, Arrow};
use crate::map::Map;
use crate::camera::ActiveRect;

fn is_arrow_passable(v: u8) -> bool {
    matches!(v, SPACE | GHOST..=11 | GENERATOR..=15 | HEART | BOMB)
}

fn score_arrow_direction(player_x: i32, player_y: i32, dir: usize, map: &Map) -> (bool, i32) {
    let delta = DIR_TO_DELTA[dir];
    let first_x = player_x + delta.0;
    let first_y = player_y + delta.1;
    let first_v = map.get(first_x, first_y);

    if !is_arrow_passable(first_v) {
        return (false, 0);
    }

    // Direct neighbor is passable. Count potential targets down line of sight (up to 12 tiles)
    let mut target_score = 0;
    let mut cx = first_x;
    let mut cy = first_y;
    for dist in 1..=12 {
        let v = map.get(cx, cy);
        match v {
            GHOST..=11 => {
                target_score += 20 - dist;
            }
            GENERATOR..=15 => {
                target_score += 30 - dist;
            }
            SPACE => {}
            _ => break,
        }
        cx += delta.0;
        cy += delta.1;
    }

    (true, target_score)
}

pub fn adjust_shoot_direction(
    player_x: i32,
    player_y: i32,
    desired_dir: usize,
    facing_dir: usize,
    map: &Map,
) -> usize {
    let delta = DIR_TO_DELTA[desired_dir];
    let direct_v = map.get(player_x + delta.0, player_y + delta.1);

    // If direct direction is passable (open space or enemy/spawner/heart/bomb), keep original aim
    if is_arrow_passable(direct_v) {
        return desired_dir;
    }

    // If desired direction was diagonal (1, 3, 5, 7) and is blocked right in front of the player:
    // Try wall-slide aim assist to the two adjacent cardinal directions
    if desired_dir % 2 != 0 {
        let dir_cw = (desired_dir + 1) & 7;   // e.g. Up-Right (1) -> Right (2)
        let dir_ccw = (desired_dir + 7) & 7;  // e.g. Up-Right (1) -> Up (0)

        let (passable_cw, score_cw) = score_arrow_direction(player_x, player_y, dir_cw, map);
        let (passable_ccw, score_ccw) = score_arrow_direction(player_x, player_y, dir_ccw, map);

        if passable_cw && !passable_ccw {
            return dir_cw;
        }
        if passable_ccw && !passable_cw {
            return dir_ccw;
        }
        if passable_cw && passable_ccw {
            // Both directions are open:
            // 1. Pick direction with enemies/spawners down line of sight
            if score_cw > score_ccw {
                return dir_cw;
            } else if score_ccw > score_cw {
                return dir_ccw;
            }
            // 2. Pick direction matching player's current walking / facing direction
            if facing_dir == dir_cw {
                return dir_cw;
            }
            if facing_dir == dir_ccw {
                return dir_ccw;
            }
            // Default to clockwise cardinal
            return dir_cw;
        }
    }

    desired_dir
}

pub fn do_smart_bomb(
    player: &mut Player,
    map: &mut Map,
    active: ActiveRect,
    sounds: &mut Vec<u8>,
) {
    let mut score_gain = 0;

    for y in active.top..(active.top + active.height) {
        for x in active.left..(active.left + active.width) {
            let v = map.get(x, y);
            if (GHOST..=GHOST + 2).contains(&v) {
                map.set(x, y, SPACE);
                score_gain += 10 * ((v - GHOST) as i32 + 1);
            } else if (GENERATOR..=GENERATOR + 2).contains(&v) {
                map.set(x, y, SPACE);
                score_gain += 100 * ((v - GENERATOR) as i32 + 1);
            }
        }
    }

    player.score += score_gain;
    sounds.push(SOUND_EXPLODE_BOMB);
}

pub fn try_move_player(
    index: usize,
    player: &mut Player,
    map: &mut Map,
    dir: usize,
    sounds: &mut Vec<u8>,
) -> bool {
    let delta = DIR_TO_DELTA[dir];
    let nx = player.x + delta.0;
    let ny = player.y + delta.1;

    let v = map.get(nx, ny);
    let mut moved = false;

    match v {
        SPACE => { moved = true; }
        LOCK => {
            if player.keys > 0 {
                player.keys -= 1;
                map.unlock(nx, ny);
                moved = true;
                sounds.push(SOUND_OPEN_DOOR);
            } else {
                sounds.push(SOUND_HAVE_NONE);
            }
        }
        DOWN => {
            // Player Escaped!
            player.dir = dir;
            map.set(player.x, player.y, SPACE);
            player.escaped = true;
            player.x = -1;
            player.y = -1;
            sounds.push(SOUND_WARP_OUT);
            return true;
        }
        KEY => {
            player.keys += 1;
            moved = true;
            sounds.push(SOUND_PICKUP_OBJECT);
        }
        FOOD => {
            player.health += 100;
            moved = true;
            sounds.push(SOUND_EAT_FOOD);
        }
        MONEY => {
            player.score += 100;
            moved = true;
            sounds.push(SOUND_PICK_MONEY);
        }
        BOMB => {
            player.bombs += 1;
            moved = true;
            sounds.push(SOUND_PICKUP_OBJECT);
        }
        _ => {}
    }

    if moved {
        player.dir = dir;
        // Erase old position
        map.set(player.x, player.y, SPACE);
        // Set new position
        player.x = nx;
        player.y = ny;
        map.set(nx, ny, PLAYER + (index as u8));
    }

    moved
}

pub fn step_player(
    index: usize,
    players: &mut [Player],
    map: &mut Map,
    active_rect: ActiveRect,
    sounds: &mut Vec<u8>,
) {
    if index >= players.len() { return; }
    let input = players[index].input_mask;

    // 1. Check Smart Bomb
    if (input & ACTION_BOMB) != 0 {
        if players[index].bombs > 0 {
            players[index].bombs -= 1;
            do_smart_bomb(&mut players[index], map, active_rect, sounds);
        } else {
            sounds.push(SOUND_HAVE_NONE);
        }
    }

    // Decrement movement cooldown unconditionally each 60 Hz frame if > 0
    if players[index].move_cooldown > 0 {
        players[index].move_cooldown -= 1;
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

    // 2. Check Shoot vs Move
    if (input & ACTION_SHOOT) != 0 {
        if players[index].arrow.is_none() {
            let raw_dir = dir_opt.unwrap_or(players[index].dir);
            let shoot_dir = adjust_shoot_direction(
                players[index].x,
                players[index].y,
                raw_dir,
                players[index].dir,
                map,
            );
            players[index].dir = shoot_dir;
            players[index].arrow = Some(Arrow {
                x: players[index].x,
                y: players[index].y,
                dir: shoot_dir,
                cooldown: ARROW_MOVE_INTERVAL as u8,
            });
            sounds.push(SOUND_SHOOT);
            step_arrow_advance(index, players, map, active_rect, sounds);
        }
    } else if players[index].move_cooldown == 0 {
        if let Some(d) = dir_opt {
            players[index].dir = d;
            // Try moving with wall-sliding
            let moved = try_move_player(index, &mut players[index], map, d, sounds);
            let any_moved = if !moved {
                let moved_left = try_move_player(index, &mut players[index], map, (d + 1) & 7, sounds);
                if !moved_left {
                    try_move_player(index, &mut players[index], map, (d + 7) & 7, sounds)
                } else {
                    true
                }
            } else {
                true
            };
            if any_moved {
                players[index].move_cooldown = PLAYER_MOVE_INTERVAL as u8;
            }
        }
    }
}

pub fn step_arrow_advance(
    index: usize,
    players: &mut [Player],
    map: &mut Map,
    active_rect: ActiveRect,
    sounds: &mut Vec<u8>,
) {
    if index >= players.len() { return; }
    if let Some(a) = players[index].arrow {
        let delta = DIR_TO_DELTA[a.dir];
        let nx = a.x + delta.0;
        let ny = a.y + delta.1;

        // Erase old arrow graphic from map if it matched this arrow
        let current_tile = map.get(a.x, a.y);
        let arrow_val = ARROW + (((a.dir + 3) & 7) as u8);
        if current_tile == arrow_val {
            map.set(a.x, a.y, SPACE);
        }

        // Viewport bounds check: arrow must stay strictly within the visible on-screen viewport
        // (Matching 6502 Atari 8-Bit M.CHECK in MIS.TXT)
        let is_on_screen = nx >= active_rect.left
            && nx < active_rect.left + active_rect.width
            && ny >= active_rect.top
            && ny < active_rect.top + active_rect.height
            && (0..MAP_WIDTH).contains(&nx)
            && (0..MAP_HEIGHT).contains(&ny);

        if !is_on_screen {
            // Reached/crossed the edge of the visible screen! Despawn arrow and free player slot.
            players[index].arrow = None;
            return;
        }

        // Check new position
        let v = map.get(nx, ny);
        let mut new_v = SPACE;
        let mut kill_arrow = true;

        match v {
            SPACE => {
                // Arrow moves forward
                players[index].arrow = Some(Arrow {
                    x: nx,
                    y: ny,
                    dir: a.dir,
                    cooldown: ARROW_MOVE_INTERVAL as u8,
                });
                new_v = arrow_val;
                kill_arrow = false;
            }
            GHOST..=11 => {
                // Hit ghost!
                players[index].score += 10;
                sounds.push(SOUND_HIT_MONSTER_1 + (v - GHOST));
                if v > GHOST {
                    new_v = v - 1; // Ghost degrades
                }
            }
            GENERATOR..=15 => {
                // Hit generator / spawner!
                players[index].score += 200;
                sounds.push(SOUND_HIT_GENERATOR);
                if v > GENERATOR {
                    new_v = v - 1; // Spawner degrades
                }
            }
            HEART => {
                // RESURRECTION!
                sounds.push(SOUND_WARP_IN);
                new_v = GHOST + 2; // Heart turns into level-3 ghost if nobody resurrected
                for (p_idx, p) in players.iter_mut().enumerate() {
                    if p.active && !p.alive {
                        p.alive = true;
                        p.x = nx;
                        p.y = ny;
                        p.health = 50; // Resurrect with 50 health
                        p.move_cooldown = 0;
                        new_v = PLAYER + (p_idx as u8);
                        break;
                    }
                }
            }
            BOMB => {
                // Hit a smart bomb tile! Trigger smart bomb
                map.set(nx, ny, SPACE);
                do_smart_bomb(&mut players[index], map, active_rect, sounds);
                new_v = SPACE;
            }
            PLAYER..=27 => {
                // Friendly fire!
                sounds.push(SOUND_HIT_PLAYER);
                new_v = v;
            }
            _ => {
                // Hit wall / door / item / obstacle. Kill arrow, don't change tile
                sounds.push(SOUND_HIT_WALL);
                new_v = v;
            }
        }

        map.set(nx, ny, new_v);
        if kill_arrow {
            players[index].arrow = None;
        }
    }
}

pub fn step_arrow(
    index: usize,
    players: &mut [Player],
    map: &mut Map,
    active_rect: ActiveRect,
    sounds: &mut Vec<u8>,
) {
    if index >= players.len() { return; }
    if let Some(mut arrow) = players[index].arrow {
        if arrow.cooldown > 0 {
            arrow.cooldown -= 1;
            players[index].arrow = Some(arrow);
        }
        if arrow.cooldown == 0 {
            step_arrow_advance(index, players, map, active_rect, sounds);
        }
    }
}

