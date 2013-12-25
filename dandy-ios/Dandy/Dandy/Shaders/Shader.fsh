//
//  Shader.fsh
//  Dandy
//
//  Created by Jack Palevich on 12/24/13.
//  Copyright (c) 2013 Jack Palevich. All rights reserved.
//

varying lowp vec4 colorVarying;

void main()
{
    gl_FragColor = colorVarying;
}
