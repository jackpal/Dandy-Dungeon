//
//  Game.swift
//  DandyIOSSwift
//
//  Created by Jack Palevich on 11/30/14.
//  Copyright (c) 2014 JacksHacks. All rights reserved.
//

import Foundation

enum Direction : UInt8 {
  case Up
  case UpRight
  case Right
  case DownRight
  case Down
  case DownLeft
  case Left
  case UpLeft
  case None
}

// Index is bitfield of Down , Up, Right, Left
let kDirTable: [Direction] = [
  // YyXx
  .None, // 0000
  .Left, // 0001
  .Right, // 0010
  .None, // 0011
  .Up, // 0100
  .UpLeft, // 0101
  .UpRight, // 0110
  .None, // 0111
  .Down, // 1000
  .DownLeft, // 1001
  .DownRight, // 1010
  .None, // 1011
  .None, // 1100
  .None, // 1101
  .None, // 1110
  .None, // 1111
]

extension Direction {
  static func direction<X : Numeric & Comparable>(deltaX dx:X, deltaY dy: X) -> Direction {
    var bitField = 0
    
    if dy > X.zero {
      bitField |= 8
    } else if dy < 0 {
      bitField |= 4
    }
    
    if dx > 0 {
      bitField |= 2
    } else if dx < 0 {
      bitField |= 1
    }
    
    //     7 0 1
    //     6 + 2
    //     5 4 3
    
    return kDirTable[bitField]
  }
}

// Direction to X,Y offsets
let kOffsets: [(x:Int, y:Int)] = [
  (0,-1), (1,-1), (1,0), (1,1), (0,1), (-1,1), (-1,0), (-1,-1)]

func moveCoords(x : Int, y : Int, direction: Direction) -> (x: Int, y: Int) {
  if direction != .None {
    // Up is zero, clockwise
    let offset = kOffsets[Int(direction.rawValue)]
    let x2 = x + offset.x
    let y2 = y + offset.y
    return (x2, y2)
  } else {
    // Debug.MyDebugBreak();
    return (x, y)
  }
}

struct LevelCamera {
  var cogX : Float32
  var cogY : Float32
  var startX : Int
  var startY : Int
  var endX : Int
  var endY : Int
  
  init(cogX : Float32, cogY : Float32,
       startX : Int, startY : Int, endX : Int, endY : Int) {
    self.cogX = cogX
    self.cogY = cogY
    self.startX = startX
    self.startY = startY
    self.endX = endX
    self.endY = endY
  }
}

class Arrow {
  enum State {
    case none
    case triggered
    case inFlight
  }
  var state : State = .none
  var alive : Bool {
    state != .none
  }
  var x : Int = 0
  var y : Int = 0
  var dir : Direction = .None
  
  func canGo(c: Cell) -> Bool
  {
    return c == .Space
  }
  
  func canHit(c: Cell) -> Bool
  {
    return c.rawValue >= Cell.Bomb.rawValue
    && c.rawValue <= Cell.Generator2.rawValue
  }
}

enum PlayerState
{
  case Normal
  case InWarp
}

let HealthMax : Int = 9

class Player {
  var x : Int = 0
  var y : Int = 0
  var health : Int = HealthMax
  var food : Int = 0
  var keys : Int = 0
  var bombs : Int = 0
  var score : Int = 0
  var state : PlayerState = .Normal
  var lastMoveTime : Int = 0
  var dir : Direction = .None
  var arrow : Arrow = Arrow()
  
  init() {}
  
  func isAlive() -> Bool {
    return health > 0
  }
  
  func isVisible() -> Bool {
    return health > 0 && state == .Normal;
  }
  
  func eatFood() {
    if food > 0 && health < HealthMax {
      food -= 1
      health = HealthMax
    }
  }
}

let PlayerCount: Int = 4

let levelViewH = 10
let levelViewW = 20

let kTestDelta = [0,-1,1]

let kTicksPerMove = 3

class World {
  var dungeon: Dungeon = Dungeon()
  var map : Level! = nil
  var levelIndex : Int = 0
  var player : [Player] = []
  var numPlayers : Int = 0 // Current number of players
  // Frame count, starts at 0
  var time: Int = 0
  
  var gridStep : Int = 0
  
  init() {
    numPlayers = 1
    for _ in 0..<numPlayers {
      player.append(Player())
    }
    loadLevel(index: 0)
  }
  
  func loadLevel(index : Int) {
    levelIndex = index
    map = dungeon.loadLevel(levelIndex: index)
    setPlayerPositions()
  }
  
  func update() {
    time += 1
    // time = DateTime.Now;
    for i in 0..<numPlayers {
      doArrowMove(p: player[i])
    }
    doMonsters()
  }
  
