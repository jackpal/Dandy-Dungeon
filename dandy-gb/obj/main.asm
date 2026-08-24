;--------------------------------------------------------
; File Created by SDCC : free open source ISO C Compiler
; Version 4.5.1 #15267 (Linux)
;--------------------------------------------------------
	.module main
	
;--------------------------------------------------------
; Public variables in this module
;--------------------------------------------------------
	.globl _main
	.globl _get_joypad_buttons
	.globl _dandy_draw_viewport
	.globl _dandy_step
	.globl _dandy_init
	.globl _font_set
	.globl _font_load
	.globl _font_init
	.globl _set_sprite_data
	.globl _get_bkg_data
	.globl _set_bkg_data
	.globl _display_off
	.globl _wait_vbl_done
	.globl _joypad
;--------------------------------------------------------
; special function registers
;--------------------------------------------------------
	.area _HRAM
;--------------------------------------------------------
; ram data
;--------------------------------------------------------
	.area _DATA
;--------------------------------------------------------
; ram data
;--------------------------------------------------------
	.area _INITIALIZED
;--------------------------------------------------------
; absolute external ram data
;--------------------------------------------------------
	.area _DABS (ABS)
;--------------------------------------------------------
; global & static initialisations
;--------------------------------------------------------
	.area _HOME
	.area _GSINIT
	.area _GSFINAL
	.area _GSINIT
;--------------------------------------------------------
; Home
;--------------------------------------------------------
	.area _HOME
	.area _HOME
;--------------------------------------------------------
; code
;--------------------------------------------------------
	.area _CODE
;src/main.c:12: uint8_t get_joypad_buttons(void) {
;	---------------------------------
; Function get_joypad_buttons
; ---------------------------------
_get_joypad_buttons::
;src/main.c:13: uint8_t joy = joypad();
	call	_joypad
	ld	c, a
;src/main.c:14: uint8_t buttons = 0;
	xor	a, a
;src/main.c:16: if (joy & J_LEFT)   buttons |= BUTTON_LEFT;
	bit	1, c
	jr	Z, 00102$
	ld	a, #0x01
00102$:
;src/main.c:17: if (joy & J_RIGHT)  buttons |= BUTTON_RIGHT;
	bit	0, c
	jr	Z, 00104$
	set	1, a
00104$:
;src/main.c:18: if (joy & J_UP)     buttons |= BUTTON_UP;
	bit	2, c
	jr	Z, 00106$
	set	2, a
00106$:
;src/main.c:19: if (joy & J_DOWN)   buttons |= BUTTON_DOWN;
	bit	3, c
	jr	Z, 00108$
	set	3, a
00108$:
;src/main.c:20: if (joy & J_A)      buttons |= BUTTON_FIRE; // Button A fires arrow
	bit	4, c
	jr	Z, 00110$
	set	4, a
00110$:
;src/main.c:21: if (joy & J_B)      buttons |= BUTTON_BOMB; // Button B uses smart bomb
	bit	5, c
	ret	Z
	set	5, a
;src/main.c:23: return buttons;
;src/main.c:24: }
	ret
