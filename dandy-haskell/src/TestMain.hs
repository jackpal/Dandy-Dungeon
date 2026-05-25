module Main where

import Dandy.Consts
import Dandy.Types
import Dandy.Game
import Dandy.Physics
import Dandy.Map
import Dandy.AI
import Data.Bits ((.|.), (.&.))
import Control.Monad (forM_, when)
import System.Exit (exitFailure, exitSuccess)
import Data.Word (Word8)

assertEq :: (Show a, Eq a) => String -> a -> a -> IO ()
assertEq name expected actual =
  if expected == actual
    then putStrLn $ "PASS: " ++ name
    else do
      putStrLn $ "FAIL: " ++ name ++ " - Expected: " ++ show expected ++ ", Got: " ++ show actual
      exitFailure

testGameInit :: IO ()
testGameInit = do
  gs <- newGame
  let ps = gPlayers gs
  assertEq "Players count is 4" 4 (length ps)
  assertEq "P1 active" True (pActive (ps !! 0))
  assertEq "P1 alive" True (pAlive (ps !! 0))
  assertEq "P2 inactive" False (pActive (ps !! 1))
  assertEq "P3 inactive" False (pActive (ps !! 2))
  assertEq "P4 inactive" False (pActive (ps !! 3))

testPlayerSpawning :: IO ()
testPlayerSpawning = do
  initialGs <- newGame
  let ps = map (\p -> p { pActive = True }) (gPlayers initialGs)
  gs <- loadGame initialGs { gPlayers = ps }
  let finalPs = gPlayers gs
  spawnOpt <- findMapTile (gMap gs) upStairsTile
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
  initialGs <- newGame
  gsLoaded <- loadGame initialGs
  let ps1 = gPlayers gsLoaded
      p2Input = actionUp
      ps2 = zipWith (\idx p -> if idx == 1 then p { pInput = p2Input } else p) [0..] ps1
      gsInput = gsLoaded { gPlayers = ps2 }
  gsStepped <- stepGame gsInput
  let finalPs = gPlayers gsStepped
  assertEq "P2 joined/active" True (pActive (finalPs !! 1))
  assertEq "P2 alive" True (pAlive (finalPs !! 1))
  spawnOpt <- findMapTile (gMap gsStepped) upStairsTile
  case spawnOpt of
    Nothing -> putStrLn "FAIL: P2 Spawning - UP stairs not found" >> exitFailure
    Just (sx, sy) -> do
      assertEq "P2 spawn X East" (sx + 1) (pX (finalPs !! 1))
      assertEq "P2 spawn Y East" sy (pY (finalPs !! 1))

testSelfResurrection :: IO ()
testSelfResurrection = do
  initialGs <- newGame
  gsLoaded <- loadGame initialGs
  let m = gMap gsLoaded
  forM_ [0..mapHeight-1] $ \y ->
    forM_ [0..mapWidth-1] $ \x ->
      setMapTile m x y spaceTile
  
  let p1 = (gPlayers gsLoaded !! 0) { pX = 5, pY = 5, pDir = 2, pHealth = 100, pAlive = True, pActive = True }
      nextPs1 = p1 : drop 1 (gPlayers gsLoaded)
  setMapTile m 5 5 playerTile

  setMapTile m 7 5 heartTile

  let p1Shoot = p1 { pInput = actionShoot }
      nextPs2 = p1Shoot : drop 1 nextPs1
      gsShoot = gsLoaded { gPlayers = nextPs2, gMap = m }
  
  gsT1 <- stepGame gsShoot
  gsT2 <- stepGame gsT1
  gsT3 <- stepGame gsT2
  gsT4 <- stepGame gsT3
  
  let psAfterShoot = gPlayers gsT4
      p1AfterShoot = psAfterShoot !! 0
  
  assertEq "P1 arrow fired" True (case pArrow p1AfterShoot of Just _ -> True; Nothing -> False)
  let Just arrow = pArrow p1AfterShoot
  assertEq "Arrow X" 6 (aX arrow)
  assertEq "Arrow Y" 5 (aY arrow)
  
  let p1Dead = p1AfterShoot { pInput = 0, pHealth = 0, pAlive = False }
      nextPs3 = p1Dead : drop 1 psAfterShoot
  setMapTile m 5 5 spaceTile
  
  let gsDead = gsT4 { gPlayers = nextPs3 }
  
  gsD1 <- stepGame gsDead
  gsD2 <- stepGame gsD1
  gsD3 <- stepGame gsD2
  gsD4 <- stepGame gsD3
  
  let finalPs = gPlayers gsD4
      finalP1 = finalPs !! 0
  
  assertEq "P1 resurrected!" True (pAlive finalP1)
  assertEq "P1 health is 50" 50 (pHealth finalP1)
  assertEq "P1 X is HEART X" 7 (pX finalP1)
  assertEq "P1 Y is HEART Y" 5 (pY finalP1)
  assertEq "P1 arrow destroyed" Nothing (pArrow finalP1)
  
  tileVal <- getMapTile m 7 5
  assertEq "Map tile at HEART is P1" playerTile tileVal
  
  oldTileVal <- getMapTile m 5 5
  assertEq "Map tile at old position is empty" spaceTile oldTileVal

