//
//  Shader.fsh
//  Dandy
//
//  Created by Jack Palevich on 12/24/13.
//  Copyright (c) 2013 Jack Palevich. All rights reserved.
//

precision mediump float;

varying vec2 vTexCoord;

void main()
{
    gl_FragColor = vec4(vTexCoord,0.5,1.0);
}
