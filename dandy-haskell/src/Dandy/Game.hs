{-# LANGUAGE FlexibleContexts #-}
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
import Control.Monad.ST (runST)
import Data.Array.MArray (writeArray)

newGame :: GameState
newGame =
  let m = emptyMap
      p1 = (newPlayer 0) { pActive = True, pAlive = True }
      ps = p1 : map newPlayer [1..3]
  in GameState
    { gMap = m
    , gPlayers = ps
    , gLevel = 0
    , gTime = 0
    , gLastMoveTime = 0
    , gRotor = 0
    , gCamera = Camera 0.0 0.0
    , gRng = newLcgRng 12345
    }

loadGame :: GameState -> GameState
loadGame gs =
  let m0 = gMap gs
      lvl = gLevel gs
      m1 = loadMap m0 lvl
      spawn = case findMapTile m1 upStairsTile of
        Just (x, y) -> (x, y)
        Nothing     -> (2, 2)

      m2 = updateMapPure m1 $ \mutArr -> do
        let startPs [] = return ()
            startPs ((idx, p):rest) = do
              if pActive p && idx < length playerSpawnDirs
                then do
                  let dir = playerSpawnDirs !! idx
                      delta = getDirDelta dir
                      px = fst spawn + fst delta
                      py = snd spawn + snd delta
                  writeArray mutArr (px, py) (playerTile + fromIntegral idx)
                  startPs rest
                else startPs rest
        startPs (zip [0..] (gPlayers gs))

      updatePlayerRecord (idx, p) =
        if pActive p && idx < length playerSpawnDirs
          then
            let dir = playerSpawnDirs !! idx
                delta = getDirDelta dir
                px = fst spawn + fst delta
                py = snd spawn + snd delta
            in startPlayer p px py dir
          else p

      nextPs = map updatePlayerRecord (zip [0..] (gPlayers gs))
      (targetX, targetY) = calculateTargetCog nextPs
      nextCam = Camera (fromIntegral targetX) (fromIntegral targetY)
  in gs
    { gMap = m2
    , gPlayers = nextPs
    , gRotor = 0
    , gCamera = nextCam
    }

stepGame :: GameState -> GameState
stepGame gs =
  let m = gMap gs
      ps = gPlayers gs
      t = gTime gs + 1
      lastT = gLastMoveTime gs
      rng1 = gRng gs
      rotor1 = gRotor gs

      joinPlayers [] currentPs currentM = (currentPs, currentM)
      joinPlayers (idx : rest) currentPs currentM =
        let p = currentPs !! idx
        in if not (pActive p) && pInput p /= 0
             then
               let spawn = case findMapTile currentM upStairsTile of
                     Just (x, y) -> (x, y)
                     Nothing     -> (2, 2)
                   dir = playerSpawnDirs !! idx
                   delta = getDirDelta dir
                   px = fst spawn + fst delta
                   py = snd spawn + snd delta
                   m' = setMapTile currentM px py (playerTile + fromIntegral idx)
                   startedP = startPlayer p px py dir
                   nextPs = updateAt idx startedP currentPs
               in joinPlayers rest nextPs m'
             else joinPlayers rest currentPs currentM

      (nextPs1, m1) = joinPlayers [1..3] ps m

  in if t - lastT >= 4
       then
         let activeRect = getActiveRect (gCamera gs)

             foldPlayers idx currentPs currentM
               | idx >= length currentPs = (currentPs, currentM)
               | otherwise =
                   let p = currentPs !! idx
                   in if pActive p && pAlive p && not (pEscaped p)
                        then
                          let (nextP, nextM) = stepPlayer idx p currentM activeRect
                              nextPs = updateAt idx nextP currentPs
                          in foldPlayers (idx + 1) nextPs nextM
                        else
                          foldPlayers (idx + 1) currentPs currentM

             (nextPs2, m2) = foldPlayers 0 nextPs1 m1

             foldArrows pList idx currentM
               | idx >= length pList = (pList, currentM)
               | otherwise =
                   let (pListNext, nextM) = if pActive (pList !! idx)
                                              then stepArrow idx pList currentM activeRect
                                              else (pList, currentM)
                   in foldArrows pListNext (idx + 1) nextM

             (nextPs3, m3) = foldArrows nextPs2 0 m2

             (nextPs4, m4, nextRotor, nextRng) = stepEnemies m3 nextPs3 activeRect rotor1 rng1

             anyJoined = any pActive nextPs4
             playersInDungeon = any (\p -> pActive p && pAlive p && not (pEscaped p)) nextPs4
             arrowsInFlight = any (\p -> pActive p && (case pArrow p of Just _ -> True; Nothing -> False)) nextPs4
             anyEscaped = any pEscaped nextPs4

         in if anyJoined && not playersInDungeon && not arrowsInFlight
              then
                if anyEscaped
                  then
                    let nextLevel = (gLevel gs + 1) `min` 25
                    in loadGame gs { gMap = m4, gLevel = nextLevel, gPlayers = nextPs4, gTime = t, gLastMoveTime = t }
                  else
                    loadGame gs { gMap = m4, gPlayers = nextPs4, gTime = t, gLastMoveTime = t }
              else
                gs
                  { gMap = m4
                  , gPlayers = nextPs4
                  , gTime = t
                  , gLastMoveTime = t
                  , gRotor = nextRotor
                  , gRng = nextRng
                  }
       else
         gs { gMap = m1, gPlayers = nextPs1, gTime = t }

canSleepGame :: GameState -> Bool
canSleepGame gs =
  let ps = gPlayers gs
      m = gMap gs
      cam = gCamera gs
      hasInput = any (\p -> pInput p /= 0) ps
  in if hasInput
       then False
       else
         let hasArrow = any (\p -> pActive p && (case pArrow p of Just _ -> True; Nothing -> False)) ps
         in if hasArrow
              then False
              else
                let (targetX, targetY) = calculateTargetCog ps
                    dx = fromIntegral targetX - camCogX cam
                    dy = fromIntegral targetY - camCogY cam
                in if abs dx >= 0.1 || abs dy >= 0.1
                     then False
                     else
                       let active = getActiveRect cam
                           left = arLeft active
                           top = arTop active
                           width = arWidth active
                           height = arHeight active
                           xRange = [left .. left + width - 1]
                           yRange = [top .. top + height - 1]
                           cells = [ (x, y) | y <- yRange, x <- xRange ]

                           checkCells [] = True
                           checkCells ((x, y) : rest) =
                             let v = getMapTile m x y
                             in if v >= ghostTile && v <= ghostTile + 2
                                  then
                                    let blocked = isGhostBlocked x y m ps
                                    in if not blocked
                                         then False
                                         else checkCells rest
                                  else if v >= generatorTile && v <= generatorTile + 2
                                    then
                                      let blocked = isGeneratorBlocked x y m
                                      in if not blocked
                                           then False
                                           else checkCells rest
                                    else
                                      checkCells rest
                       in checkCells cells
