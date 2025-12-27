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

let dirty = false;
const map = [];
let currentLevel = 0;
let rotor = 0;

let px = 0;
let py = 0;
let pHealth = 100;
let pScore = 0;
let pBombs = 0;
let pKeys = 0;
let pDir;
let pax = 0;
let pay = 0;
let paDir = -1;
let pButtons = 0;
let pOldButtons = 0;
let pPlayerMoveTimer = 0;

// The width and height of a tile when displayed in the canvas.
const windowTileWidth = 20;
const windowTileHeight = 10;

function loadLevel() {
    const level = levels[currentLevel];
    for (let y = 0; y < levelHeight; y++) {
        const line = level[y];
        for (let x = 0; x < levelWidth; x++) {
            map[x + y * levelWidth] = encoding.indexOf(line.charAt(x));
        }
    }
    setPlayerStartPosition();
    paDir = -1;
}

function findFirst(item) {
    for (let y = 0; y < levelHeight; y++) {
        for (let x = 0; x < levelWidth; x++) {
            if ( map[x + y * levelWidth] == item ) {
                return [x,y];

            }
        }
    }
    return null;
}

function setPlayerStartPosition() {
    const v = findFirst(kUp);
    let upx, upy;
    if (v) {
        upx = v[0];
        upy = v[1];
    } else {
        upx = 1;
        upy = 1;
    }
    px = upx;
    py = upy-1;
    map[px + py * levelWidth] = kPlayer1;
}

function nextLevel() {
    if (currentLevel < 25) {
        currentLevel++;
    }
    loadLevel();
}

function endGame() {
    currentLevel = 0;
    pHealth = 100;
    pKeys = 0;
    pBombs = 0;
    pScore = 0;
    loadLevel();
}

function floodFill(pos, oc, nc) {
    if (oc == map[pos]) {
        map[pos] = nc;
        floodFill(pos - levelWidth - 1, oc, nc);
        floodFill(pos - levelWidth, oc, nc);
        floodFill(pos - levelWidth + 1, oc, nc);
        floodFill(pos - 1, oc, nc);
        floodFill(pos + 1, oc, nc);
        floodFill(pos + levelWidth - 1, oc, nc);
        floodFill(pos + levelWidth, oc, nc);
        floodFill(pos + levelWidth + 1, oc, nc);
    }
}

function getVisibleTopLeftCorner() {
    return [clamp(px - (windowTileWidth >> 1), 0, levelWidth - windowTileWidth),
            clamp(py - (windowTileHeight >> 1), 0, levelHeight - windowTileHeight)];
}

function drawPicture(){
    const canvas = document.getElementById('gameCanvas');

    const context = canvas.getContext('2d');

    const tl = getVisibleTopLeftCorner();
    const baseX = tl[0];
    const baseY = tl[1];

    const canvasTileWidth = tileWidth * 2;
    const canvasTileHeight = tileHeight * 2;

    for (let y = 0; y < windowTileHeight; y++) {
        for (let x = 0; x < windowTileWidth; x++) {
            const d = map[(baseX + x) + (baseY + y)*levelWidth];
            const tx = tileWidth * (d & 15);
            const ty = tileHeight * (d >> 4);
            context.drawImage(strike, tx, ty, tileWidth, tileHeight,
                    x * canvasTileWidth, y * canvasTileHeight,
                    canvasTileWidth, canvasTileHeight);
        }
    }
}

function game() {
    loadLevel();
    setInterval(gameStep, 15);
}

function gameStep() {
    doButtons();
    moveArrow();
    moveMonsters();
    if (dirty) {
        drawPicture();
        dirty = false;
    }
    if (pHealth <= 0) {
        endGame();
    }
}

function clamp(x, min, max) {
    return Math.min(max, Math.max(min, x));
}

function move(dir) {
    const nx = clamp(px + kDirToDeltaX[dir], 0, levelWidth-1);
    const ny = clamp(py + kDirToDeltaY[dir], 0, levelHeight-1);
    const pos = nx + ny * levelWidth;
    const v = map[pos];
    let canMove = true;
    switch (v) {
    case kSpace:
        break;
    case kDoor:
        if ( pKeys > 0) {
            pKeys -= 1;
            floodFill(pos, kDoor, kSpace);
        } else {
            canMove = false;
        }
        break;
    case kMoney:
        pScore += 100;
        break;
    case kKey:
        pKeys += 1;
        break;
    case kBomb:
        pBombs += 1;
        break;
    case kFood:
        pHealth += 100;
        break;
    case kDown:
        nextLevel();
        return;
    default:
        canMove = false;
    break;
    }
    if (canMove) {
        map[px + py * levelWidth] = kSpace;
        px = nx;
        py = ny;
        map[px + py * levelWidth] = kPlayer1;
        dirty = true;
    }
    return canMove;
}

function moveArrow() {
    if (paDir != -1) {
        const nx = clamp(pax + kDirToDeltaX[paDir], 0, levelWidth-1);
        const ny = clamp(pay + kDirToDeltaY[paDir], 0, levelHeight-1);
        const tl = getVisibleTopLeftCorner();
        const baseX = tl[0];
        const baseY = tl[1];
        const pos = pax + pay * levelWidth;
        const npos = nx + ny * levelWidth;
        const v = map[pos];
        let nv = map[npos];
        if (v >= kArrow && v <= kArrow + 7) {
            map[pos] = kSpace;
        }
        if (nx < baseX || ny < baseY || nx >= baseX + windowTileWidth
                || ny >= baseY + windowTileHeight) {
            nv = -1; // Kill arrow
        }
        if (nv != kSpace) {
            paDir = -1;
            if ( nv >= kBomb && nv < kArrow ) {
                let rv = kSpace;
                if (nv == kBomb) {
                    doBomb();
                } else if (nv == kHeart) {
                    rv = kMonster3;
                } else if (nv == kMonster2 || nv == kMonster3) {
                    rv = nv - 1;
                }
                map[npos] = rv;
            }
        } else {
            map[npos] = kArrow + ((paDir - 5) & 7);
            pax = nx;
            pay = ny;
        }
        dirty = true;
    }
}

