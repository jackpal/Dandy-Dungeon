import Foundation
import Metal

class Atlas : Texture {
  // Width of a cell in texels
  let cellWidth: Int
  // Height of a cell in texels
  let cellHeight: Int
  var cellStride: Int = 0
  var cellU : Float32 = 0.0
  var cellV : Float32 = 0.0

  init?(name: String, ext: String, cellWidth: Int, cellHeight: Int) {
    self.cellWidth = cellWidth
    self.cellHeight = cellHeight
    super.init(name:name, ext:ext)
  }

  override func bind(device: MTLDevice) -> Bool {
    let result = super.bind(device: device)
    if result {
      cellStride = width / cellWidth
      cellU = Float32(cellWidth) / Float32(width)
      cellV = Float32(cellHeight) / Float32(height)
    }
    return result
  }

  func atlasCellCoord(index:Int) -> (Int, Int) {
    let y = index / cellStride
    let x = index - y * cellStride
    return (x, y)
  }

  func atlasUV(index:Int) -> (Float32, Float32) {
    let (x, y) = atlasCellCoord(index: index)
    return (Float32(x) * cellU, Float32(y) * cellV)
  }
}
