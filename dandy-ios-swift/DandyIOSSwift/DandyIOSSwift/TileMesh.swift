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
struct TileUniforms {
  var offsetX: Float32
  var offsetY: Float32
  var tileSizeX: Float32
  var tileSizeY: Float32
  var tileUVSizeX: Float32
  var tileUVSizeY: Float32
  var tileStride: CUnsignedInt
  var atlasStride: CUnsignedInt
  // Swift does not yet have fixed size arrays
  var v0x: CUnsignedChar
  var v0y: CUnsignedChar
  var v1x: CUnsignedChar
  var v1y: CUnsignedChar
  var v2x: CUnsignedChar
  var v2y: CUnsignedChar
  var v3x: CUnsignedChar
  var v3y: CUnsignedChar
  var v4x: CUnsignedChar
  var v4y: CUnsignedChar
  var v5x: CUnsignedChar
  var v5y: CUnsignedChar

  init () {
    offsetX = 0
    offsetY = 0
    tileSizeX = 0
    tileSizeY = 0
    tileUVSizeX = 0
    tileUVSizeY = 0
    tileStride = 0
    atlasStride = 0

    v0x = 0
    v0y = 0

    v1x = 1
    v1y = 0

    v2x = 0
    v2y = 1

    v3x = 1
    v3y = 0

    v4x = 0
    v4y = 1

    v5x = 1
    v5y = 1
  }
}
