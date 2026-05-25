module Dandy.Entity
  ( newPlayer
  , startPlayer
  ) where

import Dandy.Types

newPlayer :: Int -> Player
newPlayer idx = Player
  { pIndex = idx
  , pX = 0
  , pY = 0
  , pDir = 0
  , pScore = 0
  , pHealth = 0
  , pBombs = 0
  , pKeys = 0
  , pActive = False
  , pAlive = False
  , pEscaped = False
  , pArrow = Nothing
  , pInput = 0
  }

startPlayer :: Player -> Int -> Int -> Int -> Player
startPlayer p x y dir = p
  { pX = x
  , pY = y
  , pDir = dir
  , pHealth = 100
  , pBombs = 0
  , pKeys = 0
  , pActive = True
  , pAlive = True
  , pEscaped = False
  , pArrow = Nothing
  , pInput = 0
  }
