use crate::consts::*;
use crate::entity::{Player, Arrow};
use crate::map::Map;
use crate::camera::ActiveRect;

pub fn do_smart_bomb(
    player: &mut Player,
    map: &mut Map,
    active: ActiveRect,
) {
    let mut score_gain = 0;

    for y in active.top..(active.top + active.height) {
        for x in active.left..(active.left + active.width) {
            let v = map.get(x, y);
            if (GHOST..=GHOST + 2).contains(&v) {
                map.set(x, y, SPACE);
                score_gain += 10 * ((v - GHOST) as i32 + 1);
            }
        }
    }

    player.score += score_gain;
}

pub fn try_move_player(
    index: usize,
    player: &mut Player,
    map: &mut Map,
    dir: usize,
) -> bool {
    player.dir = dir;
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
            }
        }
        DOWN => {
            // Player Escaped!
            map.set(player.x, player.y, SPACE);
            player.escaped = true;
            player.x = -1;
            player.y = -1;
            return true;
        }
        KEY => {
            player.keys += 1;
            moved = true;
        }
        FOOD => {
            player.health += 100;
            moved = true;
        }
        MONEY => {
            player.score += 100;
            moved = true;
        }
        BOMB => {
            player.bombs += 1;
            moved = true;
        }
        _ => {}
    }

    if moved {
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
    player: &mut Player,
    map: &mut Map,
    active_rect: ActiveRect,
) {
    let input = player.input_mask;
    let start_x = player.x;
    let start_y = player.y;

    // 1. Check Smart Bomb
    if (input & ACTION_BOMB) != 0 && player.bombs > 0 {
        player.bombs -= 1;
        do_smart_bomb(player, map, active_rect);
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
        player.dir = d;
    }

    // 2. Check Shoot vs Move
    if (input & ACTION_SHOOT) != 0 {
        if player.arrow.is_none() {
            let shoot_dir = dir_opt.unwrap_or(player.dir);
            player.arrow = Some(Arrow {
                x: start_x,
                y: start_y,
                dir: shoot_dir,
            });
        }
    } else if let Some(d) = dir_opt {
        // Try moving with wall-sliding
        let moved = try_move_player(index, player, map, d);
        if !moved {
            let moved_left = try_move_player(index, player, map, (d + 1) & 7);
            if !moved_left {
                try_move_player(index, player, map, (d + 7) & 7);
            }
        }
    }
}

pub fn step_arrow(
    index: usize,
    players: &mut [Player],
    map: &mut Map,
    active_rect: ActiveRect,
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
                });
                new_v = arrow_val;
                kill_arrow = false;
            }
            GHOST..=11 => {
                // Hit ghost!
                players[index].score += 10;
                if v > GHOST {
                    new_v = v - 1; // Ghost degrades
                }
            }
            HEART => {
                // RESURRECTION!
                new_v = GHOST + 2; // Heart turns into level-3 ghost if nobody resurrected?
                for (p_idx, p) in players.iter_mut().enumerate() {
                    if p.active && !p.alive {
                        p.alive = true;
                        p.x = nx;
                        p.y = ny;
                        p.health = 50; // Resurrect with 50 health
                        new_v = PLAYER + (p_idx as u8);
                        break;
                    }
                }
            }
            BOMB => {
                // Hit a smart bomb tile! Trigger smart bomb
                do_smart_bomb(&mut players[index], map, active_rect);
            }
            _ => {
                // Hit wall / door / player / key / etc. Kill arrow, don't change tile
                new_v = v;
            }
        }

        map.set(nx, ny, new_v);
        if kill_arrow {
            players[index].arrow = None;
        }
    }
}
