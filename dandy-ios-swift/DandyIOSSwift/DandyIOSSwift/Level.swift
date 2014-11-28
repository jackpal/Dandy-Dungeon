

import UIKit

enum Cell : Byte {
  case Space
  case Wall
  case Door
  case Up
  case Down
  case Key
  case Food
  case Money
  case Bomb
  case Monster0, Monster1, Monster2
  case Generator0, Generator1, Generator2
  case Arrow0, Arrow1, Arrow2, Arrow3, Arrow4, Arrow5, Arrow6, Arrow7
  case Player0, Player1, Player2, Player3
}

class Level {
  let width: Int
  let height: Int
  var data: Array<Cell>
  init(width: Int, height: Int) {
    self.width = width
    self.height = height
    self.data = [Cell](count: Int(width * height), repeatedValue:Cell.Space)
  }

  func read(data:NSData) {
    var b = UnsafePointer<Byte>(data.bytes)
    var i = 0
    for y in 0..<height {
      for var x = 0; x < width; x += 2 {
        let d = b[0]
        b++
        self.data[i++] = byteToCell(d)
        self.data[i++] = byteToCell(d >> 4)
      }
    }
  }

  func byteToCell(d : Byte) -> Cell {
    if let c = Cell(rawValue:d & Byte(0xf)) {
      return c
    }
    return Cell.Space
  }

  func index(x : Int, y : Int) -> Int {
    if (x < 0 || x >= width || y < 0 || y >= height) {
      return -1
    }
    return x + width * y
  }

  subscript(x :Int, y: Int) -> Cell {
    get {
      return data[index(x,y:y)]
    }
    set {
      data[index(x,y:y)] = newValue
    }
  }
}
