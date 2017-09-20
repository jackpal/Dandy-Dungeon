//
//  Texture.swift
//  DandyIOSSwift
//
//  Created by Jack Palevich on 11/29/14.
//  Copyright (c) 2014 JacksHacks. All rights reserved.
//

import Metal
import UIKit

class Texture {
  var label: String
  var texture: MTLTexture!
  var target: MTLTextureType!
  var width: Int = 0
  var height: Int = 0
  var path: String
  var flip: Bool = false
  var mipMapped: Bool = false

  init?(name: String, ext: String) {
    label = name
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
          context.scaleBy(x: -1.0, y:-1.0)
        }
        context.draw(imageRef, in:bounds)
        let texDesc = MTLTextureDescriptor.texture2DDescriptor(
          pixelFormat: MTLPixelFormat.rgba8Unorm,
          width: Int(width), height: Int(height), mipmapped: mipMapped)
        target = texDesc.textureType
        if let texture = device.makeTexture(descriptor: texDesc) {
          self.texture = texture
          texture.label = label
          let pixels = context.data!
          let region = MTLRegionMake2D(0, 0, Int(width), Int(height))
          texture.replace(region: region, mipmapLevel: 0, withBytes: pixels, bytesPerRow: Int(bytesPerRow))
          return true
        }
      }
    }
    return false
  }
}
