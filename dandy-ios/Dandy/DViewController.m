//
//  DViewController.m
//  Dandy
//
//  Created by Jack Palevich on 12/24/13.
//  Copyright (c) 2013 Jack Palevich. All rights reserved.
//

#import "DViewController.h"
#import "DGame.h"
#import "Level.h"
#import "TextureAtlas.h"

#define BUFFER_OFFSET(i) ((char *)NULL + (i))

// Uniform index.
enum {
  UNIFORM_MODELVIEWPROJECTION_MATRIX,
  NUM_UNIFORMS
};
GLint uniforms[NUM_UNIFORMS];

GLint textureUniform;

// Attribute index.
enum {
  ATTRIB_VERTEX,
  ATTRIB_UV,
  NUM_ATTRIBUTES
};

typedef struct {
  GLfloat x, y, u, v;
} TileVertex;

const int TILES = (LEVEL_VIEW_WIDTH + 1) * (LEVEL_VIEW_HEIGHT + 1);
const int VERTS_PER_TILE = 6;

TileVertex gTileVertexData[TILES * VERTS_PER_TILE];

@interface DViewController () {
  GLuint _program;

  GLKMatrix4 _modelViewProjectionMatrix;

  GLuint _vertexArray;
  GLuint _vertexBuffer;

  // In GL window coordinate system. This is frame buffer pixels. On retina
  // displays this will be higher resolution than IOS view system coordinates.
  // Also (0,0) is the lower-left-hand corner.
  GLfloat _scissorX;
  GLfloat _scissorY;
  GLfloat _scissorW;
  GLfloat _scissorH;

  // In GL viewport coordinates, which we set equal to IOS view
  // system coordinates.
  GLfloat _gameX;
  GLfloat _gameY;

  // In GL viewport coordinates, which we set equal to IOS view
  // system coordinates.
  GLfloat _tileW;
  GLfloat _tileH;

  // Offset of game center of interest
  GLfloat _gameOffsetX;
  GLfloat _gameOffsetY;
}
@property(strong, nonatomic) EAGLContext *context;
@property(strong, nonatomic) DGame *game;
@property(strong, nonatomic) GLKTextureInfo *texture;
@property(strong, nonatomic) TextureAtlas *textureAtlas;

- (void)setupGL;
- (void)tearDownGL;

- (BOOL)loadShaders;
- (BOOL)compileShader:(GLuint *)shader type:(GLenum)type file:(NSString *)file;
- (BOOL)linkProgram:(GLuint)prog;
- (BOOL)validateProgram:(GLuint)prog;
@end

@implementation DViewController

- (void)viewDidLoad {
  [super viewDidLoad];

  self.preferredFramesPerSecond = 60;

  self.game = [[DGame alloc] init];
  self.context = [[EAGLContext alloc] initWithAPI:kEAGLRenderingAPIOpenGLES2];

  if (!self.context) {
    NSLog(@"Failed to create ES context");
  }

  GLKView *view = (GLKView *)self.view;
  view.context = self.context;

  [self setupGL];
}

- (void)didRotateFromInterfaceOrientation:(UIInterfaceOrientation)orientation {
  [super didRotateFromInterfaceOrientation:orientation];
  // Ensures we recalculate the tile geometry.
  _tileW = 0;
}

- (void)dealloc {
  [self tearDownGL];

  if ([EAGLContext currentContext] == self.context) {
    [EAGLContext setCurrentContext:nil];
  }
}

- (void)didReceiveMemoryWarning {
  [super didReceiveMemoryWarning];

  if ([self isViewLoaded] && ([[self view] window] == nil)) {
    self.view = nil;

    [self tearDownGL];

    if ([EAGLContext currentContext] == self.context) {
      [EAGLContext setCurrentContext:nil];
    }
    self.context = nil;
  }

  // Dispose of any resources that can be recreated.
}

