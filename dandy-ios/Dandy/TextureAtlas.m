//
//  TextureAtlas.m
//  Dandy
//
//  Created by Jack Palevich on 12/26/13.
//  Copyright (c) 2013 Jack Palevich. All rights reserved.
//

#import "TextureAtlas.h"

@interface TextureAtlas ()

@property (nonatomic) NSInteger textureWidth;
@property (nonatomic) NSInteger textureHeight;
@property (nonatomic) NSInteger elementWidth;
@property (nonatomic) NSInteger elementHeight;
@property (nonatomic) NSInteger elementCount;

@property (nonatomic) NSInteger elementStride;
@property (nonatomic) GLfloat elementU;
@property (nonatomic) GLfloat elementV;

@end

@implementation TextureAtlas
-(id) initTextureWidth:(NSInteger)textureWidth
         textureHeight:(NSInteger)textureHeight
          elementWidth:(NSInteger)elementWidth
         elementHeight:(NSInteger)elementHeight
          elementCount:(NSInteger)elementCount
{
  self = [super init];
  if (self) {
    _textureWidth = textureWidth;
    _textureHeight = textureHeight;
    _elementWidth = elementWidth;
    _elementHeight = elementHeight;
    _elementCount = elementCount;
    _elementStride = textureWidth / elementWidth;
    _elementU = ((GLfloat) elementWidth) / ((GLfloat) textureWidth);
    _elementV = ((GLfloat) elementHeight) / ((GLfloat) textureHeight);
  }
  return self;
}

-(void) getUvs:(GLfloat*)buffer forElementIndex:(NSInteger) index {
  if (index < 0 || index >= _elementCount) {
    @throw([NSException
            exceptionWithName: @"IndexOutOfBounds"
            reason:[NSString stringWithFormat:@"index:%d", index]
            userInfo:nil ]);
  }
  NSInteger y = index / _elementStride;
  NSInteger x = index - y * _elementStride;
  buffer[0] = _elementU * x;
  buffer[1] = _elementV * y;
  buffer[2] = _elementU * (x + 1);
  buffer[3] = _elementV * (y + 1);
}

@end
