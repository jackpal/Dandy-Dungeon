module Dandy.Game
  ( newGame
  , loadGame
  , stepGame
  , canSleepGame
  ) where

import Dandy.Consts
import Dandy.Types
import Dandy.Map
import Dandy.Camera
import Dandy.Entity
import Dandy.Physics
import Dandy.AI
import Dandy.Rng
import Data.Word (Word8, Word32)
import Control.Monad (when, forM_)
import Data.Bits ((.&.))

newGame :: IO GameState
newGame = do
  m <- newMap
  let p1 = (newPlayer 0) { pActive = True, pAlive = True }
      ps = p1 : map newPlayer [1..3]
  return GameState
    { gMap = m
    , gPlayers = ps
    , gLevel = 0
    , gTime = 0
    , gLastMoveTime = 0
    , gRotor = 0
    , gCamera = Camera 0.0 0.0
    , gRng = newLcgRng 12345
    }

loadGame :: GameState -> IO GameState
loadGame gs = do
  let m = gMap gs
      lvl = gLevel gs
  loadMap m lvl

  spawnOpt <- findMapTile m upStairsTile
  let spawn = case spawnOpt of
        Just (x, y) -> (x, y)
        Nothing     -> (2, 2)

  let startPs idx p
        | pActive p && idx < length playerSpawnDirs = do
            let dir = playerSpawnDirs !! idx
                delta = getDirDelta dir
                px = fst spawn + fst delta
                py = snd spawn + snd delta
            setMapTile m px py (playerTile + fromIntegral idx)
            return $ startPlayer p px py dir
        | otherwise = return p

  nextPs <- mapM (\(idx, p) -> startPs idx p) (zip [0..] (gPlayers gs))

  let (targetX, targetY) = calculateTargetCog nextPs
      nextCam = Camera (fromIntegral targetX) (fromIntegral targetY)

  return gs
    { gPlayers = nextPs
    , gRotor = 0
    , gCamera = nextCam
    }

stepGame :: GameState -> IO GameState
stepGame gs = do
  let m = gMap gs
      ps = gPlayers gs
      t = gTime gs + 1
      lastT = gLastMoveTime gs
      rng1 = gRng gs
      rotor1 = gRotor gs

  let joinPlayers [] currentPs = return currentPs
      joinPlayers (idx : rest) currentPs = do
        let p = currentPs !! idx
        if not (pActive p) && pInput p /= 0
          then do
            spawnOpt <- findMapTile m upStairsTile
            let spawn = case spawnOpt of
                  Just (x, y) -> (x, y)
                  Nothing     -> (2, 2)
                dir = playerSpawnDirs !! idx
                delta = getDirDelta dir
                px = fst spawn + fst delta
                py = snd spawn + snd delta
            setMapTile m px py (playerTile + fromIntegral idx)
            let startedP = startPlayer p px py dir
                nextPs = updateAt idx startedP currentPs
            joinPlayers rest nextPs
          else joinPlayers rest currentPs

  nextPs1 <- joinPlayers [1..3] ps

  if t - lastT >= 4
    then do
      let activeRect = getActiveRect (gCamera gs)

      nextPs2 <- mapM (\(idx, p) ->
        if pActive p && pAlive p && not (pEscaped p)
          then stepPlayer idx p m activeRect
          else return p) (zip [0..] nextPs1)

      let foldArrows pList idx
            | idx >= length pList = return pList
            | otherwise = do
                pListNext <- if pActive (pList !! idx)
                               then stepArrow idx pList m activeRect
                               else return pList
                foldArrows pListNext (idx + 1)

      nextPs3 <- foldArrows nextPs2 0

      (nextPs4, nextRotor, nextRng) <- stepEnemies m nextPs3 activeRect rotor1 rng1

      let anyJoined = any pActive nextPs4
          playersInDungeon = any (\p -> pActive p && pAlive p && not (pEscaped p)) nextPs4
          arrowsInFlight = any (\p -> pActive p && (case pArrow p of Just _ -> True; Nothing -> False)) nextPs4
          anyEscaped = any pEscaped nextPs4

      if anyJoined && not playersInDungeon && not arrowsInFlight
        then do
          if anyEscaped
            then do
               let nextLevel = (gLevel gs + 1) `min` 25
               loadGame gs { gLevel = nextLevel, gPlayers = nextPs4, gTime = t, gLastMoveTime = t }
            else do
               loadGame gs { gPlayers = nextPs4, gTime = t, gLastMoveTime = t }
        else
          return gs
            { gPlayers = nextPs4
            , gTime = t
            , gLastMoveTime = t
            , gRotor = nextRotor
            , gRng = nextRng
            }
    else
      return gs { gPlayers = nextPs1, gTime = t }

canSleepGame :: GameState -> IO Bool
canSleepGame gs = do
  let ps = gPlayers gs
      m = gMap gs
      cam = gCamera gs

  let hasInput = any (\p -> pInput p /= 0) ps
  if hasInput
    then return False
    else do
      let hasArrow = any (\p -> pActive p && (case pArrow p of Just _ -> True; Nothing -> False)) ps
      if hasArrow
        then return False
        else do
          let (targetX, targetY) = calculateTargetCog ps
              dx = fromIntegral targetX - camCogX cam
              dy = fromIntegral targetY - camCogY cam
          if abs dx >= 0.1 || abs dy >= 0.1
            then return False
            else do
              let active = getActiveRect cam
                  left = arLeft active
                  top = arTop active
                  width = arWidth active
                  height = arHeight active
                  xRange = [left .. left + width - 1]
                  yRange = [top .. top + height - 1]

              let checkCells [] = return True
                  checkCells ((x, y) : rest) = do
                    v <- getMapTile m x y
                    if v >= ghostTile && v <= ghostTile + 2
                      then do
                        blocked <- isGhostBlocked x y m ps
                        if not blocked
                          then return False
                          else checkCells rest
                      else if v >= generatorTile && v <= generatorTile + 2
                        then do
                          blocked <- isGeneratorBlocked x y m
                          if not blocked
                            then return False
                            else checkCells rest
                        else
                          checkCells rest

              let cells = [ (x, y) | y <- yRange, x <- xRange ]
              checkCells cells
