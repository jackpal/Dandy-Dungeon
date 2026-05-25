module Dandy.Physics
  ( doSmartBomb
  , tryMovePlayer
  , stepPlayer
  , stepArrow
  ) where

import Dandy.Consts
import Dandy.Types
import Dandy.Map
import Data.Bits ((.&.))
import Control.Monad (forM, when)

doSmartBomb :: Player -> Map -> ActiveRect -> IO Player
doSmartBomb p m active = do
  let left = arLeft active
      top = arTop active
      width = arWidth active
      height = arHeight active
      xRange = [left .. left + width - 1]
      yRange = [top .. top + height - 1]

  scores <- forM yRange $ \y -> do
    forM xRange $ \x -> do
      v <- getMapTile m x y
      if v >= ghostTile && v <= ghostTile + 2
        then do
          setMapTile m x y spaceTile
          return (10 * (fromIntegral (v - ghostTile) + 1))
        else return 0

  let scoreGain = sum (concat scores)
  return p { pScore = pScore p + scoreGain }

tryMovePlayer :: Int -> Player -> Map -> Int -> IO (Bool, Player)
tryMovePlayer idx p m dir = do
  let pWithDir = p { pDir = dir }
      delta = getDirDelta dir
      nx = pX p + fst delta
      ny = pY p + snd delta

  v <- getMapTile m nx ny

  (moved, escaped, nextP) <- case v of
    _ | v == spaceTile -> return (True, False, pWithDir)
    _ | v == lockTile ->
      if pKeys p > 0
        then do
          unlockMap m nx ny
          return (True, False, pWithDir { pKeys = pKeys p - 1 })
        else return (False, False, pWithDir)
    _ | v == downStairsTile -> do
          setMapTile m (pX p) (pY p) spaceTile
          return (True, True, pWithDir { pEscaped = True, pX = -1, pY = -1 })
    _ | v == keyTile ->
          return (True, False, pWithDir { pKeys = pKeys p + 1 })
    _ | v == foodTile ->
          return (True, False, pWithDir { pHealth = pHealth p + 100 })
    _ | v == moneyTile ->
          return (True, False, pWithDir { pScore = pScore p + 100 })
    _ | v == bombTile ->
          return (True, False, pWithDir { pBombs = pBombs p + 1 })
    _ -> return (False, False, pWithDir)

  if moved && not escaped
    then do
      setMapTile m (pX p) (pY p) spaceTile
      setMapTile m nx ny (playerTile + fromIntegral idx)
      return (True, nextP { pX = nx, pY = ny })
    else return (moved || escaped, nextP)

stepPlayer :: Int -> Player -> Map -> ActiveRect -> IO Player
stepPlayer idx p m activeRect = do
  let input = pInput p
      startX = pX p
      startY = pY p

  pAfterBomb <- if (input .&. actionBomb) /= 0 && pBombs p > 0
                  then do
                    let pBombUsed = p { pBombs = pBombs p - 1 }
                    doSmartBomb pBombUsed m activeRect
                  else return p

  let dx = (if (input .&. actionLeft) /= 0 then -1 else 0) +
           (if (input .&. actionRight) /= 0 then 1 else 0)
      dy = (if (input .&. actionUp) /= 0 then -1 else 0) +
           (if (input .&. actionDown) /= 0 then 1 else 0)

      dirOpt = case (dx, dy) of
        (0, -1) -> Just 0
        (1, -1) -> Just 1
        (1, 0)  -> Just 2
        (1, 1)  -> Just 3
        (0, 1)  -> Just 4
        (-1, 1) -> Just 5
        (-1, 0) -> Just 6
        (-1, -1)-> Just 7
        _       -> Nothing

  let pAfterDir = case dirOpt of
        Just d  -> pAfterBomb { pDir = d }
        Nothing -> pAfterBomb

  if (input .&. actionShoot) /= 0
    then
      if pArrow pAfterDir == Nothing
        then do
          let shootDir = case dirOpt of
                Just d  -> d
                Nothing -> pDir pAfterDir
          return pAfterDir { pArrow = Just (Arrow startX startY shootDir) }
        else return pAfterDir
    else case dirOpt of
      Just d -> do
        (moved, pMoved) <- tryMovePlayer idx pAfterDir m d
        if not moved
          then do
            (movedLeft, pMovedLeft) <- tryMovePlayer idx pAfterDir m ((d + 1) .&. 7)
            if not movedLeft
              then do
                (_, pMovedRight) <- tryMovePlayer idx pAfterDir m ((d + 7) .&. 7)
                return pMovedRight
              else return pMovedLeft
          else return pMoved
      Nothing -> return pAfterDir

stepArrow :: Int -> [Player] -> Map -> ActiveRect -> IO [Player]
stepArrow idx players m activeRect = do
  let p = players !! idx
  case pArrow p of
    Nothing -> return players
    Just a -> do
      let delta = getDirDelta (aDir a)
          nx = aX a + fst delta
          ny = aY a + snd delta
          arrowVal = arrowTile + fromIntegral ((aDir a + 3) .&. 7)

      currentTile <- getMapTile m (aX a) (aY a)
      when (currentTile == arrowVal) $ do
        setMapTile m (aX a) (aY a) spaceTile

      newTile <- getMapTile m nx ny

      (killArrow, newV, pScoreGain, resurrectedIdx) <- case newTile of
        _ | newTile == spaceTile -> return (False, arrowVal, 0, Nothing)
        _ | newTile >= ghostTile && newTile <= ghostTile + 2 -> do
              let nextV = if newTile > ghostTile then newTile - 1 else spaceTile
              return (True, nextV, 10, Nothing)
        _ | newTile == heartTile -> do
              let findDead [] _ = return (True, ghostTile + 2, 0, Nothing)
                  findDead (otherP : rest) oIdx =
                    if pActive otherP && not (pAlive otherP)
                      then return (True, playerTile + fromIntegral oIdx, 0, Just oIdx)
                      else findDead rest (oIdx + 1)
              findDead players 0
        _ | newTile == bombTile -> return (True, spaceTile, 0, Nothing)
        _ -> return (True, newTile, 0, Nothing)

      setMapTile m nx ny newV

      let updatePlayers pIdx otherP
            | Just pIdx == resurrectedIdx =
                let resurrectedP = otherP { pAlive = True, pX = nx, pY = ny, pHealth = 50 }
                    finalP = if pIdx == idx
                               then resurrectedP { pScore = pScore resurrectedP + pScoreGain, pArrow = Nothing }
                               else resurrectedP
                in finalP
            | pIdx == idx =
                let pWithScore = otherP { pScore = pScore otherP + pScoreGain }
                    pWithArrow = if killArrow then pWithScore { pArrow = Nothing }
                                               else pWithScore { pArrow = Just (Arrow nx ny (aDir a)) }
                in pWithArrow
            | otherwise = otherP

      let nextPlayers = zipWith updatePlayers [0..] players

      finalPlayers <- if newTile == bombTile
                        then do
                          let firingP = nextPlayers !! idx
                          updatedFiringP <- doSmartBomb firingP m activeRect
                          return $ updateAt idx updatedFiringP nextPlayers
                        else return nextPlayers

      return finalPlayers
