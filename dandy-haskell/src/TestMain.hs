module Main where

import Dandy.Consts
import Dandy.Types
import Dandy.Game
import Dandy.Map
import Dandy.Camera
import Dandy.Entity
import Data.Bits ((.|.))
import Control.Monad (when, forM_)
import System.Exit (exitFailure, exitSuccess)
import Data.Array.Unboxed (assocs)

assertEq :: (Show a, Eq a) => String -> a -> a -> IO ()
assertEq name expected actual =
  if expected == actual
    then putStrLn $ "PASS: " ++ name
    else do
      putStrLn $ "FAIL: " ++ name ++ " - Expected: " ++ show expected ++ ", Got: " ++ show actual
      exitFailure

testGameInit :: IO ()
testGameInit = do
  let gs = newGame
      ps = gPlayers gs
  assertEq "Players count is 4" 4 (length ps)
  assertEq "P1 active" True (pActive (ps !! 0))
  assertEq "P1 alive" True (pAlive (ps !! 0))
  assertEq "P2 inactive" False (pActive (ps !! 1))
  assertEq "P3 inactive" False (pActive (ps !! 2))
  assertEq "P4 inactive" False (pActive (ps !! 3))

testPlayerSpawning :: IO ()
testPlayerSpawning = do
  let initialGs = newGame
      ps = map (\p -> p { pActive = True }) (gPlayers initialGs)
      gs = loadGame initialGs { gPlayers = ps }
      finalPs = gPlayers gs
      spawnOpt = findMapTile (gMap gs) upStairsTile
  case spawnOpt of
    Nothing -> putStrLn "FAIL: Spawning - UP stairs not found" >> exitFailure
    Just (sx, sy) -> do
      assertEq "P1 spawn X" sx (pX (finalPs !! 0))
      assertEq "P1 spawn Y" (sy - 1) (pY (finalPs !! 0))
      assertEq "P1 spawn Dir" 0 (pDir (finalPs !! 0))

      assertEq "P2 spawn X" (sx + 1) (pX (finalPs !! 1))
      assertEq "P2 spawn Y" sy (pY (finalPs !! 1))
      assertEq "P2 spawn Dir" 2 (pDir (finalPs !! 1))

      assertEq "P3 spawn X" sx (pX (finalPs !! 2))
      assertEq "P3 spawn Y" (sy + 1) (pY (finalPs !! 2))
      assertEq "P3 spawn Dir" 4 (pDir (finalPs !! 2))

      assertEq "P4 spawn X" (sx - 1) (pX (finalPs !! 3))
      assertEq "P4 spawn Y" sy (pY (finalPs !! 3))
      assertEq "P4 spawn Dir" 6 (pDir (finalPs !! 3))

testHotJoin :: IO ()
testHotJoin = do
  let initialGs = newGame
      gsLoaded = loadGame initialGs
      ps1 = gPlayers gsLoaded
      p2Input = actionUp
      ps2 = zipWith (\idx p -> if idx == 1 then p { pInput = p2Input } else p) [0..] ps1
      gsInput = gsLoaded { gPlayers = ps2 }
      gsStepped = stepGame gsInput
      finalPs = gPlayers gsStepped
  assertEq "P2 joined/active" True (pActive (finalPs !! 1))
  assertEq "P2 alive" True (pAlive (finalPs !! 1))
  let spawnOpt = findMapTile (gMap gsStepped) upStairsTile
  case spawnOpt of
    Nothing -> putStrLn "FAIL: P2 Spawning - UP stairs not found" >> exitFailure
    Just (sx, sy) -> do
      assertEq "P2 spawn X East" (sx + 1) (pX (finalPs !! 1))
      assertEq "P2 spawn Y East" sy (pY (finalPs !! 1))

