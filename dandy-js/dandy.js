var kDirToDeltaX = [0, 1, 1, 1, 0, -1 , -1, -1];
var kDirToDeltaY = [-1, -1, 0, 1, 1, 1, 0, -1];
var kDeltaToDir = [[7, 0, 1], [6, 0, 2], [5, 4, 3]];
var kSearchOrder = [0, -1, 1];
var kButtonsToDir = [
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
var kButtonLeft = 1;
var kButtonRight = 2;
var kButtonUp = 4;
var kButtonDown = 8;
var kButtonFire = 16;
var kButtonBomb = 32;

var kTicksPerMove = 4;

var dirty = false;
var map = [];
var currentLevel = 0;
var rotor = 0;

var px = 0;
var py = 0;
var pHealth = 100;
var pScore = 0;
var pBombs = 0;
var pKeys = 0;
var pDir;
var pax = 0;
var pay = 0;
var paDir = -1;
var pButtons = 0;
var pOldButtons = 0;
var pPlayerMoveTimer = 0;

// The width and height of a tile when displayed in the canvas.
var windowTileWidth = 20;
var windowTileHeight = 10;

function loadLevel() {
    var level = levels[currentLevel];
    for (var y = 0; y < levelHeight; y++) {
        var line = level[y];
        for (var x = 0; x < levelWidth; x++) {
            map[x + y * levelWidth] = encoding.indexOf(line.charAt(x));
        }
    }
    setPlayerStartPosition();
    paDir = -1;
}

function findFirst(item) {
    for (var y = 0; y < levelHeight; y++) {
        for (var x = 0; x < levelWidth; x++) {
            if ( map[x + y * levelWidth] == item ) {
                return [x,y];

            }
        }
    }
    return null;
}

function setPlayerStartPosition() {
    v = findFirst(kUp);
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
    var canvas = document.getElementById('gameCanvas');

    var context = canvas.getContext('2d');

    var tl = getVisibleTopLeftCorner();
    var baseX = tl[0];
    var baseY = tl[1];

    var canvasTileWidth = tileWidth * 2;
    var canvasTileHeight = tileHeight * 2;

    for (var y = 0; y < windowTileHeight; y++) {
        for (var x = 0; x < windowTileWidth; x++) {
            var d = map[(baseX + x) + (baseY + y)*levelWidth];
            var tx = tileWidth * (d & 15);
            var ty = tileHeight * (d >> 4);
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
    nx = clamp(px + kDirToDeltaX[dir], 0, levelWidth-1);
    ny = clamp(py + kDirToDeltaY[dir], 0, levelHeight-1);
    pos = nx + ny * levelWidth;
    v = map[pos];
    canMove = true;
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
        nx = clamp(pax + kDirToDeltaX[paDir], 0, levelWidth-1);
        ny = clamp(pay + kDirToDeltaY[paDir], 0, levelHeight-1);
        var tl = getVisibleTopLeftCorner();
        var baseX = tl[0];
        var baseY = tl[1];
        pos = pax + pay * levelWidth;
        npos = nx + ny * levelWidth;
        v = map[pos];
        nv = map[npos];
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
                var rv = kSpace;
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
    var tl = getVisibleTopLeftCorner();
    var baseX = tl[0];
    var baseY = tl[1];

    for (var y = 0; y < windowTileHeight; y++) {
        for (var x = 0; x < windowTileWidth; x++) {
            var pos = (baseX + x) + (baseY + y) * levelWidth;
            var v = map[pos];
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
    var tl = getVisibleTopLeftCorner();
    var baseX = tl[0];
    var baseY = tl[1];

    var dx;
    var dy;
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
    var xBase = adjust(baseX, dx, rotor % dx);
    var yBase = adjust(baseY, dy, Math.floor(rotor / dx));
    var xEnd = baseX + windowTileWidth;
    var yEnd = baseY + windowTileHeight;
    for (var my = yBase; my < yEnd; my += dx) {
        for (var mx = xBase; mx < xEnd; mx += dy) {
            var pos = mx + my * levelWidth;
            var v = map[pos];
            if (v >= kMonster1 && v <= kMonster3) {
                var mDir = kDeltaToDir[toDelta(py, my) + 1][toDelta(px, mx) + 1];
                for (var d = 0; d < 3; d++) {
                    var dd = (mDir + kSearchOrder[d]) & 7;
                    var npos = pos + kDirToDeltaX[dd] + kDirToDeltaY[dd] * levelWidth;
                    var nv = map[npos];
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
                var ran_number=Math.floor(Math.random()*8);
                if (ran_number < 4) {
                    var gd = ran_number * 2;
                    for (var dd = 0; dd < 8; dd += 2) {
                        var gd2 = (gd + dd) % 7;
                        var gpos = pos + kDirToDeltaX[gd2] + kDirToDeltaY[gd2] * levelWidth;
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
    var deltaDown = pButtons & ~ pOldButtons;
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
    var d = kButtonsToDir[pButtons & 15];

    if (d >= 0) {
        pDir = d;
        if (pPlayerMoveTimer == 0) {
            pPlayerMoveTimer = kTicksPerMove;
            for ( var di = 0; di < 3; di++) {
                var dd = (pDir + kSearchOrder[di]) & 7;
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
    var k = 0;
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
