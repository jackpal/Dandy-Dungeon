// Main entry point for Dandy Dungeon in Rust Wasm
#![allow(dead_code)]
mod consts;
mod entity;
mod map;
mod game;

use consts::*;
use game::Game;
use std::cell::RefCell;
use std::collections::HashSet;
use std::rc::Rc;
use wasm_bindgen::prelude::*;
use wasm_bindgen::JsCast;
use web_sys::{CanvasRenderingContext2d, HtmlCanvasElement, ImageData};

const SPRITESHEET_BYTES: &[u8] = include_bytes!("../assets/dandy.bmp");

#[derive(Clone, Copy)]
struct PlayerHudCache {
    score: i32,
    health: i32,
    keys: i32,
    bombs: i32,
    active: bool,
}

#[wasm_bindgen(start)]
pub fn main_js() -> Result<(), JsValue> {
    console_error_panic_hook::set_once();

    let window = web_sys::window().expect("no global `window` exists");
    let document = window.document().expect("should have a document on window");
    
    // Get game canvas
    let canvas = document
        .get_element_by_id("gameCanvas")
        .expect("should have gameCanvas")
        .dyn_into::<HtmlCanvasElement>()?;
    
    let context = canvas
        .get_context("2d")?
        .expect("should have 2d context")
        .dyn_into::<CanvasRenderingContext2d>()?;
    
    context.set_image_smoothing_enabled(false);

    // Parse BMP and load into offscreen canvas
    let offscreen_canvas = document
        .create_element("canvas")?
        .dyn_into::<HtmlCanvasElement>()?;
    offscreen_canvas.set_width(256);
    offscreen_canvas.set_height(32);
    
    let offscreen_context = offscreen_canvas
        .get_context("2d")?
        .expect("should have offscreen 2d context")
        .dyn_into::<CanvasRenderingContext2d>()?;

    let rgba_data = parse_bmp(SPRITESHEET_BYTES);
    let image_data = ImageData::new_with_u8_clamped_array_and_sh(
        wasm_bindgen::Clamped(&rgba_data),
        256,
        32,
    )?;
    
    offscreen_context.put_image_data(&image_data, 0.0, 0.0)?;

    // Setup keyboard tracking
    let keys = Rc::new(RefCell::new(HashSet::new()));
    
    {
        let keys = keys.clone();
        let closure = Closure::<dyn FnMut(_)>::new(move |event: web_sys::KeyboardEvent| {
            keys.borrow_mut().insert(event.key());
        });
        document.add_event_listener_with_callback("keydown", closure.as_ref().unchecked_ref())?;
        closure.forget();
    }

    {
        let keys = keys.clone();
        let closure = Closure::<dyn FnMut(_)>::new(move |event: web_sys::KeyboardEvent| {
            keys.borrow_mut().remove(&event.key());
        });
        document.add_event_listener_with_callback("keyup", closure.as_ref().unchecked_ref())?;
        closure.forget();
    }

    // Initialize Game
    let mut game = Game::new();
    game.load();

    // Loop hooks
    let f = Rc::new(RefCell::new(None));
    let g = f.clone();

    // Maintain dynamic HUD states
    let mut last_huds = vec![
        PlayerHudCache { score: -1, health: -1, keys: -1, bombs: -1, active: false };
        2
    ];
    last_huds[0].active = true; // Player 1 starts active

    *g.borrow_mut() = Some(Closure::new(move || {
        let current_keys = keys.borrow();
        game.step(&current_keys);

        // Smoothly update camera offsets on every frame
        game.update_camera();

        // Draw scene
        draw_scene(&context, &offscreen_canvas, &game);

        // Generalized HUD Updates for P1 and P2
        for i in 0..2 {
            let player = &game.players[i];
            let last_hud = &mut last_huds[i];
            
            // 1. Dynamic Join/Leave HTML injection (Skip P1 since it is statically in index.html)
            if player.active != last_hud.active {
                if i > 0 {
                    let row_el = document.get_element_by_id(&format!("hud-p{}", i + 1));
                    if let Some(row) = row_el {
                        if player.active {
                            row.set_inner_html(&format!(
                                "<td class=\"text-left\">P{}</td>\
                                 <td id=\"p{}-score\" class=\"text-right\">0</td>\
                                 <td id=\"p{}-health\" class=\"text-right\">100</td>\
                                 <td id=\"p{}-keys\" class=\"text-right\">0</td>\
                                 <td id=\"p{}-bombs\" class=\"text-right\">0</td>",
                                 i + 1, i + 1, i + 1, i + 1, i + 1
                            ));
                        } else {
                            row.set_inner_html(&format!(
                                "<td colspan=\"5\" class=\"hud-p2-inactive\">Player {}: Press WASD/F/G to Join</td>",
                                i + 1
                            ));
                        }
                    }
                }
                last_hud.active = player.active;
                // Force update elements on state change
                last_hud.score = -1;
                last_hud.health = -1;
                last_hud.keys = -1;
                last_hud.bombs = -1;
            }
            
            // 2. Update Metrics text contents if active
            if player.active {
                let metrics = [
                    ("score", player.score, &mut last_hud.score),
                    ("health", player.health, &mut last_hud.health),
                    ("keys", player.keys, &mut last_hud.keys),
                    ("bombs", player.bombs, &mut last_hud.bombs),
                ];
                
                for (suffix, current_val, cached_val) in metrics {
                    if current_val != *cached_val {
                        if let Some(el) = document.get_element_by_id(&format!("p{}-{}", i + 1, suffix)) {
                            el.set_text_content(Some(&current_val.to_string()));
                            *cached_val = current_val;
                        }
                    }
                }
            }
        }

        request_animation_frame(f.borrow().as_ref().unwrap());
    }));

    request_animation_frame(g.borrow().as_ref().unwrap());

    Ok(())
}

