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
import Control.Monad (when, forM_)
import Data.Bits ((.&.))

stepEnemies :: Map -> [Player] -> ActiveRect -> Word8 -> LcgRng -> IO ([Player], Word8, LcgRng)
stepEnemies m players active curRotor curRng = do
  let nextRotor = (curRotor + 1) .&. 3
      rx = fromIntegral (nextRotor .&. 1)
      ry = fromIntegral ((nextRotor `shiftR` 1) .&. 1)
      xStart = ((arLeft active + 1) `div` 2) * 2 + rx
      yStart = ((arTop active + 1) `div` 2) * 2 + ry
      xEnd = arLeft active + arWidth active
      yEnd = arTop active + arHeight active

  let loopY y ps rng
        | y >= yEnd = return (ps, rng)
        | otherwise = do
            (nextPs, nextRng) <- loopX y xStart ps rng
            loopY (y + 2) nextPs nextRng

      loopX y x ps rng
        | x >= xEnd = return (ps, rng)
        | otherwise = do
            v <- getMapTile m x y
            if v >= ghostTile && v <= ghostTile + 2
              then do
                nextPs <- stepGhost x y v m ps
                loopX y (x + 2) nextPs rng
              else if v >= generatorTile && v <= generatorTile + 2
                then do
                  (nextPsSpawning, nextRng) <- stepGenerator x y v m ps rng
                  loopX y (x + 2) nextPsSpawning nextRng
                else
                  loopX y (x + 2) ps rng

  (finalPs, finalRng) <- loopY yStart players curRng
  return (finalPs, nextRotor, finalRng)

shiftR :: Word8 -> Int -> Word8
shiftR w n = w `div` (2 ^ n)

stepGhost :: Int -> Int -> Word8 -> Map -> [Player] -> IO [Player]
stepGhost gx gy ghostVal m players = do
  let activeAlive = filter (\(_, p) -> pActive p && pAlive p && not (pEscaped p)) (zip [0..] players)
      dists = map (\(i, p) -> (i, abs (pX p - gx) + abs (pY p - gy), p)) activeAlive

  if null dists
    then return players
    else do
      let (bestIdx, _, bestP) = minimumBy (\(_, d1, _) (_, d2, _) -> compare d1 d2) dists
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

      let tryMove [] = return players
          tryMove (offset : rest) = do
            let d = (mDir + offset) .&. 7
                delta = dirToDelta !! d
                nx = gx + fst delta
                ny = gy + snd delta
            nv <- getMapTile m nx ny
            case nv of
              _ | nv == spaceTile -> do
                    setMapTile m gx gy spaceTile
                    setMapTile m nx ny ghostVal
                    return players
              _ | nv >= playerTile && nv <= playerTile + 3 -> do
                    let pIndex = fromIntegral (nv - playerTile)
                        pain = 10 * (fromIntegral (ghostVal - ghostTile) + 1)
                    nextPs <- hurtPlayer pIndex pain m players
                    setMapTile m gx gy spaceTile
                    return nextPs
              _ | nv >= arrowTile && nv <= arrowTile + 7 -> return players
              _ -> tryMove rest

      tryMove [0, 7, 1]

hurtPlayer :: Int -> Int32 -> Map -> [Player] -> IO [Player]
hurtPlayer idx pain m players = do
  let p = players !! idx
  if pHealth p > pain
    then do
      let updatedP = p { pHealth = pHealth p - pain }
      return $ zipWith (\i op -> if i == idx then updatedP else op) [0..] players
    else do
      let remains = if pKeys p > 0 then keyTile else spaceTile
          keysNext = if pKeys p > 0 then pKeys p - 1 else 0
      setMapTile m (pX p) (pY p) remains
      let updatedP = p { pHealth = 0, pAlive = False, pKeys = keysNext }
      return $ zipWith (\i op -> if i == idx then updatedP else op) [0..] players

stepGenerator :: Int -> Int -> Word8 -> Map -> [Player] -> LcgRng -> IO ([Player], LcgRng)
stepGenerator gx gy genVal m players curRng = do
  let (ran, rng1) = lcgNext curRng
  if ran < 0.3
    then do
      let (ranDir, rng2) = lcgNext rng1
          dir = (floor (ranDir * 4.0) :: Int) * 2
          delta = dirToDelta !! dir
          nx = gx + fst delta
          ny = gy + snd delta
      nv <- getMapTile m nx ny
      if nv == spaceTile
        then do
          let newGhost = ghostTile + (genVal - generatorTile)
          setMapTile m nx ny newGhost
          return (players, rng2)
        else return (players, rng2)
    else return (players, rng1)

isGhostBlocked :: Int -> Int -> Map -> [Player] -> IO Bool
isGhostBlocked gx gy m players = do
  let activeAlive = filter (\(_, p) -> pActive p && pAlive p && not (pEscaped p)) (zip [0..] players)
      dists = map (\(i, p) -> (i, abs (pX p - gx) + abs (pY p - gy), p)) activeAlive

  if null dists
    then return True
    else do
      let (bestIdx, _, bestP) = minimumBy (\(_, d1, _) (_, d2, _) -> compare d1 d2) dists
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

      let checkSearch [] = return True
          checkSearch (offset : rest) = do
            let d = (mDir + offset) .&. 7
                delta = dirToDelta !! d
                nx = gx + fst delta
                ny = gy + snd delta
            nv <- getMapTile m nx ny
            case nv of
              _ | nv == spaceTile -> return False
              _ | nv >= playerTile && nv <= playerTile + 3 -> return False
              _ | nv >= arrowTile && nv <= arrowTile + 7 -> return True
              _ -> checkSearch rest

      checkSearch [0, 7, 1]

isGeneratorBlocked :: Int -> Int -> Map -> IO Bool
isGeneratorBlocked gx gy m = do
  let check [] = return True
      check (dir : rest) = do
        let delta = dirToDelta !! dir
            nx = gx + fst delta
            ny = gy + snd delta
        nv <- getMapTile m nx ny
        if nv == spaceTile
          then return False
          else check rest
  check [0, 2, 4, 6]
