//
//  DLevel.h
//  Dandy
//
//  Created by Jack Palevich on 12/24/13.
//  Copyright (c) 2013 Jack Palevich. All rights reserved.
//

#import <Foundation/Foundation.h>

NS_ENUM(unsigned char, _Cell) {
  kSpace,
  kWall,
  kDoor,
  kUp,
  kDown,
  kKey,
  kFood,
  kMoney,
  kBomb,
  kMonster1,
  kMonster2,
  kMonster3,
  kHeart,
  kGenerator1,
  kGenerator2,
  kGenerator3,
  kArrow, // 8 arrows
  kPlayer = kArrow + 8 // 4 players
};
typedef enum _Cell Cell;

#define LEVEL_WIDTH 60
#define LEVEL_HEIGHT 30

#define LEVEL_VIEW_WIDTH 20
#define LEVEL_VIEW_HEIGHT 10

typedef Cell *Level;

CG_INLINE bool LevelInBounds(int x, int y) {
  return x >= 0 && x < LEVEL_WIDTH && y >= 0 && y < LEVEL_HEIGHT;
}

#ifdef DEBUG
#define CHECK_LEVEL_BOUNDS 1
#endif

#ifdef CHECK_LEVEL_BOUNDS

CG_INLINE void LevelCheckBounds(int x, int y) {
  if (!LevelInBounds(x, y)) {
    @throw([NSException
            exceptionWithName: @"IndexOutOfBounds"
            reason:[NSString stringWithFormat:@"x:%d y:%d", x, y]
            userInfo:nil ]);
  }
}

#else

CG_INLINE void LevelCheckBounds(int x, int y) {}

#endif

CG_INLINE int LevelXYToIndex(int x, int y) {
  LevelCheckBounds(x,y);
  return x + y * LEVEL_WIDTH;
}

CG_INLINE Cell LevelAt(Level level, int x, int y) {
  return level[LevelXYToIndex(x,y)];
}

CG_INLINE void LevelAtPut(Level level, int x, int y, Cell data) {
  level[LevelXYToIndex(x,y)] = data;
}

Level LevelCreate();

void LevelRead(Level level, int index);

bool LevelFind(Level level, Cell cell, int* pX, int* pY);

void LevelOpenDoor(Level level, int x, int y);

void LevelDelete(Level level);

NSString *LevelToString(Level level);

// x,y are the desired center-of-view. left-top-right-bottom are the bounds
// clipped to [0..LEVEL_WIDTH] in x and [0..LEVEL_HEIGHT] in y.
void LevelGetActiveBounds(int x, int y, int* left, int* top, int* right, int* bottom);

