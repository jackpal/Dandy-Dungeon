//
//  GameControllerController.swift
//  DandyIOSSwift
//
//  Created by Jack Palevich on 11/11/18.
//  Copyright © 2018 JacksHacks. All rights reserved.
//

import GameController
import UIKit

import simd

protocol GameControllerDelegate {
  func move(player: Int, dir: Direction)
  func fire(player: Int)
  func eatFood(player: Int)
  func menu(player: Int)
}

class GameControllerController: NSObject {
  
  var delegate: GameControllerDelegate?
  
  // Gamepad
  private var gamePadCurrent: GCController?
  private var gamePadLeft: GCControllerDirectionPad?
  
  // Virtual Onscreen Controller
#if os( iOS )
  private var _virtualController: Any?
  @available(iOS 15.0, *)
  public var virtualController: GCVirtualController? {
    get { return self._virtualController as? GCVirtualController }
    set { self._virtualController = newValue }
  }
#endif
  
  var delta: CGPoint = CGPoint.zero
  var keyboard: GCKeyboard? = nil
  
  // See https://developer.apple.com/documentation/gamecontroller/supporting_game_controllers
  
  override init() {
    super.init()
    setupGameController()
  }
  
  private func setupGameController() {
    if #available(iOS 14.0, OSX 10.16, *) {
      NotificationCenter.default.addObserver(self, selector: #selector(self.handleMouseDidConnect),
                                             name: NSNotification.Name.GCMouseDidBecomeCurrent, object: nil)
      NotificationCenter.default.addObserver(self, selector: #selector(self.handleMouseDidDisconnect),
                                             name: NSNotification.Name.GCMouseDidStopBeingCurrent, object: nil)
      if let mouse = GCMouse.mice().first {
        registerMouse(mouse)
      }
    }
    
    NotificationCenter.default.addObserver(self, selector: #selector(self.handleKeyboardDidConnect),
                                           name: NSNotification.Name.GCKeyboardDidConnect, object: nil)
    
    NotificationCenter.default.addObserver(
      self, selector: #selector(self.handleControllerDidConnect),
      name: NSNotification.Name.GCControllerDidBecomeCurrent, object: nil)
    
    NotificationCenter.default.addObserver(
      self, selector: #selector(self.handleControllerDidDisconnect),
      name: NSNotification.Name.GCControllerDidStopBeingCurrent, object: nil)
    
#if os( iOS )
    if #available(iOS 15.0, *) {
      let virtualConfiguration = GCVirtualControllerConfiguration()
      virtualConfiguration.elements = [GCInputDirectionalDpad,
                                       GCInputButtonA,
                                       GCInputButtonB,
                                       GCInputButtonMenu]
      virtualController = GCVirtualController(configuration: virtualConfiguration)
      
      // Connect to the virtual controller if no physical controllers are available.
      if GCController.controllers().isEmpty {
        virtualController?.connect()
      }
    }
#endif
    
    guard let controller = GCController.controllers().first else {
      return
    }
    registerGameController(controller)
  }
  
  @objc
  func handleKeyboardDidConnect(_ notification: Notification) {
    guard let keyboard = notification.object as? GCKeyboard else {
      return
    }
    weak var weakController = self
    
    keyboard.keyboardInput?.button(forKeyCode: .spacebar)?.valueChangedHandler = {
      (_ button: GCDeviceButtonInput, _ value: Float, _ pressed: Bool) -> Void in
      guard let strongController = weakController else {
        return
      }
      if pressed {
        strongController.controllerAttack()
      }
    }
    keyboard.keyboardInput?.button(forKeyCode: .keyF)?.valueChangedHandler = {
      (_ button: GCDeviceButtonInput, _ value: Float, _ pressed: Bool) -> Void in
      guard let strongController = weakController else {
        return
      }
      if pressed {
        strongController.controllerEatFood()
      }
    }
    keyboard.keyboardInput?.button(forKeyCode: .escape)?.valueChangedHandler = {
      (_ button: GCDeviceButtonInput, _ value: Float, _ pressed: Bool) -> Void in
      guard let strongController = weakController else {
        return
      }
      if pressed {
        strongController.controllerMenu()
      }
    }
  }
  
  @objc
  func handleMouseDidConnect(_ notification: Notification) {
    if #available(iOS 14.0, OSX 10.16, *) {
      guard let mouse = notification.object as? GCMouse else {
        return
      }
      
      unregisterMouse()
      registerMouse(mouse)
      
    }
  }
  
  @objc
  func handleMouseDidDisconnect(_ notification: Notification) {
    unregisterMouse()
  }
  
  func unregisterMouse() {
    delta = CGPoint.zero
  }
  
  func registerMouse(_ mouseDevice: GCMouse) {
    if #available(iOS 14.0, OSX 10.16, *) {
      guard let mouseInput = mouseDevice.mouseInput else {
        return
      }
      
      weak var weakController = self
      mouseInput.mouseMovedHandler = {(_ mouse: GCMouseInput, _ deltaX: Float, _ deltaY: Float) -> Void in
        guard let strongController = weakController else {
          return
        }
        strongController.delta = CGPoint(x: CGFloat(deltaX), y: CGFloat(deltaY))
      }
      
      mouseInput.leftButton.valueChangedHandler = {
        (_ button: GCControllerButtonInput, _ value: Float, _ pressed: Bool) -> Void in
        guard let strongController = weakController else {
          return
        }
        
        strongController.controllerAttack()
      }
    }
  }
  
  @objc
  func handleControllerDidConnect(_ notification: Notification) {
    guard let gameController = notification.object as? GCController else {
      return
    }
    unregisterGameController()
    
#if os( iOS )
    if #available(iOS 15.0, *) {
      if gameController != virtualController?.controller {
        virtualController?.disconnect()
      }
    }
