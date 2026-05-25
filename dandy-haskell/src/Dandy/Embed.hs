{-# LANGUAGE TemplateHaskell #-}
module Dandy.Embed (embedFile) where

import Language.Haskell.TH
import Language.Haskell.TH.Syntax
import qualified Data.ByteString as BS
import Data.ByteString.Unsafe (unsafePackAddressLen)
import System.IO.Unsafe (unsafePerformIO)

embedFile :: FilePath -> Q Exp
embedFile path = do
  addDependentFile path
  bytes <- runIO $ BS.readFile path
  let len = BS.length bytes
      word8s = BS.unpack bytes
  return $ AppE (VarE 'unsafePerformIO)
                (AppE (AppE (VarE 'unsafePackAddressLen)
                            (LitE (IntegerL (fromIntegral len))))
                      (LitE (StringPrimL word8s)))
