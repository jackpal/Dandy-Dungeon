module Dandy.Rng where

import Dandy.Types (LcgRng(..))
import Data.Word (Word32)
import Data.Bits (shiftR, (.&.))

newLcgRng :: Word32 -> LcgRng
newLcgRng seed = LcgRng seed

lcgNext :: LcgRng -> (Double, LcgRng)
lcgNext (LcgRng state) =
  let nextState = state * 1103515245 + 12345
      val = (nextState `shiftR` 16) .&. 0x7fff
      d = fromIntegral val / 32768.0
  in (d, LcgRng nextState)
