{-# LANGUAGE TemplateHaskell #-}
module Dandy.Map
  ( newMap
  , getMapTile
  , setMapTile
  , findMapTile
  , unlockMap
  , loadMap
  ) where

import Dandy.Consts
import Dandy.Types (Map(..))
import Dandy.Embed (embedFile)
import Data.Word (Word8)
import Data.Array.IO (newArray, readArray, writeArray)
import Data.Bits (shiftR, (.&.))
import Control.Monad (forM_, when, filterM)

newMap :: IO Map
newMap = do
  arr <- newArray ((0, 0), (mapWidth - 1, mapHeight - 1)) spaceTile
  return (Map arr)

getMapTile :: Map -> Int -> Int -> IO Word8
getMapTile (Map arr) x y
  | x >= 0 && x < mapWidth && y >= 0 && y < mapHeight = readArray arr (x, y)
  | otherwise = return wallTile

setMapTile :: Map -> Int -> Int -> Word8 -> IO ()
setMapTile (Map arr) x y val
  | x >= 0 && x < mapWidth && y >= 0 && y < mapHeight = writeArray arr (x, y) val
  | otherwise = return ()

findMapTile :: Map -> Word8 -> IO (Maybe (Int, Int))
findMapTile (Map arr) target = do
  let search :: Int -> Int -> IO (Maybe (Int, Int))
      search x y
        | y >= mapHeight = return Nothing
        | x >= mapWidth  = search 0 (y + 1)
        | otherwise = do
            val <- readArray arr (x, y)
            if val == target
              then return (Just (x, y))
              else search (x + 1) y
  search 0 0

unlockMap :: Map -> Int -> Int -> IO ()
unlockMap m@(Map arr) startX startY = do
  startTile <- getMapTile m startX startY
  when (startTile == lockTile) $ do
    let loop [] = return ()
        loop ((cx, cy):rest) = do
          tile <- getMapTile m cx cy
          if tile == lockTile
            then do
              setMapTile m cx cy spaceTile
              let neighbors = [ (cx + dx, cy + dy)
                              | dy <- [-1..1]
                              , dx <- [-1..1]
                              , dx /= 0 || dy /= 0
                              ]
              validNeighbors <- filterM (\(nx, ny) -> do
                t <- getMapTile m nx ny
                return (t == lockTile)) neighbors
              loop (validNeighbors ++ rest)
            else loop rest
    loop [(startX, startY)]

loadMap :: Map -> Int -> IO ()
loadMap m lvlIdx = do
  let lvlData = levelMaps !! (lvlIdx `min` 25)
  forM_ (zip [0..] lvlData) $ \(i, b) -> do
    let t1 = b .&. 15
        t2 = (b `shiftR` 4) .&. 15
        idx1 = i * 2
        idx2 = i * 2 + 1
        x1 = idx1 `mod` mapWidth
        y1 = idx1 `div` mapWidth
        x2 = idx2 `mod` mapWidth
        y2 = idx2 `div` mapWidth
    setMapTile m x1 y1 t1
    setMapTile m x2 y2 t2

levelMaps :: [[Word8]]
levelMaps =
  [ $(embedFile "assets/levels/LEVEL.A")
  , $(embedFile "assets/levels/LEVEL.B")
  , $(embedFile "assets/levels/LEVEL.C")
  , $(embedFile "assets/levels/LEVEL.D")
  , $(embedFile "assets/levels/LEVEL.E")
  , $(embedFile "assets/levels/LEVEL.F")
  , $(embedFile "assets/levels/LEVEL.G")
  , $(embedFile "assets/levels/LEVEL.H")
  , $(embedFile "assets/levels/LEVEL.I")
  , $(embedFile "assets/levels/LEVEL.J")
  , $(embedFile "assets/levels/LEVEL.K")
  , $(embedFile "assets/levels/LEVEL.L")
  , $(embedFile "assets/levels/LEVEL.M")
  , $(embedFile "assets/levels/LEVEL.N")
  , $(embedFile "assets/levels/LEVEL.O")
  , $(embedFile "assets/levels/LEVEL.P")
  , $(embedFile "assets/levels/LEVEL.Q")
  , $(embedFile "assets/levels/LEVEL.R")
  , $(embedFile "assets/levels/LEVEL.S")
  , $(embedFile "assets/levels/LEVEL.T")
  , $(embedFile "assets/levels/LEVEL.U")
  , $(embedFile "assets/levels/LEVEL.V")
  , $(embedFile "assets/levels/LEVEL.W")
  , $(embedFile "assets/levels/LEVEL.X")
  , $(embedFile "assets/levels/LEVEL.Y")
  , $(embedFile "assets/levels/LEVEL.Z")
  ]
