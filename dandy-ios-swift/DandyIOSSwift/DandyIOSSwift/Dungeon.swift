import Foundation

class Dungeon {
  let levelWidth = 60
  let levelHeight = 30
  let levelDepth = 26

  var levelData: NSData!

  func loadLevel(levelIndex: Int) -> Level {
    if levelData == nil {
      if let path = NSBundle.mainBundle().pathForResource("dungeon", ofType:"levelData") {
        levelData = NSData(contentsOfFile: path)
      }
    }
    let level = Level(width: levelWidth, height: levelHeight)
    let levelSize = levelWidth * levelHeight / 2
    let subRange = NSMakeRange(levelIndex * levelSize, levelSize)
    level.read(levelData.subdataWithRange(subRange))
    return level
  }
}