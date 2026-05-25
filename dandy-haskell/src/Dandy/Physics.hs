{-# LANGUAGE ScopedTypeVariables #-}
{-# LANGUAGE FlexibleContexts #-}
module Dandy.Physics
  ( doSmartBomb
  , tryMovePlayer
  , stepPlayer
  , stepArrow
  ) where

import Dandy.Consts
import Dandy.Types
import Dandy.Map
import Data.Bits ((.&.))
import Control.Monad.ST (ST, runST)
import Data.Array.Unsafe (unsafeFreeze)
import Data.Array.ST (STUArray)
import Data.Array.MArray (readArray, writeArray, thaw)
import Data.Word (Word8)

doSmartBomb :: Player -> Map -> ActiveRect -> (Player, Map)
doSmartBomb p m active =
  let left = arLeft active
      top = arTop active
      width = arWidth active
      height = arHeight active
      xRange = [left .. left + width - 1]
      yRange = [top .. top + height - 1]
      coords = [(x, y) | y <- yRange, x <- xRange]

      (scoreGain, newMap) = runST (do
        let Map arr = m
        (mutArr :: STUArray s (Int, Int) Word8) <- thaw arr
        let loop [] acc = return acc
            loop ((x, y):cs) acc = do
              if x >= 0 && x < mapWidth && y >= 0 && y < mapHeight
                then do
                  v <- readArray mutArr (x, y)
                  if v >= ghostTile && v <= ghostTile + 2
                    then do
                      writeArray mutArr (x, y) spaceTile
                      let gain = 10 * (fromIntegral (v - ghostTile) + 1)
                      loop cs (acc + gain)
                    else loop cs acc
                else loop cs acc
        score <- loop coords 0
        frozenArr <- unsafeFreeze mutArr
        return (score, Map frozenArr) :: ST s (Int, Map))
  in (p { pScore = pScore p + fromIntegral scoreGain }, newMap)

tryMovePlayer :: Int -> Player -> Map -> Int -> (Bool, Player, Map)
tryMovePlayer idx p m dir =
  let pWithDir = p { pDir = dir }
      delta = getDirDelta dir
      nx = pX p + fst delta
      ny = pY p + snd delta
      v = getMapTile m nx ny

      (moved, escaped, nextP, m1) = case v of
        _ | v == spaceTile -> (True, False, pWithDir, m)
        _ | v == lockTile ->
          if pKeys p > 0
            then
              let mUnlocked = unlockMap m nx ny
              in (True, False, pWithDir { pKeys = pKeys p - 1 }, mUnlocked)
            else (False, False, pWithDir, m)
        _ | v == downStairsTile ->
              let mCleared = setMapTile m (pX p) (pY p) spaceTile
              in (True, True, pWithDir { pEscaped = True, pX = -1, pY = -1 }, mCleared)
        _ | v == keyTile ->
              (True, False, pWithDir { pKeys = pKeys p + 1 }, m)
        _ | v == foodTile ->
              (True, False, pWithDir { pHealth = pHealth p + 100 }, m)
        _ | v == moneyTile ->
              (True, False, pWithDir { pScore = pScore p + 100 }, m)
        _ | v == bombTile ->
              (True, False, pWithDir { pBombs = pBombs p + 1 }, m)
        _ -> (False, False, pWithDir, m)
  in if moved && not escaped
       then
         let m2 = setMapTile m1 (pX p) (pY p) spaceTile
             m3 = setMapTile m2 nx ny (playerTile + fromIntegral idx)
         in (True, nextP { pX = nx, pY = ny }, m3)
       else (moved || escaped, nextP, m1)

stepPlayer :: Int -> Player -> Map -> ActiveRect -> (Player, Map)
stepPlayer idx p m activeRect =
  let input = pInput p
      startX = pX p
      startY = pY p

      (pAfterBomb, mAfterBomb) =
        if (input .&. actionBomb) /= 0 && pBombs p > 0
          then doSmartBomb (p { pBombs = pBombs p - 1 }) m activeRect
          else (p, m)

      dx = (if (input .&. actionLeft) /= 0 then -1 else 0) +
           (if (input .&. actionRight) /= 0 then 1 else 0)
      dy = (if (input .&. actionUp) /= 0 then -1 else 0) +
           (if (input .&. actionDown) /= 0 then 1 else 0)

      dirOpt = case (dx, dy) of
        (0, -1) -> Just 0
        (1, -1) -> Just 1
        (1, 0)  -> Just 2
        (1, 1)  -> Just 3
        (0, 1)  -> Just 4
        (-1, 1) -> Just 5
        (-1, 0) -> Just 6
        (-1, -1)-> Just 7
        _       -> Nothing

      pAfterDir = case dirOpt of
        Just d  -> pAfterBomb { pDir = d }
        Nothing -> pAfterBomb
  in if (input .&. actionShoot) /= 0
       then
         if pArrow pAfterDir == Nothing
           then
             let shootDir = case dirOpt of
                   Just d  -> d
                   Nothing -> pDir pAfterDir
             in (pAfterDir { pArrow = Just (Arrow startX startY shootDir) }, mAfterBomb)
           else (pAfterDir, mAfterBomb)
       else case dirOpt of
         Just d ->
           let (moved, pMoved, mMoved) = tryMovePlayer idx pAfterDir mAfterBomb d
           in if not moved
                then
                  let (movedLeft, pMovedLeft, mMovedLeft) = tryMovePlayer idx pAfterDir mAfterBomb ((d + 1) .&. 7)
                  in if not movedLeft
                       then
                         let (_, pMovedRight, mMovedRight) = tryMovePlayer idx pAfterDir mAfterBomb ((d + 7) .&. 7)
                         in (pMovedRight, mMovedRight)
                       else (pMovedLeft, mMovedLeft)
                else (pMoved, mMoved)
         Nothing -> (pAfterDir, mAfterBomb)

stepArrow :: Int -> [Player] -> Map -> ActiveRect -> ([Player], Map)
stepArrow idx players m activeRect =
  let p = players !! idx
  in case pArrow p of
       Nothing -> (players, m)
       Just a ->
         let delta = getDirDelta (aDir a)
             nx = aX a + fst delta
             ny = aY a + snd delta
             arrowVal = arrowTile + fromIntegral ((aDir a + 3) .&. 7)

             currentTile = getMapTile m (aX a) (aY a)
             m1 = if currentTile == arrowVal
                    then setMapTile m (aX a) (aY a) spaceTile
                    else m

             newTile = getMapTile m1 nx ny

             findDead [] _ = (True, ghostTile + 2, 0, Nothing)
             findDead (otherP : rest) oIdx =
               if pActive otherP && not (pAlive otherP)
                 then (True, playerTile + fromIntegral oIdx, 0, Just oIdx)
                 else findDead rest (oIdx + 1)

             (killArrow, newV, pScoreGain, resurrectedIdx) = case newTile of
               _ | newTile == spaceTile -> (False, arrowVal, 0, Nothing)
               _ | newTile >= ghostTile && newTile <= ghostTile + 2 ->
                     let nextV = if newTile > ghostTile then newTile - 1 else spaceTile
                     in (True, nextV, 10, Nothing)
               _ | newTile == heartTile -> findDead players 0
               _ | newTile == bombTile -> (True, spaceTile, 0, Nothing)
               _ -> (True, newTile, 0, Nothing)

             m2 = setMapTile m1 nx ny newV

             updatePlayers pIdx otherP
               | Just pIdx == resurrectedIdx =
                   let resurrectedP = otherP { pAlive = True, pX = nx, pY = ny, pHealth = 50 }
                       finalP = if pIdx == idx
                                  then resurrectedP { pScore = pScore resurrectedP + pScoreGain, pArrow = Nothing }
                                  else resurrectedP
                   in finalP
               | pIdx == idx =
                   let pWithScore = otherP { pScore = pScore otherP + pScoreGain }
                       pWithArrow = if killArrow then pWithScore { pArrow = Nothing }
                                                 else pWithScore { pArrow = Just (Arrow nx ny (aDir a)) }
                   in pWithArrow
               | otherwise = otherP

             nextPlayers = zipWith updatePlayers [0..] players
         in if newTile == bombTile
              then
                let firingP = nextPlayers !! idx
                    (updatedFiringP, m3) = doSmartBomb firingP m2 activeRect
                in (updateAt idx updatedFiringP nextPlayers, m3)
              else (nextPlayers, m2)
