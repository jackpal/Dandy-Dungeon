#include <metal_stdlib>

using namespace metal;

struct TileUniforms {
  float2 offset; // Offset of tile map in screen pixels.
  float2 tileSize; // Size of a tile in homogenous coordinates
  float tileWScale; // 1 / numberOfTiles in texture
  uint tileStride; // Tiles per horizontal line
};

struct TileVertex {
  float2 xy;
  float2 uv;
};

struct TileVertexIn
{
  uchar atlasIndex;
};

struct TileVertexOut
{
  float4 position [[position]];
  float3 uvw [[user(uvw)]];
};

// This specialized shader takes a list of tiles and a vertex index and
// generates a set of tiled points.

vertex TileVertexOut tileVertex(uint vid [[ vertex_id ]],
                                uint iid [[ instance_id ]],
                                constant uchar* pAtlasIndex  [[ buffer(0) ]],
                                constant TileUniforms& uniforms [[ buffer(1) ]],
                                constant TileVertex* pQuad [[ buffer(2) ]])
{
  TileVertexOut outVertex;

  float2 offset = uniforms.offset;
  float2 tileSize = uniforms.tileSize;
  float tileWScale = uniforms.tileWScale;
  uint tileStride = uniforms.tileStride;

  TileVertex quad = pQuad[vid];

  uint tileY = iid / tileStride;
  uint tileX = iid - tileY * tileStride;

  outVertex.position = float4(offset.x + tileX * tileSize.x + quad.xy.x,
                              offset.y + tileY * tileSize.y + quad.xy.y,
                              0, 1);
  outVertex.uvw = float3(quad.uv.x, quad.uv.y, pAtlasIndex[iid] * tileWScale);
  return outVertex;
};

fragment half4 tileFragment(TileVertexOut input [[stage_in]],
                                    texture3d<half>     tex3D    [[ texture(0) ]])
{
  constexpr sampler quad_sampler;
  half4 color = tex3D.sample(quad_sampler, input.uvw);

  return color;
}
