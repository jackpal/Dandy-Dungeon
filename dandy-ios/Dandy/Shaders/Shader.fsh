//
//  Shader.fsh
//  Dandy
//
//  Created by Jack Palevich on 12/24/13.
//  Copyright (c) 2013 Jack Palevich. All rights reserved.
//

varying mediump vec2 vTexCoord;
uniform sampler2D texture;

void main()
{
    gl_FragColor = texture2D(texture,vTexCoord);
}