  func isGameOver() -> Bool {
    for i in 0..<numPlayers {
      if player[i].isAlive() {
        return false
      }
    }
    return true
  }
  
  func doMonsters() {
    let cam = getLevelCamera()
    
    // update in a grid pattern
    gridStep += 1;
    let gridXOffset = gridStep % 3
    let gridYOffset = (gridStep / 3) % 3
    for y in stride(from:cam.startY + gridYOffset, to:cam.endY, by:3) {
      for x in stride(from:cam.startX + gridXOffset, to:cam.endX, by:3) {
        let d = map[x, y]
        switch d {
        case .Monster0, .Monster1, .Monster2:
          // Move towards nearest player
          let dir = getDirectionOfNearestPlayer(x: x, y:y)
          if dir != .None {
            var mx = 0
            var my = 0
            var canMove = false
            var d2 = Cell.Space
            for test in 0..<3 {
              // Need to calculate in Int space to avoid overflow from addition.
              // (Is there an "unsafe addition" operator?
              let newDirRaw = UInt8((Int(dir.rawValue) + kTestDelta[test]) & 7)
              let newDir = Direction(rawValue: newDirRaw)!
              (mx, my) = moveCoords(x: x, y: y, direction: newDir)
              d2 = map[mx, my]
              if d2 == .Space || d2.isPlayer() {
                canMove = true
                break
              }
            }
            if canMove {
              map[x, y] = .Space
              if d2.isPlayer() {
                let p = player[Int(d2.rawValue - Cell.Player0.rawValue)]
                let monsterHit = Int(d.rawValue - Cell.Monster0.rawValue + 1)
                if p.health > monsterHit {
                  p.health = p.health - monsterHit
                } else {
                  p.health = 0
                  var remains = Cell.Space
                  if p.keys > 0 {
                    p.keys -= 1
                    remains = .Key
                  }
                  map[p.x, p.y] = remains
                }
              } else {
                map[mx, my] = d
              }
            }
          }
        case .Generator0, .Generator1, .Generator2:
          // Random generator
          if arc4random_uniform(10) < 3 {
            let (gx, gy) = moveCoords(x: x, y: y,
                                      direction: Direction(rawValue: UInt8(arc4random_uniform(4) * 2))!)
            if map[gx,gy] == .Space {
              map[gx, gy] = Cell(rawValue:Cell.Monster0.rawValue
                                 + (d.rawValue - Cell.Generator0.rawValue))!
            }
          }
        default:
          // Swift requires non-empty default case.
          _ = true
        }
      }
    }
  }
  
  func getDirectionOfNearestPlayer(x : Int, y : Int) -> Direction {
    var bestX = 0
    var bestY = 0
    var bestDistance = 10000
    for i in 0..<numPlayers {
      let pP = player[i]
      if pP.isVisible() {
        let distance = abs(pP.x - x) + abs(pP.y - y)
        if distance < bestDistance {
          bestDistance = distance
          bestX = pP.x
          bestY = pP.y
        }
      }
    }
    if bestDistance == 10000 {
      return .None
    }
    let dx = bestX - x
    let dy = bestY - y
    return Direction.direction(deltaX: dx, deltaY: dy)
  }
  
  func getCOG() -> (x: Float32, y: Float32) {
    var x : Float32 = 0.0
    var y : Float32 = 0.0
    var liveCount : Int = 0
    for i in 0..<numPlayers {
      let pP = player[i]
      if pP.isVisible() {
        x += Float32(pP.x)
        y += Float32(pP.y)
        liveCount += 1
      }
    }
    if liveCount > 0 {
      x /= Float32(liveCount)
      y /= Float32(liveCount)
    }
    return (x: x, y: y)
  }
  
  func getLevelCamera() -> LevelCamera {
    let (cogX, cogY) = getCOG()
    let (startX, startY, endX, endY) =
    getActive(x: cogX, y: cogY, xView: levelViewW, yView: levelViewH,
              xMax: map.width, yMax: map.height)
    return LevelCamera(cogX: cogX, cogY: cogY,
                       startX: startX, startY: startY, endX: endX, endY: endY)
  }
  
  func changeLevel(delta : Int) {
    let newLevel = min(25, max(0, levelIndex + delta))
    loadLevel(index: newLevel)
  }
  
  func setPlayerPositions() {
    var x = 0
    var y = 0
    if let (ux,uy) = map.find(cell: .Up) {
      x = ux
      y = uy
    } else {
      x = 4
      y = 4
    }
    for i in 0..<numPlayers {
      let p = player[i]
      if p.isAlive() {
        let (px, py) = moveCoords(x: x, y: y, direction: Direction(rawValue: UInt8(i * 2))!)
        placeInWorld(index: i, x: px, y: py)
      }
    }
  }
  
