;--------------------------------------------------------
; File Created by SDCC : free open source ISO C Compiler
; Version 4.5.1 #15267 (Linux)
;--------------------------------------------------------
	.module gameboy_hal
	
;--------------------------------------------------------
; Public variables in this module
;--------------------------------------------------------
	.globl _hal_draw_string
	.globl _fill_bkg_rect
	.globl _set_bkg_tile_xy
	.globl _hal_draw_tile
	.globl _hal_update_hud
	.globl _hal_clear_sprites
	.globl _hal_set_sprite
	.globl _hal_play_sound
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
_sound_initialized:
	.ds 1
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
;src/gameboy_hal.c:8: void hal_draw_string(uint8_t x, uint8_t y, const char* str) {
;	---------------------------------
; Function hal_draw_string
; ---------------------------------
_hal_draw_string::
	dec	sp
	dec	sp
	ldhl	sp,	#1
	ld	(hl-), a
	ld	(hl), e
;src/gameboy_hal.c:10: while (str[i] != '\0') {
	ld	c, #0x00
00101$:
	ldhl	sp,#4
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	l, c
	ld	h, #0x00
	add	hl, de
	ld	e, l
	ld	d, h
	ld	a, (de)
	or	a, a
	jr	Z, 00104$
;src/gameboy_hal.c:12: set_bkg_tile_xy(x + i, y, str[i] - 32);
	add	a, #0xe0
	ld	b, a
	ldhl	sp,	#1
	ld	a, (hl-)
	add	a, c
	push	bc
	push	bc
	inc	sp
	ld	e, (hl)
	call	_set_bkg_tile_xy
	pop	bc
;src/gameboy_hal.c:13: i++;
	inc	c
	jr	00101$
00104$:
;src/gameboy_hal.c:15: }
	inc	sp
	inc	sp
	pop	hl
	pop	af
	jp	(hl)
;src/gameboy_hal.c:18: static void hal_draw_string_inverted(uint8_t x, uint8_t y, const char* str) {
;	---------------------------------
; Function hal_draw_string_inverted
; ---------------------------------
_hal_draw_string_inverted:
	dec	sp
	dec	sp
	ldhl	sp,	#1
	ld	(hl-), a
	ld	(hl), e
;src/gameboy_hal.c:20: while (str[i] != '\0') {
	ld	c, #0x00
00101$:
	ldhl	sp,#4
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	l, c
	ld	h, #0x00
	add	hl, de
	ld	e, l
	ld	d, h
	ld	a, (de)
	or	a, a
	jr	Z, 00104$
;src/gameboy_hal.c:23: set_bkg_tile_xy(x + i, y, str[i] - 32);
	add	a, #0xe0
	ld	b, a
	ldhl	sp,	#1
	ld	a, (hl-)
	add	a, c
	push	bc
	push	bc
	inc	sp
	ld	e, (hl)
	call	_set_bkg_tile_xy
	pop	bc
;src/gameboy_hal.c:28: i++;
	inc	c
	jr	00101$
00104$:
;src/gameboy_hal.c:30: }
	inc	sp
	inc	sp
	pop	hl
	pop	af
	jp	(hl)
;src/gameboy_hal.c:33: static void u16_to_str(uint16_t val, char* buf, uint8_t digits) {
;	---------------------------------
; Function u16_to_str
; ---------------------------------
_u16_to_str:
	add	sp, #-3
	push	de
	ldhl	sp,	#2
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;src/gameboy_hal.c:34: for (int8_t i = digits - 1; i >= 0; --i) {
	ldhl	sp,	#7
	ld	a, (hl)
	dec	a
	ldhl	sp,	#4
	ld	(hl), a
00103$:
	ldhl	sp,	#4
	bit	7, (hl)
	jr	NZ, 00101$
;src/gameboy_hal.c:35: buf[i] = '0' + (val % 10);
	ld	a, (hl-)
	ld	e, a
	ld	d, #0x00
	ld	a, (hl-)
	ld	l, (hl)
	ld	h, a
	add	hl, de
	push	hl
	ld	bc, #0x000a
	pop	hl
	pop	de
	push	de
	push	hl
	call	__moduint
	pop	de
	ld	a, c
	add	a, #0x30
	ld	(de), a
;src/gameboy_hal.c:36: val /= 10;
	ld	bc, #0x000a
	pop	de
	push	de
	call	__divuint
	pop	hl
	push	bc
;src/gameboy_hal.c:34: for (int8_t i = digits - 1; i >= 0; --i) {
	ldhl	sp,	#4
	dec	(hl)
	jr	00103$
00101$:
;src/gameboy_hal.c:38: buf[digits] = '\0';
	ldhl	sp,#2
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ldhl	sp,	#7
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	ld	c, l
	ld	b, h
	xor	a, a
	ld	(bc), a
;src/gameboy_hal.c:39: }
	add	sp, #5
	pop	hl
	inc	sp
	jp	(hl)
;src/gameboy_hal.c:41: static void s16_to_str(int16_t val, char* buf, uint8_t digits) {
;	---------------------------------
; Function s16_to_str
; ---------------------------------
_s16_to_str:
	add	sp, #-8
	ldhl	sp,	#5
	ld	a, e
	ld	(hl+), a
	ld	(hl), d
	ldhl	sp,	#3
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;src/gameboy_hal.c:42: bool neg = false;
	ldhl	sp,	#0
	ld	(hl), #0x00
;src/gameboy_hal.c:43: if (val < 0) {
	ldhl	sp,	#5
	ld	a, (hl+)
	bit	7, (hl)
	jr	Z, 00102$
;src/gameboy_hal.c:44: neg = true;
	ldhl	sp,	#0
	ld	(hl), #0x01
;src/gameboy_hal.c:45: val = -val;
	ld	de, #0x0000
	ldhl	sp,	#5
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	ld	a, e
	sub	a, l
	ld	e, a
	ld	a, d
	sbc	a, h
	ldhl	sp,	#6
	ld	(hl-), a
	ld	(hl), e
00102$:
;src/gameboy_hal.c:47: for (int8_t i = digits - 1; i >= 0; --i) {
	ldhl	sp,	#10
	ld	a, (hl)
	dec	a
	ldhl	sp,	#7
	ld	(hl), a
00108$:
	ldhl	sp,	#7
	bit	7, (hl)
	jr	NZ, 00103$
;src/gameboy_hal.c:48: buf[i] = '0' + (val % 10);
	ld	e, (hl)
	ld	d, #0x00
	ldhl	sp,	#3
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	ld	e, l
	ld	d, h
	ldhl	sp,	#5
	ld	a, (hl)
	ldhl	sp,	#1
	ld	(hl), a
	ldhl	sp,	#6
	ld	a, (hl)
	ldhl	sp,	#2
	ld	(hl-), a
	push	de
	ld	bc, #0x000a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	call	__modsint
	pop	de
	ld	a, c
	add	a, #0x30
	ld	(de), a
;src/gameboy_hal.c:49: val /= 10;
	ld	bc, #0x000a
	ldhl	sp,	#1
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	call	__divsint
	ldhl	sp,	#5
	ld	a, c
	ld	(hl+), a
;src/gameboy_hal.c:47: for (int8_t i = digits - 1; i >= 0; --i) {
	ld	a, b
	ld	(hl+), a
	dec	(hl)
	jr	00108$
00103$:
;src/gameboy_hal.c:51: if (neg && digits > 0) {
	ldhl	sp,	#0
	bit	0, (hl)
	jr	Z, 00105$
	ldhl	sp,	#10
	ld	a, (hl)
	or	a, a
	jr	Z, 00105$
;src/gameboy_hal.c:52: buf[0] = '-';
	ldhl	sp,	#3
	ld	a, (hl+)
	ld	h, (hl)
	ld	l, a
	ld	(hl), #0x2d
00105$:
;src/gameboy_hal.c:54: buf[digits] = '\0';
	ldhl	sp,#3
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ldhl	sp,	#10
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	ld	c, l
	ld	b, h
	xor	a, a
	ld	(bc), a
;src/gameboy_hal.c:55: }
	add	sp, #8
	pop	hl
	inc	sp
	jp	(hl)
;src/gameboy_hal.c:59: void hal_draw_tile(uint8_t x, uint8_t y, uint8_t tile_id) {
;	---------------------------------
; Function hal_draw_tile
; ---------------------------------
_hal_draw_tile::
	ld	c, a
;src/gameboy_hal.c:61: if (tile_id >= TILE_PLAYER1 && tile_id <= TILE_PLAYER1 + 31) {
	ldhl	sp,	#2
	ld	a, (hl)
	sub	a, #0x18
	jr	C, 00102$
	ld	a, #0x37
	sub	a, (hl)
	jr	C, 00102$
;src/gameboy_hal.c:62: tile_id = TILE_PLAYER1 + ((tile_id - TILE_PLAYER1) & 7);
	ld	a, (hl)
	add	a, #0xe8
	and	a, #0x07
	add	a, #0x18
	ld	(hl), a
00102$:
;src/gameboy_hal.c:66: set_bkg_tile_xy(x, y, 128 + tile_id);
	ldhl	sp,	#2
	ld	a, (hl)
	add	a, #0x80
	push	af
	inc	sp
	ld	a, c
	call	_set_bkg_tile_xy
;src/gameboy_hal.c:67: }
	pop	hl
	inc	sp
	jp	(hl)
;src/gameboy_hal.c:69: void hal_update_hud(void) {
;	---------------------------------
; Function hal_update_hud
; ---------------------------------
_hal_update_hud::
	add	sp, #-15
;src/gameboy_hal.c:71: uint8_t p = local_player_idx;
	ld	a, (#_local_player_idx)
	ldhl	sp,	#10
	ld	(hl), a
;src/gameboy_hal.c:77: fill_bkg_rect(0, 10, 20, 8, 0);
	ld	hl, #0x08
	push	hl
	ld	hl, #0x140a
	push	hl
	xor	a, a
	push	af
	inc	sp
	call	_fill_bkg_rect
	add	sp, #5
;src/gameboy_hal.c:85: hal_draw_string_inverted(1, 11, "SCORE: ");
	ld	de, #___str_0
	push	de
	ld	e, #0x0b
	ld	a, #0x01
	call	_hal_draw_string_inverted
;src/gameboy_hal.c:86: u16_to_str(player_score[p], buf, 6);
	ldhl	sp,	#0
	ld	c, l
	ld	b, h
	ldhl	sp,	#10
	ld	a, (hl+)
	ld	e, a
	ld	d, #0x00
	sla	e
	rl	d
	ld	a, e
	ld	(hl+), a
	ld	(hl), d
	ld	de, #_player_score
	ld	a, (hl-)
	ld	l, (hl)
	ld	h, a
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#15
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#14
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	ld	l, a
	inc	de
	ld	a, (de)
	ld	h, a
	push	bc
	ld	a, #0x06
	push	af
	inc	sp
	ld	e, l
	ld	d, h
	call	_u16_to_str
	pop	bc
;src/gameboy_hal.c:87: hal_draw_string_inverted(8, 11, buf);
	push	bc
	push	bc
	ld	e, #0x0b
	ld	a, #0x08
	call	_hal_draw_string_inverted
;src/gameboy_hal.c:90: hal_draw_string_inverted(1, 12, "HP:    ");
	ld	de, #___str_1
	push	de
	ld	e, #0x0c
	ld	a, #0x01
	call	_hal_draw_string_inverted
	pop	bc
;src/gameboy_hal.c:91: s16_to_str(player_health[p], buf, 3);
	ld	de, #_player_health
	ldhl	sp,	#11
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#15
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#14
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	ld	l, a
	inc	de
	ld	a, (de)
	ld	h, a
	push	bc
	ld	a, #0x03
	push	af
	inc	sp
	ld	e, l
	ld	d, h
	call	_s16_to_str
	pop	bc
;src/gameboy_hal.c:92: hal_draw_string_inverted(8, 12, buf);
	push	bc
	push	bc
	ld	e, #0x0c
	ld	a, #0x08
	call	_hal_draw_string_inverted
;src/gameboy_hal.c:95: hal_draw_string_inverted(1, 13, "BOMBS: ");
	ld	de, #___str_2
	push	de
	ld	e, #0x0d
	ld	a, #0x01
	call	_hal_draw_string_inverted
	pop	bc
;src/gameboy_hal.c:96: u16_to_str(player_bombs[p], buf, 2);
	ld	de, #_player_bombs+0
	ldhl	sp,	#10
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	ld	e, l
	ld	d, h
	ld	a, (de)
	ld	d, #0x00
	push	bc
	ld	h, #0x02
	push	hl
	inc	sp
	ld	e, a
	call	_u16_to_str
	pop	bc
;src/gameboy_hal.c:97: hal_draw_string_inverted(8, 13, buf);
	push	bc
	push	bc
	ld	e, #0x0d
	ld	a, #0x08
	call	_hal_draw_string_inverted
;src/gameboy_hal.c:99: hal_draw_string_inverted(11, 13, "KEYS: ");
	ld	de, #___str_3
	push	de
	ld	e, #0x0d
	ld	a, #0x0b
	call	_hal_draw_string_inverted
	pop	bc
;src/gameboy_hal.c:100: u16_to_str(player_keys[p], buf, 2);
	ld	de, #_player_keys+0
	ldhl	sp,	#10
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	ld	e, l
	ld	d, h
	ld	a, (de)
	ld	d, #0x00
	push	bc
	ld	h, #0x02
	push	hl
	inc	sp
	ld	e, a
	call	_u16_to_str
	pop	bc
;src/gameboy_hal.c:101: hal_draw_string_inverted(17, 13, buf);
	push	bc
	push	bc
	ld	e, #0x0d
	ld	a, #0x11
	call	_hal_draw_string_inverted
;src/gameboy_hal.c:104: hal_draw_string_inverted(1, 14, "LEVEL: ");
	ld	de, #___str_4
	push	de
	ld	e, #0x0e
	ld	a, #0x01
	call	_hal_draw_string_inverted
	pop	bc
;src/gameboy_hal.c:105: u16_to_str(current_level + 1, buf, 2);
	ld	a, (_current_level)
	ld	d, #0x00
	ld	e, a
	inc	de
	push	bc
	ld	a, #0x02
	push	af
	inc	sp
	call	_u16_to_str
;src/gameboy_hal.c:106: hal_draw_string_inverted(8, 14, buf);
	ld	e, #0x0e
	ld	a, #0x08
	call	_hal_draw_string_inverted
;src/gameboy_hal.c:107: }
	add	sp, #15
	ret
___str_0:
	.ascii "SCORE: "
	.db 0x00
___str_1:
	.ascii "HP:    "
	.db 0x00
___str_2:
	.ascii "BOMBS: "
	.db 0x00
___str_3:
	.ascii "KEYS: "
	.db 0x00
___str_4:
	.ascii "LEVEL: "
	.db 0x00
;src/gameboy_hal.c:109: void hal_clear_sprites(uint8_t vp_left, uint8_t vp_top) {
;	---------------------------------
; Function hal_clear_sprites
; ---------------------------------
_hal_clear_sprites::
;src/gameboy_hal.c:113: for (uint8_t i = 0; i < 40; ++i) {
	ld	c, #0x00
00104$:
	ld	a, c
	sub	a, #0x28
	ret	NC
;/usr/local/google/home/jackpal/Developer/gbdk/include/gb/gb.h:1973: OAM_item_t * itm = &shadow_OAM[nb];
	ld	de, #_shadow_OAM+0
	ld	l, c
	xor	a, a
	ld	h, a
	add	hl, hl
	add	hl, hl
	add	hl, de
;/usr/local/google/home/jackpal/Developer/gbdk/include/gb/gb.h:1974: itm->y=y, itm->x=x;
	xor	a, a
	ld	(hl+), a
	ld	(hl), a
;src/gameboy_hal.c:113: for (uint8_t i = 0; i < 40; ++i) {
	inc	c
;src/gameboy_hal.c:116: }
	jr	00104$
;src/gameboy_hal.c:118: void hal_set_sprite(uint8_t sprite_idx, uint8_t x, uint8_t y, uint8_t tile_id, uint8_t flags) {
;	---------------------------------
; Function hal_set_sprite
; ---------------------------------
_hal_set_sprite::
	dec	sp
;src/gameboy_hal.c:119: if (sprite_idx >= 40) return;
	ld	c, a
	sub	a, #0x28
	jr	NC, 00109$
;src/gameboy_hal.c:122: if (tile_id >= TILE_PLAYER1 && tile_id <= TILE_PLAYER1 + 31) {
	ldhl	sp,	#4
	ld	a, (hl)
	sub	a, #0x18
	jr	C, 00104$
	ld	a, #0x37
	sub	a, (hl)
	jr	C, 00104$
;src/gameboy_hal.c:123: tile_id = TILE_PLAYER1 + ((tile_id - TILE_PLAYER1) & 7);
	ld	a, (hl)
	add	a, #0xe8
	and	a, #0x07
	add	a, #0x18
	ld	(hl), a
00104$:
;src/gameboy_hal.c:127: set_sprite_tile(sprite_idx, 128 + tile_id);
	ldhl	sp,	#4
	ld	a, (hl)
	add	a, #0x80
	ld	d, a
;/usr/local/google/home/jackpal/Developer/gbdk/include/gb/gb.h:1887: shadow_OAM[nb].tile=tile;
	ld	b, #0x00
	sla	c
	rl	b
	sla	c
	rl	b
	ld	hl,#_shadow_OAM + 1
	add	hl,bc
	inc	hl
	ld	(hl), d
;src/gameboy_hal.c:130: move_sprite(sprite_idx, x + 8, y + 16);
	ldhl	sp,	#3
	ld	a, (hl)
	add	a, #0x10
	ldhl	sp,	#0
	ld	(hl), a
	ld	a, e
	add	a, #0x08
	ld	e, a
;/usr/local/google/home/jackpal/Developer/gbdk/include/gb/gb.h:1973: OAM_item_t * itm = &shadow_OAM[nb];
	ld	hl, #_shadow_OAM
	add	hl, bc
;/usr/local/google/home/jackpal/Developer/gbdk/include/gb/gb.h:1974: itm->y=y, itm->x=x;
	push	hl
	ldhl	sp,	#2
	ld	a, (hl)
	pop	hl
	ld	(hl+), a
	ld	(hl), e
;src/gameboy_hal.c:133: set_sprite_prop(sprite_idx, flags);
	ldhl	sp,	#5
	ld	e, (hl)
;/usr/local/google/home/jackpal/Developer/gbdk/include/gb/gb.h:1946: shadow_OAM[nb].prop=prop;
	ld	hl,#_shadow_OAM + 1
	add	hl,bc
	inc	hl
	inc	hl
	ld	(hl), e
;src/gameboy_hal.c:133: set_sprite_prop(sprite_idx, flags);
00109$:
;src/gameboy_hal.c:134: }
	inc	sp
	pop	hl
	add	sp, #3
	jp	(hl)
;src/gameboy_hal.c:138: void hal_play_sound(uint8_t sound_id) {
;	---------------------------------
; Function hal_play_sound
; ---------------------------------
_hal_play_sound::
	ld	c, a
;src/gameboy_hal.c:139: if (!sound_initialized) {
	ld	hl, #_sound_initialized
	bit	0, (hl)
	jr	NZ, 00102$
;src/gameboy_hal.c:140: NR52_REG = 0x80; // Turn on Sound chip
	ld	a, #0x80
	ldh	(_NR52_REG + 0), a
;src/gameboy_hal.c:141: NR50_REG = 0x77; // Max volume on left/right channels
	ld	a, #0x77
	ldh	(_NR50_REG + 0), a
;src/gameboy_hal.c:142: NR51_REG = 0xFF; // Route all 4 channels to left/right speakers
	ld	a, #0xff
	ldh	(_NR51_REG + 0), a
;src/gameboy_hal.c:143: sound_initialized = true;
	ld	(hl), #0x01
00102$:
;src/gameboy_hal.c:146: switch (sound_id) {
	ld	a, #0x06
	sub	a, c
	ret	C
	ld	b, #0x00
	ld	hl, #00127$
	add	hl, bc
	add	hl, bc
	ld	c, (hl)
	inc	hl
	ld	h, (hl)
	ld	l, c
	jp	(hl)
00127$:
	.dw	00103$
	.dw	00104$
	.dw	00105$
	.dw	00106$
	.dw	00107$
	.dw	00108$
	.dw	00109$
;src/gameboy_hal.c:147: case SOUND_SHOOT:
00103$:
;src/gameboy_hal.c:148: NR10_REG = 0x1E;
	ld	a, #0x1e
	ldh	(_NR10_REG + 0), a
;src/gameboy_hal.c:149: NR11_REG = 0x80;
	ld	a, #0x80
	ldh	(_NR11_REG + 0), a
;src/gameboy_hal.c:150: NR12_REG = 0xF3;
	ld	a, #0xf3
	ldh	(_NR12_REG + 0), a
;src/gameboy_hal.c:151: NR13_REG = 0x00;
	xor	a, a
	ldh	(_NR13_REG + 0), a
;src/gameboy_hal.c:152: NR14_REG = 0xC7;
	ld	a, #0xc7
	ldh	(_NR14_REG + 0), a
;src/gameboy_hal.c:153: break;
	ret
;src/gameboy_hal.c:154: case SOUND_HIT:
00104$:
;src/gameboy_hal.c:155: NR21_REG = 0x80;
	ld	a, #0x80
	ldh	(_NR21_REG + 0), a
;src/gameboy_hal.c:156: NR22_REG = 0xF1;
	ld	a, #0xf1
	ldh	(_NR22_REG + 0), a
;src/gameboy_hal.c:157: NR23_REG = 0x80;
	ld	a, #0x80
	ldh	(_NR23_REG + 0), a
;src/gameboy_hal.c:158: NR24_REG = 0xC4;
	ld	a, #0xc4
	ldh	(_NR24_REG + 0), a
;src/gameboy_hal.c:159: break;
	ret
;src/gameboy_hal.c:160: case SOUND_FOOD:
00105$:
;src/gameboy_hal.c:161: NR10_REG = 0x16;
	ld	a, #0x16
	ldh	(_NR10_REG + 0), a
;src/gameboy_hal.c:162: NR11_REG = 0x80;
	ld	a, #0x80
	ldh	(_NR11_REG + 0), a
;src/gameboy_hal.c:163: NR12_REG = 0xF2;
	ld	a, #0xf2
	ldh	(_NR12_REG + 0), a
;src/gameboy_hal.c:164: NR13_REG = 0x00;
	xor	a, a
	ldh	(_NR13_REG + 0), a
;src/gameboy_hal.c:165: NR14_REG = 0xC6;
	ld	a, #0xc6
	ldh	(_NR14_REG + 0), a
;src/gameboy_hal.c:166: break;
	ret
;src/gameboy_hal.c:167: case SOUND_BOMB:
00106$:
;src/gameboy_hal.c:168: NR41_REG = 0x1F;
	ld	a, #0x1f
	ldh	(_NR41_REG + 0), a
;src/gameboy_hal.c:169: NR42_REG = 0xF7;
	ld	a, #0xf7
	ldh	(_NR42_REG + 0), a
;src/gameboy_hal.c:170: NR43_REG = 0x57;
	ld	a, #0x57
	ldh	(_NR43_REG + 0), a
;src/gameboy_hal.c:171: NR44_REG = 0xC0;
	ld	a, #0xc0
	ldh	(_NR44_REG + 0), a
;src/gameboy_hal.c:172: break;
	ret
;src/gameboy_hal.c:173: case SOUND_KEY:
00107$:
;src/gameboy_hal.c:174: NR21_REG = 0x80;
	ld	a, #0x80
	ldh	(_NR21_REG + 0), a
;src/gameboy_hal.c:175: NR22_REG = 0xF2;
	ld	a, #0xf2
	ldh	(_NR22_REG + 0), a
;src/gameboy_hal.c:176: NR23_REG = 0xF0;
	ld	a, #0xf0
	ldh	(_NR23_REG + 0), a
;src/gameboy_hal.c:177: NR24_REG = 0xC6;
	ld	a, #0xc6
	ldh	(_NR24_REG + 0), a
;src/gameboy_hal.c:178: break;
	ret
;src/gameboy_hal.c:179: case SOUND_DIE:
00108$:
;src/gameboy_hal.c:180: NR10_REG = 0x3F;
	ld	a, #0x3f
	ldh	(_NR10_REG + 0), a
;src/gameboy_hal.c:181: NR11_REG = 0x80;
	ld	a, #0x80
	ldh	(_NR11_REG + 0), a
;src/gameboy_hal.c:182: NR12_REG = 0xF5;
	ld	a, #0xf5
	ldh	(_NR12_REG + 0), a
;src/gameboy_hal.c:183: NR13_REG = 0x50;
	ld	a, #0x50
	ldh	(_NR13_REG + 0), a
;src/gameboy_hal.c:184: NR14_REG = 0xC3;
	ld	a, #0xc3
	ldh	(_NR14_REG + 0), a
;src/gameboy_hal.c:185: break;
	ret
;src/gameboy_hal.c:186: case SOUND_WARP:
00109$:
;src/gameboy_hal.c:187: NR10_REG = 0x0E;
	ld	a, #0x0e
	ldh	(_NR10_REG + 0), a
;src/gameboy_hal.c:188: NR11_REG = 0x40;
	ld	a, #0x40
	ldh	(_NR11_REG + 0), a
;src/gameboy_hal.c:189: NR12_REG = 0xF3;
	ld	a, #0xf3
	ldh	(_NR12_REG + 0), a
;src/gameboy_hal.c:190: NR13_REG = 0x00;
	xor	a, a
	ldh	(_NR13_REG + 0), a
;src/gameboy_hal.c:191: NR14_REG = 0xC7;
	ld	a, #0xc7
	ldh	(_NR14_REG + 0), a
;src/gameboy_hal.c:193: }
;src/gameboy_hal.c:194: }
	ret
	.area _CODE
	.area _INITIALIZER
__xinit__sound_initialized:
	.db #0x00	;  0
	.area _CABS (ABS)
