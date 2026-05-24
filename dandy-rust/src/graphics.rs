// Graphics utilities and Software Framebuffer Blitter for Dandy Dungeon

use crate::consts::{SCREEN_WIDTH, SCREEN_HEIGHT};

pub struct Framebuffer {
    pub pixels: Vec<u8>,
}

impl Framebuffer {
    pub fn new() -> Self {
        Self {
            pixels: vec![0u8; SCREEN_WIDTH * SCREEN_HEIGHT * 4],
        }
    }

    pub fn clear(&mut self, r: u8, g: u8, b: u8) {
        for i in (0..self.pixels.len()).step_by(4) {
            self.pixels[i] = r;
            self.pixels[i+1] = g;
            self.pixels[i+2] = b;
            self.pixels[i+3] = 255; // Fully opaque
        }
    }

    pub fn blit_tile(&mut self, spritesheet: &[u8], tile_idx: u8, dest_x: i32, dest_y: i32) {
        let tile_x = ((tile_idx & 15) as i32) * 16;
        let tile_y = ((tile_idx >> 4) as i32) * 16;

        for py in 0..16 {
            let sy = dest_y + py;
            if sy < 0 || sy >= SCREEN_HEIGHT as i32 {
                continue;
            }

            let src_row_start = ((tile_y + py) * 256) as usize;
            let dest_row_start = (sy * SCREEN_WIDTH as i32) as usize;

            for px in 0..16 {
                let sx = dest_x + px;
                if sx < 0 || sx >= SCREEN_WIDTH as i32 {
                    continue;
                }

                let src_idx = (src_row_start + (tile_x + px) as usize) * 4;
                let dest_idx = (dest_row_start + sx as usize) * 4;

                // Copy RGBA
                self.pixels[dest_idx] = spritesheet[src_idx];
                self.pixels[dest_idx + 1] = spritesheet[src_idx + 1];
                self.pixels[dest_idx + 2] = spritesheet[src_idx + 2];
                self.pixels[dest_idx + 3] = spritesheet[src_idx + 3];
            }
        }
    }
}

pub fn parse_bmp(bytes: &[u8]) -> Vec<u8> {
    assert_eq!(&bytes[0..2], b"BM");
    
    let data_offset = u32::from_le_bytes(bytes[10..14].try_into().unwrap()) as usize;
    let width = i32::from_le_bytes(bytes[18..22].try_into().unwrap()) as usize;
    let raw_height = i32::from_le_bytes(bytes[22..26].try_into().unwrap());
    let height = raw_height.abs() as usize;
    let top_down = raw_height < 0;
    
    let bpp = u16::from_le_bytes(bytes[28..30].try_into().unwrap());
    assert_eq!(bpp, 24);
    
    let mut rgba = vec![0u8; width * height * 4];
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
            rgba[rgba_idx + 3] = 255;
        }
    }
    
    rgba
}
