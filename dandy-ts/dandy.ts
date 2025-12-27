import { levels, encoding, levelHeight, levelWidth, kUp, kPlayer1, kSpace, kDoor, kMoney, kKey, kBomb, kFood, kDown, kArrow, kHeart, kMonster1, kMonster2, kMonster3, kGenerator1, kGenerator2, kGenerator3 } from './levels';
import { strike, tileWidth, tileHeight } from './strike';

const kDirToDeltaX = [0, 1, 1, 1, 0, -1 , -1, -1];
const kDirToDeltaY = [-1, -1, 0, 1, 1, 1, 0, -1];
const kDeltaToDir = [[7, 0, 1], [6, 0, 2], [5, 4, 3]];
const kSearchOrder = [0, -1, 1];
const kButtonsToDir = [
    // D U R L
    -1, // 0 0 0 0
    6, // 0 0 0 1
    2, // 0 0 1 0
    -1, // 0 0 1 1
    0, // 0 1 0 0
    7, // 0 1 0 1
    1, // 0 1 1 0
    0, // 0 1 1 1
    4, // 1 0 0 0
    5, // 1 0 0 1
    3, // 1 0 1 0
    4, // 1 0 1 1
    -1, // 1 1 0 0
    6, // 1 1 0 1
    2, // 1 1 1 0
    -1  // 1 1 1 1
];

// Masks
const kButtonLeft = 1;
const kButtonRight = 2;
const kButtonUp = 4;
const kButtonDown = 8;
const kButtonFire = 16;
const kButtonBomb = 32;

const kTicksPerMove = 4;

// The width and height of a tile when displayed in the canvas.
const windowTileWidth = 20;
const windowTileHeight = 10;

class DandyGame {
    canvas: HTMLCanvasElement;
    context: CanvasRenderingContext2D;
    dirty: boolean;
    map: number[];
    currentLevel: number;
    rotor: number;

    px: number;
    py: number;
    pHealth: number;
    pScore: number;
    pBombs: number;
    pKeys: number;
    pDir: number;
    pax: number;
    pay: number;
    paDir: number;
    pButtons: number;
    pOldButtons: number;
    pPlayerMoveTimer: number;

    boundGameStep: FrameRequestCallback;
    boundOnKeyDown: (e: KeyboardEvent) => void;
    boundOnKeyUp: (e: KeyboardEvent) => void;

    scoreDisplay: HTMLElement | null;
    healthDisplay: HTMLElement | null;
    bombDisplay: HTMLElement | null;
    keyDisplay: HTMLElement | null;

    lastScore: number;
    lastHealth: number;
    lastBombs: number;
    lastKeys: number;

    constructor() {
        this.canvas = document.getElementById('gameCanvas') as HTMLCanvasElement;
        this.context = this.canvas.getContext('2d')!;
        this.context.imageSmoothingEnabled = false;
        this.dirty = false;
        this.map = [];
        this.currentLevel = 0;
        this.rotor = 0;

        this.px = 0;
        this.py = 0;
        this.pHealth = 100;
        this.pScore = 0;
        this.pBombs = 0;
        this.pKeys = 0;
        this.pDir = 0;
        this.pax = 0;
        this.pay = 0;
        this.paDir = -1;
        this.pButtons = 0;
        this.pOldButtons = 0;
        this.pPlayerMoveTimer = 0;

        this.boundGameStep = this.gameStep.bind(this);
        this.boundOnKeyDown = this.onkeydown.bind(this);
        this.boundOnKeyUp = this.onkeyup.bind(this);

        // HUD Elements
        this.scoreDisplay = document.getElementById('score-display');
        this.healthDisplay = document.getElementById('health-display');
        this.bombDisplay = document.getElementById('bomb-display');
        this.keyDisplay = document.getElementById('key-display');

        // Cached HUD values to minimize DOM updates
        this.lastScore = -1;
        this.lastHealth = -1;
        this.lastBombs = -1;
        this.lastKeys = -1;
    }

    init() {
        document.addEventListener('keydown', this.boundOnKeyDown);
        document.addEventListener('keyup', this.boundOnKeyUp);
        this.loadLevel();
        this.updateHud();
        this.startLoop();
    }

    startLoop() {
        requestAnimationFrame(this.boundGameStep);
    }