- (void)ensureViewGeometry {
  if (_tileW != 0) {
    return;
  }
  int iosViewWidth = self.view.bounds.size.width;
  int iosViewHeight = self.view.bounds.size.height;

  // In OpenGL window coordinate system -- pixels, (0,0) is lower left
  _scissorX = 0.0f;
  _scissorY = 0.0f;
  _scissorW = iosViewWidth;
  _scissorH = iosViewHeight;
  float viewAspect =
      fabsf(self.view.bounds.size.width / self.view.bounds.size.height);
  float gameH = _scissorH;
  float gameW = _scissorW;
  // Compute the largest 8:5 aspect ratio rectangle that can fit in the view.
  float gameAspect = 8.0f / 5.0f;
  if (viewAspect >= gameAspect) {
    // View is wider than it needs to be. Center game horizontally.
    gameW = gameAspect * gameH;
    _scissorX = (_scissorW - gameW) * 0.5f;
    _scissorW = gameW;
  } else {
    // View is taller than it needs to be. Center game vertically.
    gameH = gameW / gameAspect;
    _scissorY = (_scissorH - gameH) * 0.5f;
    _scissorH = gameH;
  }

  _gameX = _scissorX;
  _gameY = _scissorY;

  _tileW = gameW / 20.0f;
  _tileH = gameH / 10.0f;

  // Calculate scale factor between view system coordinates and OpenGL coords
  float uiToPixelScale = [[UIScreen mainScreen] scale];
  _scissorX *= uiToPixelScale;
  _scissorY *= uiToPixelScale;
  _scissorW *= uiToPixelScale;
  _scissorH *= uiToPixelScale;
}

- (void)setupGL {
  [EAGLContext setCurrentContext:self.context];

  [self loadShaders];
  [self loadTextures];

  glGenVertexArraysOES(1, &_vertexArray);
  glGenBuffers(1, &_vertexBuffer);
}

- (void)tearDownGL {
  [EAGLContext setCurrentContext:self.context];

  glDeleteBuffers(1, &_vertexBuffer);
  glDeleteVertexArraysOES(1, &_vertexArray);

  if (_program) {
    glDeleteProgram(_program);
    _program = 0;
  }
}

- (void)loadTextures {
  NSString *filePath =
      [[NSBundle mainBundle] pathForResource:@"dandy" ofType:@"png"];
  self.texture = [GLKTextureLoader textureWithContentsOfFile:filePath
                                                     options:nil
                                                       error:nil];
  self.textureAtlas = [[TextureAtlas alloc] initTextureWidth:self.texture.width
                                               textureHeight:self.texture.height
                                                elementWidth:16
                                               elementHeight:16
                                                elementCount:28];
  glActiveTexture(GL_TEXTURE0);
  glBindTexture(self.texture.target, self.texture.name);
  // For that aliased look.
  glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
  glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
}

- (void)calcVertexData {
  TileVertex *pTile = gTileVertexData;
  Level level = _game.level;
  int tileLeft;
  int tileTop;
  int tileRight;
  int tileBottom;
  int cogX = LEVEL_VIEW_WIDTH / 2 - _gameOffsetX / _tileW;
  int cogY = LEVEL_VIEW_HEIGHT / 2 - _gameOffsetY / _tileH;
  LevelGetActiveBounds(cogX, cogY, &tileLeft, &tileTop, &tileRight,
                       &tileBottom);
  int tileViewWidth = tileRight - tileLeft;
  int tileViewHeight = tileBottom - tileTop;
  for (int y = 0; y < tileViewHeight; y++) {
    for (int x = 0; x < tileViewWidth; x++) {
      int vtx = x + tileLeft;
      int vty = y + tileTop;

      Cell cell = LevelAt(level, vtx, vty);

      GLfloat buffer[4];
      [self.textureAtlas getUvs:buffer forElementIndex:cell];

      // TODO: switch to indexed mesh to avoid duplicating verts a and d

      //    u
      //  a--b
      // v |\ |
      //  | \|
      //  c--d
      // Triangles a b d a d c

      GLfloat x0 = _tileW * vtx;
      GLfloat x1 = _tileW * (vtx + 1);
      GLfloat y0 = _tileH * vty;
      GLfloat y1 = _tileH * (vty + 1);

      GLfloat u0 = buffer[0];
      GLfloat v0 = buffer[1];
      GLfloat u1 = buffer[2];
      GLfloat v1 = buffer[3];

      TileVertex a = {x0, y0, u0, v0};
      TileVertex b = {x1, y0, u1, v0};
      TileVertex c = {x0, y1, u0, v1};
      TileVertex d = {x1, y1, u1, v1};

      *pTile++ = a;
      *pTile++ = b;
      *pTile++ = d;

      *pTile++ = a;
      *pTile++ = d;
      *pTile++ = c;
    }
  }
}

