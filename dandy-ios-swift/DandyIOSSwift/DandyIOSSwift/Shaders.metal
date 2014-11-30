#include <metal_stdlib>

using namespace metal;

struct TileUniforms {
  float2 offset; // Offset of tile map in screen pixels.
  float2 tileSize; // Size of a tile in homogenous coordinates
  float pointSize; // Size of a tile in screen pixels.
  float tileWScale; // 1 / numberOfTiles in texture
  uint tileStride; // Tiles per horizontal line
};

struct TileVertexIn
{
  uchar atlasIndex;
};

struct TileVertexOut
{
  float4 position [[position]];
  float size [[point_size]];
  float textureW [[user(textureW)]];
};

// This specialized shader takes a list of tiles and a vertex index and
// generates a set of tiled points.

vertex TileVertexOut tileVertex(uint vid [[ vertex_id ]],
                                  constant uchar* pAtlasIndex  [[ buffer(0) ]],
                                  constant TileUniforms& uniforms [[ buffer(1) ]])
{
  TileVertexOut outVertex;

  float2 offset = uniforms.offset;
  float2 tileSize = uniforms.tileSize;
  float tileWScale = uniforms.tileWScale;
  uint tileStride = uniforms.tileStride;

  uint tileY = vid / tileStride;
  uint tileX = vid - tileY * tileStride;

  outVertex.position = float4(offset.x + tileX * tileSize.x,
                              offset.y + tileY * tileSize.y,
                              0, 1);
  outVertex.size = uniforms.pointSize;
  outVertex.textureW = pAtlasIndex[vid] * tileWScale;
  return outVertex;
};

fragment half4 tileFragment(TileVertexOut input [[stage_in]],
                                    float2 uv [[point_coord]],
                                    texture3d<half>     tex3D    [[ texture(0) ]])
{
  constexpr sampler quad_sampler;
  half4 color = tex3D.sample(quad_sampler, float3(uv.x, uv.y, input.textureW));

  return color;
}
