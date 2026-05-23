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

    // Setup HUD Element caches
    let p1_score_el = document.get_element_by_id("p1-score");
    let p1_health_el = document.get_element_by_id("p1-health");
    let p1_keys_el = document.get_element_by_id("p1-keys");
    let p1_bombs_el = document.get_element_by_id("p1-bombs");

    let hud_p2_el = document.get_element_by_id("hud-p2");

    // Initialize Game
    let mut game = Game::new();
    game.load();

    // Loop hooks
    let f = Rc::new(RefCell::new(None));
    let g = f.clone();

    // Maintain dynamic HUD states
    let mut last_p1_score = -1;
    let mut last_p1_health = -1;
    let mut last_p1_keys = -1;
    let mut last_p1_bombs = -1;

    let mut last_p2_active = false;
    let mut last_p2_score = -1;
    let mut last_p2_health = -1;
    let mut last_p2_keys = -1;
    let mut last_p2_bombs = -1;

    *g.borrow_mut() = Some(Closure::new(move || {
        let current_keys = keys.borrow();
        game.step(&current_keys);

        // Smoothly update camera offsets on every frame
        game.update_camera();

        // Draw scene
        draw_scene(&context, &offscreen_canvas, &game);

        // Update Player 1 HUD
        if let Some(ref el) = p1_score_el {
            let val = game.players[0].score;
            if val != last_p1_score {
                el.set_text_content(Some(&val.to_string()));
                last_p1_score = val;
            }
        }
        if let Some(ref el) = p1_health_el {
            let val = game.players[0].health;
            if val != last_p1_health {
                el.set_text_content(Some(&val.to_string()));
                last_p1_health = val;
            }
        }
        if let Some(ref el) = p1_keys_el {
            let val = game.players[0].keys;
            if val != last_p1_keys {
                el.set_text_content(Some(&val.to_string()));
                last_p1_keys = val;
            }
        }
        if let Some(ref el) = p1_bombs_el {
            let val = game.players[0].bombs;
            if val != last_p1_bombs {
                el.set_text_content(Some(&val.to_string()));
                last_p1_bombs = val;
            }
        }

        // Update Player 2 HUD dynamically
        let p2_active = game.players[1].active;
        if p2_active != last_p2_active {
            if let Some(ref el) = hud_p2_el {
                if p2_active {
                    el.set_inner_html(
                        "<td class=\"text-left\">P2</td>                         <td id=\"p2-score\" class=\"text-right\">0</td>                         <td id=\"p2-health\" class=\"text-right\">100</td>                         <td id=\"p2-keys\" class=\"text-right\">0</td>                         <td id=\"p2-bombs\" class=\"text-right\">0</td>"
                    );
                } else {
                    el.set_inner_html("<td colspan=\"5\" class=\"hud-p2-inactive\">Player 2: Press WASD/F/G to Join</td>");
                }
            }
            last_p2_active = p2_active;
            // Force update elements on state change
            last_p2_score = -1;
            last_p2_health = -1;
            last_p2_keys = -1;
            last_p2_bombs = -1;
        }

        if p2_active {
            let p2_score_el = document.get_element_by_id("p2-score");
            let p2_health_el = document.get_element_by_id("p2-health");
            let p2_keys_el = document.get_element_by_id("p2-keys");
            let p2_bombs_el = document.get_element_by_id("p2-bombs");

            if let Some(ref el) = p2_score_el {
                let val = game.players[1].score;
                if val != last_p2_score {
                    el.set_text_content(Some(&val.to_string()));
                    last_p2_score = val;
                }
            }
            if let Some(ref el) = p2_health_el {
                let val = game.players[1].health;
                if val != last_p2_health {
                    el.set_text_content(Some(&val.to_string()));
                    last_p2_health = val;
                }
            }
            if let Some(ref el) = p2_keys_el {
                let val = game.players[1].keys;
                if val != last_p2_keys {
                    el.set_text_content(Some(&val.to_string()));
                    last_p2_keys = val;
                }
            }
            if let Some(ref el) = p2_bombs_el {
                let val = game.players[1].bombs;
                if val != last_p2_bombs {
                    el.set_text_content(Some(&val.to_string()));
                    last_p2_bombs = val;
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
