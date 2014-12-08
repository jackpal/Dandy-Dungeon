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
  var tileWScale: Float32
  var tileStride: CUnsignedInt

  init () {
    offsetX = 0
    offsetY = 0
    tileSizeX = 0
    tileSizeY = 0
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


class TileMeshRenderer: Renderer {
  var viewTilesX :Int
  var viewTilesY :Int

  // Bytes for the tiles.
  var kTileBufferSize :Int

  // Bytes for the tile uniforms
  let kTileUniformSize = 32

  // bytes for a single quad

  let kQuadBufferSize = 64

  var vertexBuffer: MTLBuffer! = nil
  var _tileStride: CUnsignedInt = 0
  var _tileCount: Int = 0
  var vertexUniformsBuffer: MTLBuffer! = nil
  // The vertices for a single quad.
  var quadVertexBuffer: MTLBuffer! = nil;
  var texture: Texture3D! = nil
  var pipelineState: MTLRenderPipelineState! = nil
  var bufferIndex:Int = 0

  init(viewTilesX: Int, viewTilesY: Int) {
    self.viewTilesX = viewTilesX
    self.viewTilesY = viewTilesY
    kTileBufferSize = (viewTilesX + 1) * (viewTilesY + 1)
  }

  func createResources(device: MTLDevice) {
    // generate a large enough buffer to allow streaming vertices for 3 semaphore controlled frames
    vertexBuffer = device.newBufferWithLength(MaxBuffers * kTileBufferSize, options: nil)
    vertexBuffer.label = "vertices"

    let vertexUniformsLength = MaxBuffers * kTileUniformSize
    vertexUniformsBuffer = device.newBufferWithLength(vertexUniformsLength, options: nil)
    vertexUniformsBuffer.label = "uniforms"

    let quadBufferLength = MaxBuffers * kQuadBufferSize
    quadVertexBuffer = device.newBufferWithLength(quadBufferLength, options:nil)
    quadVertexBuffer.label = "a quad"

    texture = Texture3D(name:"dandy", ext:"png", depth:32)
    if texture == nil || !texture.bind(device) {
      assert(false)
    }

    let defaultLibrary = device.newDefaultLibrary()
    let fragmentProgram = defaultLibrary?.newFunctionWithName("tileFragment")
    let vertexProgram = defaultLibrary?.newFunctionWithName("tileVertex")

    let pipelineStateDescriptor = MTLRenderPipelineDescriptor()
    pipelineStateDescriptor.vertexFunction = vertexProgram
    pipelineStateDescriptor.fragmentFunction = fragmentProgram
    pipelineStateDescriptor.colorAttachments[0].pixelFormat = .BGRA8Unorm

    var pipelineError : NSError?
    pipelineState = device.newRenderPipelineStateWithDescriptor(pipelineStateDescriptor, error: &pipelineError)
    if (pipelineState == nil) {
      println("Failed to create pipeline state, error \(pipelineError)")
    }
  }

  // Returns an unsafe mutable buffer pointer to the current tile data.
  // This pointer is only valid until the next time "render" is called.
  var data:UnsafeMutableBufferPointer<CUnsignedChar> {
    get {
      let pData = vertexBuffer.contents() + kTileBufferSize*bufferIndex
      return UnsafeMutableBufferPointer<CUnsignedChar>(
        start: UnsafeMutablePointer<CUnsignedChar>(pData),
        count:kTileBufferSize)
    }
  }

  var tileCount: Int {
    get {
      return self._tileCount
    }
    set {
      assert(newValue >= 0 && newValue <= kTileBufferSize,
        "tileCount out of range")
      self._tileCount = newValue
    }
  }

  var tileStride: CUnsignedInt {
    get {
      return self._tileStride
    }
    set {
      self._tileStride = newValue
    }
  }

  func updateUniforms(viewPixelsX: Float32, viewPixelsY: Float32) {
    // Write uniforms.
    let uData = vertexUniformsBuffer.contents()
    let vuData = UnsafeMutablePointer<TileUniforms>(uData + kTileUniformSize * bufferIndex)

    let pixelsX = viewPixelsX / Float32(viewTilesX)
    let pixelsY = viewPixelsY / Float32(viewTilesY)
    let tx = 2.0 * pixelsX / viewPixelsX
    let ty = 2.0 * pixelsY / viewPixelsY

    vuData[0].offsetX = -Float32(viewTilesX) * 0.5 * tx
    vuData[0].offsetY = Float32(viewTilesY) * 0.5 * ty
    vuData[0].tileSizeX = tx
    vuData[0].tileSizeY = -ty
    vuData[0].tileStride = CUnsignedInt(tileStride)
    vuData[0].tileWScale = 1.0 / 32.0

    updateQuad(tx, ty: ty)
  }

  func updateQuad(tx: Float32, ty: Float32) {
    let pV = UnsafeMutablePointer<TileVertex>(quadVertexBuffer.contents()
      + kQuadBufferSize * bufferIndex)
    pV[0].x = 0
    pV[0].y = -ty
    pV[0].u = 0
    pV[0].v = 1

    pV[1].x = tx
    pV[1].y = -ty
    pV[1].u = 1
    pV[1].v = 1

    pV[2].x = 0
    pV[2].y = 0
    pV[2].u = 0
    pV[2].v = 0

    pV[3].x = tx
    pV[3].y = 0
    pV[3].u = 1
    pV[3].v = 0
  }

  func render(encoder: MTLRenderCommandEncoder) {
    encoder.pushDebugGroup("draw tiles")
    encoder.setRenderPipelineState(pipelineState)
    encoder.setVertexBuffer(vertexBuffer,
      offset: kTileBufferSize*bufferIndex, atIndex: 0)
    encoder.setVertexBuffer(vertexUniformsBuffer,
      offset:kTileUniformSize * bufferIndex , atIndex: 1)
    encoder.setVertexBuffer(quadVertexBuffer,
      offset:kQuadBufferSize * bufferIndex, atIndex: 2)

    encoder.setFragmentTexture(texture.texture, atIndex:0)
    encoder.drawPrimitives(.TriangleStrip, vertexStart: 0,
      vertexCount:4, instanceCount: tileCount)

    encoder.popDebugGroup()
    bufferIndex = (bufferIndex + 1) % MaxBuffers
  }
}
