//
//  DLevel.m
//  Dandy
//
//  Created by Jack Palevich on 12/24/13.
//  Copyright (c) 2013 Jack Palevich. All rights reserved.
//

#import "Level.h"
#import "math.h"

Level LevelCreate(){
  return (Level) malloc(LEVEL_WIDTH*LEVEL_HEIGHT*sizeof(Cell));
}

void LevelDelete(Level level) {
  if (level) {
    free(level);
  }
}

void LevelRead(Level level, int index) {
  NSString *resourceName = [NSString stringWithFormat:@"%c", 'a' + index];
  NSString *filePath = [[NSBundle mainBundle] pathForResource:resourceName
                                                       ofType:@"bin"];
  NSData *data = [NSData dataWithContentsOfFile:filePath];
  const Byte *packedLevelData = [data bytes];
  Cell* dest = level;
  for (int y = 0; y < LEVEL_HEIGHT; y++) {
    for (int x = 0; x < LEVEL_WIDTH; x += 2) {
      Byte d = *packedLevelData++;
      *dest++ = (Cell) (d & 15);
      *dest++ = (Cell) (d >> 4);
    }
  }
}

bool LevelFind(Level level, Cell cell, int* pX, int* pY) {
  for (int y = 0; y < LEVEL_HEIGHT; y++) {
    for (int x = 0; x < LEVEL_WIDTH; x++) {
      if(level[x + y * LEVEL_WIDTH] == cell) {
        if (pX) {
          *pX = x;
        }
        if (pY) {
          *pY = y;
        }
        return true;
      }
    }
  }
  return false;

}

void LevelOpenDoor(Level level, int x, int y) {
  // Flood fill from this coord
  int index = x + y * LEVEL_WIDTH;
  if (level[index] == kDoor) {
    level[index] = kSpace;
    for (int dy = -1;dy <= 1; dy++) {
      for (int dx = -1;dx <= 1; dx++) {
        if (dx != 0 || dy != 0) {
          LevelOpenDoor(level, x + dx, y + dy);
        }
      }
    }
  }
}

NSString* CellToNSString(Cell c) {
  static NSArray *cellToChar;
  static dispatch_once_t onceToken;
  dispatch_once(&onceToken, ^{
      cellToChar = @[
        @" ",
        @"*",
        @"D",
        @"u",
        @"d",
        @"k",
        @"f",
        @"$",
        @"i",
        @"1",
        @"2",
        @"3",
        @"♡",
        @"n",
        @"o",
        @"p",
        @"↑",
        @"↗",
        @"→",
        @"↘",
        @"↓",
        @"↙",
        @"←",
        @"↖",
        @"P",
        @"Q",
        @"R",
        @"S"
        ];
  });
  return cellToChar[c];
}

NSString *LevelToString(Level level) {
  NSMutableString *s = [NSMutableString stringWithCapacity:(LEVEL_WIDTH + 1) * LEVEL_HEIGHT];
  const Cell* c = level;
  for (int y = 0; y < LEVEL_HEIGHT; y++) {
    for (int x = 0; x < LEVEL_WIDTH; x++) {
      [s appendString:CellToNSString(*c++)];
    }
    [s appendString:@"\n"];
  }
  return s;
}

static void ActiveBoundsHelper(int x, int* left, int* right, int width, int viewWidth) {
  x -= (viewWidth / 2);
  x = MAX(x, 0);
  x = MIN(x, width - viewWidth);
  if (left) {
    *left = x;
  }
  if (right) {
    *right = MIN(x + viewWidth + 1, width);
  }
}

void LevelGetActiveBounds(int x, int y, int* left, int* top, int* right, int* bottom){
  ActiveBoundsHelper(x, left, right, LEVEL_WIDTH, LEVEL_VIEW_WIDTH);
  ActiveBoundsHelper(y, top, bottom, LEVEL_HEIGHT, LEVEL_VIEW_HEIGHT);
}