testSelfResurrection :: IO ()
testSelfResurrection = do
  let initialGs = newGame
      gsLoaded = loadGame initialGs
      m0 = emptyMap
      p1 = (gPlayers gsLoaded !! 0) { pX = 5, pY = 5, pDir = 2, pHealth = 100, pAlive = True, pActive = True }
      nextPs1 = p1 : drop 1 (gPlayers gsLoaded)
      m1 = setMapTile m0 5 5 playerTile
      m2 = setMapTile m1 7 5 heartTile

      p1Shoot = p1 { pInput = actionShoot }
      nextPs2 = p1Shoot : drop 1 nextPs1
      gsShoot = gsLoaded { gPlayers = nextPs2, gMap = m2 }

      gsT1 = stepGame gsShoot
      gsT2 = stepGame gsT1
      gsT3 = stepGame gsT2
      gsT4 = stepGame gsT3

  let psAfterShoot = gPlayers gsT4
      p1AfterShoot = psAfterShoot !! 0

  assertEq "P1 arrow fired" True (case pArrow p1AfterShoot of Just _ -> True; Nothing -> False)
  let Just arrow = pArrow p1AfterShoot
  assertEq "Arrow X" 6 (aX arrow)
  assertEq "Arrow Y" 5 (aY arrow)

  let p1Dead = p1AfterShoot { pInput = 0, pHealth = 0, pAlive = False }
      nextPs3 = p1Dead : drop 1 psAfterShoot
      m3 = setMapTile (gMap gsT4) 5 5 spaceTile
      gsDead = gsT4 { gPlayers = nextPs3, gMap = m3 }

      gsD1 = stepGame gsDead
      gsD2 = stepGame gsD1
      gsD3 = stepGame gsD2
      gsD4 = stepGame gsD3

      finalPs = gPlayers gsD4
      finalP1 = finalPs !! 0

  assertEq "P1 resurrected!" True (pAlive finalP1)
  assertEq "P1 health is 50" 50 (pHealth finalP1)
  assertEq "P1 X is HEART X" 7 (pX finalP1)
  assertEq "P1 Y is HEART Y" 5 (pY finalP1)
  assertEq "P1 arrow destroyed" Nothing (pArrow finalP1)

  let tileVal = getMapTile (gMap gsD4) 7 5
  assertEq "Map tile at HEART is P1" playerTile tileVal

  let oldTileVal = getMapTile (gMap gsD4) 5 5
  assertEq "Map tile at old position is empty" spaceTile oldTileVal

testDiagonalSliding :: IO ()
testDiagonalSliding = do
  let initialGs = newGame
      gsLoaded = loadGame initialGs
      m0 = emptyMap
      p1 = (gPlayers gsLoaded !! 0) { pX = 5, pY = 5, pDir = 2, pHealth = 100, pAlive = True, pActive = True }
      nextPs1 = p1 : drop 1 (gPlayers gsLoaded)
      m1 = setMapTile m0 5 5 playerTile
      m2 = setMapTile m1 5 4 wallTile
      m3 = setMapTile m2 6 4 wallTile

      p1Move = p1 { pInput = actionUp .|. actionRight }
      nextPs2 = p1Move : drop 1 nextPs1
      gsMove = gsLoaded { gPlayers = nextPs2, gMap = m3 }

      gs1 = stepGame gsMove
      gs2 = stepGame gs1
      gs3 = stepGame gs2
      gs4 = stepGame gs3

      finalPs = gPlayers gs4
      finalP1 = finalPs !! 0

  assertEq "Diagonal sliding X" 6 (pX finalP1)
  assertEq "Diagonal sliding Y" 5 (pY finalP1)

  let tileVal = getMapTile (gMap gs4) 6 5
  assertEq "Map tile at slid position is P1" playerTile tileVal

  let oldTileVal = getMapTile (gMap gs4) 5 5
  assertEq "Map tile at old position is empty" spaceTile oldTileVal