  func placeInWorld(index: Int, x : Int, y : Int) {
    let p = player[index]
    // Debug.MyAssert(p.IsAlive());
    p.x = x
    p.y = y
    p.dir = Direction(rawValue: UInt8(index * 2))!
    map[p.x, p.y] = Cell(rawValue: Cell.Player0.rawValue + UInt8(index))!
    p.state = .Normal
    p.arrow.state = .none;
  }
  
  func move(stick: Int, dir: Direction) {
    if stick < 4 && dir != .None {
      if stick < numPlayers {
        let p = player[stick]
        p.dir = dir
        let delta = time - p.lastMoveTime
        if p.isVisible() && delta >= kTicksPerMove {
          p.lastMoveTime = time
          let (x, y) = moveCoords(x: p.x, y: p.y, direction: dir)
          let d = map[x,y]
          var bMove = false
          switch d  {
          case .Space:
            bMove = true
          case .Door:
            if p.keys > 0 {
              p.keys -= 1
              map.openDoor(x: x, y: y)
              bMove = true
            }
          case .Key:
            p.keys += 1
            bMove = true
          case .Food:
            p.food += 1
            bMove = true
          case .Money:
            p.score += 10
            bMove = true
          case .Bomb:
            p.bombs += 1
            bMove = true
          case .Down:
            p.state = .InWarp
            map[p.x, p.y] = .Space
            if isPartyInWarp() {
              changeLevel(delta: 1)
            }
          default:
            bMove = false
          }
          if bMove {
            map[p.x, p.y] = .Space
            map[x, y] = Cell(rawValue:Cell.Player0.rawValue + UInt8(stick))!
            p.x = x
            p.y = y
          }
        }
      }
    }
  }
  
  func isPartyInWarp() -> Bool {
    // At least one player in warp, and no players visible
    var atLeastOneWarp = false
    var atLeastOneVisible = false
    for i in 0..<numPlayers {
      if player[i].isVisible() {
        atLeastOneVisible = true
        break
      }
      if player[i].isAlive() && player[i].state == .InWarp {
        atLeastOneWarp = true
      }
    }
    if atLeastOneWarp && !atLeastOneVisible {
      return true
    }
    return false
  }
  
  func eatFood(index: Int)  {
    if index < numPlayers {
      let p = player[index]
      if p.isVisible() {
        p.eatFood()
      }
    }
  }
  
  func fire(index: Int) {
    if index < numPlayers {
      let p = player[index]
      if !p.arrow.alive {
        p.arrow.state = .triggered
        p.arrow.x = p.x;
        p.arrow.y = p.y;
        p.arrow.dir = p.dir;
      }
    }
  }
  
  func doArrowMove(p: Player) {
    var x = p.arrow.x
    var y = p.arrow.y
    switch p.arrow.state {
    case .none:
      return
    case .triggered:
      p.arrow.state = .inFlight
    case .inFlight:
      map[x, y] = .Space
    }
    (x, y) = moveCoords(x: x, y: y, direction: p.arrow.dir)
    let d = map[x,y]
    if p.arrow.canHit(c: d) {
      switch d {
      case .Bomb:
        doSmartBomb()
        map[x, y] = .Space
      case .Monster0, .Monster1, .Monster2, .Generator0, .Generator1, .Generator2:
        map[x, y] = .Space
      case .Heart:
        var foundPlayer = false
        for i in 0..<numPlayers {
          let p2 = player[i]
          if !p2.isAlive() {
            p2.health = HealthMax
            p2.state = .Normal
            placeInWorld(index: i, x: x, y: y)
            foundPlayer = true
            break
          }
        }
        if !foundPlayer {
          map[x, y] = .Monster2
        }
      default:
        _ = true
      }
      p.arrow.state = .none
    } else if p.arrow.canGo(c: d) {
      p.arrow.x = x
      p.arrow.y = y
      
      // Convert Direction to Cell arrow order. (Cell order is based on the
      // order in the dandy.png texture. Maybe we should reorder Cell and
      // the texture to match Direction
      let rotatedDir = (p.arrow.dir.rawValue + 3) & 7;
      map[x, y] = Cell(rawValue: Cell.Arrow0.rawValue + rotatedDir)!
    } else {
      p.arrow.state = .none
    }
  }
  
  func useSmartBomb(index: Int) {
    if index < numPlayers {
      let p = player[index]
      if p.bombs > 0 {
        p.bombs -= 1
        doSmartBomb()
      }
    } else {
      // Debug.MyDebugBreak();
    }
  }
  
  func doSmartBomb() {
    let cam = getLevelCamera()
    for y in cam.startY..<cam.endY {
      for x in cam.startX..<cam.endX {
        let d = map[x, y]
        if d.isEnemy() {
          // TODO: Increase score.
          map[x, y] = .Space
        }
      }
    }
  }
}
