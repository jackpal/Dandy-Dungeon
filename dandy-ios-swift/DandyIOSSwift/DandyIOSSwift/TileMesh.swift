//
//  Mesh.swift
//  DandyIOSSwift
//
//  Created by Jack Palevich on 11/29/14.
//  Copyright (c) 2014 JacksHacks. All rights reserved.
//

import Foundation
import Metal

// Layout matches Metal shader uniform declaration.
// float2 offset; // Offset of tile map in screen pixels.
// float2 tileSize; // Size of a tile in screen pixels
// float tileWScale; // 1 / numberOfTiles in texture
// uint tileStride; // Tiles per horizontal line

struct TileUniforms {
  var offsetX: Float32
  var offsetY: Float32
  var tileSizeX: Float32
  var tileSizeY: Float32
  var pointSize: Float32
  var tileWScale: Float32
  var tileStride: CUnsignedInt

  init () {
    offsetX = 0
    offsetY = 0
    tileSizeX = 0
    tileSizeY = 0
    pointSize = 0
    tileWScale = 0
    tileStride = 0
  }
}

struct TileVertex {
  var x : Float32 = 0
  var y : Float32 = 0
  var u : Float32 = 0
  var v : Float32 = 0
}