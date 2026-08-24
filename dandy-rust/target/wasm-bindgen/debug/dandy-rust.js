export class DandyApp {
    __destroy_into_raw() {
        const ptr = this.__wbg_ptr;
        this.__wbg_ptr = 0;
        DandyAppFinalization.unregister(this);
        return ptr;
    }
    free() {
        const ptr = this.__destroy_into_raw();
        wasm.__wbg_dandyapp_free(ptr, 0);
    }
    /**
     * @param {number} frames
     */
    bench_tick(frames) {
        wasm.dandyapp_bench_tick(this.__wbg_ptr, frames);
    }
    /**
     * @returns {boolean}
     */
    can_sleep() {
        const ret = wasm.dandyapp_can_sleep(this.__wbg_ptr);
        return ret !== 0;
    }
    /**
     * @param {number} ch
     * @returns {number}
     */
    get_audio_channel_sound(ch) {
        const ret = wasm.dandyapp_get_audio_channel_sound(this.__wbg_ptr, ch);
        return ret;
    }
    /**
     * @returns {string}
     */
    get_build_info() {
        let deferred1_0;
        let deferred1_1;
        try {
            const ret = wasm.dandyapp_get_build_info(this.__wbg_ptr);
            deferred1_0 = ret[0];
            deferred1_1 = ret[1];
            return getStringFromWasm0(ret[0], ret[1]);
        } finally {
            wasm.__wbindgen_free(deferred1_0, deferred1_1, 1);
        }
    }
    /**
     * @returns {number}
     */
    get_difficulty() {
        const ret = wasm.dandyapp_get_difficulty(this.__wbg_ptr);
        return ret;
    }
    /**
     * @returns {number}
     */
    get_framebuffer_ptr() {
        const ret = wasm.dandyapp_get_framebuffer_ptr(this.__wbg_ptr);
        return ret >>> 0;
    }
    /**
     * @returns {number}
     */
    get_framebuffer_size() {
        const ret = wasm.dandyapp_get_framebuffer_size(this.__wbg_ptr);
        return ret >>> 0;
    }
    /**
     * @returns {number}
     */
    get_level() {
        const ret = wasm.dandyapp_get_level(this.__wbg_ptr);
        return ret >>> 0;
    }
    /**
     * @param {number} player_idx
     * @returns {string}
     */
    get_player_class_name(player_idx) {
        let deferred1_0;
        let deferred1_1;
        try {
            const ret = wasm.dandyapp_get_player_class_name(this.__wbg_ptr, player_idx);
            deferred1_0 = ret[0];
            deferred1_1 = ret[1];
            return getStringFromWasm0(ret[0], ret[1]);
        } finally {
            wasm.__wbindgen_free(deferred1_0, deferred1_1, 1);
        }
    }
    /**
     * @param {number} player_idx
     * @returns {string}
     */
    get_player_color(player_idx) {
        let deferred1_0;
        let deferred1_1;
        try {
            const ret = wasm.dandyapp_get_player_color(this.__wbg_ptr, player_idx);
            deferred1_0 = ret[0];
            deferred1_1 = ret[1];
            return getStringFromWasm0(ret[0], ret[1]);
        } finally {
            wasm.__wbindgen_free(deferred1_0, deferred1_1, 1);
        }
    }
    /**
     * @param {number} player_idx
     * @returns {number}
     */
    get_player_dir(player_idx) {
        const ret = wasm.dandyapp_get_player_dir(this.__wbg_ptr, player_idx);
        return ret >>> 0;
    }
    /**
     * @param {number} player_idx
     * @returns {number}
     */
    get_player_x(player_idx) {
        const ret = wasm.dandyapp_get_player_x(this.__wbg_ptr, player_idx);
        return ret;
    }
    /**
     * @param {number} player_idx
     * @returns {number}
     */
    get_player_y(player_idx) {
        const ret = wasm.dandyapp_get_player_y(this.__wbg_ptr, player_idx);
        return ret;
    }
    /**
     * @returns {string}
     */
    get_route_info() {
        let deferred1_0;
        let deferred1_1;
        try {
            const ret = wasm.dandyapp_get_route_info(this.__wbg_ptr);
            deferred1_0 = ret[0];
            deferred1_1 = ret[1];
            return getStringFromWasm0(ret[0], ret[1]);
        } finally {
            wasm.__wbindgen_free(deferred1_0, deferred1_1, 1);
        }
    }
    /**
     * @returns {Uint8Array}
     */
    get_sound_events() {
        const ret = wasm.dandyapp_get_sound_events(this.__wbg_ptr);
        var v1 = getArrayU8FromWasm0(ret[0], ret[1]).slice();
        wasm.__wbindgen_free(ret[0], ret[1] * 1, 1);
        return v1;
    }
    /**
     * @returns {number}
     */
    get_sound_events_len() {
        const ret = wasm.dandyapp_get_sound_events_len(this.__wbg_ptr);
        return ret >>> 0;
    }
    /**
     * @returns {number}
     */
    get_sound_events_ptr() {
        const ret = wasm.dandyapp_get_sound_events_ptr(this.__wbg_ptr);
        return ret >>> 0;
    }
    /**
     * @returns {number}
     */
    get_sound_mask() {
        const ret = wasm.dandyapp_get_sound_mask(this.__wbg_ptr);
        return ret >>> 0;
    }
    /**
     * @param {number} sound_id
     * @returns {number}
     */
    static get_sound_pokey_channel(sound_id) {
        const ret = wasm.dandyapp_get_sound_pokey_channel(sound_id);
        return ret >>> 0;
    }
    /**
     * @param {number} sound_id
     * @returns {number}
     */
    static get_sound_priority(sound_id) {
        const ret = wasm.dandyapp_get_sound_priority(sound_id);
        return ret;
    }
    /**
     * @returns {number}
     */
    get_state_checksum() {
        const ret = wasm.dandyapp_get_state_checksum(this.__wbg_ptr);
        return ret >>> 0;
    }
    /**
     * @returns {number}
     */
    get_stats_len() {
        const ret = wasm.dandyapp_get_stats_len(this.__wbg_ptr);
        return ret >>> 0;
    }
    /**
     * @returns {number}
     */
    get_stats_ptr() {
        const ret = wasm.dandyapp_get_stats_ptr(this.__wbg_ptr);
        return ret >>> 0;
    }
    /**
     * @param {number} ch
     * @returns {boolean}
     */
    is_audio_channel_active(ch) {
        const ret = wasm.dandyapp_is_audio_channel_active(this.__wbg_ptr, ch);
        return ret !== 0;
    }
    /**
     * @param {number} player_idx
     * @returns {boolean}
     */
    is_player_active(player_idx) {
        const ret = wasm.dandyapp_is_player_active(this.__wbg_ptr, player_idx);
        return ret !== 0;
    }
    /**
     * @param {Uint8Array} bytes
     * @returns {boolean}
     */
    load_state_bytes(bytes) {
        const ptr0 = passArray8ToWasm0(bytes, wasm.__wbindgen_malloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.dandyapp_load_state_bytes(this.__wbg_ptr, ptr0, len0);
        return ret !== 0;
    }
    /**
     * @param {Uint8Array} bytes
     * @returns {number}
     */
    net_decode_handshake_version(bytes) {
        const ptr0 = passArray8ToWasm0(bytes, wasm.__wbindgen_malloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.dandyapp_net_decode_handshake_version(this.__wbg_ptr, ptr0, len0);
        return ret;
    }
    /**
     * @param {number} frame
     * @returns {Uint8Array}
     */
    net_encode_all_local_input_packets(frame) {
        const ret = wasm.dandyapp_net_encode_all_local_input_packets(this.__wbg_ptr, frame);
        var v1 = getArrayU8FromWasm0(ret[0], ret[1]).slice();
        wasm.__wbindgen_free(ret[0], ret[1] * 1, 1);
        return v1;
    }
    /**
     * @returns {Uint8Array}
     */
    net_encode_handshake_packet() {
        const ret = wasm.dandyapp_net_encode_handshake_packet(this.__wbg_ptr);
        var v1 = getArrayU8FromWasm0(ret[0], ret[1]).slice();
        wasm.__wbindgen_free(ret[0], ret[1] * 1, 1);
        return v1;
    }
    /**
     * @param {number} frame
     * @returns {Uint8Array}
     */
    net_encode_local_input_packet(frame) {
        const ret = wasm.dandyapp_net_encode_local_input_packet(this.__wbg_ptr, frame);
        var v1 = getArrayU8FromWasm0(ret[0], ret[1]).slice();
        wasm.__wbindgen_free(ret[0], ret[1] * 1, 1);
        return v1;
    }
    /**
     * @param {number} player_idx
     * @param {number} frame
     * @returns {Uint8Array}
     */
    net_encode_player_input_packet(player_idx, frame) {
        const ret = wasm.dandyapp_net_encode_player_input_packet(this.__wbg_ptr, player_idx, frame);
        var v1 = getArrayU8FromWasm0(ret[0], ret[1]).slice();
        wasm.__wbindgen_free(ret[0], ret[1] * 1, 1);
        return v1;
    }
    /**
     * @returns {string}
     */
    net_get_app_id() {
        let deferred1_0;
        let deferred1_1;
        try {
            const ret = wasm.dandyapp_net_get_app_id(this.__wbg_ptr);
            deferred1_0 = ret[0];
            deferred1_1 = ret[1];
            return getStringFromWasm0(ret[0], ret[1]);
        } finally {
            wasm.__wbindgen_free(deferred1_0, deferred1_1, 1);
        }
    }
    /**
     * @param {number} frame
     * @returns {number}
     */
    net_get_checksum_at_frame(frame) {
        const ret = wasm.dandyapp_net_get_checksum_at_frame(this.__wbg_ptr, frame);
        return ret >>> 0;
    }
    /**
     * @returns {number}
     */
    net_get_confirmed_frame() {
        const ret = wasm.dandyapp_net_get_confirmed_frame(this.__wbg_ptr);
        return ret >>> 0;
    }
    /**
     * @returns {number}
     */
    net_get_current_frame() {
        const ret = wasm.dandyapp_net_get_current_frame(this.__wbg_ptr);
        return ret >>> 0;
    }
    /**
     * @param {number} frame
     * @returns {number}
     */
    net_get_local_input_mask(frame) {
        const ret = wasm.dandyapp_net_get_local_input_mask(this.__wbg_ptr, frame);
        return ret;
    }
    /**
     * @returns {number}
     */
    net_get_local_player_mask() {
        const ret = wasm.dandyapp_net_get_local_player_mask(this.__wbg_ptr);
        return ret;
    }
    /**
     * @param {number} player_idx
     * @param {number} frame
     * @returns {number}
     */
    net_get_player_input_mask(player_idx, frame) {
        const ret = wasm.dandyapp_net_get_player_input_mask(this.__wbg_ptr, player_idx, frame);
        return ret;
    }
    /**
     * @returns {number}
     */
    net_get_protocol_version() {
        const ret = wasm.dandyapp_net_get_protocol_version(this.__wbg_ptr);
        return ret;
    }
    /**
     * @returns {number}
     */
    net_get_resimulated_frames() {
        const ret = wasm.dandyapp_net_get_resimulated_frames(this.__wbg_ptr);
        return ret >>> 0;
    }
    /**
     * @returns {number}
     */
    net_get_rollback_count() {
        const ret = wasm.dandyapp_net_get_rollback_count(this.__wbg_ptr);
        return ret >>> 0;
    }
    /**
     * @param {number} player_idx
     */
    net_hot_join(player_idx) {
        wasm.dandyapp_net_hot_join(this.__wbg_ptr, player_idx);
    }
    /**
     * @param {number} local_player_idx
     */
    net_init(local_player_idx) {
        wasm.dandyapp_net_init(this.__wbg_ptr, local_player_idx);
    }
    /**
     * @param {number} local_player_mask
     */
    net_init_mask(local_player_mask) {
        wasm.dandyapp_net_init_mask(this.__wbg_ptr, local_player_mask);
    }
    /**
     * @param {number} player_idx
     * @returns {boolean}
     */
    net_is_local_player(player_idx) {
        const ret = wasm.dandyapp_net_is_local_player(this.__wbg_ptr, player_idx);
        return ret !== 0;
    }
    /**
     * @param {number} player_idx
     * @returns {boolean}
     */
    net_is_player_joined(player_idx) {
        const ret = wasm.dandyapp_net_is_player_joined(this.__wbg_ptr, player_idx);
        return ret !== 0;
    }
    /**
     * @param {number} frame
     * @param {Uint8Array} bytes
     * @returns {boolean}
     */
    net_load_sync_state(frame, bytes) {
        const ptr0 = passArray8ToWasm0(bytes, wasm.__wbindgen_malloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.dandyapp_net_load_sync_state(this.__wbg_ptr, frame, ptr0, len0);
        return ret !== 0;
    }
    /**
     * @param {number} peer_idx
     * @param {number} frame
     * @param {number} mask
     * @returns {boolean}
     */
    net_receive_remote_input(peer_idx, frame, mask) {
        const ret = wasm.dandyapp_net_receive_remote_input(this.__wbg_ptr, peer_idx, frame, mask);
        return ret !== 0;
    }
    /**
     * @param {Uint8Array} bytes
     * @returns {boolean}
     */
    net_receive_remote_packet(bytes) {
        const ptr0 = passArray8ToWasm0(bytes, wasm.__wbindgen_malloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.dandyapp_net_receive_remote_packet(this.__wbg_ptr, ptr0, len0);
        return ret !== 0;
    }
    /**
     * @param {number} player_idx
     * @param {boolean} is_local
     */
    net_set_is_local_player(player_idx, is_local) {
        wasm.dandyapp_net_set_is_local_player(this.__wbg_ptr, player_idx, is_local);
    }
    /**
     * @param {PlayerAction} action
     * @param {boolean} pressed
     */
    net_set_local_action(action, pressed) {
        wasm.dandyapp_net_set_local_action(this.__wbg_ptr, action, pressed);
    }
    /**
     * @param {number} mask
     */
    net_set_local_input_mask(mask) {
        wasm.dandyapp_net_set_local_input_mask(this.__wbg_ptr, mask);
    }
    /**
     * @param {number} player_idx
     * @param {boolean} joined
     */
    net_set_player_joined(player_idx, joined) {
        wasm.dandyapp_net_set_player_joined(this.__wbg_ptr, player_idx, joined);
    }
    /**
     * @param {number} player_idx
     * @param {PlayerAction} action
     * @param {boolean} pressed
     */
    net_set_player_local_action(player_idx, action, pressed) {
        wasm.dandyapp_net_set_player_local_action(this.__wbg_ptr, player_idx, action, pressed);
    }
    /**
     * @param {number} player_idx
     * @param {number} mask
     */
    net_set_player_local_input_mask(player_idx, mask) {
        wasm.dandyapp_net_set_player_local_input_mask(this.__wbg_ptr, player_idx, mask);
    }
    /**
     * @returns {number}
     */
    net_step() {
        const ret = wasm.dandyapp_net_step(this.__wbg_ptr);
        return ret >>> 0;
    }
    /**
     * @param {Uint8Array} bytes
     * @returns {boolean}
     */
    net_validate_handshake_packet(bytes) {
        const ptr0 = passArray8ToWasm0(bytes, wasm.__wbindgen_malloc);
        const len0 = WASM_VECTOR_LEN;
        const ret = wasm.dandyapp_net_validate_handshake_packet(this.__wbg_ptr, ptr0, len0);
        return ret !== 0;
    }
    constructor() {
        const ret = wasm.dandyapp_new();
        this.__wbg_ptr = ret;
        DandyAppFinalization.register(this, this.__wbg_ptr, this);
        return this;
    }
    /**
     * @param {number} player_idx
     */
    remove_player(player_idx) {
        wasm.dandyapp_remove_player(this.__wbg_ptr, player_idx);
    }
    /**
     * @returns {Uint8Array}
     */
    save_state_bytes() {
        const ret = wasm.dandyapp_save_state_bytes(this.__wbg_ptr);
        var v1 = getArrayU8FromWasm0(ret[0], ret[1]).slice();
        wasm.__wbindgen_free(ret[0], ret[1] * 1, 1);
        return v1;
    }
    /**
     * @param {number} player_idx
     * @param {PlayerAction} action
     * @param {boolean} pressed
     */
    set_action(player_idx, action, pressed) {
        wasm.dandyapp_set_action(this.__wbg_ptr, player_idx, action, pressed);
    }
    /**
     * @param {number} val
     */
    set_difficulty(val) {
        wasm.dandyapp_set_difficulty(this.__wbg_ptr, val);
    }
    /**
     * @param {number} player_idx
     * @param {number} mask
     */
    set_player_input_mask(player_idx, mask) {
        wasm.dandyapp_set_player_input_mask(this.__wbg_ptr, player_idx, mask);
    }
    /**
     * @param {number} player_idx
     */
    spawn_player(player_idx) {
        wasm.dandyapp_spawn_player(this.__wbg_ptr, player_idx);
    }
    tick() {
        wasm.dandyapp_tick(this.__wbg_ptr);
    }
}
if (Symbol.dispose) DandyApp.prototype[Symbol.dispose] = DandyApp.prototype.free;

/**
 * @enum {0 | 1 | 2 | 3}
 */
export const Difficulty = Object.freeze({
    Trivial: 0, "0": "Trivial",
    Easy: 1, "1": "Easy",
    Hard: 2, "2": "Hard",
    Deadly: 3, "3": "Deadly",
});

/**
 * @enum {0 | 1 | 2 | 3 | 4 | 5}
 */
export const PlayerAction = Object.freeze({
    Up: 0, "0": "Up",
    Down: 1, "1": "Down",
    Left: 2, "2": "Left",
    Right: 3, "3": "Right",
    Shoot: 4, "4": "Shoot",
    Bomb: 5, "5": "Bomb",
});

/**
 * @returns {string}
 */
export function net_get_app_id() {
    let deferred1_0;
    let deferred1_1;
    try {
        const ret = wasm.net_get_app_id();
        deferred1_0 = ret[0];
        deferred1_1 = ret[1];
        return getStringFromWasm0(ret[0], ret[1]);
    } finally {
        wasm.__wbindgen_free(deferred1_0, deferred1_1, 1);
    }
}

/**
 * @returns {number}
 */
export function net_get_protocol_version() {
    const ret = wasm.net_get_protocol_version();
    return ret;
}

export function wasm_start() {
    wasm.wasm_start();
}
function __wbg_get_imports() {
    const import0 = {
        __proto__: null,
        __wbg___wbindgen_throw_1506f2235d1bdba0: function(arg0, arg1) {
            throw new Error(getStringFromWasm0(arg0, arg1));
        },
        __wbg_error_a6fa202b58aa1cd3: function(arg0, arg1) {
            let deferred0_0;
            let deferred0_1;
            try {
                deferred0_0 = arg0;
                deferred0_1 = arg1;
                console.error(getStringFromWasm0(arg0, arg1));
            } finally {
                wasm.__wbindgen_free(deferred0_0, deferred0_1, 1);
            }
        },
        __wbg_new_227d7c05414eb861: function() {
            const ret = new Error();
            return ret;
        },
        __wbg_stack_3b0d974bbf31e44f: function(arg0, arg1) {
            const ret = arg1.stack;
            const ptr1 = passStringToWasm0(ret, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
            const len1 = WASM_VECTOR_LEN;
            getDataViewMemory0().setInt32(arg0 + 4 * 1, len1, true);
            getDataViewMemory0().setInt32(arg0 + 4 * 0, ptr1, true);
        },
        __wbindgen_init_externref_table: function() {
            const table = wasm.__wbindgen_externrefs;
            const offset = table.grow(4);
            table.set(0, undefined);
            table.set(offset + 0, undefined);
            table.set(offset + 1, null);
            table.set(offset + 2, true);
            table.set(offset + 3, false);
        },
    };
    return {
        __proto__: null,
        "./dandy-rust_bg.js": import0,
    };
}

const DandyAppFinalization = (typeof FinalizationRegistry === 'undefined')
    ? { register: () => {}, unregister: () => {} }
    : new FinalizationRegistry(ptr => wasm.__wbg_dandyapp_free(ptr, 1));

function getArrayU8FromWasm0(ptr, len) {
    ptr = ptr >>> 0;
    return getUint8ArrayMemory0().subarray(ptr / 1, ptr / 1 + len);
}

let cachedDataViewMemory0 = null;
function getDataViewMemory0() {
    if (cachedDataViewMemory0 === null || cachedDataViewMemory0.buffer.detached === true || (cachedDataViewMemory0.buffer.detached === undefined && cachedDataViewMemory0.buffer !== wasm.memory.buffer)) {
        cachedDataViewMemory0 = new DataView(wasm.memory.buffer);
    }
    return cachedDataViewMemory0;
}

function getStringFromWasm0(ptr, len) {
    return decodeText(ptr >>> 0, len);
}

let cachedUint8ArrayMemory0 = null;
function getUint8ArrayMemory0() {
    if (cachedUint8ArrayMemory0 === null || cachedUint8ArrayMemory0.byteLength === 0) {
        cachedUint8ArrayMemory0 = new Uint8Array(wasm.memory.buffer);
    }
    return cachedUint8ArrayMemory0;
}

function passArray8ToWasm0(arg, malloc) {
    const ptr = malloc(arg.length * 1, 1) >>> 0;
    getUint8ArrayMemory0().set(arg, ptr / 1);
    WASM_VECTOR_LEN = arg.length;
    return ptr;
}

function passStringToWasm0(arg, malloc, realloc) {
    if (realloc === undefined) {
        const buf = cachedTextEncoder.encode(arg);
        const ptr = malloc(buf.length, 1) >>> 0;
        getUint8ArrayMemory0().subarray(ptr, ptr + buf.length).set(buf);
        WASM_VECTOR_LEN = buf.length;
        return ptr;
    }

    let len = arg.length;
    let ptr = malloc(len, 1) >>> 0;

    const mem = getUint8ArrayMemory0();

    let offset = 0;

    for (; offset < len; offset++) {
        const code = arg.charCodeAt(offset);
        if (code > 0x7F) break;
        mem[ptr + offset] = code;
    }
    if (offset !== len) {
        if (offset !== 0) {
            arg = arg.slice(offset);
        }
        ptr = realloc(ptr, len, len = offset + arg.length * 3, 1) >>> 0;
        const view = getUint8ArrayMemory0().subarray(ptr + offset, ptr + len);
        const ret = cachedTextEncoder.encodeInto(arg, view);

        offset += ret.written;
        ptr = realloc(ptr, len, offset, 1) >>> 0;
    }

    WASM_VECTOR_LEN = offset;
    return ptr;
}

let cachedTextDecoder = new TextDecoder('utf-8', { ignoreBOM: true, fatal: true });
cachedTextDecoder.decode();
const MAX_SAFARI_DECODE_BYTES = 2146435072;
let numBytesDecoded = 0;
function decodeText(ptr, len) {
    numBytesDecoded += len;
    if (numBytesDecoded >= MAX_SAFARI_DECODE_BYTES) {
        cachedTextDecoder = new TextDecoder('utf-8', { ignoreBOM: true, fatal: true });
        cachedTextDecoder.decode();
        numBytesDecoded = len;
    }
    return cachedTextDecoder.decode(getUint8ArrayMemory0().subarray(ptr, ptr + len));
}

const cachedTextEncoder = new TextEncoder();

if (!('encodeInto' in cachedTextEncoder)) {
    cachedTextEncoder.encodeInto = function (arg, view) {
        const buf = cachedTextEncoder.encode(arg);
        view.set(buf);
        return {
            read: arg.length,
            written: buf.length
        };
    };
}

let WASM_VECTOR_LEN = 0;

let wasmModule, wasmInstance, wasm;
function __wbg_finalize_init(instance, module) {
    wasmInstance = instance;
    wasm = instance.exports;
    wasmModule = module;
    cachedDataViewMemory0 = null;
    cachedUint8ArrayMemory0 = null;
    wasm.__wbindgen_start();
    return wasm;
}

async function __wbg_load(module, imports) {
    if (typeof Response === 'function' && module instanceof Response) {
        if (typeof WebAssembly.instantiateStreaming === 'function') {
            try {
                return await WebAssembly.instantiateStreaming(module, imports);
            } catch (e) {
                const validResponse = module.ok && expectedResponseType(module.type);

                if (validResponse && module.headers.get('Content-Type') !== 'application/wasm') {
                    console.warn("`WebAssembly.instantiateStreaming` failed because your server does not serve Wasm with `application/wasm` MIME type. Falling back to `WebAssembly.instantiate` which is slower. Original error:\n", e);

                } else { throw e; }
            }
        }

        const bytes = await module.arrayBuffer();
        return await WebAssembly.instantiate(bytes, imports);
    } else {
        const instance = await WebAssembly.instantiate(module, imports);

        if (instance instanceof WebAssembly.Instance) {
            return { instance, module };
        } else {
            return instance;
        }
    }

    function expectedResponseType(type) {
        switch (type) {
            case 'basic': case 'cors': case 'default': return true;
        }
        return false;
    }
}

function initSync(module) {
    if (wasm !== undefined) return wasm;


    if (module !== undefined) {
        if (Object.getPrototypeOf(module) === Object.prototype) {
            ({module} = module)
        } else {
            console.warn('using deprecated parameters for `initSync()`; pass a single object instead')
        }
    }

    const imports = __wbg_get_imports();
    if (!(module instanceof WebAssembly.Module)) {
        module = new WebAssembly.Module(module);
    }
    const instance = new WebAssembly.Instance(module, imports);
    return __wbg_finalize_init(instance, module);
}

async function __wbg_init(module_or_path) {
    if (wasm !== undefined) return wasm;


    if (module_or_path !== undefined) {
        if (Object.getPrototypeOf(module_or_path) === Object.prototype) {
            ({module_or_path} = module_or_path)
        } else {
            console.warn('using deprecated parameters for the initialization function; pass a single object instead')
        }
    }

    if (module_or_path === undefined) {
        module_or_path = new URL('dandy-rust_bg.wasm', import.meta.url);
    }
    const imports = __wbg_get_imports();

    if (typeof module_or_path === 'string' || (typeof Request === 'function' && module_or_path instanceof Request) || (typeof URL === 'function' && module_or_path instanceof URL)) {
        module_or_path = fetch(module_or_path);
    }

    const { instance, module } = await __wbg_load(await module_or_path, imports);

    return __wbg_finalize_init(instance, module);
}

export { initSync, __wbg_init as default };
