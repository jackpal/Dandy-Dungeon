module Dandy.AI
  ( stepEnemies
  , isGhostBlocked
  , isGeneratorBlocked
  ) where

import Dandy.Consts
import Dandy.Types
import Dandy.Map
import Dandy.Rng
import Data.Word (Word8)
import Data.Int (Int32)
import Data.List (minimumBy)
import Data.Bits ((.&.), shiftR)

stepEnemies :: Map -> [Player] -> ActiveRect -> Word8 -> LcgRng -> ([Player], Map, Word8, LcgRng)
stepEnemies m players active curRotor curRng =
  let nextRotor = (curRotor + 1) .&. 3
      rx = fromIntegral (nextRotor .&. 1)
      ry = fromIntegral ((nextRotor `shiftR` 1) .&. 1)
      xStart = ((arLeft active + 1) `div` 2) * 2 + rx
      yStart = ((arTop active + 1) `div` 2) * 2 + ry
      xEnd = arLeft active + arWidth active
      yEnd = arTop active + arHeight active

      loopY y ps mAcc rng
        | y >= yEnd = (ps, mAcc, rng)
        | otherwise =
            let (nextPs, nextM, nextRng) = loopX y xStart ps mAcc rng
            in loopY (y + 2) nextPs nextM nextRng

      loopX y x ps mAcc rng
        | x >= xEnd = (ps, mAcc, rng)
        | otherwise =
            let v = getMapTile mAcc x y
            in if v >= ghostTile && v <= ghostTile + 2
                 then
                   let (nextPs, nextM) = stepGhost x y v mAcc ps
                   in loopX y (x + 2) nextPs nextM rng
                 else if v >= generatorTile && v <= generatorTile + 2
                   then
                     let (nextPsSpawning, nextM, nextRng) = stepGenerator x y v mAcc ps rng
                     in loopX y (x + 2) nextPsSpawning nextM nextRng
                   else
                     loopX y (x + 2) ps mAcc rng

      (finalPs, finalM, finalRng) = loopY yStart players m curRng
  in (finalPs, finalM, nextRotor, finalRng)

stepGhost :: Int -> Int -> Word8 -> Map -> [Player] -> ([Player], Map)
stepGhost gx gy ghostVal m players =
  let activeAlive = filter (\(_, p) -> pActive p && pAlive p && not (pEscaped p)) (zip [0..] players)
      dists = map (\(i, p) -> (i, abs (pX p - gx) + abs (pY p - gy), p)) activeAlive
  in if null dists
       then (players, m)
       else
         let (_, _, bestP) = minimumBy (\(_, d1, _) (_, d2, _) -> compare d1 d2) dists
             px = pX bestP
             py = pY bestP
             dx = px - gx
             dy = py - gy
             mDir = case (signum dx, signum dy) of
               (0, -1) -> 0
               (1, -1) -> 1
               (1, 0)  -> 2
               (1, 1)  -> 3
               (0, 1)  -> 4
               (-1, 1) -> 5
               (-1, 0) -> 6
               (-1, -1)-> 7
               _       -> 0

             tryMove [] = (players, m)
             tryMove (offset : rest) =
               let d = (mDir + offset) .&. 7
                   delta = getDirDelta d
                   nx = gx + fst delta
                   ny = gy + snd delta
                   nv = getMapTile m nx ny
               in case nv of
                    _ | nv == spaceTile ->
                          let m1 = setMapTile m gx gy spaceTile
                              m2 = setMapTile m1 nx ny ghostVal
                          in (players, m2)
                    _ | nv >= playerTile && nv <= playerTile + 3 ->
                          let pIndexVal = fromIntegral (nv - playerTile)
                              pain = 10 * (fromIntegral (ghostVal - ghostTile) + 1)
                              (nextPs, m1) = hurtPlayer pIndexVal pain m players
                              m2 = setMapTile m1 gx gy spaceTile
                          in (nextPs, m2)
                    _ | nv >= arrowTile && nv <= arrowTile + 7 -> (players, m)
                    _ -> tryMove rest
         in tryMove [0, 7, 1]

hurtPlayer :: Int -> Int32 -> Map -> [Player] -> ([Player], Map)
hurtPlayer idx pain m players =
  let p = players !! idx
  in if pHealth p > pain
       then
         let updatedP = p { pHealth = pHealth p - pain }
         in (updateAt idx updatedP players, m)
       else
         let remains = if pKeys p > 0 then keyTile else spaceTile
             keysNext = if pKeys p > 0 then pKeys p - 1 else 0
             m1 = setMapTile m (pX p) (pY p) remains
             updatedP = p { pHealth = 0, pAlive = False, pKeys = keysNext }
         in (updateAt idx updatedP players, m1)

stepGenerator :: Int -> Int -> Word8 -> Map -> [Player] -> LcgRng -> ([Player], Map, LcgRng)
stepGenerator gx gy genVal m players curRng =
  let (ran, rng1) = lcgNext curRng
  in if ran < 0.3
       then
         let (ranDir, rng2) = lcgNext rng1
             dir = (floor (ranDir * 4.0) :: Int) * 2
             delta = getDirDelta dir
             nx = gx + fst delta
             ny = gy + snd delta
             nv = getMapTile m nx ny
         in if nv == spaceTile
              then
                let newGhost = ghostTile + (genVal - generatorTile)
                    m1 = setMapTile m nx ny newGhost
                in (players, m1, rng2)
              else (players, m, rng2)
       else (players, m, rng1)

isGhostBlocked :: Int -> Int -> Map -> [Player] -> Bool
isGhostBlocked gx gy m players =
  let activeAlive = filter (\(_, p) -> pActive p && pAlive p && not (pEscaped p)) (zip [0..] players)
      dists = map (\(i, p) -> (i, abs (pX p - gx) + abs (pY p - gy), p)) activeAlive
  in if null dists
       then True
       else
         let (_, _, bestP) = minimumBy (\(_, d1, _) (_, d2, _) -> compare d1 d2) dists
             px = pX bestP
             py = pY bestP
             dx = px - gx
             dy = py - gy
             mDir = case (signum dx, signum dy) of
               (0, -1) -> 0
               (1, -1) -> 1
               (1, 0)  -> 2
               (1, 1)  -> 3
               (0, 1)  -> 4
               (-1, 1) -> 5
               (-1, 0) -> 6
               (-1, -1)-> 7
               _       -> 0

             checkSearch [] = True
             checkSearch (offset : rest) =
               let d = (mDir + offset) .&. 7
                   delta = getDirDelta d
                   nx = gx + fst delta
                   ny = gy + snd delta
                   nv = getMapTile m nx ny
               in case nv of
                    _ | nv == spaceTile -> False
                    _ | nv >= playerTile && nv <= playerTile + 3 -> False
                    _ | nv >= arrowTile && nv <= arrowTile + 7 -> True
                    _ -> checkSearch rest
         in checkSearch [0, 7, 1]

isGeneratorBlocked :: Int -> Int -> Map -> Bool
isGeneratorBlocked gx gy m =
  let check [] = True
      check (dir : rest) =
        let delta = getDirDelta dir
            nx = gx + fst delta
            ny = gy + snd delta
            nv = getMapTile m nx ny
        in if nv == spaceTile
             then False
             else check rest
  in check [0, 2, 4, 6]
