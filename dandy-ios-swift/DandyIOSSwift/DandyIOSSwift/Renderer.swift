//
//  RendererProtocol.swift
//  DandyIOSSwift
//
//  Created by Jack Palevich on 12/7/14.
//  Copyright (c) 2014 JacksHacks. All rights reserved.
//

import Foundation
import Metal

protocol Renderer {
  func createResources(device: MTLDevice)
  func render(encoder: MTLRenderCommandEncoder)
}
