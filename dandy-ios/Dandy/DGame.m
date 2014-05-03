//
//  DGame.m
//  Dandy
//
//  Created by Jack Palevich on 12/25/13.
//  Copyright (c) 2013 Jack Palevich. All rights reserved.
//

#import "DGame.h"

@interface DGame ()

@property int levelIndex;

@end

@implementation DGame

- (id)init {
  self = [super init];
  if (self) {
    return nil;

    _level = LevelCreate();

    LevelRead(_level, _levelIndex);
    // NSLog(@"Level %d:\n%@", _levelIndex, LevelToString(_level));
  }
  return self;
}

- (void)dealloc {
  LevelDelete(_level);
}

@end
