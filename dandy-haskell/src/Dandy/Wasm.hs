{-# LANGUAGE ForeignFunctionInterface #-}
{-# LANGUAGE TemplateHaskell #-}
module Dandy.Wasm where

import Dandy.Consts
import Dandy.Types
import Dandy.Game
import Dandy.Map
import Dandy.Graphics
import Dandy.Camera (calculateTargetCog, getCameraOffsets, getActiveRect, updateCamera)
import Dandy.Embed (embedFile)
import Data.Word (Word8)
import Data.Int (Int32)
import Foreign.Ptr (Ptr, nullPtr)
import Foreign.StablePtr (StablePtr, newStablePtr, deRefStablePtr, freeStablePtr)
import Foreign.Marshal.Alloc (mallocBytes, free)
import Foreign.Storable (pokeElemOff)
import Data.IORef (IORef, newIORef, readIORef, writeIORef, modifyIORef')
import qualified Data.ByteString as BS
import Control.Monad (forM_, when)
import Data.Bits (shiftL, (.&.), (.|.), complement)

spritesheetBytes :: BS.ByteString
spritesheetBytes = BS.pack $(embedFile "assets/dandy.bmp")

data DandyApp = DandyApp
  { appState       :: !(IORef GameState)
  , appSpritesheet :: !BS.ByteString
  , appFramebuffer :: !(Ptr Word8)
  , appStats       :: !(Ptr Int32)
  }

foreign import ccall unsafe "hs_init" c_hs_init :: Ptr () -> Ptr () -> IO ()

foreign export ccall hs_init_game :: IO (StablePtr DandyApp)
foreign export ccall hs_game_tick :: StablePtr DandyApp -> IO ()
foreign export ccall hs_set_action :: StablePtr DandyApp -> Int -> Int -> Bool -> IO ()
foreign export ccall hs_can_sleep :: StablePtr DandyApp -> IO Bool
foreign export ccall hs_get_framebuffer_ptr :: StablePtr DandyApp -> IO (Ptr Word8)
foreign export ccall hs_get_framebuffer_size :: StablePtr DandyApp -> IO Int
foreign export ccall hs_get_stats_ptr :: StablePtr DandyApp -> IO (Ptr Int32)
foreign export ccall hs_get_stats_len :: StablePtr DandyApp -> IO Int
foreign export ccall hs_get_level :: StablePtr DandyApp -> IO Int
foreign export ccall hs_free_game :: StablePtr DandyApp -> IO ()

hs_init_game :: IO (StablePtr DandyApp)
hs_init_game = do
  when (1 == 0) $ c_hs_init nullPtr nullPtr
  initialGs <- newGame
  loadedGs <- loadGame initialGs
  stateRef <- newIORef loadedGs

  let parsedSheet = parseBmp spritesheetBytes
      fbSize = screenWidth * screenHeight * 4
  fbPtr <- mallocBytes fbSize
  
  let statsSize = 28 * 4
  statsPtr <- mallocBytes statsSize

  let app = DandyApp
        { appState = stateRef
        , appSpritesheet = parsedSheet
        , appFramebuffer = fbPtr
        , appStats = statsPtr
        }

  updateStatsBuffer app loadedGs
  renderFramebuffer app loadedGs

  newStablePtr app

hs_game_tick :: StablePtr DandyApp -> IO ()
hs_game_tick sp = do
  app <- deRefStablePtr sp
  gs <- readIORef (appState app)
  
  nextGs <- stepGame gs
  
  let (tx, ty) = calculateTargetCog (gPlayers nextGs)
      nextCam = updateCamera (gCamera nextGs) tx ty
      finalGs = nextGs { gCamera = nextCam }

  writeIORef (appState app) finalGs

  renderFramebuffer app finalGs
  updateStatsBuffer app finalGs

renderFramebuffer :: DandyApp -> GameState -> IO ()
renderFramebuffer app gs = do
  let fb = appFramebuffer app
      sheet = appSpritesheet app
      m = gMap gs
      cam = gCamera gs
      (offsetX, offsetY) = getCameraOffsets cam
      active = getActiveRect cam

  clearFramebuffer fb 0 0 0

  let left = arLeft active
      top = arTop active
      width = arWidth active
      height = arHeight active

  forM_ [0..height-1] $ \y -> do
    let dy = top + y
    forM_ [0..width-1] $ \x -> do
      let dx = left + x
      tileVal <- getMapTile m dx dy
      let destX = floor (offsetX + fromIntegral (dx * tileSize))
          destY = floor (offsetY + fromIntegral (dy * tileSize))
      blitTile fb sheet tileVal destX destY

updateStatsBuffer :: DandyApp -> GameState -> IO ()
updateStatsBuffer app gs = do
  let ptr = appStats app
      players = gPlayers gs
  
  forM_ (zip [0..] players) $ \(idx, p) -> do
    let baseIdx = idx * 7
    pokeElemOff ptr baseIdx (if pActive p then 1 else 0)
    pokeElemOff ptr (baseIdx + 1) (if pAlive p then 1 else 0)
    pokeElemOff ptr (baseIdx + 2) (if pEscaped p then 1 else 0)
    pokeElemOff ptr (baseIdx + 3) (pScore p)
    pokeElemOff ptr (baseIdx + 4) (pHealth p)
    pokeElemOff ptr (baseIdx + 5) (pKeys p)
    pokeElemOff ptr (baseIdx + 6) (pBombs p)

hs_set_action :: StablePtr DandyApp -> Int -> Int -> Bool -> IO ()
hs_set_action sp playerIdx actionIdx pressed = do
  app <- deRefStablePtr sp
  modifyIORef' (appState app) $ \gs ->
    let ps = gPlayers gs
    in if playerIdx < length ps
         then
           let p = ps !! playerIdx
               bit = 1 `shiftL` actionIdx
               nextInput = if pressed
                             then pInput p .|. bit
                             else pInput p .&. complement bit
               updatedP = p { pInput = nextInput }
               nextPs = zipWith (\i op -> if i == playerIdx then updatedP else op) [0..] ps
           in gs { gPlayers = nextPs }
         else gs

hs_can_sleep :: StablePtr DandyApp -> IO Bool
hs_can_sleep sp = do
  app <- deRefStablePtr sp
  gs <- readIORef (appState app)
  canSleepGame gs

hs_get_framebuffer_ptr :: StablePtr DandyApp -> IO (Ptr Word8)
hs_get_framebuffer_ptr sp = do
  app <- deRefStablePtr sp
  return (appFramebuffer app)

hs_get_framebuffer_size :: StablePtr DandyApp -> IO Int
hs_get_framebuffer_size _ = return (screenWidth * screenHeight * 4)

hs_get_stats_ptr :: StablePtr DandyApp -> IO (Ptr Int32)
hs_get_stats_ptr sp = do
  app <- deRefStablePtr sp
  return (appStats app)

hs_get_stats_len :: StablePtr DandyApp -> IO Int
hs_get_stats_len _ = return 28

hs_get_level :: StablePtr DandyApp -> IO Int
hs_get_level sp = do
  app <- deRefStablePtr sp
  gs <- readIORef (appState app)
  return (gLevel gs)

hs_free_game :: StablePtr DandyApp -> IO ()
hs_free_game sp = do
  app <- deRefStablePtr sp
  free (appFramebuffer app)
  free (appStats app)
  freeStablePtr sp
