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
        // Safety: Casting u8 slice to u32 slice is safe since u32 has no invalid bit representations.
        let (prefix, words, suffix) = unsafe { self.pixels.align_to_mut::<u32>() };
        let color = u32::from_ne_bytes([r, g, b, 255]);
        if prefix.is_empty() && suffix.is_empty() {
            words.fill(color);
        } else {
            for chunk in self.pixels.chunks_exact_mut(4) {
                chunk[0] = r;
                chunk[1] = g;
                chunk[2] = b;
                chunk[3] = 255;
            }
        }
    }

    pub fn blit_tile(&mut self, spritesheet: &[u8], tile_idx: u8, dest_x: i32, dest_y: i32) {
        if spritesheet.len() < 256 * 256 * 4 {
            return;
        }

        let tile_x = ((tile_idx & 15) as i32) * 16;
        let tile_y = ((tile_idx >> 4) as i32) * 16;

        // Vertical clipping
        let start_py = std::cmp::max(0, -dest_y);
        let end_py = std::cmp::min(16, SCREEN_HEIGHT as i32 - dest_y);
        if start_py >= end_py {
            return;
        }

        // Horizontal clipping
        let start_x = std::cmp::max(0, dest_x);
        let end_x = std::cmp::min(SCREEN_WIDTH as i32, dest_x + 16);
        if start_x >= end_x {
            return;
        }

        let start_px = start_x - dest_x;
        let end_px = end_x - dest_x;
        let num_pixels = (end_px - start_px) as usize;
        if num_pixels == 0 {
            return;
        }

        for py in start_py..end_py {
            let sy = dest_y + py;
            let src_row_start = ((tile_y + py) * 256) as usize;
            let dest_row_start = (sy * SCREEN_WIDTH as i32) as usize;

            let src_start_idx = (src_row_start + (tile_x + start_px) as usize) * 4;
            let src_end_idx = src_start_idx + num_pixels * 4;

            let dest_start_idx = (dest_row_start + start_x as usize) * 4;
            let dest_end_idx = dest_start_idx + num_pixels * 4;

            self.pixels[dest_start_idx..dest_end_idx]
                .copy_from_slice(&spritesheet[src_start_idx..src_end_idx]);
        }
    }
}

pub fn parse_bmp(bytes: &[u8]) -> Vec<u8> {
    if bytes.len() < 54 || &bytes[0..2] != b"BM" {
        return Vec::new();
    }
    
    let data_offset = u32::from_le_bytes([bytes[10], bytes[11], bytes[12], bytes[13]]) as usize;
    let width = i32::from_le_bytes([bytes[18], bytes[19], bytes[20], bytes[21]]) as usize;
    let raw_height = i32::from_le_bytes([bytes[22], bytes[23], bytes[24], bytes[25]]);
    let height = raw_height.unsigned_abs() as usize;
    let top_down = raw_height < 0;
    
    let bpp = u16::from_le_bytes([bytes[28], bytes[29]]);
    if bpp != 24 {
        return Vec::new();
    }
    
    let mut rgba = vec![0u8; width * height * 4];
    let row_stride = (width * 3 + 3) & !3;
    
    for y in 0..height {
        let bmp_y = if top_down { y } else { height - 1 - y };
        let row_start = data_offset + bmp_y * row_stride;
        
        for x in 0..width {
            let px_start = row_start + x * 3;
            if px_start + 2 < bytes.len() {
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
    }
    
    rgba
}