    updateHud() {
        if (this.pScore !== this.lastScore) {
            if (this.scoreDisplay) this.scoreDisplay.textContent = this.pScore.toString();
            this.lastScore = this.pScore;
        }
        if (this.pHealth !== this.lastHealth) {
            if (this.healthDisplay) this.healthDisplay.textContent = this.pHealth.toString();
            this.lastHealth = this.pHealth;
        }
        if (this.pBombs !== this.lastBombs) {
            if (this.bombDisplay) this.bombDisplay.textContent = this.pBombs.toString();
            this.lastBombs = this.pBombs;
        }
        if (this.pKeys !== this.lastKeys) {
            if (this.keyDisplay) this.keyDisplay.textContent = this.pKeys.toString();
            this.lastKeys = this.pKeys;
        }
    }

    gameStep() {
        this.doButtons();
        this.moveArrow();
        this.moveMonsters();
        
        // Update HUD (could be optimized to only run when values change, but 60fps DOM update for text is usually fine here)
        this.updateHud();

        if (this.dirty) {
            this.drawPicture();
            this.dirty = false;
        }
        if (this.pHealth <= 0) {
            this.endGame();
        }
        requestAnimationFrame(this.boundGameStep);
    }

    loadLevel() {
        const level = levels[this.currentLevel];
        for (let y = 0; y < levelHeight; y++) {
            const line = level[y];
            for (let x = 0; x < levelWidth; x++) {
                this.map[x + y * levelWidth] = encoding.indexOf(line.charAt(x));
            }
        }
        this.setPlayerStartPosition();
        this.paDir = -1;
        this.dirty = true;
    }

    findFirst(item: number): [number, number] | null {
        for (let y = 0; y < levelHeight; y++) {
            for (let x = 0; x < levelWidth; x++) {
                if (this.map[x + y * levelWidth] == item) {
                    return [x, y];
                }
            }
        }
        return null;
    }

    setPlayerStartPosition() {
        const v = this.findFirst(kUp);
        let upx, upy;
        if (v) {
            upx = v[0];
            upy = v[1];
        } else {
            upx = 1;
            upy = 1;
        }
        this.px = upx;
        this.py = upy - 1;
        this.map[this.px + this.py * levelWidth] = kPlayer1;
    }

    nextLevel() {
        if (this.currentLevel < 25) {
            this.currentLevel++;
        }
        this.loadLevel();
    }

    endGame() {
        this.currentLevel = 0;
        this.pHealth = 100;
        this.pKeys = 0;
        this.pBombs = 0;
        this.pScore = 0;
        this.loadLevel();
    }

    floodFill(pos: number, oc: number, nc: number) {
        if (oc == this.map[pos]) {
            this.map[pos] = nc;
            this.floodFill(pos - levelWidth - 1, oc, nc);
            this.floodFill(pos - levelWidth, oc, nc);
            this.floodFill(pos - levelWidth + 1, oc, nc);
            this.floodFill(pos - 1, oc, nc);
            this.floodFill(pos + 1, oc, nc);
            this.floodFill(pos + levelWidth - 1, oc, nc);
            this.floodFill(pos + levelWidth, oc, nc);
            this.floodFill(pos + levelWidth + 1, oc, nc);
        }
    }

    getVisibleTopLeftCorner() {
        return [this.clamp(this.px - (windowTileWidth >> 1), 0, levelWidth - windowTileWidth),
        this.clamp(this.py - (windowTileHeight >> 1), 0, levelHeight - windowTileHeight)];
    }

    drawPicture() {
        const tl = this.getVisibleTopLeftCorner();
        const baseX = tl[0];
        const baseY = tl[1];

        const canvasTileWidth = tileWidth * 2;
        const canvasTileHeight = tileHeight * 2;

        for (let y = 0; y < windowTileHeight; y++) {
            for (let x = 0; x < windowTileWidth; x++) {
                const d = this.map[(baseX + x) + (baseY + y) * levelWidth];
                const tx = tileWidth * (d & 15);
                const ty = tileHeight * (d >> 4);
                this.context.drawImage(strike, tx, ty, tileWidth, tileHeight,
                    x * canvasTileWidth, y * canvasTileHeight,
                    canvasTileWidth, canvasTileHeight);
            }
        }
    }