testSleepMode :: IO ()
testSleepMode = do
  let initialGs = newGame
      gsLoaded = loadGame initialGs
      p1 = (gPlayers gsLoaded !! 0) { pX = 3, pY = 5, pAlive = True, pActive = True }
      ps = p1 : drop 1 (gPlayers gsLoaded)
      m0 = setMapTile emptyMap 3 5 playerTile
      gsClean = gsLoaded { gPlayers = ps, gMap = m0, gCamera = Camera 56.0 88.0 }

  -- Basic sleep should succeed
  assertEq "can sleep basic" True (canSleepGame gsClean)

  -- Should NOT sleep with player input
  let gsWithInput = gsClean { gPlayers = (p1 { pInput = actionUp }) : drop 1 ps }
  assertEq "cannot sleep with player input" False (canSleepGame gsWithInput)

  -- Should NOT sleep with arrow in flight
  let gsWithArrow = gsClean { gPlayers = (p1 { pArrow = Just (Arrow 5 5 0) }) : drop 1 ps }
  assertEq "cannot sleep with arrow in flight" False (canSleepGame gsWithArrow)

  -- Ghost tests
  let mWithGhost = setMapTile m0 5 5 ghostTile
      gsWithGhost = gsClean { gMap = mWithGhost }
  assertEq "cannot sleep with unblocked ghost" False (canSleepGame gsWithGhost)

  -- Block the ghost
  let mGhostBlocked = setMapTile (setMapTile (setMapTile mWithGhost 4 5 wallTile) 4 4 wallTile) 4 6 wallTile
      gsGhostBlocked = gsClean { gMap = mGhostBlocked }
  assertEq "can sleep when ghost is blocked" True (canSleepGame gsGhostBlocked)

  -- Generator tests
  let mWithGen = setMapTile m0 5 5 generatorTile
      gsWithGen = gsClean { gMap = mWithGen }
  assertEq "cannot sleep with unblocked generator" False (canSleepGame gsWithGen)

  -- Block the generator
  let mGenBlocked = setMapTile (setMapTile (setMapTile (setMapTile mWithGen 5 4 wallTile) 6 5 wallTile) 5 6 wallTile) 4 5 wallTile
      gsGenBlocked = gsClean { gMap = mGenBlocked }
  assertEq "can sleep when generator is blocked" True (canSleepGame gsGenBlocked)

  -- Camera movement tests
  assertEq "can sleep with settled camera" True (canSleepGame gsClean)

  let gsMovingCam = gsClean { gCamera = Camera 0.0 0.0 }
  assertEq "cannot sleep with moving camera" False (canSleepGame gsMovingCam)

