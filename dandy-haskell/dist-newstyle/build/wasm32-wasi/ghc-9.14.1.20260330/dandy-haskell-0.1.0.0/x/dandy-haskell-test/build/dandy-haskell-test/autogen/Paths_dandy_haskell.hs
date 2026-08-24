{-# LANGUAGE CPP #-}
{-# LANGUAGE NoRebindableSyntax #-}
#if __GLASGOW_HASKELL__ >= 810
{-# OPTIONS_GHC -Wno-prepositive-qualified-module #-}
#endif
{-# OPTIONS_GHC -fno-warn-missing-import-lists #-}
{-# OPTIONS_GHC -w #-}
module Paths_dandy_haskell (
    version,
    getBinDir, getLibDir, getDynLibDir, getDataDir, getLibexecDir,
    getDataFileName, getSysconfDir
  ) where


import qualified Control.Exception as Exception
import qualified Data.List as List
import Data.Version (Version(..))
import System.Environment (getEnv)
import Prelude


#if defined(VERSION_base)

#if MIN_VERSION_base(4,0,0)
catchIO :: IO a -> (Exception.IOException -> IO a) -> IO a
#else
catchIO :: IO a -> (Exception.Exception -> IO a) -> IO a
#endif

#else
catchIO :: IO a -> (Exception.IOException -> IO a) -> IO a
#endif
catchIO = Exception.catch

version :: Version
version = Version [0,1,0,0] []

getDataFileName :: FilePath -> IO FilePath
getDataFileName name = do
  dir <- getDataDir
  return (dir `joinFileName` name)

getBinDir, getLibDir, getDynLibDir, getDataDir, getLibexecDir, getSysconfDir :: IO FilePath




bindir, libdir, dynlibdir, datadir, libexecdir, sysconfdir :: FilePath
bindir     = "/usr/local/google/home/jackpal/.cabal/bin"
libdir     = "/usr/local/google/home/jackpal/.cabal/lib/wasm32-wasi-ghc-9.14.1.20260330-4b5d/dandy-haskell-0.1.0.0-inplace-dandy-haskell-test"
dynlibdir  = "/usr/local/google/home/jackpal/.cabal/lib/wasm32-wasi-ghc-9.14.1.20260330-4b5d"
datadir    = "/usr/local/google/home/jackpal/.cabal/share/wasm32-wasi-ghc-9.14.1.20260330-4b5d/dandy-haskell-0.1.0.0"
libexecdir = "/usr/local/google/home/jackpal/.cabal/libexec/wasm32-wasi-ghc-9.14.1.20260330-4b5d/dandy-haskell-0.1.0.0"
sysconfdir = "/usr/local/google/home/jackpal/.cabal/etc"

getBinDir     = catchIO (getEnv "dandy_haskell_bindir")     (\_ -> return bindir)
getLibDir     = catchIO (getEnv "dandy_haskell_libdir")     (\_ -> return libdir)
getDynLibDir  = catchIO (getEnv "dandy_haskell_dynlibdir")  (\_ -> return dynlibdir)
getDataDir    = catchIO (getEnv "dandy_haskell_datadir")    (\_ -> return datadir)
getLibexecDir = catchIO (getEnv "dandy_haskell_libexecdir") (\_ -> return libexecdir)
getSysconfDir = catchIO (getEnv "dandy_haskell_sysconfdir") (\_ -> return sysconfdir)



joinFileName :: String -> String -> FilePath
joinFileName ""  fname = fname
joinFileName "." fname = fname
joinFileName dir ""    = dir
joinFileName dir fname
  | isPathSeparator (List.last dir) = dir ++ fname
  | otherwise                       = dir ++ pathSeparator : fname

pathSeparator :: Char
pathSeparator = '/'

isPathSeparator :: Char -> Bool
isPathSeparator c = c == '/'
