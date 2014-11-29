#include <metal_stdlib>

using namespace metal;

struct VertexInOut
{
    float4  position [[position]];
    float2  uv [[user(texturecoord)]];
};

vertex VertexInOut passThroughVertex(uint vid [[ vertex_id ]],
                                     constant packed_float4* position  [[ buffer(0) ]],
                                     constant packed_float2* uv    [[ buffer(1) ]])
{
    VertexInOut outVertex;
    
    outVertex.position = position[vid];
    outVertex.uv    = uv[vid];
    
    return outVertex;
};

fragment half4 texturedQuadFragment(VertexInOut     inFrag    [[ stage_in ]],
                                    texture2d<half>  tex2D     [[ texture(0) ]])
{
  constexpr sampler quad_sampler;
  half4 color = tex2D.sample(quad_sampler, inFrag.uv);

  return color;
}
