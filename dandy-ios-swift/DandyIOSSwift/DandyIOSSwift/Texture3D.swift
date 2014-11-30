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
  var width: UInt = 0
  var height: UInt = 0
  var depth: UInt
  var path: String
  var flip: Bool = false

  init?(name: String, ext: String, depth: UInt) {
    label = name
    self.depth = depth
    if let p = NSBundle.mainBundle().pathForResource(name, ofType:ext) {
      path = p
    } else {
      path = ""
      return nil
    }
  }

  func bind(device: MTLDevice) -> Bool {
    if let image = UIImage(contentsOfFile: path) {
      let imageRef = image.CGImage

      width = CGImageGetWidth(imageRef)
      height = CGImageGetHeight(imageRef)

      let rgbColorSpace = CGColorSpaceCreateDeviceRGB()
      if rgbColorSpace == nil {
        return false
      }
      let bytesPerRow = 4 * width
      let bitsPerComponent :UInt = 8

      let bitmapInfo = CGBitmapInfo(CGImageAlphaInfo.PremultipliedLast.rawValue)

      if let context = CGBitmapContextCreate(nil, width, height, bitsPerComponent, bytesPerRow, rgbColorSpace, bitmapInfo) {
        let bounds = CGRectMake(0, 0, CGFloat(width), CGFloat(height))
        CGContextClearRect(context, bounds)
        if flip {
          CGContextTranslateCTM(context, CGFloat(width), CGFloat(height))
          CGContextScaleCTM(context, -1.0, -1.0)
        }
        CGContextDrawImage(context, bounds, imageRef)
        let texDesc = MTLTextureDescriptor.init()
        texDesc.textureType = MTLTextureType.Type3D
        texDesc.pixelFormat = MTLPixelFormat.RGBA8Unorm
        let sliceHeight = height / depth
        texDesc.width = Int(width)
        texDesc.height = Int(sliceHeight)
        texDesc.depth = Int(depth)
        
        target = texDesc.textureType
        if let texture = device.newTextureWithDescriptor(texDesc) {
          self.texture = texture
          texture.label = label
          let pixels = CGBitmapContextGetData(context)
          let region = MTLRegionMake3D(0, 0, 0, Int(width), Int(sliceHeight), Int(depth))
          let bytesPerImage = Int(sliceHeight * bytesPerRow)
          texture.replaceRegion(region,
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