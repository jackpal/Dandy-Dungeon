import { WASI, Fd, File } from "https://cdn.jsdelivr.net/npm/@bjorn3/browser_wasi_shim@0.3.0/dist/index.js";

async function init() {
    const args = ["dandy-haskell"];
    const env = [];
    const fds = [
        new Fd(), // stdin
        new Fd(), // stdout
        new Fd(), // stderr
    ];
    const wasi = new WASI(args, env, fds);

    const importObj = {
        wasi_snapshot_preview1: wasi.wasiImport,
    };

    const response = await fetch("dandy-haskell.wasm");
    const buffer = await response.arrayBuffer();
    const { instance } = await WebAssembly.instantiate(buffer, importObj);

    // Initialize WASI / GHC RTS reactor model
    wasi.initialize(instance);

    // Invoke our exported FFI initialization
    const appPtr = instance.exports.hs_init_game();

    let sleeping = false;
    const pressedKeys = new Set();

    const canvas = document.getElementById("gameCanvas");
    const ctx = canvas.getContext("2d");

    const PlayerAction = {
        Up: 0,
        Down: 1,
        Left: 2,
        Right: 3,
        Shoot: 4,
        Bomb: 5
    };

    const controlRegistry = {
        "ArrowUp": { player: 0, action: PlayerAction.Up },
        "ArrowDown": { player: 0, action: PlayerAction.Down },
        "ArrowLeft": { player: 0, action: PlayerAction.Left },
        "ArrowRight": { player: 0, action: PlayerAction.Right },
        " ": { player: 0, action: PlayerAction.Shoot },
        "b": { player: 0, action: PlayerAction.Bomb },
        "B": { player: 0, action: PlayerAction.Bomb },

        "w": { player: 1, action: PlayerAction.Up },
        "W": { player: 1, action: PlayerAction.Up },
        "s": { player: 1, action: PlayerAction.Down },
        "S": { player: 1, action: PlayerAction.Down },
        "a": { player: 1, action: PlayerAction.Left },
        "A": { player: 1, action: PlayerAction.Left },
        "d": { player: 1, action: PlayerAction.Right },
        "D": { player: 1, action: PlayerAction.Right },
        "f": { player: 1, action: PlayerAction.Shoot },
        "F": { player: 1, action: PlayerAction.Shoot },
        "g": { player: 1, action: PlayerAction.Bomb },
        "G": { player: 1, action: PlayerAction.Bomb }
    };

    window.addEventListener("keydown", (e) => {
        const bind = controlRegistry[e.key];
        if (bind !== undefined) {
            pressedKeys.add(e.key);
            instance.exports.hs_set_action(appPtr, bind.player, bind.action, true);

            if (sleeping) {
                sleeping = false;
                requestAnimationFrame(gameLoop);
            }

            if (e.key === " " || e.key.startsWith("Arrow")) {
                e.preventDefault();
            }
        }
    });

    window.addEventListener("keyup", (e) => {
        const bind = controlRegistry[e.key];
        if (bind !== undefined) {
            pressedKeys.delete(e.key);
            instance.exports.hs_set_action(appPtr, bind.player, bind.action, false);
        }
    });

    window.addEventListener("blur", () => {
        pressedKeys.clear();
        for (const key in controlRegistry) {
            const bind = controlRegistry[key];
            instance.exports.hs_set_action(appPtr, bind.player, bind.action, false);
        }
    });

    const lastHuds = [
        { active: false, score: -1, health: -1, keys: -1, bombs: -1 },
        { active: false, score: -1, health: -1, keys: -1, bombs: -1 },
        { active: false, score: -1, health: -1, keys: -1, bombs: -1 },
        { active: false, score: -1, health: -1, keys: -1, bombs: -1 }
    ];

    function updateHUD(statsArray) {
        for (let i = 0; i < 4; i++) {
            const offset = i * 7;
            const active = statsArray[offset] === 1;
            const score = statsArray[offset + 3];
            const health = statsArray[offset + 4];
            const keys = statsArray[offset + 5];
            const bombs = statsArray[offset + 6];

            const cache = lastHuds[i];

            if (active !== cache.active) {
                if (i > 0) {
                    const row = document.getElementById("hud-p" + (i + 1));
                    if (row) {
                        if (active) {
                            row.innerHTML = `
                                <td class="text-left">P${i + 1}</td>
                                <td id="p${i + 1}-score" class="text-right">0</td>
                                <td id="p${i + 1}-health" class="text-right">100</td>
                                <td id="p${i + 1}-keys" class="text-right">0</td>
                                <td id="p${i + 1}-bombs" class="text-right">0</td>
                            `;
                        } else {
                            if (i === 1) {
                                row.innerHTML = `<td colspan="5" class="hud-p2-inactive">Player 2: Press WASD/F/G to Join</td>`;
                            } else {
                                row.innerHTML = `<td colspan="5" class="hud-p2-inactive">Player ${i + 1}: Connect Gamepad ${i - 1} & Press A to Join</td>`;
                            }
                        }
                    }
                }
                cache.active = active;
                cache.score = -1;
                cache.health = -1;
                cache.keys = -1;
                cache.bombs = -1;
            }

            if (active) {
                const metrics = [
                    { suffix: "score", val: score, prop: "score" },
                    { suffix: "health", val: health, prop: "health" },
                    { suffix: "keys", val: keys, prop: "keys" },
                    { suffix: "bombs", val: bombs, prop: "bombs" }
                ];

                for (const m of metrics) {
                    if (m.val !== cache[m.prop]) {
                        const el = document.getElementById("p" + (i + 1) + "-" + m.suffix);
                        if (el) {
                            el.textContent = m.val.toString();
                        }
                        cache[m.prop] = m.val;
                    }
                }
            }
        }
    }

    const gamepadRegistry = [
        { player: 2, state: { up: false, down: false, left: false, right: false, shoot: false, bomb: false } },
        { player: 3, state: { up: false, down: false, left: false, right: false, shoot: false, bomb: false } }
    ];

    function pollGamepads() {
        const gamepads = navigator.getGamepads ? navigator.getGamepads() : [];
        for (let i = 0; i < 2; i++) {
            const gp = gamepads[i];
            const reg = gamepadRegistry[i];
            if (gp) {
                const axisThreshold = 0.5;
                const left = (gp.axes[0] < -axisThreshold) || (gp.buttons[14] && gp.buttons[14].pressed);
                const right = (gp.axes[0] > axisThreshold) || (gp.buttons[15] && gp.buttons[15].pressed);
                const up = (gp.axes[1] < -axisThreshold) || (gp.buttons[12] && gp.buttons[12].pressed);
                const down = (gp.axes[1] > axisThreshold) || (gp.buttons[13] && gp.buttons[13].pressed);
                
                const shoot = gp.buttons[0] && gp.buttons[0].pressed;
                const bomb = (gp.buttons[1] && gp.buttons[1].pressed) || (gp.buttons[2] && gp.buttons[2].pressed);

                const actions = [
                    { action: PlayerAction.Up, next: up, prev: reg.state.up, name: "up" },
                    { action: PlayerAction.Down, next: down, prev: reg.state.down, name: "down" },
                    { action: PlayerAction.Left, next: left, prev: reg.state.left, name: "left" },
                    { action: PlayerAction.Right, next: right, prev: reg.state.right, name: "right" },
                    { action: PlayerAction.Shoot, next: shoot, prev: reg.state.shoot, name: "shoot" },
                    { action: PlayerAction.Bomb, next: bomb, prev: reg.state.bomb, name: "bomb" }
                ];

                let anyNewPress = false;
                for (const act of actions) {
                    if (act.next !== act.prev) {
                        instance.exports.hs_set_action(appPtr, reg.player, act.action, act.next);
                        reg.state[act.name] = act.next;
                        if (act.next) {
                            anyNewPress = true;
                        }
                    }
                }

                if (anyNewPress && sleeping) {
                    sleeping = false;
                    requestAnimationFrame(gameLoop);
                }
            }
        }
    }

    function gameLoop() {
        pollGamepads();
        instance.exports.hs_game_tick(appPtr);

        const fbPtr = instance.exports.hs_get_framebuffer_ptr(appPtr);
        const fbSize = instance.exports.hs_get_framebuffer_size(appPtr);
        const fbBytes = new Uint8ClampedArray(instance.exports.memory.buffer, fbPtr, fbSize);

        const imgData = new ImageData(fbBytes, 320, 160);
        ctx.putImageData(imgData, 0, 0);

        const statsPtr = instance.exports.hs_get_stats_ptr(appPtr);
        const statsLen = instance.exports.hs_get_stats_len(appPtr);
        const statsArray = new Int32Array(instance.exports.memory.buffer, statsPtr, statsLen);

        updateHUD(statsArray);

        if (pressedKeys.size === 0 && instance.exports.hs_can_sleep(appPtr) === 1) {
            sleeping = true;
            return;
        }

        requestAnimationFrame(gameLoop);
    }

    requestAnimationFrame(gameLoop);
}

init();
