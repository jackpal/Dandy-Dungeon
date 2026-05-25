module Dandy.Consts where

import Data.Word (Word8)
import Data.Bits (shiftL)

tileSize :: Int
tileSize = 16

mapWidth :: Int
mapWidth = 60

mapHeight :: Int
mapHeight = 30

viewportWidth :: Int
viewportWidth = 20

viewportHeight :: Int
viewportHeight = 10

screenWidth :: Int
screenWidth = 320

screenHeight :: Int
screenHeight = 160

-- Tile Constants
spaceTile :: Word8
spaceTile = 0

wallTile :: Word8
wallTile = 1

lockTile :: Word8
lockTile = 2

upStairsTile :: Word8
upStairsTile = 3

downStairsTile :: Word8
downStairsTile = 4

keyTile :: Word8
keyTile = 5

foodTile :: Word8
foodTile = 6

moneyTile :: Word8
moneyTile = 7

bombTile :: Word8
bombTile = 8

ghostTile :: Word8
ghostTile = 9 -- 9, 10, 11

heartTile :: Word8
heartTile = 12

generatorTile :: Word8
generatorTile = 13 -- 13, 14, 15

arrowTile :: Word8
arrowTile = 16 -- 16..23

playerTile :: Word8
playerTile = 24 -- 24..27

-- Movement Directions: 0 is Up, clockwise (0..7)
getDirDelta :: Int -> (Int, Int)
getDirDelta 0 = (0, -1)
getDirDelta 1 = (1, -1)
getDirDelta 2 = (1, 0)
getDirDelta 3 = (1, 1)
getDirDelta 4 = (0, 1)
getDirDelta 5 = (-1, 1)
getDirDelta 6 = (-1, 0)
getDirDelta 7 = (-1, -1)
getDirDelta _ = (0, 0)

playerSpawnDirs :: [Int]
playerSpawnDirs = [0, 2, 4, 6]

-- Player logical input actions (Bitmask)
actionUp :: Word8
actionUp = 1 `shiftL` 0

actionDown :: Word8
actionDown = 1 `shiftL` 1

actionLeft :: Word8
actionLeft = 1 `shiftL` 2

actionRight :: Word8
actionRight = 1 `shiftL` 3

actionShoot :: Word8
actionShoot = 1 `shiftL` 4

actionBomb :: Word8
actionBomb = 1 `shiftL` 5
