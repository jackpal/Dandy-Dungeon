;--------------------------------------------------------
; File Created by SDCC : free open source ISO C Compiler
; Version 4.5.1 #15267 (Linux)
;--------------------------------------------------------
	.module dandy_core
	
;--------------------------------------------------------
; Public variables in this module
;--------------------------------------------------------
	.globl _memset
	.globl _hal_play_sound
	.globl _hal_set_sprite
	.globl _hal_clear_sprites
	.globl _hal_update_hud
	.globl _hal_draw_tile
	.globl _is_dirty
	.globl _arrow_dir
	.globl _arrow_y
	.globl _arrow_x
	.globl _player_move_timer
	.globl _player_dir
	.globl _player_keys
	.globl _player_bombs
	.globl _player_score
	.globl _player_health
	.globl _player_y
	.globl _player_x
	.globl _local_player_idx
	.globl _player_joined
	.globl _monster_rotor
	.globl _current_level
	.globl _dandy_map
	.globl _dandy_num_levels
	.globl _delta_to_dir
	.globl _buttons_to_dir
	.globl _search_order
	.globl _dir_delta_y
	.globl _dir_delta_x
	.globl _row_offsets
	.globl _dandy_init
	.globl _dandy_load_level
	.globl _dandy_step
	.globl _dandy_draw_viewport
	.globl _dandy_join_player
	.globl _dandy_is_player_joined
;--------------------------------------------------------
; special function registers
;--------------------------------------------------------
	.area _HRAM
;--------------------------------------------------------
; ram data
;--------------------------------------------------------
	.area _DATA
_dandy_map::
	.ds 1800
_current_level::
	.ds 1
_monster_rotor::
	.ds 1
_player_joined::
	.ds 4
_local_player_idx::
	.ds 1
_player_x::
	.ds 4
_player_y::
	.ds 4
_player_health::
	.ds 8
_player_score::
	.ds 8
_player_bombs::
	.ds 4
_player_keys::
	.ds 4
_player_dir::
	.ds 4
_player_move_timer::
	.ds 4
_arrow_x::
	.ds 4
_arrow_y::
	.ds 4
_arrow_dir::
	.ds 4
_is_dirty::
	.ds 1
_flood_stack_x:
	.ds 64
_flood_stack_y:
	.ds 64
_do_player_buttons_old_buttons_10000_160:
	.ds 4
_move_monsters_rand_seed_80002_267:
	.ds 2
;--------------------------------------------------------
; ram data
;--------------------------------------------------------
	.area _INITIALIZED
_flood_stack_ptr:
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
;src/dandy_core.c:403: static uint8_t old_buttons[MAX_PLAYERS] = {0, 0, 0, 0};
	ld	hl, #_do_player_buttons_old_buttons_10000_160
	ld	(hl), #0x00
	inc	hl
	ld	(hl), #0x00
	ld	hl, #_do_player_buttons_old_buttons_10000_160 + 2
	ld	(hl), #0x00
	ld	hl, #_do_player_buttons_old_buttons_10000_160 + 3
	ld	(hl), #0x00
;src/dandy_core.c:689: static uint16_t rand_seed = 0xACE1;
	ld	hl, #_move_monsters_rand_seed_80002_267
	ld	(hl), #0xe1
	inc	hl
	ld	(hl), #0xac
;--------------------------------------------------------
; Home
;--------------------------------------------------------
	.area _HOME
	.area _HOME
;--------------------------------------------------------
; code
;--------------------------------------------------------
	.area _CODE
