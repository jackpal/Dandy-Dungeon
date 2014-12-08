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

class GameViewController: UIViewController {

  let device = { MTLCreateSystemDefaultDevice() }()
  let metalLayer = { CAMetalLayer() }()

  var commandQueue: MTLCommandQueue! = nil
  var timer: CADisplayLink! = nil

  var tileMeshRenderer: TileMeshRenderer! = nil

  let inflightSemaphore = dispatch_semaphore_create(MaxBuffers)
  var bufferIndex = 0

  let world : World = World()

  override func viewDidLoad() {
    super.viewDidLoad()

    metalLayer.device = device
    metalLayer.pixelFormat = .BGRA8Unorm
    metalLayer.framebufferOnly = true

    self.resize()

    tileMeshRenderer = TileMeshRenderer(viewTilesX: 20, viewTilesY:10)
    tileMeshRenderer.createResources(device)

    view.layer.addSublayer(metalLayer)
    view.opaque = true
    view.backgroundColor = nil

    let tapGesture = UITapGestureRecognizer(target: self, action: "handleTap:")
    view.addGestureRecognizer(tapGesture)

    commandQueue = device.newCommandQueue()
    commandQueue.label = "main command queue"

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

    tileMeshRenderer.render(renderEncoder)

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
    world.update()
    updateTiles()
    updateTileUniforms()
  }

  func updateTileUniforms() {
    let viewPixelsX = Float32(metalLayer.drawableSize.width)
    let viewPixelsY = Float32(metalLayer.drawableSize.height)
    tileMeshRenderer.updateUniforms(viewPixelsX,
      viewPixelsY: viewPixelsY)
  }

  func updateTiles() {
    // vData is pointer to the tile buffer
    let vData = tileMeshRenderer.data

    // Write tile data.

    let cam = world.getLevelCamera()
    let tileStride = CUnsignedInt(cam.endX - cam.startX)
    tileMeshRenderer.tileStride = tileStride
    tileMeshRenderer.tileCount = Int(tileStride) * (cam.endY - cam.startY)

    let level = world.map
    var i = 0
    for y in cam.startY..<cam.endY {
      for x in cam.startX..<cam.endX {
        vData[i++] = CUnsignedChar(level[x,y].rawValue)
      }
    }
  }

  func handleTap(recognizer: UITapGestureRecognizer) {
    let tapLocation = recognizer.locationInView(view)
    
  }

}