    clamp(x: number, min: number, max: number) {
        return Math.min(max, Math.max(min, x));
    }

    move(dir: number) {
        const nx = this.clamp(this.px + kDirToDeltaX[dir], 0, levelWidth - 1);
        const ny = this.clamp(this.py + kDirToDeltaY[dir], 0, levelHeight - 1);
        const pos = nx + ny * levelWidth;
        const v = this.map[pos];
        let canMove = true;
        switch (v) {
            case kSpace:
                break;
            case kDoor:
                if (this.pKeys > 0) {
                    this.pKeys -= 1;
                    this.floodFill(pos, kDoor, kSpace);
                } else {
                    canMove = false;
                }
                break;
            case kMoney:
                this.pScore += 100;
                break;
            case kKey:
                this.pKeys += 1;
                break;
            case kBomb:
                this.pBombs += 1;
                break;
            case kFood:
                this.pHealth += 100;
                break;
            case kDown:
                this.nextLevel();
                return;
            default:
                canMove = false;
                break;
        }
        if (canMove) {
            this.map[this.px + this.py * levelWidth] = kSpace;
            this.px = nx;
            this.py = ny;
            this.map[this.px + this.py * levelWidth] = kPlayer1;
            this.dirty = true;
        }
        return canMove;
    }

    moveArrow() {
        if (this.paDir != -1) {
            const nx = this.clamp(this.pax + kDirToDeltaX[this.paDir], 0, levelWidth - 1);
            const ny = this.clamp(this.pay + kDirToDeltaY[this.paDir], 0, levelHeight - 1);
            const tl = this.getVisibleTopLeftCorner();
            const baseX = tl[0];
            const baseY = tl[1];
            const pos = this.pax + this.pay * levelWidth;
            const npos = nx + ny * levelWidth;
            const v = this.map[pos];
            let nv = this.map[npos];
            if (v >= kArrow && v <= kArrow + 7) {
                this.map[pos] = kSpace;
            }
            if (nx < baseX || ny < baseY || nx >= baseX + windowTileWidth
                || ny >= baseY + windowTileHeight) {
                nv = -1; // Kill arrow
            }
            if (nv != kSpace) {
                this.paDir = -1;
                if (nv >= kBomb && nv < kArrow) {
                    let rv = kSpace;
                    if (nv == kBomb) {
                        this.doBomb();
                    } else if (nv == kHeart) {
                        rv = kMonster3;
                    } else if (nv == kMonster2 || nv == kMonster3) {
                        rv = nv - 1;
                    }
                    this.map[npos] = rv;
                }
            } else {
                this.map[npos] = kArrow + ((this.paDir - 5) & 7);
                this.pax = nx;
                this.pay = ny;
            }
            this.dirty = true;
        }
    }

    doBomb() {
        const tl = this.getVisibleTopLeftCorner();
        const baseX = tl[0];
        const baseY = tl[1];

        for (let y = 0; y < windowTileHeight; y++) {
            for (let x = 0; x < windowTileWidth; x++) {
                const pos = (baseX + x) + (baseY + y) * levelWidth;
                const v = this.map[pos];
                if ((v >= kMonster1 && v <= kMonster3) ||
                    (v >= kGenerator1 && v <= kGenerator3)) {
                    this.map[pos] = kSpace;
                }
            }
        }
        this.dirty = true;
    }

    toDelta(a: number, b: number) {
        if (a > b) {
            return 1;
        } else if (a < b) {
            return -1;
        } else {
            return 0;
        }
    }

    adjust(x: number, m: number, dx: number) {
        return m * Math.floor(x / m) + dx;
    }