testCooperativeLevelFlow :: IO ()
testCooperativeLevelFlow = do
  -- 1. P1 Escape Progression
  let gs0 = newGame
      gsLoaded = loadGame gs0
      mLoaded = gMap gsLoaded

  let Just (dx, dy) = findMapTile mLoaded downStairsTile
      Just (p1x, p1y) = findMapTile mLoaded playerTile
      m1 = setMapTile (setMapTile mLoaded p1x p1y spaceTile) dx (dy - 1) playerTile

      p1Near = (gPlayers gsLoaded !! 0) { pX = dx, pY = dy - 1, pDir = 4, pInput = actionDown }
      gsReady = gsLoaded { gPlayers = p1Near : drop 1 (gPlayers gsLoaded), gMap = m1 }

      gs1 = stepGame gsReady -- t=1
      gs2 = stepGame gs1     -- t=2
      gs3 = stepGame gs2     -- t=3
      gs4 = stepGame gs3     -- t=4 (Physics tick)

  assertEq "P1 escaped: Level is 1" 1 (gLevel gs4)
  let p1After = gPlayers gs4 !! 0
  assertEq "P1 is active on Level 1" True (pActive p1After)
  assertEq "P1 is alive on Level 1" True (pAlive p1After)
  assertEq "P1 is not escaped on Level 1" False (pEscaped p1After)

  let mLevel1 = gMap gs4
      Just (u1x, u1y) = findMapTile mLevel1 upStairsTile
  assertEq "P1 X near UP stairs" u1x (pX p1After)
  assertEq "P1 Y near UP stairs" (u1y - 1) (pY p1After)

  -- 2. P2 Hot-Join Keeping Level
  let p2Join = (gPlayers gs4 !! 1) { pInput = actionUp }
      gs5 = gs4 { gPlayers = updateAt 1 p2Join (gPlayers gs4) }
      gs6 = stepGame gs5 -- t=5. P2 joins
      p2After = gPlayers gs6 !! 1

  assertEq "P2 joined: Level is still 1" 1 (gLevel gs6)
  assertEq "P2 is active" True (pActive p2After)
  assertEq "P2 is alive" True (pAlive p2After)
  assertEq "P2 X near UP stairs" (u1x + 1) (pX p2After)
  assertEq "P2 Y near UP stairs" u1y (pY p2After)

  -- 3. P1 Escape + P2 Death Progression
  let mLevel1_active = gMap gs6
      Just (d1x, d1y) = findMapTile mLevel1_active downStairsTile
      Just (p1x_old, p1y_old) = findMapTile mLevel1_active playerTile
      Just (p2x_old, p2y_old) = findMapTile mLevel1_active (playerTile + 1)
      mClear = setMapTile (setMapTile mLevel1_active p1x_old p1y_old spaceTile) p2x_old p2y_old spaceTile
      mP1Near = setMapTile mClear d1x (d1y - 1) playerTile

      p1Near1 = (gPlayers gs6 !! 0) { pX = d1x, pY = d1y - 1, pDir = 4, pInput = actionDown }
      p2Dead = (gPlayers gs6 !! 1) { pAlive = False, pHealth = 0, pX = -1, pY = -1 }
      gsP1EscapeP2Dead = gs6 { gPlayers = [p1Near1, p2Dead, gPlayers gs6 !! 2, gPlayers gs6 !! 3]
                             , gMap = mP1Near
                             , gLastMoveTime = gTime gs6
                             }

      gsE1 = stepGame gsP1EscapeP2Dead -- t=6
      gsE2 = stepGame gsE1             -- t=7
      gsE3 = stepGame gsE2             -- t=8
      gsE4 = stepGame gsE3             -- t=9 (Physics tick)

  assertEq "P1 escaped + P2 dead: Level is 2" 2 (gLevel gsE4)
  let p1Level2 = gPlayers gsE4 !! 0
      p2Level2 = gPlayers gsE4 !! 1

  assertEq "P1 active on L2" True (pActive p1Level2)
  assertEq "P1 alive on L2" True (pAlive p1Level2)
  assertEq "P2 active on L2" True (pActive p2Level2)
  assertEq "P2 resurrected on L2" True (pAlive p2Level2)
  assertEq "P2 health is 100" 100 (pHealth p2Level2)

  -- 4. Level Restart on Death
  let mLevel2 = gMap gsE4
      Just (p1x_l2, p1y_l2) = findMapTile mLevel2 playerTile
      Just (p2x_l2, p2y_l2) = findMapTile mLevel2 (playerTile + 1)
      mClearL2 = setMapTile (setMapTile mLevel2 p1x_l2 p1y_l2 spaceTile) p2x_l2 p2y_l2 spaceTile

      p1Dead = (gPlayers gsE4 !! 0) { pAlive = False, pHealth = 0 }
      p2Dead2 = (gPlayers gsE4 !! 1) { pAlive = False, pHealth = 0 }
      gsAllDead = gsE4 { gPlayers = [p1Dead, p2Dead2, gPlayers gsE4 !! 2, gPlayers gsE4 !! 3]
                       , gMap = mClearL2
                       , gLastMoveTime = gTime gsE4
                       }

      gsD1 = stepGame gsAllDead -- t=10
      gsD2 = stepGame gsD1             -- t=11
      gsD3 = stepGame gsD2             -- t=12
      gsD4 = stepGame gsD3             -- t=13 (Physics tick)

  assertEq "All dead: Level is still 2" 2 (gLevel gsD4)
  let p1Respawn = gPlayers gsD4 !! 0
      p2Respawn = gPlayers gsD4 !! 1

  assertEq "P1 resurrected after wipe" True (pAlive p1Respawn)
  assertEq "P2 resurrected after wipe" True (pAlive p2Respawn)
  assertEq "P1 health reset" 100 (pHealth p1Respawn)
  assertEq "P2 health reset" 100 (pHealth p2Respawn)

main :: IO ()
main = do
  putStrLn "Running Haskell Dandy Dungeon Test Suite..."
  testGameInit
  testPlayerSpawning
  testHotJoin
  testSelfResurrection
  testDiagonalSliding
  testSleepMode
  testCooperativeLevelFlow
  putStrLn "Tests Complete!"
  exitSuccess
