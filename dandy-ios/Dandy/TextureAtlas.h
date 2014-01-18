//
//  TextureAtlas.h
//  Dandy
//
//  Created by Jack Palevich on 12/26/13.
//  Copyright (c) 2013 Jack Palevich. All rights reserved.
//

#import <Foundation/Foundation.h>

@interface TextureAtlas : NSObject

- (id)initTextureWidth:(NSInteger)textureWidth
         textureHeight:(NSInteger)textureHeight
          elementWidth:(NSInteger)elementWidth
         elementHeight:(NSInteger)elementHeight
          elementCount:(NSInteger)elementCount;

// Returns [u0 v0 u1 v1]
- (void)getUvs:(GLfloat *)buffer forElementIndex:(NSInteger)index;

@end
