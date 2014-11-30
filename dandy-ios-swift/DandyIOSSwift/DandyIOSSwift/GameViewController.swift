//
//  GameViewController.swift
//  DandyIOSSwift
//
//  Created by Jack Palevich on 11/27/14.
//  Copyright (c) 2014 JacksHacks. All rights reserved.
//

import UIKit
import Metal
import QuartzCore

let MaxBuffers = 3
let ConstantBufferSize = 1024*1024

let viewTilesX = 20
let viewTilesY = 10

// Bytes for the tiles.
let kTileBufferSize = viewTilesX * viewTilesY

// Bytes for the tile uniforms
let kTileUniformSize = 32


class GameViewController: UIViewController {

  let device = { MTLCreateSystemDefaultDevice() }()
  let metalLayer = { CAMetalLayer() }()

  var commandQueue: MTLCommandQueue! = nil
  var timer: CADisplayLink! = nil
  var pipelineState: MTLRenderPipelineState! = nil
  var vertexBuffer: MTLBuffer! = nil
  var vertexUniformsBuffer: MTLBuffer! = nil
  var texture: Texture3D! = nil

  let inflightSemaphore = dispatch_semaphore_create(MaxBuffers)
  var bufferIndex = 0

  override func viewDidLoad() {
    super.viewDidLoad()

    metalLayer.device = device
    metalLayer.pixelFormat = .BGRA8Unorm
    metalLayer.framebufferOnly = true

    self.resize()

    view.layer.addSublayer(metalLayer)
    view.opaque = true
    view.backgroundColor = nil

    commandQueue = device.newCommandQueue()
    commandQueue.label = "main command queue"

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

    // generate a large enough buffer to allow streaming vertices for 3 semaphore controlled frames
    vertexBuffer = device.newBufferWithLength(ConstantBufferSize, options: nil)
    vertexBuffer.label = "vertices"

    let vertexUniformsLength = MaxBuffers * kTileUniformSize
    vertexUniformsBuffer = device.newBufferWithLength(vertexUniformsLength, options: nil)
    vertexUniformsBuffer.label = "uniforms"

    texture = Texture3D(name:"dandy", ext:"png", depth:32)
    if texture == nil || !texture.bind(device) {
      assert(false)
    }

    timer = CADisplayLink(target: self, selector: Selector("renderLoop"))
    timer.addToRunLoop(NSRunLoop.mainRunLoop(), forMode: NSDefaultRunLoopMode)
  }

  override func viewDidLayoutSubviews() {
    self.resize()
  }

  func resize() {
    if (view.window == nil) {
      return
    }

    let window = view.window!
    let nativeScale = window.screen.nativeScale
    view.contentScaleFactor = nativeScale
    metalLayer.frame = view.layer.frame

    var drawableSize = view.bounds.size
    drawableSize.width = drawableSize.width * CGFloat(view.contentScaleFactor)
    drawableSize.height = drawableSize.height * CGFloat(view.contentScaleFactor)

    metalLayer.drawableSize = drawableSize
  }

  override func prefersStatusBarHidden() -> Bool {
    return true
  }

  deinit {
    timer.invalidate()
  }

  func renderLoop() {
    autoreleasepool {
      self.render()
    }
  }

  func render() {

    // use semaphore to encode 3 frames ahead
    dispatch_semaphore_wait(inflightSemaphore, DISPATCH_TIME_FOREVER)

    self.update()

    let commandBuffer = commandQueue.commandBuffer()
    commandBuffer.label = "Frame command buffer"

    let drawable = metalLayer.nextDrawable()
    let renderPassDescriptor = MTLRenderPassDescriptor()
    renderPassDescriptor.colorAttachments[0].texture = drawable.texture
    renderPassDescriptor.colorAttachments[0].loadAction = .Clear
    renderPassDescriptor.colorAttachments[0].clearColor = MTLClearColor(red: 0.65, green: 0.65, blue: 0.65, alpha: 1.0)
    renderPassDescriptor.colorAttachments[0].storeAction = .Store

    let renderEncoder = commandBuffer.renderCommandEncoderWithDescriptor(renderPassDescriptor)!
    renderEncoder.label = "render encoder"

    renderEncoder.pushDebugGroup("draw tiles")
    renderEncoder.setRenderPipelineState(pipelineState)
    renderEncoder.setVertexBuffer(vertexBuffer, offset: kTileBufferSize*bufferIndex, atIndex: 0)
    renderEncoder.setVertexBuffer(vertexUniformsBuffer, offset:kTileUniformSize * bufferIndex , atIndex: 1)
    renderEncoder.setFragmentTexture(texture.texture, atIndex:0)
    renderEncoder.drawPrimitives(.Point, vertexStart: 0, vertexCount: kTileBufferSize, instanceCount: 1)

    renderEncoder.popDebugGroup()
    renderEncoder.endEncoding()

    // use completion handler to signal the semaphore when this frame is completed allowing the encoding of the next frame to proceed
    // use capture list to avoid any retain cycles if the command buffer gets retained anywhere besides this stack frame
    commandBuffer.addCompletedHandler{ [weak self] commandBuffer in
      if let strongSelf = self {
        dispatch_semaphore_signal(strongSelf.inflightSemaphore)
      }
      return
    }

    // bufferIndex matches the current semaphore controled frame index to ensure writing occurs at the correct region in the vertex buffer
    bufferIndex = (bufferIndex + 1) % MaxBuffers

    commandBuffer.presentDrawable(drawable)
    commandBuffer.commit()
  }

  func update() {
    updateTiles()
    updateTileUniforms()
  }

  func updateTiles() {
    // vData is pointer to the tile buffer
    let pData = vertexBuffer.contents()
    let vData = UnsafeMutablePointer<CUnsignedChar>(pData + kTileBufferSize*bufferIndex)

    // Write tile data.
    for i in 0..<10*20 {
      vData[i] = CUnsignedChar(i & 31)
    }
  }

  func updateTileUniforms() {
    // Write uniforms.
    let uData = vertexUniformsBuffer.contents()
    let vuData = UnsafeMutablePointer<TileUniforms>(uData + kTileUniformSize * bufferIndex)

    let viewPixelsX = Float32(metalLayer.drawableSize.width)
    let viewPixelsY = Float32(metalLayer.drawableSize.height)
    let pixelsX = viewPixelsX / Float32(viewTilesX)
    let pixelsY = viewPixelsY / Float32(viewTilesY)
    let pixelSize = max(pixelsX, pixelsY)
    let tx = pixelSize / viewPixelsX
    let ty = pixelSize / viewPixelsY

    vuData[0].offsetX = -Float32(viewTilesX) * 0.5 * tx
    vuData[0].offsetY = Float32(viewTilesY) * 0.5 * ty
    vuData[0].tileSizeX = tx
    vuData[0].tileSizeY = -ty
    vuData[0].pointSize = pixelSize * 0.5
    vuData[0].tileStride = 20
    vuData[0].tileWScale = 1.0 / 32.0
  }
}