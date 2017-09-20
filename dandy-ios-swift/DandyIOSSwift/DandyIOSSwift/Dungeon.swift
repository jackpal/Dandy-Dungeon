import Foundation

class Dungeon {
  let levelWidth = 60
  let levelHeight = 30
  let levelDepth = 26

  var levelData: Data!

  init() {}

  func loadLevel(levelIndex: Int) -> Level {
    if levelData == nil {
      if let path = Bundle.main.path(forResource: "dungeon", ofType:"levelData") {
        levelData = try! Data(contentsOf: URL(fileURLWithPath:path))
      }
    }
    let level = Level(width: levelWidth, height: levelHeight)
    let levelSize = levelWidth * levelHeight / 2
    let levelStart = levelIndex * levelSize
    let levelEnd = levelStart + levelSize
    let subRange = levelStart..<levelEnd
    level.read(data:levelData.subdata(in: Range(subRange)))
    return level
  }
}
