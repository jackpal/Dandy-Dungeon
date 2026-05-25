module Dandy.Graphics
  ( parseBmp
  , blitTile
  , clearFramebuffer
  ) where

import Dandy.Consts
import Data.Word (Word8, Word32)
import Data.Bits (shiftL, shiftR, (.&.), (.|.))
import qualified Data.ByteString as BS
import qualified Data.ByteString.Unsafe as BSU
import qualified Data.ByteString.Internal as BSI
import Foreign.Ptr (Ptr, castPtr, plusPtr)
import Foreign.Storable (peekElemOff, pokeElemOff)
import Foreign.Marshal.Utils (copyBytes)
import System.IO.Unsafe (unsafePerformIO)
import Control.Monad (when)

parseBmp :: BS.ByteString -> BS.ByteString
parseBmp bs = unsafePerformIO $ do
  let header = BS.take 2 bs
  if header /= BS.pack [66, 77]
    then error "Invalid BMP format"
    else BSU.unsafeUseAsCString bs $ \cInPtr -> do
      let inPtr = castPtr cInPtr :: Ptr Word8
          
          read32 :: Int -> IO Int
          read32 offset = do
            b0 <- fromIntegral <$> peekElemOff inPtr offset
            b1 <- fromIntegral <$> peekElemOff inPtr (offset + 1)
            b2 <- fromIntegral <$> peekElemOff inPtr (offset + 2)
            b3 <- fromIntegral <$> peekElemOff inPtr (offset + 3)
            return $ b0 .|. (b1 `shiftL` 8) .|. (b2 `shiftL` 16) .|. (b3 `shiftL` 24)

          read16 :: Int -> IO Int
          read16 offset = do
            b0 <- fromIntegral <$> peekElemOff inPtr offset
            b1 <- fromIntegral <$> peekElemOff inPtr (offset + 1)
            return $ b0 .|. (b1 `shiftL` 8)

      dataOffset <- read32 10
      width <- read32 18
      rawHeight <- read32 22
      let height = abs rawHeight
          topDown = rawHeight < 0
      bpp <- read16 28
      if bpp /= 24
        then error "Only 24bpp BMP supported"
        else do
          let rowStride = ((width * 3 + 3) `div` 4) * 4
          BSI.create (width * height * 4) $ \outPtr -> do
            let loop y x
                  | y >= height = return ()
                  | x >= width  = loop (y + 1) 0
                  | otherwise = do
                      let bmpY = if topDown then y else height - 1 - y
                          rowStart = dataOffset + bmpY * rowStride
                          pxStart = rowStart + x * 3
                          outIdx = (y * width + x) * 4
                      b <- peekElemOff inPtr pxStart
                      g <- peekElemOff inPtr (pxStart + 1)
                      r <- peekElemOff inPtr (pxStart + 2)
                      pokeElemOff outPtr outIdx r
                      pokeElemOff outPtr (outIdx + 1) g
                      pokeElemOff outPtr (outIdx + 2) b
                      pokeElemOff outPtr (outIdx + 3) 255
                      loop y (x + 1)
            loop 0 0

blitTile :: Ptr Word8 -> BS.ByteString -> Word8 -> Int -> Int -> IO ()
blitTile fb spritesheet tileIdx destX destY = do
  let tileX = (fromIntegral (tileIdx .&. 15)) * 16
      tileY = (fromIntegral (tileIdx `shiftR` 4)) * 16
      startPy = max 0 (-destY)
      endPy = min 16 (screenHeight - destY)

  when (startPy < endPy) $ do
    let startX = max 0 destX
        endX = min screenWidth (destX + 16)

    when (startX < endX) $ do
      let startPx = startX - destX
          endPx = endX - destX
          numPixels = endPx - startPx

      BSU.unsafeUseAsCString spritesheet $ \cSpritesheet -> do
        let pSpritesheet = castPtr cSpritesheet :: Ptr Word8
            loop py
              | py >= endPy = return ()
              | otherwise = do
                  let sy = destY + py
                      srcRowStart = (tileY + py) * 256
                      destRowStart = sy * screenWidth
                      srcStartIdx = (srcRowStart + (tileX + startPx)) * 4
                      destStartIdx = (destRowStart + startX) * 4
                      
                      srcPtr = pSpritesheet `plusPtr` srcStartIdx
                      destPtr = fb `plusPtr` destStartIdx

                  copyBytes destPtr srcPtr (numPixels * 4)
                  loop (py + 1)
        loop startPy

clearFramebuffer :: Ptr Word8 -> Word8 -> Word8 -> Word8 -> IO ()
clearFramebuffer fb r g b = do
  let packedColor :: Word32
      packedColor =
        (fromIntegral r)
        .|. (fromIntegral g `shiftL` 8)
        .|. (fromIntegral b `shiftL` 16)
        .|. (255 `shiftL` 24)
      fb32 = castPtr fb :: Ptr Word32
      totalPixels = screenWidth * screenHeight
      loop idx
        | idx >= totalPixels = return ()
        | otherwise = do
            pokeElemOff fb32 idx packedColor
            loop (idx + 1)
  loop 0
