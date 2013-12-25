//
//  Shader.vsh
//  Dandy
//
//  Created by Jack Palevich on 12/24/13.
//  Copyright (c) 2013 Jack Palevich. All rights reserved.
//

attribute vec2 position;
attribute vec2 texCoord;

varying vec2 vTexCoord;

uniform mat4 modelViewProjectionMatrix;

void main()
{
    vTexCoord = texCoord;
    
    gl_Position = modelViewProjectionMatrix * vec4(position, 0.0, 1.0);
}
