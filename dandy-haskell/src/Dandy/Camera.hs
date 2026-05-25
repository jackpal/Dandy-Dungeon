module Dandy.Camera
  ( updateCamera
  , getCameraOffsets
  , getActiveRect
  , calculateTargetCog
  ) where

import Dandy.Consts
import Dandy.Types

updateCamera :: Camera -> Int -> Int -> Camera
updateCamera (Camera cogX cogY) targetX targetY =
  let maxRate = fromIntegral tileSize / 4.0
      dx = fromIntegral targetX - cogX
      dy = fromIntegral targetY - cogY
      clampedDx = if dx == 0.0 then 0.0 else max (-maxRate) (min maxRate dx)
      clampedDy = if dy == 0.0 then 0.0 else max (-maxRate) (min maxRate dy)
  in Camera (cogX + clampedDx) (cogY + clampedDy)

getCameraOffsets :: Camera -> (Double, Double)
getCameraOffsets (Camera cogX cogY) =
  let sw = fromIntegral screenWidth
      sh = fromIntegral screenHeight
      mw = fromIntegral (mapWidth * tileSize)
      mh = fromIntegral (mapHeight * tileSize)
      offsetX = -cogX + sw / 2.0
      offsetY = -cogY + sh / 2.0
      clampedX = max (-(mw - sw)) (min 0.0 offsetX)
      clampedY = max (-(mh - sh)) (min 0.0 offsetY)
  in (clampedX, clampedY)

getActiveRect :: Camera -> ActiveRect
getActiveRect cam =
  let (offsetX, offsetY) = getCameraOffsets cam
      ts = fromIntegral tileSize
      sw = fromIntegral screenWidth
      sh = fromIntegral screenHeight
      
      left = floor (-offsetX / ts)
      right = floor ((-offsetX + sw + ts - 1.0) / ts)
      top = floor (-offsetY / ts)
      bottom = floor ((-offsetY + sh + ts - 1.0) / ts)
      
      clampedLeft = max 0 (min mapWidth left)
      clampedRight = max 0 (min mapWidth right)
      clampedTop = max 0 (min mapHeight top)
      clampedBottom = max 0 (min mapHeight bottom)
  in ActiveRect
       { arLeft = clampedLeft
       , arTop = clampedTop
       , arWidth = clampedRight - clampedLeft
       , arHeight = clampedBottom - clampedTop
       }

calculateTargetCog :: [Player] -> (Int, Int)
calculateTargetCog ps =
  let activeAlive = filter (\p -> pActive p && pAlive p && not (pEscaped p)) ps
      numActive = length activeAlive
  in if numActive > 0
       then
         let sumX = sum (map (\p -> pX p * tileSize) activeAlive)
             sumY = sum (map (\p -> pY p * tileSize) activeAlive)
             cogX = sumX `div` numActive
             cogY = sumY `div` numActive
         in (cogX + tileSize `div` 2, cogY + tileSize `div` 2)
       else
         (10 * tileSize + tileSize `div` 2, 5 * tileSize + tileSize `div` 2)
