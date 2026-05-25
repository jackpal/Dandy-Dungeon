module Dandy.Types where

import Data.Word (Word8, Word32)
import Data.Int (Int32)
import Data.Array.IO (IOUArray)

newtype Map = Map (IOUArray (Int, Int) Word8)

data Arrow = Arrow
  { aX   :: !Int
  , aY   :: !Int
  , aDir :: !Int
  } deriving (Show, Eq)

data Player = Player
  { pIndex    :: !Int
  , pX        :: !Int
  , pY        :: !Int
  , pDir      :: !Int
  , pScore    :: !Int32
  , pHealth   :: !Int32
  , pBombs    :: !Int32
  , pKeys     :: !Int32
  , pActive   :: !Bool
  , pAlive    :: !Bool
  , pEscaped  :: !Bool
  , pArrow    :: !(Maybe Arrow)
  , pInput    :: !Word8
  } deriving (Show, Eq)

data Camera = Camera
  { camCogX :: !Double
  , camCogY :: !Double
  } deriving (Show, Eq)

newtype LcgRng = LcgRng Word32 deriving (Show, Eq)

data ActiveRect = ActiveRect
  { arLeft   :: !Int
  , arTop    :: !Int
  , arWidth  :: !Int
  , arHeight :: !Int
  } deriving (Show, Eq)

data GameState = GameState
  { gMap          :: !Map
  , gPlayers      :: ![Player]
  , gLevel        :: !Int
  , gTime         :: !Word32
  , gLastMoveTime :: !Word32
  , gRotor        :: !Word8
  , gCamera       :: !Camera
  , gRng          :: !LcgRng
  }
