//
//  Texture.swift
//  DandyIOSSwift
//
//  Created by Jack Palevich on 11/29/14.
//  Copyright (c) 2014 JacksHacks. All rights reserved.
//

import Metal
import UIKit

class Texture3D {
  var label: String
  var texture: MTLTexture!
  var target: MTLTextureType!
  var width: Int = 0
  var height: Int = 0
  var depth: Int
  var path: String
  var flip: Bool = false

  init?(name: String, ext: String, depth: Int) {
    label = name
    self.depth = depth
    if let p = Bundle.main.path(forResource: name, ofType:ext) {
      path = p
    } else {
      path = ""
      return nil
    }
  }

  func bind(device: MTLDevice) -> Bool {
    if let image = UIImage(contentsOfFile: path) {
      let imageRef = image.cgImage!

      width = imageRef.width
      height = imageRef.height

      let rgbColorSpace = CGColorSpaceCreateDeviceRGB()
      let bytesPerRow = 4 * width
      let bitsPerComponent = 8

      let bitmapInfo = CGBitmapInfo(rawValue: CGImageAlphaInfo.premultipliedLast.rawValue)

      if let context = CGContext(data: nil, width: width, height: height, bitsPerComponent: bitsPerComponent, bytesPerRow: bytesPerRow, space: rgbColorSpace, bitmapInfo: bitmapInfo.rawValue) {
        let bounds = CGRect(x:0, y:0, width:width, height:height)
        context.clear(bounds)
        if flip {
          context.translateBy(x:CGFloat(width), y:CGFloat(height))
          context.scaleBy(x:-1.0, y:-1.0)
        }
        context.draw(imageRef, in: bounds)
        let texDesc = MTLTextureDescriptor.init()
        texDesc.textureType = MTLTextureType.type3D
        texDesc.pixelFormat = MTLPixelFormat.rgba8Unorm
        let sliceHeight = height / depth
        texDesc.width = width
        texDesc.height = sliceHeight
        texDesc.depth = depth
        
        target = texDesc.textureType
        if let texture = device.makeTexture(descriptor: texDesc) {
          self.texture = texture
          texture.label = label
          let pixels = context.data!
          let region = MTLRegionMake3D(0, 0, 0, width, sliceHeight, depth)
          let bytesPerImage = Int(sliceHeight * bytesPerRow)
          texture.replace(region: region,
            mipmapLevel: 0,
            slice:0,
            withBytes: pixels,
            bytesPerRow: Int(bytesPerRow),
            bytesPerImage:Int(bytesPerImage))
          return true
        }
      }
    }
    return false
  }
}
