{-# LANGUAGE TemplateHaskell #-}
{-# LANGUAGE RankNTypes #-}
{-# LANGUAGE FlexibleContexts #-}
module Dandy.Map
  ( emptyMap
  , getMapTile
  , setMapTile
  , findMapTile
  , unlockMap
  , loadMap
  , updateMapPure
  ) where

import Dandy.Consts
import Dandy.Types (Map(..))
import Dandy.Embed (embedFile)
import Data.Word (Word8)
import Data.Array.Unboxed (UArray, array, (!), assocs, (//))
import Data.Array.ST (STUArray)
import Data.Array.Unsafe (unsafeFreeze)
import Control.Monad.ST (ST, runST)
import Data.Bits (shiftR, (.&.))
import Control.Monad (forM_, when, filterM)
import qualified Data.ByteString as BS
import Data.Array.MArray (readArray, writeArray, thaw)

emptyMap :: Map
emptyMap = Map $ array ((0, 0), (mapWidth - 1, mapHeight - 1))
  [((x, y), spaceTile) | y <- [0..mapHeight-1], x <- [0..mapWidth-1]]

getMapTile :: Map -> Int -> Int -> Word8
getMapTile (Map arr) x y
  | x >= 0 && x < mapWidth && y >= 0 && y < mapHeight = arr ! (x, y)
  | otherwise = wallTile

setMapTile :: Map -> Int -> Int -> Word8 -> Map
setMapTile (Map arr) x y val
  | x >= 0 && x < mapWidth && y >= 0 && y < mapHeight = Map $ arr // [((x, y), val)]
  | otherwise = Map arr

findMapTile :: Map -> Word8 -> Maybe (Int, Int)
findMapTile (Map arr) target =
  let assocList = assocs arr
      matches = filter (\(_, val) -> val == target) assocList
  in case matches of
       ((pos, _):_) -> Just pos
       [] -> Nothing

updateMapPure :: Map -> (forall s. STUArray s (Int, Int) Word8 -> ST s ()) -> Map
updateMapPure (Map arr) action = Map $ runST $ do
  mutArr <- thaw arr
  action mutArr
  unsafeFreeze mutArr

unlockMap :: Map -> Int -> Int -> Map
unlockMap m startX startY =
  let startTile = getMapTile m startX startY
  in if startTile /= lockTile
       then m
       else updateMapPure m $ \mutArr -> do
         writeArray mutArr (startX, startY) spaceTile
         let loop [] = return ()
             loop ((cx, cy):rest) = do
               let neighbors = [ (cx + dx, cy + dy)
                               | dy <- [-1..1]
                               , dx <- [-1..1]
                               , dx /= 0 || dy /= 0
                               ]
               validNeighbors <- filterM (\(nx, ny) -> do
                 if nx >= 0 && nx < mapWidth && ny >= 0 && ny < mapHeight
                   then do
                     t <- readArray mutArr (nx, ny)
                     if t == lockTile
                       then do
                         writeArray mutArr (nx, ny) spaceTile
                         return True
                       else return False
                   else return False) neighbors
               loop (rest ++ validNeighbors)
         loop [(startX, startY)]

loadMap :: Map -> Int -> Map
loadMap m lvlIdx = updateMapPure m $ \mutArr -> do
  let clampedIdx = (lvlIdx `max` 0) `min` 25
      lvlData = levelMaps !! clampedIdx
      len = BS.length lvlData
  forM_ [0..len-1] $ \i -> do
    let b = BS.index lvlData i
        t1 = b .&. 15
        t2 = (b `shiftR` 4) .&. 15
        idx1 = i * 2
        idx2 = i * 2 + 1
        x1 = idx1 `mod` mapWidth
        y1 = idx1 `div` mapWidth
        x2 = idx2 `mod` mapWidth
        y2 = idx2 `div` mapWidth
    when (x1 >= 0 && x1 < mapWidth && y1 >= 0 && y1 < mapHeight) $
      writeArray mutArr (x1, y1) t1
    when (x2 >= 0 && x2 < mapWidth && y2 >= 0 && y2 < mapHeight) $
      writeArray mutArr (x2, y2) t2
levelMaps :: [BS.ByteString]
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