#endif
    
    registerGameController(gameController)
  }
  
  @objc
  func handleControllerDidDisconnect(_ notification: Notification) {
    unregisterGameController()
    
#if os( iOS )
    if #available(iOS 15.0, *) {
      if GCController.controllers().isEmpty {
        virtualController?.connect()
      }
    }
#endif
  }
  
  func registerGameController(_ gameController: GCController) {
    
    var buttonFire: GCControllerButtonInput?
    var buttonEatFood: GCControllerButtonInput?
    var buttonMenu: GCControllerButtonInput?
    
    weak var weakController = self
    gamePadCurrent = gameController
    
    if let gamepad = gameController.extendedGamepad {
      self.gamePadLeft = gamepad.dpad
      buttonFire = gamepad.buttonA
      buttonEatFood = gamepad.buttonB
      buttonMenu = gamepad.buttonMenu
    } else if let gamepad = gameController.microGamepad {
      self.gamePadLeft = gamepad.dpad
      buttonFire = gamepad.buttonA
      buttonEatFood = gamepad.buttonX
      buttonMenu = gamepad.buttonMenu
    }
    
    buttonFire?.valueChangedHandler = {(_ button: GCControllerButtonInput, _ value: Float, _ pressed: Bool) -> Void in
      guard let strongController = weakController else {
        return
      }
      if pressed {
        strongController.controllerAttack()
      }
    }
    
    buttonEatFood?.valueChangedHandler = {(_ button: GCControllerButtonInput, _ value: Float, _ pressed: Bool) -> Void in
      guard let strongController = weakController else {
        return
      }
      if pressed {
        strongController.controllerEatFood()
      }
    }
    
    buttonMenu?.valueChangedHandler = {(_ button: GCControllerButtonInput, _ value: Float, _ pressed: Bool) -> Void in
      guard let strongController = weakController else {
        return
      }
      if pressed {
        strongController.controllerMenu()
      }
    }  }
  
  func unregisterGameController() {
    gamePadLeft = nil
    gamePadCurrent = nil
  }
  
  func pollInput() {
    var characterDirection : simd_float2
    
    if let gamePadLeft = self.gamePadLeft {
      characterDirection = simd_make_float2(gamePadLeft.xAxis.value, -gamePadLeft.yAxis.value)
    } else {
      characterDirection = simd_make_float2(0)
    }
    
    // Mouse
    // let mouseSpeed: CGFloat = 0.02
    // self.cameraDirection += simd_make_float2(-Float(self.delta.x * mouseSpeed), Float(self.delta.y * mouseSpeed))
    // self.delta = CGPoint.zero
    
    // Keyboard
    if let keyboard = GCKeyboard.coalesced?.keyboardInput {
      if keyboard.button(forKeyCode: .keyA)?.isPressed ?? false { characterDirection.x = -1.0 }
      if keyboard.button(forKeyCode: .keyD)?.isPressed ?? false { characterDirection.x = 1.0 }
      if keyboard.button(forKeyCode: .keyW)?.isPressed ?? false { characterDirection.y = -1.0 }
      if keyboard.button(forKeyCode: .keyS)?.isPressed ?? false { characterDirection.y = 1.0 }
      
      if keyboard.button(forKeyCode: .leftArrow)?.isPressed ?? false { characterDirection.x = -1.0 }
      if keyboard.button(forKeyCode: .rightArrow)?.isPressed ?? false { characterDirection.x = 1.0 }
      if keyboard.button(forKeyCode: .upArrow)?.isPressed ?? false { characterDirection.y = -1.0 }
      if keyboard.button(forKeyCode: .downArrow)?.isPressed ?? false { characterDirection.y = 1.0 }
      
      // self.runModifier = (keyboard.button(forKeyCode: .leftShift)?.value ?? 0.0) + 1.0
    }
    let dir = Direction.direction(deltaX: characterDirection.x, deltaY: characterDirection.y)
    delegate?.move(player:0, dir:dir)
  }
  
  // MARK: - Controlling the Character
  
  func controllerEatFood() {
    delegate?.eatFood(player: 0)
  }
  
  func controllerAttack() {
    delegate?.fire(player: 0)
  }
  
  func controllerMenu() {
    delegate?.menu(player: 0)
  }
  
}