;src/main.c:26: void main(void) {
;	---------------------------------
; Function main
; ---------------------------------
_main::
	add	sp, #-16
;src/main.c:30: DISPLAY_OFF; // Turn off screen during VRAM modifications
	call	_display_off
;src/main.c:42: BGP_REG = 0xE4;
	ld	a, #0xe4
	ldh	(_BGP_REG + 0), a
;src/main.c:44: OBP0_REG = 0xD8;
	ld	a, #0xd8
	ldh	(_OBP0_REG + 0), a
;src/main.c:45: OBP1_REG = 0xD8;
	ld	a, #0xd8
	ldh	(_OBP1_REG + 0), a
;src/main.c:51: font_init();
	call	_font_init
;src/main.c:52: ibm_font = font_load(font_ibm);
	ld	de, #_font_ibm
	push	de
	call	_font_load
	pop	hl
;src/main.c:53: font_set(ibm_font);
	push	de
	call	_font_set
	pop	hl
;src/main.c:60: set_bkg_data(128, DANDY_NUM_TILES, dandy_tiles_light);
	ld	bc, #_dandy_tiles_light+0
	push	bc
	ld	hl, #0x2080
	push	hl
	call	_set_bkg_data
	add	sp, #4
;src/main.c:61: set_sprite_data(128, DANDY_NUM_TILES, dandy_tiles_light);
	push	bc
	ld	hl, #0x2080
	push	hl
	call	_set_sprite_data
	add	sp, #4
;src/main.c:70: for (uint16_t i = 0; i < 96; ++i) {
	ld	bc, #0x0000
00112$:
	ld	e, c
	ld	d, b
	ld	a, e
	sub	a, #0x60
	ld	a, d
	sbc	a, #0x00
	jr	NC, 00102$
;src/main.c:71: get_bkg_data(i, 1, tile_buf);
	ld	d, c
	push	de
	ld	hl, #2
	add	hl, sp
	push	hl
	ld	a, #0x01
	push	af
	inc	sp
	push	de
	inc	sp
	call	_get_bkg_data
	add	sp, #4
	pop	de
;src/main.c:72: for (uint8_t j = 0; j < 16; ++j) {
	ld	e, #0x00
00109$:
	ld	a, e
	sub	a, #0x10
	jr	NC, 00101$
;src/main.c:73: tile_buf[j] = ~tile_buf[j];
	push	de
	ld	d, #0x00
	ld	hl, #2
	add	hl, sp
	add	hl, de
	pop	de
	ld	a, (hl)
	cpl
	ld	(hl), a
;src/main.c:72: for (uint8_t j = 0; j < 16; ++j) {
	inc	e
	jr	00109$
00101$:
;src/main.c:75: set_bkg_data(160 + i, 1, tile_buf);
	ld	a, d
	add	a, #0xa0
	ld	d, a
	ld	hl, #0
	add	hl, sp
	push	hl
	ld	a, #0x01
	push	af
	inc	sp
	push	de
	inc	sp
	call	_set_bkg_data
	add	sp, #4
;src/main.c:70: for (uint16_t i = 0; i < 96; ++i) {
	inc	bc
	jr	00112$
00102$:
;src/main.c:80: SHOW_BKG;
	ldh	a, (_LCDC_REG + 0)
	or	a, #0x01
	ldh	(_LCDC_REG + 0), a
;src/main.c:81: SHOW_SPRITES;
	ldh	a, (_LCDC_REG + 0)
	or	a, #0x02
	ldh	(_LCDC_REG + 0), a
;src/main.c:83: DISPLAY_ON; // Turn screen back on
	ldh	a, (_LCDC_REG + 0)
	or	a, #0x80
	ldh	(_LCDC_REG + 0), a
;src/main.c:86: dandy_init();
	call	_dandy_init
;src/main.c:89: while (1) {
00106$:
;src/main.c:91: uint8_t inputs[MAX_PLAYERS] = {0, 0, 0, 0};
	ldhl	sp,	#12
	xor	a, a
	ld	(hl+), a
	ld	(hl+), a
	xor	a, a
	ld	(hl+), a
	ld	(hl), a
;src/main.c:92: inputs[0] = get_joypad_buttons();
	call	_get_joypad_buttons
	ldhl	sp,	#12
	ld	(hl), a
;src/main.c:93: dandy_step(inputs);
	ld	hl, #12
	add	hl, sp
	ld	e, l
	ld	d, h
	call	_dandy_step
;src/main.c:96: if (is_dirty) {
	ld	hl, #_is_dirty
	bit	0, (hl)
	jr	Z, 00104$
;src/main.c:97: dandy_draw_viewport(local_player_idx);
	ld	a, (_local_player_idx)
	call	_dandy_draw_viewport
;src/main.c:98: is_dirty = false;
	xor	a, a
	ld	(#_is_dirty),a
00104$:
;src/main.c:102: wait_vbl_done();
	call	_wait_vbl_done
	jr	00106$
;src/main.c:104: }
	add	sp, #16
	ret
	.area _CODE
	.area _INITIALIZER
	.area _CABS (ABS)
