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
  var texture: MTLTexture?
  var target: MTLTextureType?
  var width: UInt = 0
  var height: UInt = 0
  var path: String
  var flip: Bool = false
  var mipMapped: Bool = false

  init?(name: String, ext: String) {
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
        let texDesc = MTLTextureDescriptor.texture2DDescriptorWithPixelFormat(
          MTLPixelFormat.RGBA8Unorm, width: Int(width), height: Int(height), mipmapped: mipMapped)
        target = texDesc.textureType
        if let texture = device.newTextureWithDescriptor(texDesc) {
          let pixels = CGBitmapContextGetData(context)
          let region = MTLRegionMake2D(0, 0, Int(width), Int(height))
          let bytesPerImage = Int(height * bytesPerRow)
          texture.replaceRegion(region, mipmapLevel: 0, withBytes: pixels, bytesPerRow: Int(bytesPerRow))
          return true
        }
      }
    }
    return false
  }
}