#pragma mark - GLKView and GLKViewController delegate methods

- (void)update {
  [self ensureViewGeometry];
  float width = self.view.bounds.size.width;
  float height = self.view.bounds.size.height;
  float left = -_gameX;
  float right = left + width;
  float top = -_gameY;
  float bottom = top + height;
  GLKMatrix4 projectionMatrix =
      GLKMatrix4MakeOrtho(left, right, bottom, top, 0.1f, 10.0f);

  GLKMatrix4 baseModelViewMatrix =
      GLKMatrix4MakeTranslation(_gameOffsetX, _gameOffsetY, -4.0f);

  // Compute the model view matrix for the object rendered with ES2
  GLKMatrix4 modelViewMatrix = GLKMatrix4MakeTranslation(0.0f, 0.0f, 1.5f);
  modelViewMatrix = GLKMatrix4Multiply(baseModelViewMatrix, modelViewMatrix);

  _modelViewProjectionMatrix =
      GLKMatrix4Multiply(projectionMatrix, modelViewMatrix);
}

- (void)glkView:(GLKView *)view drawInRect:(CGRect)rect {
  glClearColor(0.0f, 0.0f, 0.0f, 1.0f);
  glClear(GL_COLOR_BUFFER_BIT);

  [self calcVertexData];

  glBindVertexArrayOES(_vertexArray);
  glBindBuffer(GL_ARRAY_BUFFER, _vertexBuffer);
  glBufferData(GL_ARRAY_BUFFER, sizeof(gTileVertexData), gTileVertexData,
               GL_DYNAMIC_DRAW);

  glEnableVertexAttribArray(GLKVertexAttribPosition);
  glVertexAttribPointer(GLKVertexAttribPosition, 2, GL_FLOAT, GL_FALSE,
                        sizeof(TileVertex), BUFFER_OFFSET(0));
  glEnableVertexAttribArray(GLKVertexAttribTexCoord0);
  glVertexAttribPointer(GLKVertexAttribTexCoord0, 2, GL_FLOAT, GL_FALSE,
                        sizeof(TileVertex), BUFFER_OFFSET(8));

  glUseProgram(_program);

  glUniformMatrix4fv(uniforms[UNIFORM_MODELVIEWPROJECTION_MATRIX], 1, 0,
                     _modelViewProjectionMatrix.m);
  glUniform1i(textureUniform, 0);

  glScissor(_scissorX, _scissorY, _scissorW, _scissorH);
  glEnable(GL_SCISSOR_TEST);
  glDrawArrays(GL_TRIANGLES, 0, sizeof(gTileVertexData) / sizeof(TileVertex));
  glDisable(GL_SCISSOR_TEST);
}

#pragma mark - OpenGL ES 2 shader compilation

- (BOOL)loadShaders {
  GLuint vertShader, fragShader;
  NSString *vertShaderPathname, *fragShaderPathname;

  // Create shader program.
  _program = glCreateProgram();

  // Create and compile vertex shader.
  vertShaderPathname =
      [[NSBundle mainBundle] pathForResource:@"Shader" ofType:@"vsh"];
  if (![self compileShader:&vertShader
                      type:GL_VERTEX_SHADER
                      file:vertShaderPathname]) {
    NSLog(@"Failed to compile vertex shader");
    return NO;
  }

  // Create and compile fragment shader.
  fragShaderPathname =
      [[NSBundle mainBundle] pathForResource:@"Shader" ofType:@"fsh"];
  if (![self compileShader:&fragShader
                      type:GL_FRAGMENT_SHADER
                      file:fragShaderPathname]) {
    NSLog(@"Failed to compile fragment shader");
    return NO;
  }

  // Attach vertex shader to program.
  glAttachShader(_program, vertShader);

  // Attach fragment shader to program.
  glAttachShader(_program, fragShader);

  // Bind attribute locations.
  // This needs to be done prior to linking.
  glBindAttribLocation(_program, GLKVertexAttribPosition, "position");
  glBindAttribLocation(_program, GLKVertexAttribTexCoord0, "texCoord");

  // Link program.
  if (![self linkProgram:_program]) {
    NSLog(@"Failed to link program: %d", _program);

    if (vertShader) {
      glDeleteShader(vertShader);
      vertShader = 0;
    }
    if (fragShader) {
      glDeleteShader(fragShader);
      fragShader = 0;
    }
    if (_program) {
      glDeleteProgram(_program);
      _program = 0;
    }

    return NO;
  }

  // Get uniform locations.
  uniforms[UNIFORM_MODELVIEWPROJECTION_MATRIX] =
      glGetUniformLocation(_program, "modelViewProjectionMatrix");
  textureUniform = glGetUniformLocation(_program, "texture");

  // Release vertex and fragment shaders.
  if (vertShader) {
    glDetachShader(_program, vertShader);
    glDeleteShader(vertShader);
  }
  if (fragShader) {
    glDetachShader(_program, fragShader);
    glDeleteShader(fragShader);
  }

  return YES;
}

