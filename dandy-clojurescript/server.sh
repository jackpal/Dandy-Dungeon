#!/bin/bash
lein cljsbuild auto&
python -m SimpleHTTPServer
