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
        if spritesheet.is_empty() {
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

            if src_end_idx <= spritesheet.len() && dest_end_idx <= self.pixels.len() {
                self.pixels[dest_start_idx..dest_end_idx]
                    .copy_from_slice(&spritesheet[src_start_idx..src_end_idx]);
            }
        }
    }
}

pub fn parse_bmp(bytes: &[u8]) -> Vec<u8> {
    if bytes.len() < 54 || &bytes[0..2] != b"BM" {
        return Vec::new();
    }
    
    let data_offset = u32::from_le_bytes([bytes[10], bytes[11], bytes[12], bytes[13]]) as usize;
    let raw_width = i32::from_le_bytes([bytes[18], bytes[19], bytes[20], bytes[21]]);
    let raw_height = i32::from_le_bytes([bytes[22], bytes[23], bytes[24], bytes[25]]);
    if data_offset >= bytes.len() || raw_width <= 0 || raw_height == 0 || raw_width > 4096 || raw_height.unsigned_abs() > 4096 {
        return Vec::new();
    }
    let width = raw_width as usize;
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

#[cfg(test)]
mod tests {
    use super::*;

    const SPRITESHEET_BYTES: &[u8] = include_bytes!("../assets/dandy.bmp");

    #[test]
    fn test_parse_bmp_dandy_spritesheet() {
        let rgba = parse_bmp(SPRITESHEET_BYTES);
        assert_eq!(rgba.len(), 256 * 32 * 4, "Spritesheet must parse to 256x32x4 bytes");
        // Verify non-zero color channels exist in spritesheet
        let has_non_zero_rgb = rgba.chunks_exact(4).any(|px| px[0] != 0 || px[1] != 0 || px[2] != 0);
        assert!(has_non_zero_rgb, "Spritesheet must contain non-zero RGB pixel data");
    }

    #[test]
    fn test_parse_bmp_invalid_inputs() {
        assert!(parse_bmp(&[]).is_empty());
        assert!(parse_bmp(b"INVALID").is_empty());
        let mut corrupted = SPRITESHEET_BYTES.to_vec();
        corrupted[0] = b'X';
        assert!(parse_bmp(&corrupted).is_empty());
    }

    #[test]
    fn test_framebuffer_blit_tile_and_clear() {
        let mut fb = Framebuffer::new();
        assert_eq!(fb.pixels.len(), SCREEN_WIDTH * SCREEN_HEIGHT * 4);

        fb.clear(10, 20, 30);
        assert_eq!(fb.pixels[0], 10);
        assert_eq!(fb.pixels[1], 20);
        assert_eq!(fb.pixels[2], 30);
        assert_eq!(fb.pixels[3], 255);

        let spritesheet = parse_bmp(SPRITESHEET_BYTES);
        // Blit Wall tile (tile index 1) at (0, 0)
        fb.clear(0, 0, 0);
        fb.blit_tile(&spritesheet, 1, 0, 0);

        let non_zero_rgb = fb.pixels.chunks_exact(4).any(|px| px[0] != 0 || px[1] != 0 || px[2] != 0);
        assert!(non_zero_rgb, "Framebuffer must contain non-zero RGB data after blitting wall tile");
    }

    #[test]
    fn test_blit_tile_clipping_bounds_safety() {
        let mut fb = Framebuffer::new();
        let spritesheet = parse_bmp(SPRITESHEET_BYTES);

        // Blit offscreen (negative and out-of-bounds) coordinates - must not panic
        fb.blit_tile(&spritesheet, 1, -100, -100);
        fb.blit_tile(&spritesheet, 1, 500, 500);
        fb.blit_tile(&spritesheet, 1, -8, -8); // Partially off-screen top-left
        fb.blit_tile(&spritesheet, 1, SCREEN_WIDTH as i32 - 8, SCREEN_HEIGHT as i32 - 8); // Partially off-screen bottom-right
        fb.blit_tile(&[], 1, 0, 0); // Empty spritesheet safety
    }

    #[test]
    fn test_blit_tile_exact_pixel_transfer_and_quadrant_clipping() {
        let mut fb = Framebuffer::new();
        let spritesheet = parse_bmp(SPRITESHEET_BYTES);
        assert!(!spritesheet.is_empty(), "Parsed spritesheet must not be empty");

        // Blit multiple tile indices across the 256x32 spritesheet (row 0: tiles 0..15, row 1: tiles 16..31)
        for tile_idx in [0u8, 1, 2, 7, 15, 16, 17, 31] {
            fb.clear(0, 0, 0);
            fb.blit_tile(&spritesheet, tile_idx, 32, 32);

            let tile_col = (tile_idx & 15) as usize;
            let tile_row = (tile_idx >> 4) as usize;
            let src_x = tile_col * 16;
            let src_y = tile_row * 16;

            // Check sample pixel inside the 16x16 destination region matches spritesheet source
            for py in 0..16 {
                for px in 0..16 {
                    let dest_idx = ((32 + py) * SCREEN_WIDTH + (32 + px)) * 4;
                    let src_idx = ((src_y + py) * 256 + (src_x + px)) * 4;
                    assert_eq!(
                        &fb.pixels[dest_idx..dest_idx + 4],
                        &spritesheet[src_idx..src_idx + 4],
                        "Pixel mismatch for tile {} at offset ({}, {})",
                        tile_idx, px, py
                    );
                }
            }
        }

        // Test clipping on all 4 quadrants (partial overlap without panic or out-of-bound writes)
        fb.clear(0, 0, 0);
        // Top edge clipping (y = -8)
        fb.blit_tile(&spritesheet, 1, 100, -8);
        // Bottom edge clipping (y = SCREEN_HEIGHT - 8)
        fb.blit_tile(&spritesheet, 1, 100, SCREEN_HEIGHT as i32 - 8);
        // Left edge clipping (x = -8)
        fb.blit_tile(&spritesheet, 1, -8, 50);
        // Right edge clipping (x = SCREEN_WIDTH - 8)
        fb.blit_tile(&spritesheet, 1, SCREEN_WIDTH as i32 - 8, 50);

        let active_pixels = fb.pixels.chunks_exact(4).filter(|px| px[0] != 0 || px[1] != 0 || px[2] != 0).count();
        assert!(active_pixels > 0, "Clipped tiles must draw non-zero pixels inside visible bounds");
    }
}
