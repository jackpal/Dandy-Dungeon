{-# LANGUAGE TemplateHaskell #-}
module Dandy.Embed (embedFile) where

import Language.Haskell.TH
import Language.Haskell.TH.Syntax
import qualified Data.ByteString as BS

embedFile :: FilePath -> Q Exp
embedFile path = do
  addDependentFile path
  bytes <- runIO $ BS.readFile path
  let word8s = BS.unpack bytes
  return $ ListE (map (LitE . IntegerL . fromIntegral) word8s)