testDiagonalSliding :: IO ()
testDiagonalSliding = do
  initialGs <- newGame
  gsLoaded <- loadGame initialGs
  let m = gMap gsLoaded
  forM_ [0..mapHeight-1] $ \y ->
    forM_ [0..mapWidth-1] $ \x ->
      setMapTile m x y spaceTile
  
  let p1 = (gPlayers gsLoaded !! 0) { pX = 5, pY = 5, pDir = 2, pHealth = 100, pAlive = True, pActive = True }
      nextPs1 = p1 : drop 1 (gPlayers gsLoaded)
  setMapTile m 5 5 playerTile

  setMapTile m 5 4 wallTile
  setMapTile m 6 4 wallTile
  
  let p1Move = p1 { pInput = actionUp .|. actionRight }
      nextPs2 = p1Move : drop 1 nextPs1
      gsMove = gsLoaded { gPlayers = nextPs2, gMap = m }
  
  gs1 <- stepGame gsMove
  gs2 <- stepGame gs1
  gs3 <- stepGame gs2
  gs4 <- stepGame gs3
  
  let finalPs = gPlayers gs4
      finalP1 = finalPs !! 0
  
  assertEq "Diagonal sliding X" 6 (pX finalP1)
  assertEq "Diagonal sliding Y" 5 (pY finalP1)
  
  tileVal <- getMapTile m 6 5
  assertEq "Map tile at slid position is P1" playerTile tileVal
  
  oldTileVal <- getMapTile m 5 5
  assertEq "Map tile at old position is empty" spaceTile oldTileVal

testSleepMode :: IO ()
testSleepMode = do
  initialGs <- newGame
  gsLoaded <- loadGame initialGs
  let m = gMap gsLoaded
  
  -- Clear viewport active rect of any ghosts & generators
  forM_ [0..mapHeight-1] $ \y ->
    forM_ [0..mapWidth-1] $ \x -> do
      v <- getMapTile m x y
      when ((v >= ghostTile && v <= ghostTile + 2) || (v >= generatorTile && v <= generatorTile + 2)) $
        setMapTile m x y spaceTile

  -- Basic sleep should succeed
  sleepy1 <- canSleepGame gsLoaded
  assertEq "can sleep basic" True sleepy1

  -- Should NOT sleep with player input
  let p1Input = (gPlayers gsLoaded !! 0) { pInput = actionUp }
      gsWithInput = gsLoaded { gPlayers = p1Input : drop 1 (gPlayers gsLoaded) }
  sleepy2 <- canSleepGame gsWithInput
  assertEq "cannot sleep with player input" False sleepy2

  -- Should NOT sleep with arrow in flight
  let p1Arrow = (gPlayers gsLoaded !! 0) { pArrow = Just (Arrow 5 5 0) }
      gsWithArrow = gsLoaded { gPlayers = p1Arrow : drop 1 (gPlayers gsLoaded) }
  sleepy3 <- canSleepGame gsWithArrow
  assertEq "cannot sleep with arrow in flight" False sleepy3

  -- Clear map and place a ghost near player at (3,5) and ghost at (5,5)
  forM_ [0..mapHeight-1] $ \y ->
    forM_ [0..mapWidth-1] $ \x ->
      setMapTile m x y spaceTile

  let p1Near = (gPlayers gsLoaded !! 0) { pX = 3, pY = 5, pAlive = True, pActive = True }
      nextPs = p1Near : drop 1 (gPlayers gsLoaded)
  setMapTile m 3 5 playerTile
  setMapTile m 5 5 ghostTile
  
  let gsWithGhost = gsLoaded { gPlayers = nextPs, gMap = m, gCamera = Camera 56.0 88.0 }
  sleepy4 <- canSleepGame gsWithGhost
  assertEq "cannot sleep with unblocked ghost" False sleepy4

  -- Block the ghost by blocking its three candidate move directions: Left, Up-Left, Down-Left
  setMapTile m 4 5 wallTile
  setMapTile m 4 4 wallTile
  setMapTile m 4 6 wallTile

  sleepy5 <- canSleepGame gsWithGhost
  assertEq "can sleep when ghost is blocked" True sleepy5

main :: IO ()
main = do
  putStrLn "Running Haskell Dandy Dungeon Test Suite..."
  testGameInit
  testPlayerSpawning
  testHotJoin
  testSelfResurrection
  testDiagonalSliding
  testSleepMode
  putStrLn "Tests Complete!"
  exitSuccess
