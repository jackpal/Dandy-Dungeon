//
//  DLevel.m
//  Dandy
//
//  Created by Jack Palevich on 12/24/13.
//  Copyright (c) 2013 Jack Palevich. All rights reserved.
//

#import "Level.h"

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