fn request_animation_frame(f: &Closure<dyn FnMut()>) {
    web_sys::window()
        .unwrap()
        .request_animation_frame(f.as_ref().unchecked_ref())
        .unwrap();
}

fn draw_scene(context: &CanvasRenderingContext2d, offscreen: &HtmlCanvasElement, game: &Game) {
    let (offset_x, offset_y) = game.get_camera_offsets();
    let active = game.get_active_rect();
    
    // Clear canvas to black
    context.set_fill_style_str("#000000");
    context.fill_rect(0.0, 0.0, 640.0, 320.0);
    
    // Render viewport active grid
    for y in 0..active.height {
        let dy = active.top + y;
        for x in 0..active.width {
            let dx = active.left + x;
            let tile_val = game.map.get(dx, dy);
            
            // Calculate offset in spritesheet (16x16 tiles)
            let tx = ((tile_val & 15) as f64) * 16.0;
            let ty = ((tile_val >> 4) as f64) * 16.0;

            // Double-scaled pixel position
            let dest_x = (offset_x + (dx * TILE_SIZE) as f64) * 2.0;
            let dest_y = (offset_y + (dy * TILE_SIZE) as f64) * 2.0;

            let _ = context.draw_image_with_html_canvas_element_and_sw_and_sh_and_dx_and_dy_and_dw_and_dh(
                offscreen,
                tx, ty, 16.0, 16.0,
                dest_x, dest_y, 32.0, 32.0,
            );
        }
    }
}

fn parse_bmp(bytes: &[u8]) -> Vec<u8> {
    assert_eq!(&bytes[0..2], b"BM");
    
    let data_offset = u32::from_le_bytes(bytes[10..14].try_into().unwrap()) as usize;
    let width = i32::from_le_bytes(bytes[18..22].try_into().unwrap()) as usize;
    let raw_height = i32::from_le_bytes(bytes[22..26].try_into().unwrap());
    let height = raw_height.abs() as usize;
    let top_down = raw_height < 0;
    
    let bpp = u16::from_le_bytes(bytes[28..30].try_into().unwrap());
    assert_eq!(bpp, 24);
    
    let mut rgba = vec![0u8; width * height * 4];
    
    // DWORD alignment padding calculation (each row padded to multiple of 4 bytes)
    let row_stride = (width * 3 + 3) & !3;
    
    for y in 0..height {
        let bmp_y = if top_down { y } else { height - 1 - y };
        let row_start = data_offset + bmp_y * row_stride;
        
        for x in 0..width {
            let px_start = row_start + x * 3;
            let b = bytes[px_start];
            let g = bytes[px_start + 1];
            let r = bytes[px_start + 2];
            
            let rgba_idx = (x + y * width) * 4;
            rgba[rgba_idx] = r;
            rgba[rgba_idx + 1] = g;
            rgba[rgba_idx + 2] = b;
            rgba[rgba_idx + 3] = 255; // Fully opaque
        }
    }
    
    rgba
}