;src/dandy_core.c:103: static void flood_push(uint8_t x, uint8_t y) {
;	---------------------------------
; Function flood_push
; ---------------------------------
_flood_push:
	ld	c, a
	ld	b, e
;src/dandy_core.c:104: if (flood_stack_ptr < FLOOD_STACK_SIZE) {
	ld	hl, #_flood_stack_ptr
	ld	a, (hl)
	xor	a, #0x80
	sub	a, #0xc0
	ret	NC
;src/dandy_core.c:105: flood_stack_x[flood_stack_ptr] = x;
	ld	de, #_flood_stack_x+0
	push	hl
	ld	a, (hl)
	pop	hl
	ld	l, a
	rlca
	sbc	a, a
	ld	h, a
	add	hl, de
	ld	(hl), c
;src/dandy_core.c:106: flood_stack_y[flood_stack_ptr] = y;
	ld	de, #_flood_stack_y+0
	ld	a, (_flood_stack_ptr)
	ld	l, a
	rlca
	sbc	a, a
	ld	h, a
	add	hl, de
	ld	(hl), b
;src/dandy_core.c:107: flood_stack_ptr++;
	ld	hl, #_flood_stack_ptr
	inc	(hl)
;src/dandy_core.c:109: }
	ret
_row_offsets:
	.dw #0x0000
	.dw #0x003c
	.dw #0x0078
	.dw #0x00b4
	.dw #0x00f0
	.dw #0x012c
	.dw #0x0168
	.dw #0x01a4
	.dw #0x01e0
	.dw #0x021c
	.dw #0x0258
	.dw #0x0294
	.dw #0x02d0
	.dw #0x030c
	.dw #0x0348
	.dw #0x0384
	.dw #0x03c0
	.dw #0x03fc
	.dw #0x0438
	.dw #0x0474
	.dw #0x04b0
	.dw #0x04ec
	.dw #0x0528
	.dw #0x0564
	.dw #0x05a0
	.dw #0x05dc
	.dw #0x0618
	.dw #0x0654
	.dw #0x0690
	.dw #0x06cc
_dir_delta_x:
	.db #0x00	;  0
	.db #0x01	;  1
	.db #0x01	;  1
	.db #0x01	;  1
	.db #0x00	;  0
	.db #0xff	; -1
	.db #0xff	; -1
	.db #0xff	; -1
_dir_delta_y:
	.db #0xff	; -1
	.db #0xff	; -1
	.db #0x00	;  0
	.db #0x01	;  1
	.db #0x01	;  1
	.db #0x01	;  1
	.db #0x00	;  0
	.db #0xff	; -1
_search_order:
	.db #0x00	;  0
	.db #0xff	; -1
	.db #0x01	;  1
_buttons_to_dir:
	.db #0xff	; -1
	.db #0x06	;  6
	.db #0x02	;  2
	.db #0xff	; -1
	.db #0x00	;  0
	.db #0x07	;  7
	.db #0x01	;  1
	.db #0x00	;  0
	.db #0x04	;  4
	.db #0x05	;  5
	.db #0x03	;  3
	.db #0x04	;  4
	.db #0xff	; -1
	.db #0x06	;  6
	.db #0x02	;  2
	.db #0xff	; -1
_delta_to_dir:
	.db #0x07	;  7
	.db #0x00	;  0
	.db #0x01	;  1
	.db #0x06	;  6
	.db #0x00	;  0
	.db #0x02	;  2
	.db #0x05	;  5
	.db #0x04	;  4
	.db #0x03	;  3
_dandy_num_levels:
	.db #0x1a	; 26
;src/dandy_core.c:113: void dandy_init(void) {
;	---------------------------------
; Function dandy_init
; ---------------------------------
_dandy_init::
;src/dandy_core.c:114: current_level = 0;
	xor	a, a
	ld	(#_current_level),a
;src/dandy_core.c:115: player_joined[0] = true; // Player 1 is joined by default
	ld	bc, #_player_joined+0
	ld	a, #0x01
	ld	(bc), a
;src/dandy_core.c:116: for (uint8_t p = 1; p < MAX_PLAYERS; ++p) {
	ld	e, #0x01
00104$:
	ld	a, e
	sub	a, #0x04
	jr	NC, 00101$
;src/dandy_core.c:117: player_joined[p] = false;
	ld	l, e
	ld	h, #0x00
	add	hl, bc
	ld	(hl), #0x00
;src/dandy_core.c:116: for (uint8_t p = 1; p < MAX_PLAYERS; ++p) {
	inc	e
	jr	00104$
00101$:
;src/dandy_core.c:119: local_player_idx = 0;
;src/dandy_core.c:120: monster_rotor = 0;
	xor	a, a
	ld	(#_local_player_idx), a
	ld	(#_monster_rotor),a
;src/dandy_core.c:122: for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
	ld	c, #0x00
00107$:
	ld	a, c
	sub	a, #0x04
	jr	NC, 00102$
;src/dandy_core.c:123: player_score[p] = 0;
	ld	l, c
	ld	h, #0x00
	add	hl, hl
	ld	e, l
	ld	d, h
	ld	hl, #_player_score
	add	hl, de
	xor	a, a
	ld	(hl+), a
	ld	(hl), a
;src/dandy_core.c:124: player_health[p] = 100;
	ld	hl, #_player_health
	add	hl, de
	ld	a, #0x64
	ld	(hl+), a
	ld	(hl), #0x00
;src/dandy_core.c:125: player_bombs[p] = 0;
	ld	hl, #_player_bombs
	ld	b, #0x00
	add	hl, bc
	ld	(hl), #0x00
;src/dandy_core.c:126: player_keys[p] = 0;
	ld	hl, #_player_keys
	ld	b, #0x00
	add	hl, bc
	ld	(hl), #0x00
;src/dandy_core.c:127: player_dir[p] = 0;
	ld	hl, #_player_dir
	ld	b, #0x00
	add	hl, bc
	ld	(hl), #0x00
;src/dandy_core.c:128: player_move_timer[p] = 0;
	ld	hl, #_player_move_timer
	ld	b, #0x00
	add	hl, bc
	ld	(hl), #0x00
;src/dandy_core.c:129: arrow_dir[p] = -1;
	ld	hl, #_arrow_dir
	ld	b, #0x00
	add	hl, bc
	ld	(hl), #0xff
;src/dandy_core.c:122: for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
	inc	c
	jr	00107$
00102$:
;src/dandy_core.c:132: dandy_load_level(current_level);
	ld	a, (_current_level)
;src/dandy_core.c:133: }
	jp	_dandy_load_level
;src/dandy_core.c:135: void dandy_load_level(uint8_t level_idx) {
;	---------------------------------
; Function dandy_load_level
; ---------------------------------
_dandy_load_level::
	add	sp, #-13
;src/dandy_core.c:136: if (level_idx >= DANDY_NUM_LEVELS) {
	ld	c, a
	sub	a, #0x1a
	jr	C, 00102$
;src/dandy_core.c:137: level_idx = DANDY_NUM_LEVELS - 1;
	ld	c, #0x19
00102$:
;src/dandy_core.c:142: memset(dandy_map, TILE_WALL, MAP_SIZE);
	ld	de, #0x0708
	push	de
	ld	de, #0x0001
	push	de
	ld	de, #_dandy_map
	push	de
	call	_memset
	add	sp, #6
;src/dandy_core.c:145: const uint8_t* src = dandy_levels[level_idx];
	xor	a, a
	ld	b, a
	sla	c
	rl	b
	ld	hl, #_dandy_levels
	add	hl, bc
	ld	e, l
	ld	d, h
	ld	a, (de)
	ldhl	sp,	#7
	ld	(hl+), a
	inc	de
	ld	a, (de)
	ld	(hl), a
;src/dandy_core.c:146: const uint8_t* src_end = src + dandy_level_sizes[level_idx];
	ld	hl, #_dandy_level_sizes
	add	hl, bc
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	ldhl	sp,	#7
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, bc
	push	hl
	ld	a, l
	ldhl	sp,	#4
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#3
;src/dandy_core.c:147: uint8_t bit_cache = 0;
	ld	(hl+), a
	inc	hl
;src/dandy_core.c:148: uint8_t bit_count = 0;
	xor	a, a
	ld	(hl+), a
	ld	(hl), a
;src/dandy_core.c:152: for (uint8_t y = 1; y <= 28; ++y) {
	ldhl	sp,	#9
	ld	(hl), #0x01
00136$:
	ld	a, #0x1c
	ldhl	sp,	#9
	sub	a, (hl)
	jp	C, 00130$
;src/dandy_core.c:155: uint8_t* dst = &dandy_map[row_offsets[y] + 1];
	ld	a, (hl+)
	inc	hl
	ld	(hl+), a
	xor	a, a
	ld	(hl-), a
	ld	a, (hl)
	ldhl	sp,	#0
	ld	(hl+), a
	xor	a, a
	ld	(hl-), a
	sla	(hl)
	inc	hl
	rl	(hl)
	pop	de
	push	de
	ld	hl, #_row_offsets
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#13
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#12
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	ld	c, a
	inc	de
	ld	a, (de)
	ld	b, a
	inc	bc
	ld	hl, #_dandy_map
	add	hl, bc
	ld	c, l
	ld	a, h
	ldhl	sp,	#10
	ld	(hl), c
	inc	hl
;src/dandy_core.c:157: for (uint8_t x = 1; x <= 58; ++x) {
	ld	(hl+), a
	ld	(hl), #0x01
00133$:
	ld	a, #0x3a
	ldhl	sp,	#12
	sub	a, (hl)
	jp	C, 00137$
;src/dandy_core.c:159: if (bit_count == 0) {
	ldhl	sp,	#6
	ld	a, (hl)
	or	a, a
	jr	NZ, 00104$
;src/dandy_core.c:160: bit_cache = (src < src_end) ? *src++ : 0;
	ldhl	sp,	#7
	ld	e, l
	ld	d, h
	ldhl	sp,	#2
	ld	a, (de)
	inc	de
	sub	a, (hl)
	inc	hl
	ld	a, (de)
	sbc	a, (hl)
	jr	NC, 00143$
	ldhl	sp,#7
	ld	a, (hl+)
	ld	e, a
	ld	a, (hl-)
	ld	d, a
	ld	a, (de)
	inc	(hl)
	jr	NZ, 00144$
	inc	hl
	inc	(hl)
	jr	00144$
00143$:
	xor	a, a
00144$:
	ldhl	sp,	#5
;src/dandy_core.c:161: bit_count = 8;
	ld	(hl+), a
	ld	(hl), #0x08
00104$:
;src/dandy_core.c:168: bit_cache <<= 1;
	ldhl	sp,	#5
	ld	a, (hl-)
	add	a, a
;src/dandy_core.c:169: bit_count--;
	ld	(hl+), a
	inc	hl
	dec	(hl)
;src/dandy_core.c:165: if ((bit_cache & 0x80) == 0) {
	push	hl
	dec	hl
	bit	7, (hl)
	pop	hl
	jr	NZ, 00127$
;src/dandy_core.c:167: *dst = TILE_SPACE;
	ldhl	sp,	#10
	ld	a, (hl+)
	ld	h, (hl)
	ld	l, a
	ld	(hl), #0x00
;src/dandy_core.c:168: bit_cache <<= 1;
	ldhl	sp,	#4
	ld	a, (hl+)
	ld	(hl), a
;src/dandy_core.c:169: bit_count--;
	jp	00128$
00127$:
;src/dandy_core.c:172: bit_cache <<= 1;
;src/dandy_core.c:173: bit_count--;
;src/dandy_core.c:175: if (bit_count == 0) {
	ldhl	sp,	#6
	ld	a, (hl)
	or	a, a
	jr	NZ, 00106$
;src/dandy_core.c:176: bit_cache = (src < src_end) ? *src++ : 0;
	ldhl	sp,	#7
	ld	e, l
	ld	d, h
	ldhl	sp,	#2
	ld	a, (de)
	inc	de
	sub	a, (hl)
	inc	hl
	ld	a, (de)
	sbc	a, (hl)
	jr	NC, 00145$
	ldhl	sp,#7
	ld	a, (hl+)
	ld	e, a
	ld	a, (hl-)
	dec	hl
	ld	d, a
	ld	a, (de)
	ld	(hl+), a
	inc	(hl)
	jr	NZ, 00146$
	inc	hl
	inc	(hl)
	jr	00146$
00145$:
	ldhl	sp,	#6
	ld	(hl), #0x00
00146$:
	ldhl	sp,	#6
	ld	a, (hl-)
	dec	hl
;src/dandy_core.c:177: bit_count = 8;
	ld	(hl+), a
	inc	hl
	ld	(hl), #0x08
00106$:
;src/dandy_core.c:168: bit_cache <<= 1;
	ldhl	sp,	#4
	ld	a, (hl+)
	add	a, a
;src/dandy_core.c:169: bit_count--;
	ld	(hl+), a
	dec	(hl)
;src/dandy_core.c:181: if ((bit_cache & 0x80) == 0) {
	push	hl
	dec	hl
	dec	hl
	bit	7, (hl)
	pop	hl
	jp	Z, 00128$
;src/dandy_core.c:185: bit_cache <<= 1;
;src/dandy_core.c:186: bit_count--;
;src/dandy_core.c:189: bit_cache <<= 1;
;src/dandy_core.c:190: bit_count--;
;src/dandy_core.c:196: if (bit_count == 0) { bit_cache = (src < src_end) ? *src++ : 0; bit_count = 8; }
	ldhl	sp,	#6
	ld	a, (hl)
	or	a, a
	jr	NZ, 00108$
	ldhl	sp,	#7
	ld	e, l
	ld	d, h
	ldhl	sp,	#2
	ld	a, (de)
	inc	de
	sub	a, (hl)
	inc	hl
	ld	a, (de)
	sbc	a, (hl)
	jr	NC, 00147$
	ldhl	sp,#7
	ld	a, (hl+)
	ld	e, a
	ld	a, (hl-)
	dec	hl
	ld	d, a
	ld	a, (de)
	ld	(hl+), a
	inc	(hl)
	jr	NZ, 00341$
	inc	hl
	inc	(hl)
00341$:
	ldhl	sp,	#6
	ld	a, (hl)
	jr	00148$
00147$:
	xor	a, a
00148$:
	ldhl	sp,	#5
	ld	(hl+), a
	ld	(hl), #0x08
00108$:
;src/dandy_core.c:197: tile_id <<= 1; if (bit_cache & 0x80) tile_id |= 1; bit_cache <<= 1; bit_count--;
	ld	c, #0x00
	push	hl
	ldhl	sp,	#7
	bit	7, (hl)
	pop	hl
	jr	Z, 00110$
	ld	c, #0x01
00110$:
	ldhl	sp,	#5
	ld	a, (hl+)
	add	a, a
	ld	e, (hl)
	dec	e
	jr	NZ, 00112$
;src/dandy_core.c:200: if (bit_count == 0) { bit_cache = (src < src_end) ? *src++ : 0; bit_count = 8; }
	ldhl	sp,	#7
	ld	e, l
	ld	d, h
	ldhl	sp,	#2
	ld	a, (de)
	inc	de
	sub	a, (hl)
	inc	hl
	ld	a, (de)
	sbc	a, (hl)
	jr	NC, 00149$
	ldhl	sp,#7
	ld	a, (hl+)
	ld	e, a
	ld	a, (hl-)
	ld	d, a
	ld	a, (de)
	inc	(hl)
	jr	NZ, 00150$
	inc	hl
	inc	(hl)
	jr	00150$
00149$:
	xor	a, a
00150$:
	ld	e, #0x08
00112$:
;src/dandy_core.c:201: tile_id <<= 1; if (bit_cache & 0x80) tile_id |= 1; bit_cache <<= 1; bit_count--;
	sla	c
	bit	7, a
	jr	Z, 00114$
	set	0, c
00114$:
	add	a, a
	dec	e
	jr	NZ, 00116$
;src/dandy_core.c:204: if (bit_count == 0) { bit_cache = (src < src_end) ? *src++ : 0; bit_count = 8; }
	ldhl	sp,	#7
	ld	e, l
	ld	d, h
	ldhl	sp,	#2
	ld	a, (de)
	inc	de
	sub	a, (hl)
	inc	hl
	ld	a, (de)
	sbc	a, (hl)
	jr	NC, 00151$
	ldhl	sp,#7
	ld	a, (hl+)
	ld	e, a
	ld	a, (hl-)
	ld	d, a
	ld	a, (de)
	inc	(hl)
	jr	NZ, 00152$
	inc	hl
	inc	(hl)
	jr	00152$
00151$:
	xor	a, a
00152$:
	ld	e, #0x08
00116$:
;src/dandy_core.c:205: tile_id <<= 1; if (bit_cache & 0x80) tile_id |= 1; bit_cache <<= 1; bit_count--;
	sla	c
	bit	7, a
	jr	Z, 00118$
	set	0, c
00118$:
	add	a, a
	dec	e
	jr	NZ, 00120$
;src/dandy_core.c:208: if (bit_count == 0) { bit_cache = (src < src_end) ? *src++ : 0; bit_count = 8; }
	ldhl	sp,	#7
	ld	e, l
	ld	d, h
	ldhl	sp,	#2
	ld	a, (de)
	inc	de
	sub	a, (hl)
	inc	hl
	ld	a, (de)
	sbc	a, (hl)
	jr	NC, 00153$
	ldhl	sp,#7
	ld	a, (hl+)
	ld	e, a
	ld	a, (hl-)
	ld	d, a
	ld	a, (de)
	inc	(hl)
	jr	NZ, 00154$
	inc	hl
	inc	(hl)
	jr	00154$
00153$:
	xor	a, a
00154$:
	ld	e, #0x08
00120$:
;src/dandy_core.c:209: tile_id <<= 1; if (bit_cache & 0x80) tile_id |= 1; bit_cache <<= 1; bit_count--;
	sla	c
	bit	7, a
	jr	Z, 00122$
	set	0, c
00122$:
	add	a, a
	ldhl	sp,	#5
	ld	(hl+), a
	ld	a, e
	dec	a
	ld	(hl), a
;src/dandy_core.c:211: *dst = tile_id;
	ldhl	sp,	#10
	ld	a, (hl+)
	ld	h, (hl)
	ld	l, a
	ld	(hl), c
00128$:
;src/dandy_core.c:216: dst++;
	ldhl	sp,	#10
	inc	(hl)
	jr	NZ, 00349$
	inc	hl
	inc	(hl)
00349$:
;src/dandy_core.c:157: for (uint8_t x = 1; x <= 58; ++x) {
	ldhl	sp,	#12
	inc	(hl)
	jp	00133$
00137$:
;src/dandy_core.c:152: for (uint8_t y = 1; y <= 28; ++y) {
	ldhl	sp,	#9
	inc	(hl)
	jp	00136$
00130$:
;src/dandy_core.c:221: set_player_start_position();
	call	_set_player_start_position
;src/dandy_core.c:223: for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
	ld	c, #0x00
00139$:
	ld	a, c
	sub	a, #0x04
	jr	NC, 00131$
;src/dandy_core.c:224: arrow_dir[p] = -1;
	ld	hl, #_arrow_dir
	ld	b, #0x00
	add	hl, bc
	ld	(hl), #0xff
;src/dandy_core.c:223: for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
	inc	c
	jr	00139$
00131$:
;src/dandy_core.c:226: is_dirty = true;
	ld	hl, #_is_dirty
	ld	(hl), #0x01
;src/dandy_core.c:227: }
	add	sp, #13
	ret
;src/dandy_core.c:229: void dandy_step(const uint8_t player_inputs[MAX_PLAYERS]) {
;	---------------------------------
; Function dandy_step
; ---------------------------------
_dandy_step::
	add	sp, #-6
	ldhl	sp,	#3
	ld	a, e
	ld	(hl+), a
;src/dandy_core.c:231: for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
	ld	a, d
	ld	(hl+), a
	ld	(hl), #0x00
00119$:
	ldhl	sp,	#5
	ld	a, (hl)
	sub	a, #0x04
	jr	NC, 00107$
;src/dandy_core.c:232: if (player_joined[p]) {
	ld	de, #_player_joined
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	ld	c, l
	ld	b, h
	ld	a, (bc)
	bit	0,a
	jr	Z, 00120$
;src/dandy_core.c:233: if (player_x[p] >= DANDY_LEVEL_WIDTH) player_x[p] = DANDY_LEVEL_WIDTH - 1;
	ld	de, #_player_x
	ldhl	sp,	#5
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#3
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#2
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	sub	a, #0x3c
	jr	C, 00102$
	ld	a, (hl-)
	ld	l, (hl)
	ld	h, a
	ld	(hl), #0x3b
00102$:
;src/dandy_core.c:234: if (player_y[p] >= DANDY_LEVEL_HEIGHT) player_y[p] = DANDY_LEVEL_HEIGHT - 1;
	ld	de, #_player_y
	ldhl	sp,	#5
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	ld	c, l
	ld	b, h
	ld	a, (bc)
	sub	a, #0x1e
	jr	C, 00120$
	ld	a, #0x1d
	ld	(bc), a
00120$:
;src/dandy_core.c:231: for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
	ldhl	sp,	#5
	inc	(hl)
	jr	00119$
00107$:
;src/dandy_core.c:237: for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
	ld	c, #0x00
00122$:
	ld	a, c
	sub	a, #0x04
	jr	NC, 00111$
;src/dandy_core.c:238: if (player_joined[p] && player_health[p] > 0) {
	ld	hl, #_player_joined
	ld	b, #0x00
	add	hl, bc
	ld	b, (hl)
	bit	0, b
	jr	Z, 00123$
	ld	l, c
	xor	a, a
	ld	h, a
	add	hl, hl
	ld	de, #_player_health
	add	hl, de
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	ld	e, h
	xor	a, a
	ld	d, a
	cp	a, l
	sbc	a, h
	bit	7, e
	jr	Z, 00229$
	bit	7, d
	jr	NZ, 00230$
	cp	a, a
	jr	00230$
00229$:
	bit	7, d
	jr	Z, 00230$
	scf
00230$:
	jr	NC, 00123$
;src/dandy_core.c:239: do_player_buttons(p, player_inputs[p]);
	ldhl	sp,#3
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	l, c
	ld	h, #0x00
	add	hl, de
	ld	e, l
	ld	d, h
	ld	a, (de)
	push	bc
	ld	e, a
	ld	a, c
	call	_do_player_buttons
	pop	bc
00123$:
;src/dandy_core.c:237: for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
	inc	c
	jr	00122$
00111$:
;src/dandy_core.c:242: move_arrows();
	call	_move_arrows
;src/dandy_core.c:243: move_monsters();
	call	_move_monsters
;src/dandy_core.c:246: hal_update_hud();
	call	_hal_update_hud
;src/dandy_core.c:249: bool all_dead = true;
	ldhl	sp,	#0
	ld	(hl), #0x01
;src/dandy_core.c:250: for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
	ldhl	sp,	#5
	ld	(hl), #0x00
00125$:
	ldhl	sp,	#5
	ld	a, (hl)
	sub	a, #0x04
	jr	NC, 00115$
;src/dandy_core.c:251: if (player_joined[p] && player_health[p] > 0) {
	ld	de, #_player_joined
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#3
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#2
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	bit	0,a
	jr	Z, 00126$
	ldhl	sp,	#5
	ld	c, (hl)
	xor	a, a
	ld	l, c
	ld	h, a
	add	hl, hl
	ld	de, #_player_health
	add	hl, de
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	ld	e, b
	xor	a, a
	ld	d, a
	cp	a, c
	sbc	a, b
	bit	7, e
	jr	Z, 00231$
	bit	7, d
	jr	NZ, 00232$
	cp	a, a
	jr	00232$
00231$:
	bit	7, d
	jr	Z, 00232$
	scf
00232$:
	jr	NC, 00126$
;src/dandy_core.c:252: all_dead = false;
	ldhl	sp,	#0
	ld	(hl), #0x00
;src/dandy_core.c:253: break;
	jr	00115$
00126$:
;src/dandy_core.c:250: for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
	ldhl	sp,	#5
	inc	(hl)
	jr	00125$
00115$:
;src/dandy_core.c:257: if (all_dead) {
	ldhl	sp,	#0
	bit	0, (hl)
	jr	Z, 00127$
;src/dandy_core.c:258: end_game();
	call	_end_game
00127$:
;src/dandy_core.c:260: }
	add	sp, #6
	ret
;src/dandy_core.c:262: static void get_camera_target(uint8_t p_idx, int16_t* out_x, int16_t* out_y) {
;	---------------------------------
; Function get_camera_target
; ---------------------------------
_get_camera_target:
	add	sp, #-11
	ld	c, a
	ldhl	sp,	#8
	ld	a, e
	ld	(hl+), a
	ld	(hl), d
;src/dandy_core.c:263: int16_t target_x = player_x[p_idx];
	ld	hl, #_player_x
	ld	b, #0x00
	add	hl, bc
	ld	a, (hl)
	ldhl	sp,	#0
	ld	(hl+), a
	ld	(hl), #0x00
;src/dandy_core.c:264: int16_t target_y = player_y[p_idx];
	ld	hl, #_player_y
	ld	b, #0x00
	add	hl, bc
	ld	a, (hl)
	ldhl	sp,	#2
	ld	(hl+), a
	ld	(hl), #0x00
;src/dandy_core.c:267: if (player_health[p_idx] <= 0) {
	ld	l, c
	xor	a, a
	ld	h, a
	add	hl, hl
	ld	de, #_player_health
	add	hl, de
	ld	a,	(hl+)
	ld	b, (hl)
	ld	l, a
	ld	e, b
	xor	a, a
	ld	d, a
	cp	a, l
	sbc	a, b
	bit	7, e
	jr	Z, 00165$
	bit	7, d
	jr	NZ, 00166$
	cp	a, a
	jr	00166$
00165$:
	bit	7, d
	jr	Z, 00166$
	scf
00166$:
	jp	C, 00109$
;src/dandy_core.c:268: uint16_t sum_x = 0;
	xor	a, a
	ldhl	sp,	#4
	ld	(hl+), a
;src/dandy_core.c:269: uint16_t sum_y = 0;
	ld	(hl+), a
	xor	a, a
	ld	(hl+), a
	ld	(hl), a
;src/dandy_core.c:271: for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
	ldhl	sp,	#10
	ld	(hl), #0x00
	ld	b, #0x00
00111$:
	ld	a, b
	sub	a, #0x04
	jr	NC, 00105$
;src/dandy_core.c:272: if (p != p_idx && player_joined[p] && player_health[p] > 0) {
	ld	a, c
	sub	a, b
	jr	Z, 00112$
	ld	a, #<(_player_joined)
	add	a, b
	ld	l, a
	ld	a, #>(_player_joined)
	adc	a, #0x00
	ld	h, a
	bit	0, (hl)
	jr	Z, 00112$
	ld	l, b
	xor	a, a
	ld	h, a
	add	hl, hl
	ld	de, #_player_health
	add	hl, de
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	ld	e, h
	xor	a, a
	ld	d, a
	cp	a, l
	sbc	a, h
	bit	7, e
	jr	Z, 00168$
	bit	7, d
	jr	NZ, 00169$
	cp	a, a
	jr	00169$
00168$:
	bit	7, d
	jr	Z, 00169$
	scf
00169$:
	jr	NC, 00112$
;src/dandy_core.c:273: sum_x += player_x[p];
	ld	a, #<(_player_x)
	add	a, b
	ld	l, a
	ld	a, #>(_player_x)
	adc	a, #0x00
	ld	h, a
	ld	a, (hl)
	ldhl	sp,	#4
	ld	e, (hl)
	inc	hl
	ld	d, (hl)
	ld	l, #0x00
	add	a, e
	ld	e, a
	ld	a, l
	adc	a, d
	ldhl	sp,	#4
	ld	(hl), e
	inc	hl
	ld	(hl), a
;src/dandy_core.c:274: sum_y += player_y[p];
	ld	a, #<(_player_y)
	add	a, b
	ld	l, a
	ld	a, #>(_player_y)
	adc	a, #0x00
	ld	h, a
	ld	a, (hl)
	ldhl	sp,	#6
	ld	e, (hl)
	inc	hl
	ld	d, (hl)
	ld	l, a
	ld	h, #0x00
	add	hl, de
	ld	e, l
	ld	d, h
	ldhl	sp,	#6
	ld	a, e
	ld	(hl+), a
	ld	(hl), d
;src/dandy_core.c:275: alive_count++;
	ldhl	sp,	#10
	inc	(hl)
00112$:
;src/dandy_core.c:271: for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
	inc	b
	jr	00111$
00105$:
;src/dandy_core.c:278: if (alive_count > 0) {
	ldhl	sp,	#10
	ld	a, (hl)
	or	a, a
	jr	Z, 00109$
;src/dandy_core.c:279: target_x = sum_x / alive_count;
	ld	c, (hl)
	ld	b, #0x00
	push	bc
	ldhl	sp,	#6
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	call	__divuint
	ld	e, c
	ld	d, b
	pop	bc
	inc	sp
	inc	sp
	push	de
;src/dandy_core.c:280: target_y = sum_y / alive_count;
	ldhl	sp,	#6
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	call	__divuint
	ldhl	sp,	#2
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
00109$:
;src/dandy_core.c:283: *out_x = target_x;
	ldhl	sp,	#8
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ldhl	sp,	#0
	ld	a, (hl+)
	ld	(de), a
	inc	de
	ld	a, (hl)
	ld	(de), a
;src/dandy_core.c:284: *out_y = target_y;
	ldhl	sp,	#13
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	ldhl	sp,	#2
	ld	a, (hl+)
	ld	(bc), a
	inc	bc
	ld	a, (hl)
	ld	(bc), a
;src/dandy_core.c:285: }
	add	sp, #11
	pop	hl
	pop	af
	jp	(hl)
;src/dandy_core.c:287: void dandy_draw_viewport(uint8_t local_p_idx) {
;	---------------------------------
; Function dandy_draw_viewport
; ---------------------------------
_dandy_draw_viewport::
	add	sp, #-22
;src/dandy_core.c:288: if (local_p_idx >= MAX_PLAYERS || !player_joined[local_p_idx]) local_p_idx = 0;
	ld	c, a
	sub	a, #0x04
	jr	NC, 00101$
	ld	hl, #_player_joined
	ld	b, #0x00
	add	hl, bc
	bit	0, (hl)
	jr	NZ, 00102$
00101$:
	ld	c, #0x00
00102$:
;src/dandy_core.c:291: get_camera_target(local_p_idx, &target_x, &target_y);
	ldhl	sp,	#0
	ld	e, l
	ld	d, h
	ld	hl, #2
	add	hl, sp
	push	hl
	ld	a, c
	call	_get_camera_target
;src/dandy_core.c:293: int16_t vp_left = clamp(target_x - 10, 0, DANDY_LEVEL_WIDTH - 20);
	ldhl	sp,	#0
	ld	a, (hl+)
	ld	c, (hl)
	add	a, #0xf6
	ld	e, a
	ld	a, c
	adc	a, #0xff
	ld	bc, #0x0028
	push	bc
	ld	bc, #0x0000
	ld	d, a
	call	_clamp
	ldhl	sp,	#4
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;src/dandy_core.c:294: int16_t vp_top = clamp(target_y - 5, 0, DANDY_LEVEL_HEIGHT - 10);
	ldhl	sp,	#2
	ld	a, (hl+)
	ld	c, (hl)
	add	a, #0xfb
	ld	e, a
	ld	a, c
	adc	a, #0xff
	ld	bc, #0x0014
	push	bc
	ld	bc, #0x0000
	ld	d, a
	call	_clamp
	ldhl	sp,	#6
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;src/dandy_core.c:297: hal_clear_sprites((uint8_t)vp_left, (uint8_t)vp_top);
	ldhl	sp,	#6
	ld	a, (hl-)
	dec	hl
	ld	e, a
	ld	a, (hl)
	call	_hal_clear_sprites
;src/dandy_core.c:298: uint8_t sprite_count = 0;
	ldhl	sp,	#21
	ld	(hl), #0x00
;src/dandy_core.c:301: for (uint8_t sy = 0; sy < 10; ++sy) {
	ldhl	sp,	#18
	ld	(hl), #0x00
00138$:
	ldhl	sp,	#18
	ld	a, (hl)
	sub	a, #0x0a
	jp	NC, 00140$
;src/dandy_core.c:302: uint16_t row_offset = row_offsets[vp_top + sy];
	ldhl	sp,	#6
	ld	a, (hl)
	ldhl	sp,	#17
	ld	(hl+), a
	ld	a, (hl+)
	inc	hl
	ld	(hl), a
	ldhl	sp,	#17
	add	a, (hl)
	ldhl	sp,	#20
	ld	(hl), a
	ld	a, (hl-)
	ld	(hl+), a
	rlca
	sbc	a, a
	ld	(hl-), a
	ld	a, (hl)
	ldhl	sp,	#16
	ld	(hl), a
	ldhl	sp,	#20
	ld	a, (hl)
	ldhl	sp,	#17
	ld	(hl-), a
	sla	(hl)
	inc	hl
	rl	(hl)
	dec	hl
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #_row_offsets
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#21
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#20
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	ldhl	sp,	#8
	ld	(hl+), a
	inc	de
	ld	a, (de)
	ld	(hl), a
;src/dandy_core.c:303: for (uint8_t sx = 0; sx < 20; ++sx) {
	ldhl	sp,	#18
	ld	a, (hl)
	add	a, a
	add	a, a
	add	a, a
	ldhl	sp,	#10
	ld	(hl), a
	ldhl	sp,	#21
	ld	a, (hl-)
	dec	hl
	ld	(hl+), a
	ld	(hl), #0x00
00135$:
	ldhl	sp,	#20
;src/dandy_core.c:304: uint8_t tile = dandy_map[row_offset + (vp_left + sx)];
	ld	a,(hl)
	cp	a,#0x14
	jp	NC,00163$
	ld	c, #0x00
	ldhl	sp,	#4
	ld	e, (hl)
	inc	hl
	ld	d, (hl)
	ld	l, a
	ld	h, c
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#13
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#12
	ld	(hl), a
	ldhl	sp,	#8
	ld	a, (hl+)
	ld	c, (hl)
	inc	hl
	inc	hl
	ld	e, (hl)
	inc	hl
	ld	d, (hl)
	ld	l, a
	ld	h, c
	add	hl, de
	ld	de, #_dandy_map
	add	hl, de
	ld	a, (hl)
	ldhl	sp,	#13
	ld	(hl), a
;src/dandy_core.c:307: bool is_sprite = false;
	ld	c, #0x00
;src/dandy_core.c:312: } else if (tile >= TILE_ARROW && tile <= TILE_ARROW + 7) {
	ldhl	sp,	#13
	ld	a, (hl)
	sub	a, #0x10
	ld	a, #0x00
	rla
	ldhl	sp,	#17
	ld	(hl), a
	ld	a, #0x17
	ldhl	sp,	#13
	sub	a, (hl)
	ld	a, #0x00
	rla
	ldhl	sp,	#21
	ld	(hl), a
;src/dandy_core.c:308: if (tile >= 24 && tile <= 55) {
	ldhl	sp,	#13
	ld	a, (hl)
	sub	a, #0x18
	jr	C, 00112$
	ld	a, #0x37
	sub	a, (hl)
	jr	C, 00112$
;src/dandy_core.c:309: is_sprite = true; // Players
	ld	c, #0x01
	jr	00113$
00112$:
;src/dandy_core.c:310: } else if (tile >= TILE_MONSTER1 && tile <= TILE_MONSTER3) {
	ldhl	sp,	#13
	ld	a, (hl)
	sub	a, #0x09
	jr	C, 00108$
	ld	a, #0x0b
	sub	a, (hl)
	jr	C, 00108$
;src/dandy_core.c:311: is_sprite = true; // Monsters
	ld	c, #0x01
	jr	00113$
00108$:
;src/dandy_core.c:312: } else if (tile >= TILE_ARROW && tile <= TILE_ARROW + 7) {
	ldhl	sp,	#17
	bit	0, (hl)
	jr	NZ, 00113$
	ldhl	sp,	#21
	bit	0, (hl)
	jr	NZ, 00113$
;src/dandy_core.c:313: is_sprite = true; // Arrows
	ld	c, #0x01
00113$:
;src/dandy_core.c:316: if (is_sprite) {
	bit	0, c
	jp	Z, 00127$
;src/dandy_core.c:318: hal_draw_tile(sx, sy, TILE_SPACE);
	xor	a, a
	push	af
	inc	sp
	ldhl	sp,	#19
	ld	a, (hl+)
	inc	hl
	ld	e, a
	ld	a, (hl)
	call	_hal_draw_tile
;src/dandy_core.c:321: if (sprite_count < 40) {
	ldhl	sp,	#19
	ld	a, (hl)
	sub	a, #0x28
	jp	NC, 00136$
;src/dandy_core.c:322: uint8_t sprite_flags = 0;
	ldhl	sp,	#14
	ld	(hl), #0x00
;src/dandy_core.c:323: if (tile >= TILE_ARROW && tile <= TILE_ARROW + 7) {
	ldhl	sp,	#17
	bit	0, (hl)
	jp	NZ, 00122$
	ldhl	sp,	#21
	bit	0, (hl)
	jp	NZ, 00122$
;src/dandy_core.c:325: for (uint8_t ap = 0; ap < MAX_PLAYERS; ++ap) {
	ldhl	sp,	#15
	ld	(hl), #0x00
	ldhl	sp,	#21
	ld	(hl), #0x00
00132$:
	ldhl	sp,	#21
	ld	a, (hl)
	sub	a, #0x04
	jr	NC, 00122$
;src/dandy_core.c:326: if (player_joined[ap] && arrow_dir[ap] != -1 &&
	ld	de, #_player_joined
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#18
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#17
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	bit	0,a
	jr	Z, 00133$
	ld	de, #_arrow_dir
	ldhl	sp,	#21
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	ld	c, l
	ld	b, h
	ld	a, (bc)
	inc	a
	jr	Z, 00133$
;src/dandy_core.c:327: arrow_x[ap] == (vp_left + sx) && arrow_y[ap] == (vp_top + sy)) {
	ld	de, #_arrow_x
	ldhl	sp,	#21
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	ld	c, l
	ld	b, h
	ld	a, (bc)
	ld	c, a
	ld	b, #0x00
	ldhl	sp,	#11
	ld	a, (hl)
	sub	a, c
	jr	NZ, 00133$
	inc	hl
	ld	a, (hl)
	sub	a, b
	jr	NZ, 00133$
	ld	de, #_arrow_y
	ldhl	sp,	#21
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	ld	c, l
	ld	b, h
	ld	a, (bc)
	ld	c, a
	ldhl	sp,	#18
	ld	a, (hl)
	ld	b, #0x00
	ldhl	sp,	#6
	ld	e, (hl)
	inc	hl
	ld	d, (hl)
	ld	l, a
	ld	h, b
	add	hl, de
	ld	b, #0x00
	ld	a, l
	sub	a, c
	jr	NZ, 00133$
	ld	a, h
	sub	a, b
	jr	NZ, 00133$
;src/dandy_core.c:328: sprite_flags = ap; // Store player index (0..3) in flags
	ldhl	sp,	#15
	ld	a, (hl-)
	ld	(hl), a
;src/dandy_core.c:329: break;
	jr	00122$
00133$:
;src/dandy_core.c:325: for (uint8_t ap = 0; ap < MAX_PLAYERS; ++ap) {
	ldhl	sp,	#21
	inc	(hl)
	ld	a, (hl)
	ldhl	sp,	#15
	ld	(hl), a
	jr	00132$
00122$:
;src/dandy_core.c:333: hal_set_sprite(sprite_count++, sx * 8, sy * 8, tile, sprite_flags);
	ldhl	sp,	#20
	ld	a, (hl-)
	add	a, a
	add	a, a
	add	a, a
	ld	e, a
	ld	a, (hl)
	inc	(hl)
	ldhl	sp,	#14
	ld	h, (hl)
	push	hl
	inc	sp
	ldhl	sp,	#14
	ld	h, (hl)
	push	hl
	inc	sp
	ldhl	sp,	#12
	ld	h, (hl)
	push	hl
	inc	sp
	call	_hal_set_sprite
	jr	00136$
00127$:
;src/dandy_core.c:337: hal_draw_tile(sx, sy, tile);
	ldhl	sp,	#13
	ld	a, (hl)
	push	af
	inc	sp
	ldhl	sp,	#19
	ld	a, (hl+)
	inc	hl
	ld	e, a
	ld	a, (hl)
	call	_hal_draw_tile
00136$:
;src/dandy_core.c:303: for (uint8_t sx = 0; sx < 20; ++sx) {
	ldhl	sp,	#20
	inc	(hl)
	jp	00135$
00163$:
	ldhl	sp,	#19
	ld	a, (hl+)
	inc	hl
	ld	(hl), a
;src/dandy_core.c:301: for (uint8_t sy = 0; sy < 10; ++sy) {
	ldhl	sp,	#18
	inc	(hl)
	jp	00138$
00140$:
;src/dandy_core.c:341: }
	add	sp, #22
	ret
;src/dandy_core.c:346: static void set_player_start_position(void) {
;	---------------------------------
; Function set_player_start_position
; ---------------------------------
_set_player_start_position:
	add	sp, #-11
;src/dandy_core.c:347: int16_t up_x = 1, up_y = 2; // Fallback defaults
	ldhl	sp,	#0
	ld	a, #0x01
	ld	(hl+), a
;src/dandy_core.c:348: bool found = false;
	ld	a, #0x02
	ld	(hl+), a
	ld	(hl), #0x00
;src/dandy_core.c:352: for (uint8_t y = 0; y < DANDY_LEVEL_HEIGHT; ++y) {
	ldhl	sp,	#9
	ld	(hl), #0x00
00114$:
	ldhl	sp,	#9
	ld	a, (hl)
	sub	a, #0x1e
	jr	NC, 00106$
;src/dandy_core.c:353: uint16_t row_offset = row_offsets[y];
	ld	c, (hl)
	xor	a, a
	ld	l, c
	ld	h, a
	add	hl, hl
	ld	de, #_row_offsets
	add	hl, de
	ld	e, l
	ld	d, h
	ld	a, (de)
	ldhl	sp,	#3
	ld	(hl+), a
	inc	de
	ld	a, (de)
	ld	(hl), a
;src/dandy_core.c:354: for (uint8_t x = 0; x < DANDY_LEVEL_WIDTH; ++x) {
	ldhl	sp,	#5
	ld	(hl), #0x00
	ldhl	sp,	#10
	ld	(hl), #0x00
00111$:
	ldhl	sp,	#10
;src/dandy_core.c:355: if (dandy_map[row_offset + x] == TILE_UP) {
	ld	a,(hl)
	cp	a,#0x3c
	jr	NC, 00103$
	ldhl	sp,	#6
	ld	(hl), a
	ldhl	sp,	#3
	ld	a, (hl)
	ldhl	sp,	#7
	ld	(hl), a
	ldhl	sp,	#4
	ld	a, (hl)
	ldhl	sp,	#8
	ld	(hl-), a
	dec	hl
	ld	a, (hl+)
	ld	c, a
	ld	b, #0x00
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, bc
	ld	c, l
	ld	b, h
	ld	hl, #_dandy_map
	add	hl, bc
	ld	a, (hl)
	sub	a, #0x03
	jr	NZ, 00112$
;src/dandy_core.c:356: up_x = x;
	ldhl	sp,	#5
	ld	a, (hl)
	ldhl	sp,	#0
	ld	(hl), a
;src/dandy_core.c:357: up_y = y;
	ldhl	sp,	#9
	ld	a, (hl)
	ldhl	sp,	#1
;src/dandy_core.c:358: found = true;
	ld	(hl+), a
	ld	(hl), #0x01
;src/dandy_core.c:359: break;
	jr	00103$
00112$:
;src/dandy_core.c:354: for (uint8_t x = 0; x < DANDY_LEVEL_WIDTH; ++x) {
	ldhl	sp,	#10
	inc	(hl)
	ld	a, (hl)
	ldhl	sp,	#5
	ld	(hl), a
	jr	00111$
00103$:
;src/dandy_core.c:362: if (found) break;
	ldhl	sp,	#2
	bit	0, (hl)
	jr	NZ, 00106$
;src/dandy_core.c:352: for (uint8_t y = 0; y < DANDY_LEVEL_HEIGHT; ++y) {
	ldhl	sp,	#9
	inc	(hl)
	jr	00114$
00106$:
;src/dandy_core.c:365: for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
	ldhl	sp,	#10
	ld	(hl), #0x00
00117$:
	ldhl	sp,	#10
	ld	a, (hl)
	sub	a, #0x04
	jp	NC, 00119$
;src/dandy_core.c:366: int16_t px = clamp(up_x + spawn_offsets_x[p], 0, DANDY_LEVEL_WIDTH - 1);
	ld	de, #_spawn_offsets_x
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#10
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#9
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	ld	(hl), a
	ldhl	sp,	#4
	ld	(hl+), a
	rlca
	sbc	a, a
	ld	(hl), a
	ldhl	sp,	#0
	ld	a, (hl)
	ldhl	sp,	#6
	ld	(hl+), a
	xor	a, a
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ldhl	sp,	#4
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#10
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#9
	ld	(hl-), a
	ld	de, #0x003b
	push	de
	ld	bc, #0x0000
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	call	_clamp
	ldhl	sp,	#6
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;src/dandy_core.c:367: int16_t py = clamp(up_y + spawn_offsets_y[p], 0, DANDY_LEVEL_HEIGHT - 1);
	ld	de, #_spawn_offsets_y
	ldhl	sp,	#10
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	ld	c, l
	ld	b, h
	ld	a, (bc)
	ld	c, a
	rlca
	sbc	a, a
	ld	b, a
	ldhl	sp,	#1
	ld	a, (hl)
	ld	d, #0x00
	add	a, c
	ld	e, a
	ld	a, d
	adc	a, b
	ld	d, a
	ld	bc, #0x001d
	push	bc
	ld	bc, #0x0000
	call	_clamp
;src/dandy_core.c:369: player_x[p] = (uint8_t)px;
	ld	de, #_player_x
	ldhl	sp,	#10
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#10
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#9
	ld	(hl), a
	ldhl	sp,	#6
	ld	a, (hl+)
	inc	hl
	ld	e, (hl)
	inc	hl
	ld	h, (hl)
	ld	l, e
	ld	(hl), a
;src/dandy_core.c:370: player_y[p] = (uint8_t)py;
	ld	de, #_player_y
	ldhl	sp,	#10
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	ld	e, l
	ld	d, h
	ld	a, c
	ld	(de), a
;src/dandy_core.c:373: if (player_joined[p]) {
	push	de
	ld	de, #_player_joined
	ldhl	sp,	#12
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	pop	de
	ld	c, l
	ld	b, h
	ld	a, (bc)
	ld	c, a
	bit	0, c
	jr	Z, 00118$
;src/dandy_core.c:374: dandy_map[row_offsets[player_y[p]] + player_x[p]] = GET_PLAYER_TILE(p, player_dir[p]);
	ld	a, (de)
	ld	h, #0x00
	ld	l, a
	add	hl, hl
	ld	de, #_row_offsets
	add	hl, de
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	ldhl	sp,#8
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	ld	l, a
	ld	h, #0x00
	add	hl, bc
	ld	a, l
	add	a, #<(_dandy_map)
	ld	c, a
	ld	a, h
	adc	a, #>(_dandy_map)
	ld	b, a
	ldhl	sp,	#10
	ld	a, (hl-)
	add	a, a
	add	a, a
	add	a, a
	add	a, #0x18
	ld	(hl+), a
	ld	de, #_player_dir
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	ld	e, l
	ld	d, h
	ld	a, (de)
	ldhl	sp,	#9
	add	a, (hl)
	ld	(bc), a
00118$:
;src/dandy_core.c:365: for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
	ldhl	sp,	#10
	inc	(hl)
	jp	00117$
00119$:
;src/dandy_core.c:377: }
	add	sp, #11
	ret
_spawn_offsets_x:
	.db #0x00	;  0
	.db #0x01	;  1
	.db #0x00	;  0
	.db #0xff	; -1
_spawn_offsets_y:
	.db #0xff	; -1
	.db #0x00	;  0
	.db #0x01	;  1
	.db #0x00	;  0
;src/dandy_core.c:379: static void next_level(void) {
;	---------------------------------
; Function next_level
; ---------------------------------
_next_level:
;src/dandy_core.c:380: if (current_level < DANDY_NUM_LEVELS - 1) {
	ld	hl, #_current_level
	ld	a, (hl)
	sub	a, #0x19
	jr	NC, 00102$
;src/dandy_core.c:381: current_level++;
	inc	(hl)
00102$:
;src/dandy_core.c:383: dandy_load_level(current_level);
	ld	a, (_current_level)
;src/dandy_core.c:384: }
	jp	_dandy_load_level
;src/dandy_core.c:386: static void end_game(void) {
;	---------------------------------
; Function end_game
; ---------------------------------
_end_game:
;src/dandy_core.c:387: current_level = 0;
	xor	a, a
	ld	(#_current_level),a
;src/dandy_core.c:388: player_joined[0] = true;
	ld	bc, #_player_joined+0
	ld	a, #0x01
	ld	(bc), a
;src/dandy_core.c:389: for (uint8_t p = 1; p < MAX_PLAYERS; ++p) {
	ld	e, #0x01
00104$:
	ld	a, e
	sub	a, #0x04
	jr	NC, 00101$
;src/dandy_core.c:390: player_joined[p] = false;
	ld	l, e
	ld	h, #0x00
	add	hl, bc
	ld	(hl), #0x00
;src/dandy_core.c:389: for (uint8_t p = 1; p < MAX_PLAYERS; ++p) {
	inc	e
	jr	00104$
00101$:
;src/dandy_core.c:392: for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
	ld	c, #0x00
00107$:
	ld	a, c
	sub	a, #0x04
	jr	NC, 00102$
;src/dandy_core.c:393: player_health[p] = 100;
	ld	l, c
	ld	h, #0x00
	add	hl, hl
	ld	e, l
	ld	d, h
	ld	hl, #_player_health
	add	hl, de
	ld	a, #0x64
	ld	(hl+), a
	ld	(hl), #0x00
;src/dandy_core.c:394: player_keys[p] = 0;
	ld	hl, #_player_keys
	ld	b, #0x00
	add	hl, bc
	ld	(hl), #0x00
;src/dandy_core.c:395: player_bombs[p] = 0;
	ld	hl, #_player_bombs
	ld	b, #0x00
	add	hl, bc
	ld	(hl), #0x00
;src/dandy_core.c:396: player_score[p] = 0;
	ld	hl, #_player_score
	add	hl, de
	xor	a, a
	ld	(hl+), a
	ld	(hl), a
;src/dandy_core.c:397: player_dir[p] = 0;
	ld	hl, #_player_dir
	ld	b, #0x00
	add	hl, bc
	ld	(hl), #0x00
;src/dandy_core.c:392: for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
	inc	c
	jr	00107$
00102$:
;src/dandy_core.c:399: dandy_load_level(current_level);
	ld	a, (_current_level)
;src/dandy_core.c:400: }
	jp	_dandy_load_level
;src/dandy_core.c:402: static void do_player_buttons(uint8_t p_idx, uint8_t buttons) {
;	---------------------------------
; Function do_player_buttons
; ---------------------------------
_do_player_buttons:
	add	sp, #-4
	ld	c, a
	ld	b, e
;src/dandy_core.c:404: uint8_t delta_down = buttons & ~old_buttons[p_idx];
	ld	de, #_do_player_buttons_old_buttons_10000_160+0
	ld	l, c
	ld	h, #0x00
	add	hl, de
	ld	a, (hl)
	cpl
	and	a, b
;src/dandy_core.c:405: old_buttons[p_idx] = buttons;
	ld	(hl), b
;src/dandy_core.c:408: if (delta_down & BUTTON_BOMB) {
	bit	5, a
	jr	Z, 00104$
;src/dandy_core.c:409: if (player_bombs[p_idx] > 0) {
	ld	de, #_player_bombs+0
	ld	l, c
	ld	h, #0x00
	add	hl, de
	ld	a, (hl)
	or	a, a
	jr	Z, 00104$
;src/dandy_core.c:410: player_bombs[p_idx]--;
	dec	a
	ld	(hl), a
;src/dandy_core.c:411: do_bomb(p_idx);
	push	bc
	ld	a, c
	call	_do_bomb
;src/dandy_core.c:412: hal_play_sound(SOUND_BOMB);
	ld	a, #0x03
	call	_hal_play_sound
	pop	bc
00104$:
;src/dandy_core.c:417: if (buttons & BUTTON_FIRE) {
	bit	4, b
	jr	Z, 00108$
;src/dandy_core.c:418: if (arrow_dir[p_idx] == -1) {
	ld	de, #_arrow_dir
	ld	l, c
	ld	h, #0x00
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#4
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#3
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	inc	a
	jr	NZ, 00108$
;src/dandy_core.c:419: arrow_x[p_idx] = player_x[p_idx];
	ld	a, #<(_arrow_x)
	add	a, c
	ld	e, a
	ld	a, #>(_arrow_x)
	adc	a, #0x00
	ld	d, a
	ld	a, #<(_player_x)
	add	a, c
	ld	l, a
	ld	a, #>(_player_x)
	adc	a, #0x00
	ld	h, a
	ld	a, (hl)
	ld	(de), a
;src/dandy_core.c:420: arrow_y[p_idx] = player_y[p_idx];
	ld	a, #<(_arrow_y)
	add	a, c
	ld	e, a
	ld	a, #>(_arrow_y)
	adc	a, #0x00
	ld	d, a
	ld	a, #<(_player_y)
	add	a, c
	ld	l, a
	ld	a, #>(_player_y)
	adc	a, #0x00
	ld	h, a
	ld	a, (hl)
	ld	(de), a
;src/dandy_core.c:421: arrow_dir[p_idx] = player_dir[p_idx];
	ld	de, #_player_dir+0
	ld	l, c
	ld	h, #0x00
	add	hl, de
	ld	a, (hl)
	pop	de
	pop	hl
	push	hl
	push	de
	ld	(hl), a
;src/dandy_core.c:422: hal_play_sound(SOUND_SHOOT);
	push	bc
	xor	a, a
	call	_hal_play_sound
	pop	bc
00108$:
;src/dandy_core.c:427: int8_t d = buttons_to_dir[buttons & 0x0F];
	ld	de, #_buttons_to_dir+0
	ld	a, b
	and	a, #0x0f
	ld	l, a
	ld	h, #0x00
	add	hl, de
	ld	b, (hl)
;src/dandy_core.c:428: if (d >= 0) {
	bit	7, b
	jr	NZ, 00115$
;src/dandy_core.c:429: player_dir[p_idx] = d;
	ld	de, #_player_dir
	ld	l, c
	ld	h, #0x00
	add	hl, de
	inc	sp
	inc	sp
	push	hl
	ld	(hl), b
;src/dandy_core.c:431: dandy_map[row_offsets[player_y[p_idx]] + player_x[p_idx]] = GET_PLAYER_TILE(p_idx, player_dir[p_idx]);
	ld	de, #_player_y+0
	ld	l, c
	ld	h, #0x00
	add	hl, de
	ld	l, (hl)
	ld	h, #0x00
	add	hl, hl
	ld	de, #_row_offsets
	add	hl, de
	ld	e, l
	ld	d, h
	ld	a, (de)
	ldhl	sp,	#2
	ld	(hl+), a
	inc	de
	ld	a, (de)
	ld	(hl), a
	ld	de, #_player_x+0
	ld	l, c
	ld	h, #0x00
	add	hl, de
	ld	a, (hl)
	pop	hl
	pop	de
	push	de
	push	hl
	ld	l, a
	ld	h, #0x00
	add	hl, de
	ld	de, #_dandy_map
	add	hl, de
	ld	a, c
	add	a, a
	add	a, a
	add	a, a
	add	a, #0x18
	add	a, b
	ld	(hl), a
;src/dandy_core.c:432: is_dirty = true;
	ld	hl, #_is_dirty
	ld	(hl), #0x01
;src/dandy_core.c:434: if (player_move_timer[p_idx] == 0) {
	ld	hl, #_player_move_timer
	ld	b, #0x00
	add	hl, bc
	ld	a, (hl)
	or	a, a
	jr	NZ, 00115$
;src/dandy_core.c:435: player_move_timer[p_idx] = TICKS_PER_MOVE;
	ld	(hl), #0x04
;src/dandy_core.c:437: for (uint8_t di = 0; di < 3; ++di) {
	ld	b, #0x00
00119$:
	ld	a, b
	sub	a, #0x03
	jr	NC, 00115$
;src/dandy_core.c:438: int8_t dd = (player_dir[p_idx] + search_order[di]) & 7;
	pop	de
	push	de
	ld	a, (de)
	ld	l, a
	ld	a, #<(_search_order)
	add	a, b
	ld	e, a
	ld	a, #>(_search_order)
	adc	a, #0x00
	ld	d, a
	ld	a, (de)
	add	a, l
	and	a, #0x07
;src/dandy_core.c:439: if (move_player(p_idx, dd)) {
	push	bc
	ld	e, a
	ld	a, c
	call	_move_player
	ld	e, a
	pop	bc
	bit	0, e
	jr	NZ, 00115$
;src/dandy_core.c:437: for (uint8_t di = 0; di < 3; ++di) {
	inc	b
	jr	00119$
00115$:
;src/dandy_core.c:446: if (player_move_timer[p_idx] > 0) {
	ld	hl, #_player_move_timer
	ld	b, #0x00
	add	hl, bc
	ld	a, (hl)
	or	a, a
	jr	Z, 00121$
;src/dandy_core.c:447: player_move_timer[p_idx]--;
	dec	a
	ld	(hl), a
00121$:
;src/dandy_core.c:449: }
	add	sp, #4
	ret
;src/dandy_core.c:451: static bool move_player(uint8_t p_idx, uint8_t dir) {
;	---------------------------------
; Function move_player
; ---------------------------------
_move_player:
	add	sp, #-11
	ldhl	sp,	#10
	ld	(hl-), a
;src/dandy_core.c:452: int16_t nx = clamp((int16_t)player_x[p_idx] + dir_delta_x[dir], 0, DANDY_LEVEL_WIDTH - 1);
	ld	a, e
	ld	(hl+), a
	ld	de, #_player_x
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	inc	sp
	inc	sp
	ld	e, l
	ld	d, h
	push	de
	ld	a, (de)
	ldhl	sp,	#8
	ld	(hl+), a
	ld	de, #_dir_delta_x
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	ld	c, l
	ld	b, h
	ld	a, (bc)
	ldhl	sp,	#7
	ld	(hl), a
	ld	a, (hl-)
	dec	hl
	ld	(hl+), a
	rlca
	sbc	a, a
	ld	(hl+), a
	inc	hl
	ld	a, (hl-)
	ld	(hl+), a
	xor	a, a
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ldhl	sp,	#5
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	ld	e, l
	ld	d, h
	ld	bc, #0x003b
	push	bc
	ld	bc, #0x0000
	call	_clamp
	ldhl	sp,	#2
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;src/dandy_core.c:453: int16_t ny = clamp((int16_t)player_y[p_idx] + dir_delta_y[dir], 0, DANDY_LEVEL_HEIGHT - 1);
	ld	de, #_player_y
	ldhl	sp,	#10
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#6
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#5
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	ld	c, a
	ld	de, #_dir_delta_y+0
	ldhl	sp,	#9
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	ld	e, l
	ld	d, h
	ld	a, (de)
	ld	l, a
	rlca
	sbc	a, a
	ld	h, a
	ld	b, #0x00
	add	hl, bc
	ld	e, l
	ld	d, h
	ld	bc, #0x001d
	push	bc
	ld	bc, #0x0000
	call	_clamp
;src/dandy_core.c:454: uint16_t pos = row_offsets[ny] + nx;
	ld	l, c
	ld	h, b
	add	hl, hl
	ld	de, #_row_offsets
	add	hl, de
	ld	e, l
	ld	d, h
	ld	a, (de)
	ldhl	sp,	#7
	ld	(hl+), a
	inc	de
	ld	a, (de)
	ld	(hl), a
	pop	hl
	pop	de
	push	de
	push	hl
	ldhl	sp,	#7
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	ld	e, l
	ld	d, h
;src/dandy_core.c:455: uint8_t tile = dandy_map[pos];
	ld	hl, #_dandy_map
	add	hl, de
	ld	e, (hl)
;src/dandy_core.c:456: bool can_move = true;
	ldhl	sp,	#6
;src/dandy_core.c:464: iterative_flood_fill(nx, ny, TILE_DOOR, TILE_SPACE);
	ld	a, #0x01
	ld	(hl+), a
	ld	(hl), c
	ldhl	sp,	#2
	ld	a, (hl)
	ldhl	sp,	#8
	ld	(hl), a
;src/dandy_core.c:458: switch (tile) {
	ld	a, #0x08
	sub	a, e
	jp	C, 00111$
;src/dandy_core.c:471: player_score[p_idx] += 100;
	inc	hl
	inc	hl
	ld	c, (hl)
	ld	b, #0x00
	sla	c
	rl	b
;src/dandy_core.c:458: switch (tile) {
	ld	d, #0x00
	ld	hl, #00140$
	add	hl, de
	add	hl, de
	ld	e, (hl)
	inc	hl
	ld	h, (hl)
	ld	l, e
	jp	(hl)
00140$:
	.dw	00112$
	.dw	00111$
	.dw	00102$
	.dw	00111$
	.dw	00110$
	.dw	00107$
	.dw	00109$
	.dw	00106$
	.dw	00108$
;src/dandy_core.c:461: case TILE_DOOR:
00102$:
;src/dandy_core.c:462: if (player_keys[p_idx] > 0) {
	ld	bc, #_player_keys+0
	ldhl	sp,	#10
	ld	l, (hl)
	ld	h, #0x00
	add	hl, bc
	ld	c, l
	ld	b, h
	ld	a, (bc)
	or	a, a
	jr	Z, 00104$
;src/dandy_core.c:463: player_keys[p_idx]--;
	dec	a
	ld	(bc), a
;src/dandy_core.c:464: iterative_flood_fill(nx, ny, TILE_DOOR, TILE_SPACE);
	ld	hl, #0x02
	push	hl
	ldhl	sp,	#9
	ld	a, (hl+)
	ld	e, a
	ld	a, (hl)
	call	_iterative_flood_fill
;src/dandy_core.c:465: hal_play_sound(SOUND_KEY);
	ld	a, #0x04
	call	_hal_play_sound
	jr	00112$
00104$:
;src/dandy_core.c:467: can_move = false;
	ldhl	sp,	#6
	ld	(hl), #0x00
;src/dandy_core.c:469: break;
	jr	00112$
;src/dandy_core.c:470: case TILE_MONEY:
00106$:
;src/dandy_core.c:471: player_score[p_idx] += 100;
	ld	hl, #_player_score
	add	hl, bc
	ld	c,l
	ld	b,h
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	ld	de, #0x0064
	add	hl, de
	ld	a, l
	ld	(bc), a
	inc	bc
	ld	a, h
	ld	(bc), a
;src/dandy_core.c:472: hal_play_sound(SOUND_KEY);
	ld	a, #0x04
	call	_hal_play_sound
;src/dandy_core.c:473: break;
	jr	00112$
;src/dandy_core.c:474: case TILE_KEY:
00107$:
;src/dandy_core.c:475: player_keys[p_idx]++;
	ld	bc, #_player_keys+0
	ldhl	sp,	#10
	ld	l, (hl)
	ld	h, #0x00
	add	hl, bc
	ld	c, l
	ld	b, h
	ld	a, (bc)
	inc	a
	ld	(bc), a
;src/dandy_core.c:476: hal_play_sound(SOUND_KEY);
	ld	a, #0x04
	call	_hal_play_sound
;src/dandy_core.c:477: break;
	jr	00112$
;src/dandy_core.c:478: case TILE_BOMB:
00108$:
;src/dandy_core.c:479: player_bombs[p_idx]++;
	ld	bc, #_player_bombs+0
	ldhl	sp,	#10
	ld	l, (hl)
	ld	h, #0x00
	add	hl, bc
	ld	c, l
	ld	b, h
	ld	a, (bc)
	inc	a
	ld	(bc), a
;src/dandy_core.c:480: hal_play_sound(SOUND_KEY);
	ld	a, #0x04
	call	_hal_play_sound
;src/dandy_core.c:481: break;
	jr	00112$
;src/dandy_core.c:482: case TILE_FOOD:
00109$:
;src/dandy_core.c:483: player_health[p_idx] += 100;
	ld	hl, #_player_health
	add	hl, bc
	ld	c,l
	ld	b,h
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	ld	de, #0x0064
	add	hl, de
	ld	a, l
	ld	(bc), a
	inc	bc
	ld	a, h
	ld	(bc), a
;src/dandy_core.c:484: hal_play_sound(SOUND_FOOD);
	ld	a, #0x02
	call	_hal_play_sound
;src/dandy_core.c:485: break;
	jr	00112$
;src/dandy_core.c:486: case TILE_DOWN:
00110$:
;src/dandy_core.c:487: hal_play_sound(SOUND_WARP);
	ld	a, #0x06
	call	_hal_play_sound
;src/dandy_core.c:488: next_level();
	call	_next_level
;src/dandy_core.c:489: return true;
	ld	a, #0x01
	jr	00115$
;src/dandy_core.c:490: default:
00111$:
;src/dandy_core.c:491: can_move = false;
	ldhl	sp,	#6
	ld	(hl), #0x00
;src/dandy_core.c:493: }
00112$:
;src/dandy_core.c:495: if (can_move) {
	ldhl	sp,	#6
	bit	0, (hl)
	jr	Z, 00114$
;src/dandy_core.c:497: dandy_map[row_offsets[player_y[p_idx]] + player_x[p_idx]] = TILE_SPACE;
	dec	hl
	dec	hl
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	ld	h, #0x00
	ld	l, a
	add	hl, hl
	ld	de, #_row_offsets
	add	hl, de
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	pop	de
	push	de
	ld	a, (de)
	ld	h, #0x00
	ld	l, a
	add	hl, bc
	ld	de, #_dandy_map
	add	hl, de
	ld	(hl), #0x00
;src/dandy_core.c:499: player_x[p_idx] = (uint8_t)nx;
	pop	de
	push	de
	ldhl	sp,	#8
	ld	a, (hl)
	ld	(de), a
;src/dandy_core.c:500: player_y[p_idx] = (uint8_t)ny;
	ldhl	sp,	#4
	ld	a, (hl+)
	ld	e, a
	ld	a, (hl+)
	inc	hl
	ld	d, a
	ld	a, (hl)
	ld	(de), a
;src/dandy_core.c:502: dandy_map[row_offsets[player_y[p_idx]] + player_x[p_idx]] = GET_PLAYER_TILE(p_idx, player_dir[p_idx]);
	ld	c, (hl)
	xor	a, a
	ld	l, c
	ld	h, a
	add	hl, hl
	ld	de, #_row_offsets
	add	hl, de
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	pop	de
	push	de
	ld	a, (de)
	ld	h, #0x00
	ld	l, a
	add	hl, bc
	ld	a, l
	add	a, #<(_dandy_map)
	ld	c, a
	ld	a, h
	adc	a, #>(_dandy_map)
	ld	b, a
	ldhl	sp,	#10
	ld	a, (hl-)
	dec	hl
	add	a, a
	add	a, a
	add	a, a
	add	a, #0x18
	ld	(hl+), a
	inc	hl
	ld	de, #_player_dir
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	ld	e, l
	ld	d, h
	ld	a, (de)
	ldhl	sp,	#8
	add	a, (hl)
	ld	(bc), a
;src/dandy_core.c:503: is_dirty = true;
	ld	hl, #_is_dirty
	ld	(hl), #0x01
00114$:
;src/dandy_core.c:506: return can_move;
	ldhl	sp,	#6
	ld	a, (hl)
00115$:
;src/dandy_core.c:507: }
	add	sp, #11
	ret
;src/dandy_core.c:509: static void move_arrows(void) {
;	---------------------------------
; Function move_arrows
; ---------------------------------
_move_arrows:
	add	sp, #-20
;src/dandy_core.c:510: for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
	ldhl	sp,	#19
	ld	(hl), #0x00
00130$:
	ldhl	sp,	#19
	ld	a, (hl)
	sub	a, #0x04
	jp	NC, 00131$
;src/dandy_core.c:511: if (player_joined[p] && arrow_dir[p] != -1) {
	ld	de, #_player_joined
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	ld	c, l
	ld	b, h
	ld	a, (bc)
	ldhl	sp,	#18
	ld	(hl), a
	bit	0, (hl)
	jp	Z, 00127$
	inc	hl
	ld	de, #_arrow_dir
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	inc	sp
	inc	sp
	ld	e, l
	ld	d, h
	push	de
	ld	a, (de)
	ld	c, a
	inc	a
	jp	Z, 00127$
;src/dandy_core.c:512: int16_t nx = clamp((int16_t)arrow_x[p] + dir_delta_x[arrow_dir[p]], 0, DANDY_LEVEL_WIDTH - 1);
	ld	de, #_arrow_x
	ldhl	sp,	#19
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#4
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#3
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	ld	e, a
	ld	a, c
	rlca
	sbc	a, a
	ld	b, a
	ld	hl, #_dir_delta_x
	add	hl, bc
	ld	a, (hl)
	ld	l, a
	rlca
	sbc	a, a
	ld	h, a
	ld	d, #0x00
	add	hl, de
	ld	e, l
	ld	d, h
	ld	bc, #0x003b
	push	bc
	ld	bc, #0x0000
	call	_clamp
	ldhl	sp,	#4
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;src/dandy_core.c:513: int16_t ny = clamp((int16_t)arrow_y[p] + dir_delta_y[arrow_dir[p]], 0, DANDY_LEVEL_HEIGHT - 1);
	ld	de, #_arrow_y
	ldhl	sp,	#19
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#8
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#7
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	ld	c, a
	pop	de
	push	de
	ld	a, (de)
	ld	e, a
	rlca
	sbc	a, a
	ld	d, a
	ld	hl, #_dir_delta_y
	add	hl, de
	ld	a, (hl)
	ld	l, a
	rlca
	sbc	a, a
	ld	h, a
	ld	b, #0x00
	add	hl, bc
	ld	e, l
	ld	d, h
	ld	bc, #0x001d
	push	bc
	ld	bc, #0x0000
	call	_clamp
	ldhl	sp,	#8
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;src/dandy_core.c:515: uint16_t old_pos = row_offsets[arrow_y[p]] + arrow_x[p];
	ldhl	sp,#6
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	ld	h, #0x00
	ld	l, a
	add	hl, hl
	ld	de, #_row_offsets
	add	hl, de
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	ldhl	sp,#2
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	ld	l, a
	ld	h, #0x00
	add	hl, bc
	ld	c, l
	ld	a, h
	ldhl	sp,	#14
	ld	(hl), c
	inc	hl
	ld	(hl), a
;src/dandy_core.c:516: uint16_t new_pos = row_offsets[ny] + nx;
	ldhl	sp,	#8
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	sla	c
	rl	b
	ld	hl, #_row_offsets
	add	hl, bc
	ld	a, (hl+)
	ld	b, (hl)
	ldhl	sp,	#4
	ld	c, (hl)
	inc	hl
	ld	e, (hl)
	add	a, c
	ld	c, a
	ld	a, b
	adc	a, e
	ld	b, a
;src/dandy_core.c:518: uint8_t tile_at_old = dandy_map[old_pos];
	ldhl	sp,#14
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #_dandy_map
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#18
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#17
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	a, (hl+)
	ld	d, a
	ld	a, (de)
	ld	(hl), a
;src/dandy_core.c:519: uint8_t tile_at_new = dandy_map[new_pos];
	ld	hl, #_dandy_map
	add	hl, bc
	push	hl
	ld	a, l
	ldhl	sp,	#12
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#11
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	a, (hl+)
	ld	d, a
	ld	a, (de)
	ld	(hl), a
;src/dandy_core.c:522: if (tile_at_old >= TILE_ARROW && tile_at_old <= TILE_ARROW + 7) {
	ldhl	sp,	#18
	ld	a, (hl)
	sub	a, #0x10
	jr	C, 00102$
	ld	a, #0x17
	sub	a, (hl)
	jr	C, 00102$
;src/dandy_core.c:523: dandy_map[old_pos] = TILE_SPACE;
	dec	hl
	ld	a, (hl-)
	ld	l, (hl)
	ld	h, a
	ld	(hl), #0x00
00102$:
;src/dandy_core.c:527: int16_t vp_left = clamp((int16_t)player_x[p] - 10, 0, DANDY_LEVEL_WIDTH - 20);
	ld	de, #_player_x
	ldhl	sp,	#19
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	ld	c, l
	ld	b, h
	ld	a, (bc)
	ld	c, #0x00
	add	a, #0xf6
	ld	e, a
	ld	a, c
	adc	a, #0xff
	ld	bc, #0x0028
	push	bc
	ld	bc, #0x0000
	ld	d, a
	call	_clamp
	ldhl	sp,	#17
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;src/dandy_core.c:528: int16_t vp_top = clamp((int16_t)player_y[p] - 5, 0, DANDY_LEVEL_HEIGHT - 10);
	ld	de, #_player_y
	ldhl	sp,	#19
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	ld	c, l
	ld	b, h
	ld	a, (bc)
	ld	c, #0x00
	add	a, #0xfb
	ld	e, a
	ld	a, c
	adc	a, #0xff
	ld	bc, #0x0014
	push	bc
	ld	bc, #0x0000
	ld	d, a
	call	_clamp
	ldhl	sp,	#13
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;src/dandy_core.c:530: if (nx < vp_left || ny < vp_top || nx >= vp_left + 20 || ny >= vp_top + 10) {
	ldhl	sp,	#4
	ld	e, l
	ld	d, h
	ldhl	sp,	#17
	ld	a, (de)
	inc	de
	sub	a, (hl)
	inc	hl
	ld	a, (de)
	sbc	a, (hl)
	ld	a, (de)
	ld	d, a
	ld	e, (hl)
	bit	7, e
	jr	Z, 00241$
	bit	7, d
	jr	NZ, 00242$
	cp	a, a
	jr	00242$
00241$:
	bit	7, d
	jr	Z, 00242$
	scf
00242$:
	jp	C, 00104$
	ldhl	sp,	#8
	ld	e, l
	ld	d, h
	ldhl	sp,	#13
	ld	a, (de)
	inc	de
	sub	a, (hl)
	inc	hl
	ld	a, (de)
	sbc	a, (hl)
	ld	a, (de)
	ld	d, a
	ld	e, (hl)
	bit	7, e
	jr	Z, 00243$
	bit	7, d
	jr	NZ, 00244$
	cp	a, a
	jr	00244$
00243$:
	bit	7, d
	jr	Z, 00244$
	scf
00244$:
	jp	C, 00104$
	ldhl	sp,	#17
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	ld	hl, #0x0014
	add	hl, bc
	push	hl
	ld	a, l
	ldhl	sp,	#17
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#16
	ld	(hl), a
	ldhl	sp,	#4
	ld	a, (hl)
	ldhl	sp,	#17
	ld	(hl), a
	ldhl	sp,	#5
	ld	a, (hl)
	ldhl	sp,	#18
	ld	(hl), a
	ldhl	sp,	#17
	ld	e, l
	ld	d, h
	ldhl	sp,	#15
	ld	a, (de)
	inc	de
	sub	a, (hl)
	inc	hl
	ld	a, (de)
	sbc	a, (hl)
	ld	a, (de)
	ld	d, a
	ld	e, (hl)
	bit	7, e
	jr	Z, 00245$
	bit	7, d
	jr	NZ, 00246$
	cp	a, a
	jr	00246$
00245$:
	bit	7, d
	jr	Z, 00246$
	scf
00246$:
	jr	NC, 00104$
	ldhl	sp,	#13
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	ld	hl, #0x000a
	add	hl, bc
	push	hl
	ld	a, l
	ldhl	sp,	#17
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#16
	ld	(hl), a
	ldhl	sp,	#8
	ld	a, (hl)
	ldhl	sp,	#17
	ld	(hl), a
	ldhl	sp,	#9
	ld	a, (hl)
	ldhl	sp,	#18
	ld	(hl), a
	ldhl	sp,	#17
	ld	e, l
	ld	d, h
	ldhl	sp,	#15
	ld	a, (de)
	inc	de
	sub	a, (hl)
	inc	hl
	ld	a, (de)
	sbc	a, (hl)
	ld	a, (de)
	ld	d, a
	ld	e, (hl)
	bit	7, e
	jr	Z, 00247$
	bit	7, d
	jr	NZ, 00248$
	cp	a, a
	jr	00248$
00247$:
	bit	7, d
	jr	Z, 00248$
	scf
00248$:
	jr	C, 00105$
00104$:
;src/dandy_core.c:531: arrow_dir[p] = -1;
	pop	hl
	ld	(hl), #0xff
	push	hl
;src/dandy_core.c:532: is_dirty = true;
	ld	hl, #_is_dirty
	ld	(hl), #0x01
;src/dandy_core.c:533: continue;
	jp	00127$
00105$:
;src/dandy_core.c:536: if (tile_at_new != TILE_SPACE) {
	ldhl	sp,	#12
	ld	a, (hl)
	or	a, a
	jr	Z, 00122$
;src/dandy_core.c:537: arrow_dir[p] = -1; // Die on hit
	pop	hl
	ld	(hl), #0xff
	push	hl
;src/dandy_core.c:539: if (tile_at_new >= TILE_BOMB && tile_at_new < TILE_ARROW) {
	ldhl	sp,	#12
	ld	a,(hl)
	cp	a,#0x08
	jr	C, 00123$
	sub	a, #0x10
	jr	NC, 00123$
;src/dandy_core.c:540: uint8_t replacement = TILE_SPACE;
	ldhl	sp,	#18
	ld	(hl), #0x00
;src/dandy_core.c:541: if (tile_at_new == TILE_BOMB) {
	ldhl	sp,	#12
	ld	a, (hl)
	sub	a, #0x08
	jr	NZ, 00116$
;src/dandy_core.c:542: do_bomb(p); // Triggered by player p's arrow
	ldhl	sp,	#19
	ld	a, (hl)
	call	_do_bomb
	jr	00117$
00116$:
;src/dandy_core.c:543: } else if (tile_at_new == TILE_HEART) {
	ldhl	sp,	#12
	ld	a, (hl)
	sub	a, #0x0c
	jr	NZ, 00113$
;src/dandy_core.c:544: replacement = TILE_MONSTER3;
	ldhl	sp,	#18
	ld	(hl), #0x0b
	jr	00117$
00113$:
;src/dandy_core.c:545: } else if (tile_at_new == TILE_MONSTER2 || tile_at_new == TILE_MONSTER3) {
	ldhl	sp,	#12
	ld	a, (hl)
	sub	a, #0x0a
	jr	Z, 00109$
	ldhl	sp,	#12
	ld	a, (hl)
	sub	a, #0x0b
	jr	NZ, 00117$
00109$:
;src/dandy_core.c:546: replacement = tile_at_new - 1;
	ldhl	sp,	#12
	ld	a, (hl)
	dec	a
	ldhl	sp,	#18
	ld	(hl), a
00117$:
;src/dandy_core.c:548: dandy_map[new_pos] = replacement;
	ldhl	sp,	#10
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ldhl	sp,	#18
	ld	a, (hl)
	ld	(de), a
;src/dandy_core.c:549: hal_play_sound(SOUND_HIT);
	ld	a, #0x01
	call	_hal_play_sound
	jr	00123$
00122$:
;src/dandy_core.c:553: dandy_map[new_pos] = TILE_ARROW + ((arrow_dir[p] - 5) & 7);
	pop	de
	push	de
	ld	a, (de)
	ldhl	sp,	#18
	ld	(hl), a
	add	a, #0xfb
	ld	(hl), a
	and	a, #0x07
	ld	(hl), a
	add	a, #0x10
	ldhl	sp,	#10
	ld	e, (hl)
	inc	hl
	ld	h, (hl)
	ld	l, e
	ld	(hl), a
;src/dandy_core.c:554: arrow_x[p] = (uint8_t)nx;
	ldhl	sp,	#4
	ld	a, (hl)
	pop	de
	pop	hl
	push	hl
	push	de
	ld	(hl), a
;src/dandy_core.c:555: arrow_y[p] = (uint8_t)ny;
	ldhl	sp,	#8
	ld	a, (hl-)
	dec	hl
	ld	e, (hl)
	inc	hl
	ld	h, (hl)
	ld	l, e
	ld	(hl), a
00123$:
;src/dandy_core.c:557: is_dirty = true;
	ld	hl, #_is_dirty
	ld	(hl), #0x01
00127$:
;src/dandy_core.c:510: for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
	ldhl	sp,	#19
	inc	(hl)
	jp	00130$
00131$:
;src/dandy_core.c:560: }
	add	sp, #20
	ret
;src/dandy_core.c:562: static void do_bomb(uint8_t p_idx) {
;	---------------------------------
; Function do_bomb
; ---------------------------------
_do_bomb:
	add	sp, #-10
	ld	e, a
;src/dandy_core.c:564: int16_t vp_left = clamp((int16_t)player_x[p_idx] - 10, 0, DANDY_LEVEL_WIDTH - 20);
	ld	hl, #_player_x
	ld	d, #0x00
	add	hl, de
	ld	a, (hl)
	ld	c, #0x00
	add	a, #0xf6
	ld	l, a
	ld	a, c
	adc	a, #0xff
	ld	d, a
	push	de
	ld	bc, #0x0028
	push	bc
	ld	bc, #0x0000
	ld	e, l
	call	_clamp
	ldhl	sp,	#4
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
	pop	de
;src/dandy_core.c:565: int16_t vp_top = clamp((int16_t)player_y[p_idx] - 5, 0, DANDY_LEVEL_HEIGHT - 10);
	ld	hl, #_player_y
	ld	d, #0x00
	add	hl, de
	ld	a, (hl)
	ld	c, #0x00
	add	a, #0xfb
	ld	e, a
	ld	a, c
	adc	a, #0xff
	ld	d, a
	ld	bc, #0x0014
	push	bc
	ld	bc, #0x0000
	call	_clamp
	ldhl	sp,	#4
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;src/dandy_core.c:567: for (uint8_t y = 0; y < 10; ++y) {
	ldhl	sp,	#9
	ld	(hl), #0x00
00112$:
	ldhl	sp,	#9
	ld	a, (hl)
	sub	a, #0x0a
	jr	NC, 00107$
;src/dandy_core.c:568: uint16_t row_offset = row_offsets[vp_top + y];
	ldhl	sp,	#4
	ld	a, (hl+)
	inc	hl
	ld	(hl), a
	ldhl	sp,	#9
	ld	a, (hl-)
	ld	(hl), a
	ld	a, (hl-)
	dec	hl
	add	a, (hl)
	inc	hl
	inc	hl
	ld	(hl), a
	ld	a, (hl-)
	ld	(hl+), a
	rlca
	sbc	a, a
	ld	(hl-), a
	sla	(hl)
	inc	hl
	rl	(hl)
	dec	hl
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #_row_offsets
	add	hl, de
	inc	sp
	inc	sp
	ld	e, l
	ld	d, h
	push	de
	ld	a, (de)
	ld	c, a
	inc	de
	ld	a, (de)
	ld	b, a
;src/dandy_core.c:569: for (uint8_t x = 0; x < 20; ++x) {
	ld	e, #0x00
00109$:
	ld	a, e
	sub	a, #0x14
	jr	NC, 00113$
;src/dandy_core.c:570: uint16_t pos = row_offset + (vp_left + x);
	ldhl	sp,	#0
	ld	a, e
	ld	(hl+), a
	xor	a, a
	ld	(hl+), a
	ld	a, (hl)
	ldhl	sp,	#7
	ld	(hl), a
	ldhl	sp,	#3
	ld	a, (hl)
	ldhl	sp,	#8
	ld	(hl-), a
	push	de
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ldhl	sp,	#2
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	pop	de
	ld	d, l
	ld	a, h
	ld	l, c
	ld	h, b
	add	a, l
	ld	l, a
	ld	a, d
	adc	a, h
	ld	h, a
;src/dandy_core.c:571: uint8_t tile = dandy_map[pos];
	push	de
	ld	de, #_dandy_map
	add	hl, de
	pop	de
	ld	a, (hl)
;src/dandy_core.c:572: if ((tile >= TILE_MONSTER1 && tile <= TILE_MONSTER3) ||
	cp	a, #0x09
	jr	C, 00105$
	cp	a, #0x0c
	jr	C, 00101$
00105$:
;src/dandy_core.c:573: (tile >= TILE_GENERATOR1 && tile <= TILE_GENERATOR3)) {
	cp	a, #0x0d
	jr	C, 00110$
	cp	a, #0x10
	jr	NC, 00110$
00101$:
;src/dandy_core.c:574: dandy_map[pos] = TILE_SPACE;
	ld	(hl), #0x00
00110$:
;src/dandy_core.c:569: for (uint8_t x = 0; x < 20; ++x) {
	inc	e
	jr	00109$
00113$:
;src/dandy_core.c:567: for (uint8_t y = 0; y < 10; ++y) {
	ldhl	sp,	#9
	inc	(hl)
	jr	00112$
00107$:
;src/dandy_core.c:578: is_dirty = true;
	ld	hl, #_is_dirty
	ld	(hl), #0x01
;src/dandy_core.c:579: }
	add	sp, #10
	ret
;src/dandy_core.c:582: static uint8_t get_nearest_player(uint8_t mx, uint8_t my) {
;	---------------------------------
; Function get_nearest_player
; ---------------------------------
_get_nearest_player:
	add	sp, #-12
	ldhl	sp,	#10
	ld	(hl-), a
	ld	(hl), e
;src/dandy_core.c:583: uint8_t nearest = 0;
	ldhl	sp,	#0
;src/dandy_core.c:584: uint16_t min_dist = 0xFFFF;
	xor	a, a
	ld	(hl+), a
	ld	a, #0xff
	ld	(hl+), a
	ld	(hl), #0xff
;src/dandy_core.c:585: for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
	ldhl	sp,	#11
	ld	(hl), #0x00
00108$:
	ldhl	sp,	#11
	ld	a, (hl)
	sub	a, #0x04
	jp	NC, 00106$
;src/dandy_core.c:586: if (player_joined[p] && player_health[p] > 0) {
	ld	de, #_player_joined
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#9
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#8
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	bit	0,a
	jp	Z, 00109$
	ldhl	sp,	#11
	ld	c, (hl)
	xor	a, a
	ld	l, c
	ld	h, a
	add	hl, hl
	ld	de, #_player_health
	add	hl, de
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	ld	e, b
	xor	a, a
	ld	d, a
	cp	a, c
	sbc	a, b
	bit	7, e
	jr	Z, 00166$
	bit	7, d
	jr	NZ, 00167$
	cp	a, a
	jr	00167$
00166$:
	bit	7, d
	jr	Z, 00167$
	scf
00167$:
	jp	NC, 00109$
;src/dandy_core.c:587: uint16_t dist = (player_x[p] > mx ? player_x[p] - mx : mx - player_x[p]) +
	ld	de, #_player_x
	ldhl	sp,	#11
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	ld	c, l
	ld	b, h
	ld	a, (bc)
	ld	c, a
	ldhl	sp,	#5
	ld	a, c
	ld	(hl+), a
	ld	(hl), #0x00
	ldhl	sp,	#10
	ld	a, (hl)
	ldhl	sp,	#7
	ld	(hl+), a
	xor	a, a
	ld	(hl+), a
	inc	hl
	ld	a, (hl)
	sub	a, c
	jr	NC, 00112$
	ldhl	sp,#5
	ld	a, (hl+)
	ld	e, a
	ld	a, (hl+)
	ld	d, a
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	ld	a, e
	sub	a, l
	ld	e, a
	ld	a, d
	sbc	a, h
	ldhl	sp,	#4
	ld	(hl-), a
	ld	(hl), e
	jr	00113$
00112$:
	ldhl	sp,#7
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ldhl	sp,	#5
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	ld	a, e
	sub	a, l
	ld	e, a
	ld	a, d
	sbc	a, h
	ldhl	sp,	#4
	ld	(hl-), a
	ld	(hl), e
00113$:
	ld	de, #_player_y
	ldhl	sp,	#11
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	ld	c, l
	ld	b, h
	ld	a, (bc)
	ld	e, a
	ldhl	sp,	#5
	ld	a, e
	ld	(hl+), a
	ld	(hl), #0x00
	ldhl	sp,	#9
	ld	c, (hl)
	ld	b, #0x00
	ld	a, (hl)
	sub	a, e
	jr	NC, 00114$
	ldhl	sp,#5
	ld	a, (hl+)
	ld	e, a
	ld	a, (hl+)
	inc	hl
	ld	d, a
	ld	a, e
	sub	a, c
	ld	e, a
	ld	a, d
	sbc	a, b
	ld	(hl-), a
	ld	(hl), e
	jr	00115$
00114$:
	ldhl	sp,#5
	ld	a, (hl+)
	ld	e, a
	ld	a, (hl+)
	inc	hl
	ld	d, a
	ld	a, c
	sub	a, e
	ld	e, a
	ld	a, b
	sbc	a, d
	ld	(hl-), a
	ld	(hl), e
00115$:
	ldhl	sp,#3
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ldhl	sp,	#7
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	ld	c, l
	ld	b, h
;src/dandy_core.c:589: if (dist < min_dist) {
	ldhl	sp,	#1
	ld	a, c
	sub	a, (hl)
	inc	hl
	ld	a, b
	sbc	a, (hl)
	jr	NC, 00109$
;src/dandy_core.c:590: min_dist = dist;
	ldhl	sp,	#1
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;src/dandy_core.c:591: nearest = p;
	ldhl	sp,	#11
	ld	a, (hl)
	ldhl	sp,	#0
	ld	(hl), a
00109$:
;src/dandy_core.c:585: for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
	ldhl	sp,	#11
	inc	(hl)
	jp	00108$
00106$:
;src/dandy_core.c:595: return nearest;
	ldhl	sp,	#0
	ld	a, (hl)
;src/dandy_core.c:596: }
	add	sp, #12
	ret
;src/dandy_core.c:598: static void move_monsters(void) {
;	---------------------------------
; Function move_monsters
; ---------------------------------
_move_monsters:
	add	sp, #-44
;src/dandy_core.c:602: monster_rotor++;
	ld	hl, #_monster_rotor
	inc	(hl)
;src/dandy_core.c:603: if (monster_rotor >= 16) {
	ld	a, (hl)
	sub	a, #0x10
	jr	C, 00176$
;src/dandy_core.c:604: monster_rotor = 0;
	ld	(hl), #0x00
;src/dandy_core.c:611: for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
00176$:
	ldhl	sp,	#43
	ld	(hl), #0x00
00155$:
	ldhl	sp,	#43
	ld	a, (hl)
	sub	a, #0x04
	jp	NC, 00105$
;src/dandy_core.c:612: if (player_joined[p]) {
	ld	de, #_player_joined
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	ld	c, l
	ld	b, h
	ld	a, (bc)
	bit	0,a
	jr	Z, 00156$
;src/dandy_core.c:614: get_camera_target(p, &target_x, &target_y);
	ldhl	sp,	#16
	ld	c, l
	ld	d, h
	ld	hl, #18
	add	hl, sp
	push	hl
	ld	e, c
	ldhl	sp,	#45
	ld	a, (hl)
	call	_get_camera_target
;src/dandy_core.c:616: vp_lefts[p] = clamp(target_x - 10, 0, DANDY_LEVEL_WIDTH - 20);
	ldhl	sp,	#43
	ld	a, (hl-)
	dec	hl
	ld	c, a
	ld	b, #0x00
	sla	c
	rl	b
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
	push	hl
	ld	hl, #2
	add	hl, sp
	ld	e, l
	ld	d, h
	pop	hl
	ldhl	sp,	#41
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	ld	e, l
	ld	d, h
	ldhl	sp,	#16
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	ld	a, c
	add	a, #0xf6
	ld	l, a
	ld	a, b
	adc	a, #0xff
	ld	h, a
	push	de
	ld	bc, #0x0028
	push	bc
	ld	bc, #0x0000
	ld	e, l
	ld	d, h
	call	_clamp
	pop	de
	ld	a, c
	ld	(de), a
	inc	de
	ld	a, b
	ld	(de), a
;src/dandy_core.c:617: vp_tops[p] = clamp(target_y - 5, 0, DANDY_LEVEL_HEIGHT - 10);
	push	hl
	ld	hl, #10
	add	hl, sp
	ld	e, l
	ld	d, h
	pop	hl
	ldhl	sp,	#41
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	ld	e, l
	ld	d, h
	ldhl	sp,	#18
	ld	a, (hl+)
	ld	c, (hl)
	add	a, #0xfb
	ld	l, a
	ld	a, c
	adc	a, #0xff
	ld	h, a
	push	de
	ld	bc, #0x0014
	push	bc
	ld	bc, #0x0000
	ld	e, l
	ld	d, h
	call	_clamp
	pop	de
	ld	a, c
	ld	(de), a
	inc	de
	ld	a, b
	ld	(de), a
00156$:
;src/dandy_core.c:611: for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
	ldhl	sp,	#43
	inc	(hl)
	jp	00155$
00105$:
;src/dandy_core.c:622: uint8_t x_start = monster_rotor % dx;
	ld	a, (#_monster_rotor)
	and	a, #0x03
	ldhl	sp,	#20
	ld	(hl), a
;src/dandy_core.c:623: uint8_t y_start = monster_rotor / dx;
	ld	e, #0x04
	ld	a, (_monster_rotor)
;src/dandy_core.c:625: for (uint8_t my = y_start; my < DANDY_LEVEL_HEIGHT; my += dy) {
	call	__divuchar
	ldhl	sp,	#41
	ld	(hl), c
00169$:
	ldhl	sp,	#41
	ld	a, (hl)
	sub	a, #0x1e
	jp	NC, 00171$
;src/dandy_core.c:626: uint16_t row_offset = row_offsets[my];
	ld	a, (hl)
	ldhl	sp,	#21
	ld	(hl+), a
	xor	a, a
	ld	(hl-), a
	ld	c, (hl)
	ld	b, #0x00
	sla	c
	rl	b
	ld	hl, #_row_offsets
	add	hl, bc
	ld	e, l
	ld	d, h
	ld	a, (de)
	ldhl	sp,	#23
	ld	(hl+), a
	inc	de
	ld	a, (de)
	ld	(hl), a
;src/dandy_core.c:627: for (uint8_t mx = x_start; mx < DANDY_LEVEL_WIDTH; mx += dx) {
	ldhl	sp,	#20
	ld	a, (hl)
	ldhl	sp,	#42
	ld	(hl), a
00167$:
	ldhl	sp,	#42
;src/dandy_core.c:628: uint16_t pos = row_offset + mx;
	ld	a,(hl)
	cp	a,#0x3c
	jp	NC,00170$
	ldhl	sp,	#35
	ld	(hl+), a
	ld	(hl), #0x00
	ldhl	sp,	#23
	ld	a, (hl)
	ldhl	sp,	#37
	ld	(hl), a
	ldhl	sp,	#24
	ld	a, (hl)
	ldhl	sp,	#38
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ldhl	sp,	#35
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#41
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#40
;src/dandy_core.c:629: uint8_t tile = dandy_map[pos];
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	hl, #_dandy_map
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#27
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#26
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	a, (hl+)
	ld	d, a
	ld	a, (de)
;src/dandy_core.c:632: if ((tile >= TILE_MONSTER1 && tile <= TILE_MONSTER3) ||
	ld	(hl+), a
	sub	a, #0x09
	ld	a, #0x00
	rla
	ld	(hl-), a
	ld	a, #0x0b
	sub	a, (hl)
	inc	hl
	inc	hl
	ld	a, #0x00
	rla
;src/dandy_core.c:633: (tile >= TILE_GENERATOR1 && tile <= TILE_GENERATOR3)) {
	ld	(hl-), a
	dec	hl
	ld	a, (hl)
	sub	a, #0x0d
	ld	a, #0x00
	rla
	ldhl	sp,	#30
	ld	(hl), a
	ld	a, #0x0f
	ldhl	sp,	#27
	sub	a, (hl)
	ld	a, #0x00
	rla
	ldhl	sp,	#31
	ld	(hl), a
;src/dandy_core.c:639: if (mx >= vp_lefts[p] && mx < vp_lefts[p] + 20 &&
	ldhl	sp,	#42
	ld	a, (hl)
	ldhl	sp,	#32
	ld	(hl+), a
	ld	(hl), #0x00
	ldhl	sp,	#42
	ld	a, (hl)
	ldhl	sp,	#34
	ld	(hl+), a
	ld	(hl), #0x00
;src/dandy_core.c:640: my >= vp_tops[p] && my < vp_tops[p] + 10) {
	ldhl	sp,	#41
	ld	a, (hl)
	ldhl	sp,	#36
	ld	(hl+), a
	ld	(hl), #0x00
;src/dandy_core.c:632: if ((tile >= TILE_MONSTER1 && tile <= TILE_MONSTER3) ||
	ldhl	sp,	#28
	bit	0, (hl)
	jr	NZ, 00120$
	inc	hl
	bit	0, (hl)
	jr	Z, 00116$
00120$:
;src/dandy_core.c:633: (tile >= TILE_GENERATOR1 && tile <= TILE_GENERATOR3)) {
	ldhl	sp,	#30
	bit	0, (hl)
	jp	NZ, 00117$
	inc	hl
	bit	0, (hl)
	jp	NZ, 00117$
00116$:
;src/dandy_core.c:636: bool is_visible = false;
	ldhl	sp,	#38
	ld	(hl), #0x00
;src/dandy_core.c:637: for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
	ldhl	sp,	#43
	ld	(hl), #0x00
00158$:
	ldhl	sp,	#43
	ld	a, (hl)
	sub	a, #0x04
	jp	NC, 00113$
;src/dandy_core.c:638: if (player_joined[p]) {
	ld	de, #_player_joined
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	ld	c, l
	ld	b, h
	ld	a, (bc)
	ld	c, a
	bit	0, c
	jp	Z, 00159$
;src/dandy_core.c:639: if (mx >= vp_lefts[p] && mx < vp_lefts[p] + 20 &&
	ldhl	sp,	#43
	ld	c, (hl)
	xor	a, a
	sla	c
	adc	a, a
	ldhl	sp,	#39
	ld	(hl), c
	inc	hl
	ld	(hl), a
	push	hl
	ld	hl, #2
	add	hl, sp
	ld	e, l
	ld	d, h
	pop	hl
	ldhl	sp,	#39
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	ldhl	sp,	#32
	ld	a, (hl+)
	sub	a, c
	ld	a, (hl)
	sbc	a, b
	ld	d, (hl)
	ld	a, b
	ld	e, a
	bit	7, e
	jr	Z, 00417$
	bit	7, d
	jr	NZ, 00418$
	cp	a, a
	jr	00418$
00417$:
	bit	7, d
	jr	Z, 00418$
	scf
00418$:
	jr	C, 00159$
	ld	hl, #0x0014
	add	hl, bc
	ld	c, l
	ld	b, h
	ldhl	sp,	#34
	ld	a, (hl+)
	sub	a, c
	ld	a, (hl)
	sbc	a, b
	ld	d, (hl)
	ld	a, b
	ld	e, a
	bit	7, e
	jr	Z, 00419$
	bit	7, d
	jr	NZ, 00420$
	cp	a, a
	jr	00420$
00419$:
	bit	7, d
	jr	Z, 00420$
	scf
00420$:
	jr	NC, 00159$
;src/dandy_core.c:640: my >= vp_tops[p] && my < vp_tops[p] + 10) {
	push	hl
	ld	hl, #10
	add	hl, sp
	ld	e, l
	ld	d, h
	pop	hl
	ldhl	sp,	#39
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	ldhl	sp,	#36
	ld	a, (hl+)
	sub	a, c
	ld	a, (hl)
	sbc	a, b
	ld	d, (hl)
	ld	a, b
	ld	e, a
	bit	7, e
	jr	Z, 00421$
	bit	7, d
	jr	NZ, 00422$
	cp	a, a
	jr	00422$
00421$:
	bit	7, d
	jr	Z, 00422$
	scf
00422$:
	jr	C, 00159$
	ld	hl, #0x000a
	add	hl, bc
	ld	c, l
	ld	b, h
	ldhl	sp,	#21
	ld	a, (hl+)
	sub	a, c
	ld	a, (hl)
	sbc	a, b
	ld	d, (hl)
	ld	a, b
	ld	e, a
	bit	7, e
	jr	Z, 00423$
	bit	7, d
	jr	NZ, 00424$
	cp	a, a
	jr	00424$
00423$:
	bit	7, d
	jr	Z, 00424$
	scf
00424$:
	jr	NC, 00159$
;src/dandy_core.c:641: is_visible = true;
	ldhl	sp,	#38
	ld	(hl), #0x01
;src/dandy_core.c:642: break;
	jr	00113$
00159$:
;src/dandy_core.c:637: for (uint8_t p = 0; p < MAX_PLAYERS; ++p) {
	ldhl	sp,	#43
	inc	(hl)
	jp	00158$
00113$:
;src/dandy_core.c:646: if (!is_visible) {
	ldhl	sp,	#38
	bit	0, (hl)
	jp	Z, 00151$
;src/dandy_core.c:647: continue; // Freeze this off-screen monster/generator!
00117$:
;src/dandy_core.c:660: uint16_t n_pos = row_offsets[my + dir_delta_y[dd]] + (mx + dir_delta_x[dd]);
	ldhl	sp,	#41
	ld	a, (hl+)
	inc	hl
	ld	(hl), a
;src/dandy_core.c:651: if (tile >= TILE_MONSTER1 && tile <= TILE_MONSTER3) {
	ldhl	sp,	#28
	bit	0, (hl)
	jp	NZ, 00148$
	inc	hl
	bit	0, (hl)
	jp	NZ, 00148$
;src/dandy_core.c:653: uint8_t target_p = get_nearest_player(mx, my);
	ldhl	sp,	#41
	ld	a, (hl+)
	ld	e, a
	ld	a, (hl)
	call	_get_nearest_player
	ld	e, a
;src/dandy_core.c:654: int8_t p_dy = to_delta(player_y[target_p], my);
	ld	hl, #_player_y
	ld	d, #0x00
	add	hl, de
	ld	a, (hl)
	ld	d, #0x00
	push	de
	ldhl	sp,	#38
	ld	c, (hl)
	ld	b, #0x00
	ld	e, a
	call	_to_delta
	ldhl	sp,	#42
	ld	(hl), a
	pop	de
;src/dandy_core.c:655: int8_t p_dx = to_delta(player_x[target_p], mx);
	ld	l, e
	ld	h, #0x00
	ld	de, #_player_x
	add	hl, de
	ld	e, (hl)
	xor	a, a
	ldhl	sp,	#32
	ld	c, (hl)
	ld	b, #0x00
	ld	d, a
	call	_to_delta
	ld	c, a
;src/dandy_core.c:656: int8_t m_dir = delta_to_dir[p_dy + 1][p_dx + 1];
	ldhl	sp,	#40
	ld	a, (hl)
	inc	a
	ld	e, a
	rlca
	sbc	a, a
	ld	d, a
	ld	l, e
	ld	h, d
	add	hl, hl
	add	hl, de
	ld	de, #_delta_to_dir
	add	hl, de
	ld	a, c
	inc	a
	add	a, l
	ld	l, a
	ld	a, #0x00
	adc	a, h
	ld	h, a
	ld	a, (hl)
	ldhl	sp,	#36
	ld	(hl), a
;src/dandy_core.c:658: for (uint8_t d = 0; d < 3; ++d) {
	ldhl	sp,	#40
	ld	(hl), #0x00
00161$:
	ldhl	sp,	#40
	ld	a, (hl)
	sub	a, #0x03
	jp	NC, 00151$
;src/dandy_core.c:659: int8_t dd = (m_dir + search_order[d]) & 7;
	ld	de, #_search_order
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	ld	c, l
	ld	b, h
	ld	a, (bc)
	ldhl	sp,	#36
	add	a, (hl)
	and	a, #0x07
;src/dandy_core.c:660: uint16_t n_pos = row_offsets[my + dir_delta_y[dd]] + (mx + dir_delta_x[dd]);
	ldhl	sp,	#39
	ld	(hl), a
	ld	de, #_dir_delta_y
	ld	l, (hl)
	ld	h, #0x00
	add	hl, de
	ld	c, l
	ld	b, h
	ld	a, (bc)
	ldhl	sp,	#43
	add	a, (hl)
	ld	l, a
	rlca
	sbc	a, a
	ld	h, a
	add	hl, hl
	ld	de, #_row_offsets
	add	hl, de
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	ldhl	sp,	#39
	ld	e, (hl)
	ld	d, #0x00
	ld	hl, #_dir_delta_x
	add	hl, de
	ld	e, l
	ld	d, h
	ld	a, (de)
	ld	e, a
	rlca
	sbc	a, a
	ld	d, a
	ldhl	sp,	#34
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	add	hl, bc
	ld	c, l
	ld	b, h
;src/dandy_core.c:661: uint8_t n_tile = dandy_map[n_pos];
	ld	hl, #_dandy_map
	add	hl, bc
	push	hl
	ld	a, l
	ldhl	sp,	#39
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#38
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	a, (hl+)
	ld	d, a
	ld	a, (de)
;src/dandy_core.c:663: if (IS_PLAYER(n_tile)) {
	ld	(hl), a
	sub	a, #0x18
	jp	C, 00133$
	ld	a, #0x37
	sub	a, (hl)
	jp	C, 00133$
;src/dandy_core.c:665: uint8_t hit_p = (n_tile - TILE_PLAYER1) >> 3;
	ld	a, (hl)
	ld	b, #0x00
	add	a, #0xe8
	ld	c, a
	ld	a, b
	adc	a, #0xff
	ld	b, a
	ld	a, #0x03
00425$:
	sra	b
	rr	c
	dec	a
	jr	NZ, 00425$
;src/dandy_core.c:666: if (player_joined[hit_p]) {
	ld	hl, #_player_joined
	ld	b, #0x00
	add	hl, bc
	ld	b, (hl)
	bit	0, b
	jp	Z, 00151$
;src/dandy_core.c:667: dandy_map[pos] = TILE_SPACE;
	ldhl	sp,	#25
	ld	a, (hl+)
	ld	h, (hl)
	ld	l, a
	ld	(hl), #0x00
;src/dandy_core.c:668: player_health[hit_p] -= 10 * (tile - TILE_MONSTER1 + 1);
	xor	a, a
	ld	b, a
	sla	c
	rl	b
	ld	hl, #_player_health
	add	hl, bc
	push	hl
	ld	a, l
	ldhl	sp,	#41
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#40
	ld	(hl-), a
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ld	a, (de)
	ld	c, a
	inc	de
	ld	a, (de)
	ld	b, a
	ldhl	sp,	#27
	ld	e, (hl)
	ld	d, #0x00
	ld	hl, #0xfff8
	add	hl, de
	ld	e, l
	ld	d, h
	add	hl, hl
	add	hl, hl
	add	hl, de
	add	hl, hl
	ld	a, c
	sub	a, l
	ld	c, a
	ld	a, b
	sbc	a, h
	ld	b, a
	ldhl	sp,	#39
	ld	a, (hl+)
	ld	h, (hl)
	ld	l, a
	ld	a, c
	ld	(hl+), a
	ld	(hl), b
;src/dandy_core.c:669: if (player_health[hit_p] <= 0) {
	ld	e, b
	xor	a, a
	ld	d, a
	cp	a, c
	sbc	a, b
	bit	7, e
	jr	Z, 00427$
	bit	7, d
	jr	NZ, 00428$
	cp	a, a
	jr	00428$
00427$:
	bit	7, d
	jr	Z, 00428$
	scf
00428$:
	jr	C, 00122$
;src/dandy_core.c:670: player_health[hit_p] = 0;
	ldhl	sp,	#39
	ld	a, (hl+)
	ld	h, (hl)
	ld	l, a
	xor	a, a
	ld	(hl+), a
	ld	(hl), a
;src/dandy_core.c:671: dandy_map[n_pos] = TILE_SPACE; // Clear player's tile from the map immediately
	ldhl	sp,	#37
	ld	a, (hl+)
	ld	h, (hl)
	ld	l, a
	ld	(hl), #0x00
;src/dandy_core.c:672: hal_play_sound(SOUND_DIE);
	ld	a, #0x05
	call	_hal_play_sound
	jr	00123$
00122$:
;src/dandy_core.c:674: hal_play_sound(SOUND_HIT);
	ld	a, #0x01
	call	_hal_play_sound
00123$:
;src/dandy_core.c:676: is_dirty = true;
	ld	hl, #_is_dirty
	ld	(hl), #0x01
;src/dandy_core.c:678: break;
	jp	00151$
00133$:
;src/dandy_core.c:679: } else if (n_tile == TILE_SPACE) {
	ldhl	sp,	#39
	ld	a, (hl)
	or	a, a
	jr	NZ, 00130$
;src/dandy_core.c:680: dandy_map[pos] = TILE_SPACE;
	ldhl	sp,	#25
	ld	a, (hl+)
	ld	h, (hl)
	ld	l, a
	ld	(hl), #0x00
;src/dandy_core.c:681: dandy_map[n_pos] = tile;
	ldhl	sp,	#37
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ldhl	sp,	#27
	ld	a, (hl)
	ld	(de), a
;src/dandy_core.c:682: is_dirty = true;
	ld	hl, #_is_dirty
	ld	(hl), #0x01
;src/dandy_core.c:683: break;
	jp	00151$
00130$:
;src/dandy_core.c:684: } else if (n_tile >= TILE_ARROW && n_tile <= TILE_ARROW + 7) {
	ldhl	sp,	#39
	ld	a, (hl)
	sub	a, #0x10
	jr	C, 00134$
	ld	a, #0x17
	sub	a, (hl)
	jp	NC, 00151$
;src/dandy_core.c:685: break;
00134$:
;src/dandy_core.c:658: for (uint8_t d = 0; d < 3; ++d) {
	ldhl	sp,	#40
	inc	(hl)
	jp	00161$
00148$:
;src/dandy_core.c:688: } else if (tile >= TILE_GENERATOR1 && tile <= TILE_GENERATOR3) {
	ldhl	sp,	#30
	bit	0, (hl)
	jp	NZ, 00151$
	inc	hl
	bit	0, (hl)
	jp	NZ, 00151$
;src/dandy_core.c:690: uint8_t lsb = rand_seed & 1;
	ld	a, (_move_monsters_rand_seed_80002_267)
	and	a, #0x01
	ld	c, a
;src/dandy_core.c:691: rand_seed >>= 1;
	ld	hl, #_move_monsters_rand_seed_80002_267 + 1
	srl	(hl)
	dec	hl
	rr	(hl)
;src/dandy_core.c:692: if (lsb) {
	ld	a, c
	or	a, a
	jr	Z, 00138$
;src/dandy_core.c:693: rand_seed ^= 0xB400u;
	ld	a, (hl+)
	ld	c, a
	ld	a, (hl-)
	xor	a, #0xb4
	ld	(hl), c
	inc	hl
	ld	(hl), a
00138$:
;src/dandy_core.c:696: if ((rand_seed & 7) < 4) {
	ld	a, (_move_monsters_rand_seed_80002_267)
	ld	hl, #_move_monsters_rand_seed_80002_267 + 1
	and	a, #0x07
	ld	b, a
	ld	c, #0x00
	ld	a, b
	sub	a, #0x04
	jr	NC, 00151$
;src/dandy_core.c:697: uint8_t spawn_dir = (rand_seed & 3) * 2;
	dec	hl
	ld	a, (hl)
	and	a, #0x03
	add	a, a
	ldhl	sp,	#38
	ld	(hl), a
;src/dandy_core.c:698: for (uint8_t dd = 0; dd < 8; dd += 2) {
	ld	c, #0x00
00164$:
	ld	a, c
	sub	a, #0x08
	jr	NC, 00151$
;src/dandy_core.c:699: uint8_t check_dir = (spawn_dir + dd) % 8;
	ldhl	sp,	#38
	ld	a, (hl)
	ld	b, c
	add	a, b
	and	a, #0x07
;src/dandy_core.c:700: uint16_t g_pos = row_offsets[my + dir_delta_y[check_dir]] + (mx + dir_delta_x[check_dir]);
	ld	b, a
	add	a,#<(_dir_delta_y)
	ld	l, a
	ld	a, #>(_dir_delta_y)
	adc	a, #0x00
	ld	h, a
	ld	a, (hl)
	ldhl	sp,	#43
	add	a, (hl)
	ld	l, a
	rlca
	sbc	a, a
	ld	h, a
	add	hl, hl
	ld	de, #_row_offsets
	add	hl, de
	ld	e, l
	ld	d, h
	ld	a, (de)
	ldhl	sp,	#39
	ld	(hl+), a
	inc	de
	ld	a, (de)
	ld	(hl), a
	ld	l, b
	ld	h, #0x00
	ld	de, #_dir_delta_x
	add	hl, de
	ld	a, (hl)
	ld	e, a
	rlca
	sbc	a, a
	ld	d, a
	ldhl	sp,	#34
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	ld	b, l
	ld	a, h
	ldhl	sp,	#39
	ld	e, (hl)
	inc	hl
	ld	d, (hl)
	ld	l, b
	ld	h, a
	add	hl, de
;src/dandy_core.c:701: if (dandy_map[g_pos] == TILE_SPACE) {
	ld	a, l
	add	a, #<(_dandy_map)
	ld	e, a
	ld	a, h
	adc	a, #>(_dandy_map)
	ld	d, a
	ld	a, (de)
	or	a, a
	jr	NZ, 00165$
;src/dandy_core.c:702: dandy_map[g_pos] = TILE_MONSTER1 + (tile - TILE_GENERATOR1);
	ldhl	sp,	#27
	ld	a, (hl)
	add	a, #0xfc
	ld	(de), a
;src/dandy_core.c:703: is_dirty = true;
	ld	hl, #_is_dirty
	ld	(hl), #0x01
;src/dandy_core.c:704: break;
	jr	00151$
00165$:
;src/dandy_core.c:698: for (uint8_t dd = 0; dd < 8; dd += 2) {
	inc	c
	inc	c
	jr	00164$
00151$:
;src/dandy_core.c:627: for (uint8_t mx = x_start; mx < DANDY_LEVEL_WIDTH; mx += dx) {
	ldhl	sp,	#42
	inc	(hl)
	inc	(hl)
	inc	(hl)
	inc	(hl)
	jp	00167$
00170$:
;src/dandy_core.c:625: for (uint8_t my = y_start; my < DANDY_LEVEL_HEIGHT; my += dy) {
	ldhl	sp,	#41
	inc	(hl)
	inc	(hl)
	inc	(hl)
	inc	(hl)
	jp	00169$
00171$:
;src/dandy_core.c:711: }
	add	sp, #44
	ret
;src/dandy_core.c:714: static void iterative_flood_fill(uint8_t start_x, uint8_t start_y, uint8_t oc, uint8_t nc) {
;	---------------------------------
; Function iterative_flood_fill
; ---------------------------------
_iterative_flood_fill:
	add	sp, #-12
	ldhl	sp,	#11
	ld	(hl-), a
	ld	(hl), e
;src/dandy_core.c:715: if (oc == nc || dandy_map[row_offsets[start_y] + start_x] != oc) return;
	ldhl	sp,	#14
	ld	a, (hl+)
	sub	a, (hl)
	jp	Z, 00126$
	ldhl	sp,	#10
	ld	c, (hl)
	xor	a, a
	ld	l, c
	ld	h, a
	add	hl, hl
	ld	de, #_row_offsets
	add	hl, de
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	ldhl	sp,	#11
	ld	l, (hl)
	ld	h, #0x00
	add	hl, bc
	ld	a, l
	add	a, #<(_dandy_map)
	ld	c, a
	ld	a, h
	adc	a, #>(_dandy_map)
	ld	b, a
	ld	a, (bc)
	ld	e, a
	ldhl	sp,	#14
	ld	a, (hl)
	sub	a, e
	jp	NZ, 00126$
;src/dandy_core.c:717: flood_stack_ptr = 0;
	xor	a, a
	ld	(#_flood_stack_ptr),a
;src/dandy_core.c:720: dandy_map[row_offsets[start_y] + start_x] = nc;
	ldhl	sp,	#15
	ld	a, (hl)
	ld	(bc), a
;src/dandy_core.c:721: flood_push(start_x, start_y);
	ldhl	sp,	#10
	ld	a, (hl+)
	ld	e, a
	ld	a, (hl)
	call	_flood_push
;src/dandy_core.c:723: while (flood_stack_ptr > 0) {
00119$:
	ld	hl, #_flood_stack_ptr
	ld	e, (hl)
	xor	a, a
	ld	d, a
	sub	a, (hl)
	bit	7, e
	jr	Z, 00222$
	bit	7, d
	jr	NZ, 00223$
	cp	a, a
	jr	00223$
00222$:
	bit	7, d
	jr	Z, 00223$
	scf
00223$:
	jp	NC, 00126$
;src/dandy_core.c:725: flood_stack_ptr--;
	ld	hl, #_flood_stack_ptr
	dec	(hl)
;src/dandy_core.c:726: uint8_t x = flood_stack_x[flood_stack_ptr];
	ld	a, (hl)
	ld	c, a
	rlca
	sbc	a, a
	ld	b, a
	ld	hl, #_flood_stack_x
	add	hl, bc
	ld	a, (hl)
	ldhl	sp,	#0
	ld	(hl), a
;src/dandy_core.c:727: uint8_t y = flood_stack_y[flood_stack_ptr];
	ld	hl, #_flood_stack_y
	add	hl, bc
	ld	a, (hl)
	ldhl	sp,	#1
	ld	(hl), a
;src/dandy_core.c:730: for (int8_t dy = -1; dy <= 1; ++dy) {
	ld	c, #0xff
00125$:
	ld	e, c
	ld	a,#0x01
	ld	d,a
	sub	a, c
	bit	7, e
	jr	Z, 00224$
	bit	7, d
	jr	NZ, 00225$
	cp	a, a
	jr	00225$
00224$:
	bit	7, d
	jr	Z, 00225$
	scf
00225$:
	jr	C, 00119$
;src/dandy_core.c:731: int16_t ny = (int16_t)y + dy;
	ldhl	sp,	#1
	ld	l, (hl)
	ld	a, c
	ld	e, a
	rlca
	sbc	a, a
	ld	d, a
	ld	h, #0x00
	add	hl, de
	ld	b, l
	ld	a, h
	ldhl	sp,	#2
	ld	(hl), b
	inc	hl
;src/dandy_core.c:732: if (ny < 0 || ny >= DANDY_LEVEL_HEIGHT) continue;
	ld	(hl-), a
	ld	a, (hl)
	ldhl	sp,	#8
	ld	(hl), a
	ldhl	sp,	#3
	ld	a, (hl)
	ldhl	sp,	#9
	ld	(hl), a
	bit	7, (hl)
	jp	NZ, 00117$
	dec	hl
	ld	a, (hl+)
	sub	a, #0x1e
	ld	a, (hl)
	sbc	a, #0x00
	jp	NC, 00117$
;src/dandy_core.c:734: uint16_t row_offset = row_offsets[ny];
	pop	hl
	pop	de
	push	de
	push	hl
	sla	e
	rl	d
	ld	hl, #_row_offsets
	add	hl, de
	ld	e, l
	ld	d, h
	ld	a, (de)
	ldhl	sp,	#4
	ld	(hl+), a
	inc	de
	ld	a, (de)
	ld	(hl), a
;src/dandy_core.c:736: for (int8_t dx = -1; dx <= 1; ++dx) {
	ld	b, #0xff
00123$:
	ld	e, b
	ld	a,#0x01
	ld	d,a
	sub	a, b
	bit	7, e
	jr	Z, 00227$
	bit	7, d
	jr	NZ, 00228$
	cp	a, a
	jr	00228$
00227$:
	bit	7, d
	jr	Z, 00228$
	scf
00228$:
	jr	C, 00117$
;src/dandy_core.c:737: if (dx == 0 && dy == 0) continue;
	ld	a, b
	or	a, a
	jr	NZ, 00108$
	or	a, c
	jr	Z, 00115$
00108$:
;src/dandy_core.c:739: int16_t nx = (int16_t)x + dx;
	ldhl	sp,	#0
	ld	e, (hl)
	ld	a, b
	ld	l, a
	rlca
	sbc	a, a
	ld	h, a
	ld	d, #0x00
	add	hl, de
	ld	e, l
	ld	a, h
	ldhl	sp,	#6
	ld	(hl), e
	inc	hl
;src/dandy_core.c:740: if (nx < 0 || nx >= DANDY_LEVEL_WIDTH) continue;
	ld	(hl-), a
	ld	a, (hl+)
	inc	hl
	ld	(hl-), a
	ld	a, (hl+)
	inc	hl
	ld	(hl), a
	bit	7, (hl)
	jr	NZ, 00115$
	dec	hl
	ld	a, (hl+)
	sub	a, #0x3c
	ld	a, (hl)
	sbc	a, #0x00
	jr	NC, 00115$
;src/dandy_core.c:742: uint16_t pos = row_offset + nx;
	ldhl	sp,	#6
	ld	a, (hl+)
	ld	e, a
	ld	d, (hl)
	ldhl	sp,	#4
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	add	hl, de
	ld	e, l
	ld	d, h
;src/dandy_core.c:743: if (dandy_map[pos] == oc) {
	ld	hl, #_dandy_map
	add	hl, de
	ld	e, l
	ld	d, h
	ld	a, (de)
	ldhl	sp,	#14
	sub	a, (hl)
	jr	NZ, 00115$
;src/dandy_core.c:744: dandy_map[pos] = nc; // Mark immediately to prevent double-queuing!
	ldhl	sp,	#15
	ld	a, (hl)
	ld	(de), a
;src/dandy_core.c:745: flood_push((uint8_t)nx, (uint8_t)ny);
	ldhl	sp,	#2
	ld	e, (hl)
	ldhl	sp,	#6
	ld	a, (hl)
	push	bc
	call	_flood_push
	pop	bc
00115$:
;src/dandy_core.c:736: for (int8_t dx = -1; dx <= 1; ++dx) {
	inc	b
	jr	00123$
00117$:
;src/dandy_core.c:730: for (int8_t dy = -1; dy <= 1; ++dy) {
	inc	c
	jp	00125$
00126$:
;src/dandy_core.c:750: }
	add	sp, #12
	pop	hl
	pop	af
	jp	(hl)
;src/dandy_core.c:754: static int16_t clamp(int16_t val, int16_t min, int16_t max) {
;	---------------------------------
; Function clamp
; ---------------------------------
_clamp:
	push	de
;src/dandy_core.c:755: if (val < min) return min;
	ldhl	sp,	#0
	ld	a, (hl+)
	sub	a, c
	ld	a, (hl)
	sbc	a, b
	ld	d, (hl)
	ld	a, b
	ld	e, a
	bit	7, e
	jr	Z, 00121$
	bit	7, d
	jr	NZ, 00122$
	cp	a, a
	jr	00122$
00121$:
	bit	7, d
	jr	Z, 00122$
	scf
00122$:
	jr	C, 00105$
;src/dandy_core.c:756: if (val > max) return max;
	ldhl	sp,	#4
	ld	e, l
	ld	d, h
	ldhl	sp,	#0
	ld	a, (de)
	inc	de
	sub	a, (hl)
	inc	hl
	ld	a, (de)
	sbc	a, (hl)
	ld	a, (de)
	ld	d, a
	ld	e, (hl)
	bit	7, e
	jr	Z, 00123$
	bit	7, d
	jr	NZ, 00124$
	cp	a, a
	jr	00124$
00123$:
	bit	7, d
	jr	Z, 00124$
	scf
00124$:
	jr	NC, 00104$
	ldhl	sp,	#4
	ld	a, (hl+)
	ld	c, a
	ld	b, (hl)
	jr	00105$
00104$:
;src/dandy_core.c:757: return val;
	pop	bc
	push	bc
00105$:
;src/dandy_core.c:758: }
	inc	sp
	inc	sp
	pop	hl
	pop	af
	jp	(hl)
;src/dandy_core.c:760: static int8_t to_delta(int16_t target, int16_t current) {
;	---------------------------------
; Function to_delta
; ---------------------------------
_to_delta:
	ld	l, e
	ld	h, d
;src/dandy_core.c:761: if (target > current) return 1;
	ld	e, h
	ld	d, b
	ld	a, c
	sub	a, l
	ld	a, b
	sbc	a, h
	bit	7, e
	jr	Z, 00121$
	bit	7, d
	jr	NZ, 00122$
	cp	a, a
	jr	00122$
00121$:
	bit	7, d
	jr	Z, 00122$
	scf
00122$:
	jr	NC, 00102$
	ld	a, #0x01
	ret
00102$:
;src/dandy_core.c:762: if (target < current) return -1;
	ld	e, b
	ld	d, h
	ld	a, l
	sub	a, c
	ld	a, h
	sbc	a, b
	bit	7, e
	jr	Z, 00123$
	bit	7, d
	jr	NZ, 00124$
	cp	a, a
	jr	00124$
00123$:
	bit	7, d
	jr	Z, 00124$
	scf
00124$:
	jr	NC, 00104$
	ld	a, #0xff
	ret
00104$:
;src/dandy_core.c:763: return 0;
	xor	a, a
;src/dandy_core.c:764: }
	ret
;src/dandy_core.c:766: void dandy_join_player(uint8_t p_idx) {
;	---------------------------------
; Function dandy_join_player
; ---------------------------------
_dandy_join_player::
	add	sp, #-4
;src/dandy_core.c:767: if (p_idx >= MAX_PLAYERS) return;
	ld	c, a
	sub	a, #0x04
	jp	NC, 00105$
;src/dandy_core.c:768: if (!player_joined[p_idx]) {
	ld	hl, #_player_joined
	ld	b, #0x00
	add	hl, bc
	bit	0, (hl)
	jp	NZ, 00105$
;src/dandy_core.c:769: player_joined[p_idx] = true;
	ld	(hl), #0x01
;src/dandy_core.c:770: player_health[p_idx] = 100;
	ld	l, c
	ld	h, #0x00
	add	hl, hl
	ld	e, l
	ld	d, h
	ld	hl, #_player_health
	add	hl, de
	ld	a, #0x64
	ld	(hl+), a
	ld	(hl), #0x00
;src/dandy_core.c:771: player_score[p_idx] = 0;
	ld	hl, #_player_score
	add	hl, de
	xor	a, a
	ld	(hl+), a
	ld	(hl), a
;src/dandy_core.c:772: player_bombs[p_idx] = 0;
	ld	hl, #_player_bombs
	ld	b, #0x00
	add	hl, bc
	ld	(hl), #0x00
;src/dandy_core.c:773: player_keys[p_idx] = 0;
	ld	hl, #_player_keys
	ld	b, #0x00
	add	hl, bc
	ld	(hl), #0x00
;src/dandy_core.c:774: player_dir[p_idx] = 0;
	ld	de, #_player_dir
	ld	l, c
	ld	h, #0x00
	add	hl, de
	inc	sp
	inc	sp
	ld	(hl), #0x00
	push	hl
;src/dandy_core.c:775: arrow_dir[p_idx] = -1;
	ld	hl, #_arrow_dir
	ld	b, #0x00
	add	hl, bc
	ld	(hl), #0xff
;src/dandy_core.c:778: uint8_t px = player_x[p_idx];
	ld	hl, #_player_x
	ld	b, #0x00
	add	hl, bc
	ld	b, (hl)
;src/dandy_core.c:779: uint8_t py = player_y[p_idx];
	ld	de, #_player_y+0
	ld	l, c
	ld	h, #0x00
	add	hl, de
	ld	e, (hl)
;src/dandy_core.c:782: dandy_map[row_offsets[py] + px] = GET_PLAYER_TILE(p_idx, player_dir[p_idx]);
	xor	a, a
	ld	l, e
	ld	h, a
	add	hl, hl
	ld	de, #_row_offsets
	add	hl, de
	ld	a,	(hl+)
	ld	h, (hl)
	ld	l, a
	ld	e, b
	ld	d, #0x00
	add	hl, de
	ld	e, l
	ld	d, h
	ld	hl, #_dandy_map
	add	hl, de
	push	hl
	ld	a, l
	ldhl	sp,	#4
	ld	(hl), a
	pop	hl
	ld	a, h
	ldhl	sp,	#3
	ld	(hl), a
	ld	a, c
	add	a, a
	add	a, a
	add	a, a
	add	a, #0x18
	ld	c, a
	pop	de
	push	de
	ld	a, (de)
	add	a, c
	pop	de
	pop	hl
	push	hl
	push	de
	ld	(hl), a
;src/dandy_core.c:783: is_dirty = true;
	ld	hl, #_is_dirty
	ld	(hl), #0x01
00105$:
;src/dandy_core.c:785: }
	add	sp, #4
	ret
;src/dandy_core.c:787: bool dandy_is_player_joined(uint8_t p_idx) {
;	---------------------------------
; Function dandy_is_player_joined
; ---------------------------------
_dandy_is_player_joined::
;src/dandy_core.c:788: if (p_idx >= MAX_PLAYERS) return false;
	ld	c, a
	sub	a, #0x04
	jr	C, 00102$
	xor	a, a
	ret
00102$:
;src/dandy_core.c:789: return player_joined[p_idx];
	ld	hl, #_player_joined
	ld	b, #0x00
	add	hl, bc
	ld	a, (hl)
;src/dandy_core.c:790: }
	ret
	.area _CODE
	.area _INITIALIZER
__xinit__flood_stack_ptr:
	.db #0x00	;  0
	.area _CABS (ABS)