    moveMonsters() {
        const tl = this.getVisibleTopLeftCorner();
        const baseX = tl[0];
        const baseY = tl[1];

        let dx;
        let dy;
        if (true) {
            dx = 4;
            dy = 4;
        } else {
            dx = 2;
            dy = 2;
        }
        if (++this.rotor >= (dx * dy)) {
            this.rotor = 0;
        }
        const xBase = this.adjust(baseX, dx, this.rotor % dx);
        const yBase = this.adjust(baseY, dy, Math.floor(this.rotor / dx));
        const xEnd = baseX + windowTileWidth;
        const yEnd = baseY + windowTileHeight;
        for (let my = yBase; my < yEnd; my += dx) {
            for (let mx = xBase; mx < xEnd; mx += dy) {
                const pos = mx + my * levelWidth;
                const v = this.map[pos];
                if (v >= kMonster1 && v <= kMonster3) {
                    const mDir = kDeltaToDir[this.toDelta(this.py, my) + 1][this.toDelta(this.px, mx) + 1];
                    for (let d = 0; d < 3; d++) {
                        const dd = (mDir + kSearchOrder[d]) & 7;
                        const npos = pos + kDirToDeltaX[dd] + kDirToDeltaY[dd] * levelWidth;
                        const nv = this.map[npos];
                        if (nv == kPlayer1) {
                            this.map[pos] = kSpace;
                            this.pHealth -= 10 * (v - kMonster1 + 1);
                            this.dirty = true;
                            break;
                        } else if (nv == kSpace) {
                            this.map[pos] = kSpace;
                            this.map[npos] = v;
                            this.dirty = true;
                            break;
                        } else if (nv >= kArrow && nv <= kArrow + 7) {
                            // Don't try to walk around arrows.
                            break;
                        }
                    }
                } else if (v >= kGenerator1 && v <= kGenerator3) {
                    const ran_number = Math.floor(Math.random() * 8);
                    if (ran_number < 4) {
                        const gd = ran_number * 2;
                        for (let dd = 0; dd < 8; dd += 2) {
                            const gd2 = (gd + dd) % 7;
                            const gpos = pos + kDirToDeltaX[gd2] + kDirToDeltaY[gd2] * levelWidth;
                            if (this.map[gpos] == kSpace) {
                                this.map[gpos] = kMonster1 + (v - kGenerator1);
                                break;
                            }
                        }
                    }
                }
            }
        }
    }

    fire() {
        if (this.paDir == -1) {
            this.pax = this.px;
            this.pay = this.py;
            this.paDir = this.pDir;
        }
    }

    doButtons() {
        const deltaDown = this.pButtons & ~this.pOldButtons;
        this.pOldButtons = this.pButtons;
        if (deltaDown & kButtonBomb) {
            if (this.pBombs > 0) {
                this.pBombs--;
                this.doBomb();
            }
        }

        if (this.pButtons & kButtonFire) {
            this.fire();
        }
        const d = kButtonsToDir[this.pButtons & 15];

        if (d >= 0) {
            this.pDir = d;
            if (this.pPlayerMoveTimer == 0) {
                this.pPlayerMoveTimer = kTicksPerMove;
                for (let di = 0; di < 3; di++) {
                    const dd = (this.pDir + kSearchOrder[di]) & 7;
                    if (this.move(dd)) {
                        break;
                    }
                }
            }
        }

        if (this.pPlayerMoveTimer > 0) {
            this.pPlayerMoveTimer--;
        }
    }

    onkeydown(e: KeyboardEvent) {
        this.pButtons = this.updateMask(this.pButtons, e.code, 1);
        // Suppress default behavior for game keys
        if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space', 'KeyB'].includes(e.code)) {
             e.preventDefault();
             // In TS/React world returning false doesn't always work for suppression but preventDefault does.
             // We will keep the return structure but rely on preventDefault.
        }
    }

    onkeyup(e: KeyboardEvent) {
        this.pButtons = this.updateMask(this.pButtons, e.code, 0);
    }

    updateMask(mask: number, code: string, down: number) {
        let k = 0;
        switch (code) {
            case 'ArrowLeft':
                k = kButtonLeft;
                break;
            case 'ArrowUp':
                k = kButtonUp;
                break;
            case 'ArrowRight':
                k = kButtonRight;
                break;
            case 'ArrowDown':
                k = kButtonDown;
                break;
            case 'KeyB':
                k = kButtonBomb;
                break;
            case 'Space':
                k = kButtonFire;
                break;
            default:
                return mask;
        }
        if (down) {
            mask = mask | k;
        } else {
            mask = mask & ~k;
        }
        return mask;
    }
}

// Export for usage if needed, or just run it.
function game() {
    const dandy = new DandyGame();
    dandy.init();
}

// If running in browser context, expose game function to window or run it automatically if preferred
// The HTML calls game() on load. We can attach it to window.
if (typeof window !== 'undefined') {
    (window as any).game = game;
}
