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

  let device = { MTLCreateSystemDefaultDevice()! }()
  let metalLayer = { CAMetalLayer() }()

  var commandQueue: MTLCommandQueue! = nil
  var timer: CADisplayLink! = nil

  var tileMeshRenderer: TileMeshRenderer! = nil

  let inflightSemaphore = DispatchSemaphore(value: MaxBuffers)
  var bufferIndex = 0

  let world : World = World()

  let gameControllerController = GameControllerController()

  override var prefersHomeIndicatorAutoHidden: Bool { get {return true} }

  override func viewDidLoad() {
    super.viewDidLoad()

    metalLayer.device = device
    metalLayer.pixelFormat = .bgra8Unorm
    metalLayer.framebufferOnly = true

    self.resize()

    tileMeshRenderer = TileMeshRenderer(viewTilesX: 20, viewTilesY:10)
    tileMeshRenderer.createResources(device: device)

    view.layer.addSublayer(metalLayer)
    view.isOpaque = true
    view.backgroundColor = nil

    let tapGesture = UITapGestureRecognizer(target: self,
                                            action: #selector(GameViewController.handleTap))
    view.addGestureRecognizer(tapGesture)

    commandQueue = device.makeCommandQueue()
    commandQueue.label = "main command queue"

    timer = CADisplayLink(target: self, selector: #selector(GameViewController.renderLoop))
    timer.add(to: RunLoop.main, forMode: RunLoop.Mode.default)
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

  override var prefersStatusBarHidden: Bool {
    return true
  }

  deinit {
    timer.invalidate()
  }

  @objc
  func renderLoop() {
    autoreleasepool {
      self.render()
    }
  }

  func render() {

    // use semaphore to encode 3 frames ahead
    _ = inflightSemaphore.wait(timeout:DispatchTime.distantFuture)

    self.update()

    let commandBuffer = commandQueue.makeCommandBuffer()!
    commandBuffer.label = "Frame command buffer"

    let drawable = metalLayer.nextDrawable()!
    let renderPassDescriptor = MTLRenderPassDescriptor()
    renderPassDescriptor.colorAttachments[0].texture = drawable.texture
    renderPassDescriptor.colorAttachments[0].loadAction = .clear
    renderPassDescriptor.colorAttachments[0].clearColor = MTLClearColor(red: 0.65, green: 0.65, blue: 0.65, alpha: 1.0)
    renderPassDescriptor.colorAttachments[0].storeAction = .store

    let renderEncoder = commandBuffer.makeRenderCommandEncoder(descriptor: renderPassDescriptor)!
    renderEncoder.label = "render encoder"

    tileMeshRenderer.render(encoder: renderEncoder)

    renderEncoder.endEncoding()

    // use completion handler to signal the semaphore when this frame is completed allowing the encoding of the next frame to proceed
    // use capture list to avoid any retain cycles if the command buffer gets retained anywhere besides this stack frame
    commandBuffer.addCompletedHandler{ [weak self] commandBuffer in
      if let strongSelf = self {
        strongSelf.inflightSemaphore.signal()
      }
      return
    }

    // bufferIndex matches the current semaphore controled frame index to ensure writing occurs at the correct region in the vertex buffer
    bufferIndex = (bufferIndex + 1) % MaxBuffers

    commandBuffer.present(drawable)
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
    tileMeshRenderer.updateUniforms(viewPixelsX: viewPixelsX,
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

    let level = world.map!
    var i = 0
    for y in cam.startY..<cam.endY {
      for x in cam.startX..<cam.endX {
        vData[i] = CUnsignedChar(level[x,y].rawValue)
        i += 1
      }
    }
  }

  @objc
  func handleTap(recognizer: UITapGestureRecognizer) {
    // let tapLocation = recognizer.location(in: view)
    // Just for testing, cycle level
    world.changeLevel(delta: 1)
  }

}
