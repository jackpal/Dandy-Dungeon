import Foundation
import Metal

class Atlas : Texture {
  // Width of a cell in texels
  let cellWidth: UInt
  // Height of a cell in texels
  let cellHeight: UInt
  var cellStride: UInt = 0
  var cellU : Float32 = 0.0
  var cellV : Float32 = 0.0

  init?(name: String, ext: String, cellWidth: UInt, cellHeight: UInt) {
    self.cellWidth = cellWidth
    self.cellHeight = cellHeight
    super.init(name:name, ext:ext)
  }

  override func bind(device: MTLDevice) -> Bool {
    let result = super.bind(device)
    if result {
      cellStride = width / cellWidth
      cellU = Float32(cellWidth) / Float32(width)
      cellV = Float32(cellHeight) / Float32(height)
    }
    return result
  }

  func atlasCellCoord(index:UInt) -> (UInt, UInt) {
    let y = index / cellStride
    let x = index - y * cellStride
    return (x, y)
  }

  func atlasUV(index:UInt) -> (Float32, Float32) {
    let (x, y) = atlasCellCoord(index)
    return (Float32(x) * cellU, Float32(y) * cellV)
  }
}