- (BOOL)compileShader:(GLuint *)shader type:(GLenum)type file:(NSString *)file {
  GLint status;
  const GLchar *source;

  source = (GLchar *)[[NSString stringWithContentsOfFile:file
                                                encoding:NSUTF8StringEncoding
                                                   error:nil] UTF8String];
  if (!source) {
    NSLog(@"Failed to load vertex shader");
    return NO;
  }

  *shader = glCreateShader(type);
  glShaderSource(*shader, 1, &source, NULL);
  glCompileShader(*shader);

#if defined(DEBUG)
  GLint logLength;
  glGetShaderiv(*shader, GL_INFO_LOG_LENGTH, &logLength);
  if (logLength > 0) {
    GLchar *log = (GLchar *)malloc(logLength);
    glGetShaderInfoLog(*shader, logLength, &logLength, log);
    NSLog(@"Shader compile log:\n%s", log);
    free(log);
  }
#endif

  glGetShaderiv(*shader, GL_COMPILE_STATUS, &status);
  if (status == 0) {
    glDeleteShader(*shader);
    return NO;
  }

  return YES;
}

- (BOOL)linkProgram:(GLuint)prog {
  GLint status;
  glLinkProgram(prog);

#if defined(DEBUG)
  GLint logLength;
  glGetProgramiv(prog, GL_INFO_LOG_LENGTH, &logLength);
  if (logLength > 0) {
    GLchar *log = (GLchar *)malloc(logLength);
    glGetProgramInfoLog(prog, logLength, &logLength, log);
    NSLog(@"Program link log:\n%s", log);
    free(log);
  }
#endif

  glGetProgramiv(prog, GL_LINK_STATUS, &status);
  if (status == 0) {
    return NO;
  }

  return YES;
}

- (BOOL)validateProgram:(GLuint)prog {
  GLint logLength, status;

  glValidateProgram(prog);
  glGetProgramiv(prog, GL_INFO_LOG_LENGTH, &logLength);
  if (logLength > 0) {
    GLchar *log = (GLchar *)malloc(logLength);
    glGetProgramInfoLog(prog, logLength, &logLength, log);
    NSLog(@"Program validate log:\n%s", log);
    free(log);
  }

  glGetProgramiv(prog, GL_VALIDATE_STATUS, &status);
  if (status == 0) {
    return NO;
  }

  return YES;
}

#pragma mark - touch input

- (void)touchesBegan:(NSSet *)touches withEvent:(UIEvent *)event {
  [super touchesBegan:touches withEvent:event];
  // NSLog(@"TouchesBegan ");
}

- (void)touchesMoved:(NSSet *)touches withEvent:(UIEvent *)event {
  [super touchesMoved:touches withEvent:event];
  // NSLog(@"touchesMoved ");
  UITouch *aTouch = [touches anyObject];
  UIView *view = self.view;
  CGPoint loc = [aTouch locationInView:view];
  CGPoint prevloc = [aTouch previousLocationInView:view];
  _gameOffsetX += (loc.x - prevloc.x);
  _gameOffsetY += (loc.y - prevloc.y);
}

- (void)touchesEnded:(NSSet *)touches withEvent:(UIEvent *)event {
  [super touchesEnded:touches withEvent:event];
  // NSLog(@"touchesEnded ");
}

- (void)touchesCancelled:(NSSet *)touches withEvent:(UIEvent *)event {
  [super touchesCancelled:touches withEvent:event];
  // NSLog(@"touchesCancelled ");
}

@end