function doBomb() {
    const tl = getVisibleTopLeftCorner();
    const baseX = tl[0];
    const baseY = tl[1];

    for (let y = 0; y < windowTileHeight; y++) {
        for (let x = 0; x < windowTileWidth; x++) {
            const pos = (baseX + x) + (baseY + y) * levelWidth;
            const v = map[pos];
            if ((v >= kMonster1 && v <= kMonster3) ||
                    (v >= kGenerator1 && v <= kGenerator3)) {
                map[pos] = kSpace;
            }
        }
    }
    dirty = true;
}

function toDelta(a, b) {
    if (a > b) {
        return 1;
    } else if (a < b) {
        return -1;
    } else {
        return 0;
    }
}

function adjust(x, m, dx) {
    return m * Math.floor(x / m) + dx;
}

function moveMonsters() {
    const tl = getVisibleTopLeftCorner();
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
    if (++rotor >= (dx * dy)) {
        rotor = 0;
    }
    const xBase = adjust(baseX, dx, rotor % dx);
    const yBase = adjust(baseY, dy, Math.floor(rotor / dx));
    const xEnd = baseX + windowTileWidth;
    const yEnd = baseY + windowTileHeight;
    for (let my = yBase; my < yEnd; my += dx) {
        for (let mx = xBase; mx < xEnd; mx += dy) {
            const pos = mx + my * levelWidth;
            const v = map[pos];
            if (v >= kMonster1 && v <= kMonster3) {
                const mDir = kDeltaToDir[toDelta(py, my) + 1][toDelta(px, mx) + 1];
                for (let d = 0; d < 3; d++) {
                    const dd = (mDir + kSearchOrder[d]) & 7;
                    const npos = pos + kDirToDeltaX[dd] + kDirToDeltaY[dd] * levelWidth;
                    const nv = map[npos];
                    if (nv == kPlayer1)  {
                        map[pos] = kSpace;
                        pHealth -= 10 * (v - kMonster1 + 1);
                        dirty = true;
                        break;
                    } else if (nv == kSpace ) {
                        map[pos] = kSpace;
                        map[npos] = v;
                        dirty = true;
                        break;
                    } else if (nv >= kArrow && nv <= kArrow+7) {
                        // Don't try to walk around arrows.
                        break;
                    }
                }
            } else if (v >= kGenerator1 && v <= kGenerator3) {
                const ran_number=Math.floor(Math.random()*8);
                if (ran_number < 4) {
                    const gd = ran_number * 2;
                    for (let dd = 0; dd < 8; dd += 2) {
                        const gd2 = (gd + dd) % 7;
                        const gpos = pos + kDirToDeltaX[gd2] + kDirToDeltaY[gd2] * levelWidth;
                        if (map[gpos] == kSpace) {
                            map[gpos] = kMonster1 + (v - kGenerator1);
                            break;
                        }
                    }
                }
            }
        }
    }
}

function fire() {
    if (paDir == -1) {
        pax = px;
        pay = py;
        paDir = pDir;
    }
}

function doButtons() {
    const deltaDown = pButtons & ~ pOldButtons;
    pOldButtons = pButtons;
    if (deltaDown & kButtonBomb) {
        if (pBombs > 0) {
            pBombs--;
            doBomb();
        }
    }

    if (pButtons & kButtonFire) {
        fire();
    }
    const d = kButtonsToDir[pButtons & 15];

    if (d >= 0) {
        pDir = d;
        if (pPlayerMoveTimer == 0) {
            pPlayerMoveTimer = kTicksPerMove;
            for ( let di = 0; di < 3; di++) {
                const dd = (pDir + kSearchOrder[di]) & 7;
                if (move(dd)) {
                    break;
                }
            }
        }
    }

    if (pPlayerMoveTimer > 0) {
        pPlayerMoveTimer--;
    }
}

function onkeydown(e) {
    if(!e) {
        e = window.event;
    }
    pButtons = updateMask(pButtons, e.keyCode, 1);
    // Suppress default behavior
    return false;
}

function onkeyup(e) {
    if(!e) {
        e = window.event;
    }
    pButtons = updateMask(pButtons, e.keyCode, 0);
    // Suppress default behavior
    return false;
}

function updateMask(mask, code, down) {
    let k = 0;
    switch (code) {
    case 37:
        k = kButtonLeft;
        break;
    case 38:
        k = kButtonUp;
        break;
    case 39:
        k = kButtonRight;
        break;
    case 40:
        k = kButtonDown;
        break;
    case 66:
        k = kButtonBomb;
        break;
    case 32:
        k = kButtonFire;
        break;
    default:
        return mask;
    }
    if ( down ) {
        mask = mask | k;
    } else {
        mask = mask & ~ k;
    }
    return mask;
}

document.onkeydown = onkeydown;
document.onkeyup = onkeyup;