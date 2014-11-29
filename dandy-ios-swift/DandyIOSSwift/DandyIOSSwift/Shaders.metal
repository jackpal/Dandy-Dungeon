#include <metal_stdlib>

using namespace metal;

struct TileUniforms {
  float2 offset;
  float2 tileSize; // Size of a particular tile
  float2 tileUVSize; // size in (u,v) of a tile
  uint tileStride;
  uint atlasStride;
  uchar2 indexToXY[6];
};

struct TileVertexIn
{
  uchar atlasIndex;
};

struct TileVertexInOut
{
    float4  position [[position]];
    half2  uv [[user(texturecoord)]];
};

// This specialized shader takes a list of tiles and a vertex index and
// generates a mesh.
//
//  [0] ---- [1][4]
//   |        //|
//   |       // |
//   |      //  |
//   |     //   |
//   |    //    |
//   |   //     |
//   |  //      |
//   | //       |
//   |//        |
// [2][3] ---- [5]

vertex TileVertexInOut tileVertex(uint vid [[ vertex_id ]],
                                  constant uchar* pAtlasIndex  [[ buffer(0) ]],
                                  constant TileUniforms& uniforms [[ buffer(1) ]])
{
  TileVertexInOut outVertex;

  float2 offset = uniforms.offset;
  uint tileStride = uniforms.tileStride;
  uint atlasStride = uniforms.atlasStride;
  float2 tileSize = uniforms.tileSize;
  float2 tileUVSize = uniforms.tileUVSize;

  uint tileID = vid / 6;
  uint vertIndex = vid - 6 * tileID;

  uchar2 indexToXY = uniforms.indexToXY[vertIndex];

  uint tileY = tileID / tileStride;
  uint tileX = tileID - tileY * tileStride;

  uchar atlasIndex = pAtlasIndex[tileID];
  uchar atlasY = atlasIndex / atlasStride;
  uchar atlasX = atlasIndex - atlasY * atlasStride;

  uchar2 xy = indexToXY[vertIndex];

  outVertex.position = float4(offset.x + (tileX + xy.x) * tileSize.x,
                              offset.y + (tileY + xy.y) * tileSize.y,
                              0, 1);
  outVertex.uv = half2((atlasX + xy.x) * tileUVSize.x,
                       (atlasY + xy.y) * tileUVSize.y);
    
  return outVertex;
};

fragment half4 texturedQuadFragment(TileVertexInOut     inFrag    [[ stage_in ]],
                                    texture2d<half>     tex2D    [[ texture(0) ]])
{
  constexpr sampler quad_sampler;
  half4 color = tex2D.sample(quad_sampler, float2(inFrag.uv));

  return color;
}
