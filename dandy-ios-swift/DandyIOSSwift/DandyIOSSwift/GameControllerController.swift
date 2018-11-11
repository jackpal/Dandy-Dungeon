//
//  GameControllerController.swift
//  DandyIOSSwift
//
//  Created by Jack Palevich on 11/11/18.
//  Copyright © 2018 JacksHacks. All rights reserved.
//

import GameController
import UIKit

class GameControllerController: NSObject {

  public private(set) var hasMiFiControllers : Bool {
    didSet {
      if oldValue != hasMiFiControllers {
          UIApplication.shared.isIdleTimerDisabled = hasMiFiControllers
      }
    }
  }

  override init() {
    hasMiFiControllers = false
    super.init()
  NotificationCenter.default.addObserver(self, selector: #selector(controllerDidConnect(notification:)), name: .GCControllerDidConnect, object: nil)
  NotificationCenter.default.addObserver(self, selector: #selector(controllerDidDisconnect(notification:)), name: .GCControllerDidDisconnect, object: nil)

    GCController.startWirelessControllerDiscovery {
      NSLog("Finished searching for wireless controllers")
    }

    updateActiveControllers()
  }

  @objc
  private func controllerDidConnect(notification:Notification) {
    self.updateActiveControllers()
  }

  @objc
  private func controllerDidDisconnect(notification:Notification) {
    self.updateActiveControllers()
  }

  private func updateActiveControllers() {
    hasMiFiControllers = !GCController.controllers().isEmpty
  }
}
