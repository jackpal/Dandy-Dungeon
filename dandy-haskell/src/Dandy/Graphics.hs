module Dandy.Graphics
  ( parseBmp
  , blitTile
  , clearFramebuffer
  ) where

import Dandy.Consts
import Data.Word (Word8)
import Data.Bits (shiftR, (.&.))
import qualified Data.ByteString as BS
import Foreign.Ptr (Ptr)
import Foreign.Storable (pokeElemOff)
import Control.Monad (when, forM_)

readWord32LE :: BS.ByteString -> Int -> Int
readWord32LE bs offset =
  let b0 = fromIntegral (BS.index bs offset)
      b1 = fromIntegral (BS.index bs (offset + 1))
      b2 = fromIntegral (BS.index bs (offset + 2))
      b3 = fromIntegral (BS.index bs (offset + 3))
  in b0 .|. (b1 `shiftL` 8) .|. (b2 `shiftL` 16) .|. (b3 `shiftL` 24)
  where
    b1 `shiftL` n = b1 * (2 ^ n)
    b0 .|. b1 = b0 + b1

readWord16LE :: BS.ByteString -> Int -> Int
readWord16LE bs offset =
  let b0 = fromIntegral (BS.index bs offset)
      b1 = fromIntegral (BS.index bs (offset + 1))
  in b0 .|. (b1 `shiftL` 8)
  where
    b1 `shiftL` n = b1 * (2 ^ n)
    b0 .|. b1 = b0 + b1

parseBmp :: BS.ByteString -> BS.ByteString
parseBmp bs =
  let header = BS.take 2 bs
  in if header /= BS.pack [66, 77]
       then error "Invalid BMP format"
       else
         let dataOffset = readWord32LE bs 10
             width = readWord32LE bs 18
             rawHeight = readWord32LE bs 22
             height = abs rawHeight
             topDown = rawHeight < 0
             bpp = readWord16LE bs 28
         in if bpp /= 24
              then error "Only 24bpp BMP supported"
              else
                let rowStride = ((width * 3 + 3) `div` 4) * 4
                    rgbaBytes = concat
                      [ let bmpY = if topDown then y else height - 1 - y
                            rowStart = dataOffset + bmpY * rowStride
                        in concat
                             [ let pxStart = rowStart + x * 3
                                   b = BS.index bs pxStart
                                   g = BS.index bs (pxStart + 1)
                                   r = BS.index bs (pxStart + 2)
                               in [r, g, b, 255]
                             | x <- [0..width-1]
                             ]
                      | y <- [0..height-1]
                      ]
                in BS.pack rgbaBytes

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

      forM_ [startPy..endPy - 1] $ \py -> do
        let sy = destY + py
            srcRowStart = (tileY + py) * 256
            destRowStart = sy * screenWidth
            srcStartIdx = (srcRowStart + (tileX + startPx)) * 4
            destStartIdx = (destRowStart + startX) * 4

        forM_ [0..numPixels - 1] $ \px -> do
          let sIdx = srcStartIdx + px * 4
              dIdx = destStartIdx + px * 4
              r = BS.index spritesheet sIdx
              g = BS.index spritesheet (sIdx + 1)
              b = BS.index spritesheet (sIdx + 2)
              a = BS.index spritesheet (sIdx + 3)

          pokeElemOff fb dIdx r
          pokeElemOff fb (dIdx + 1) g
          pokeElemOff fb (dIdx + 2) b
          pokeElemOff fb (dIdx + 3) a

clearFramebuffer :: Ptr Word8 -> Word8 -> Word8 -> Word8 -> IO ()
clearFramebuffer fb r g b = do
  let totalBytes = screenWidth * screenHeight * 4
      loop idx
        | idx >= totalBytes = return ()
        | otherwise = do
            pokeElemOff fb idx r
            pokeElemOff fb (idx + 1) g
            pokeElemOff fb (idx + 2) b
            pokeElemOff fb (idx + 3) 255
            loop (idx + 4)
  loop 0
