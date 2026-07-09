import { Filter, GlProgram, GpuProgram } from "pixi.js";

/**
 * Custom filters written twice — GLSL for the WebGL fallback and WGSL for the
 * WebGPU renderer — so the same effects run on either backend.
 */

// ---------------------------------------------------------------------------
// Shared filter vertex shaders (standard Pixi v8 filter templates)
// ---------------------------------------------------------------------------
const glVertex = /* glsl */ `
  in vec2 aPosition;
  out vec2 vTextureCoord;

  uniform vec4 uInputSize;
  uniform vec4 uOutputFrame;
  uniform vec4 uOutputTexture;

  vec4 filterVertexPosition( void )
  {
      vec2 position = aPosition * uOutputFrame.zw + uOutputFrame.xy;
      position.x = position.x * (2.0 / uOutputTexture.x) - 1.0;
      position.y = position.y * (2.0 * uOutputTexture.z / uOutputTexture.y) - uOutputTexture.z;
      return vec4(position, 0.0, 1.0);
  }

  vec2 filterTextureCoord( void )
  {
      return aPosition * (uOutputFrame.zw * uInputSize.zw);
  }

  void main(void)
  {
      gl_Position = filterVertexPosition();
      vTextureCoord = filterTextureCoord();
  }
`;

const wgslHeader = /* wgsl */ `
  struct GlobalFilterUniforms {
    uInputSize: vec4<f32>,
    uInputPixel: vec4<f32>,
    uInputClamp: vec4<f32>,
    uOutputFrame: vec4<f32>,
    uGlobalFrame: vec4<f32>,
    uOutputTexture: vec4<f32>,
  };

  @group(0) @binding(0) var<uniform> gfu: GlobalFilterUniforms;
  @group(0) @binding(1) var uTexture: texture_2d<f32>;
  @group(0) @binding(2) var uSampler: sampler;

  struct VSOutput {
    @builtin(position) position: vec4<f32>,
    @location(0) uv: vec2<f32>,
  };

  fn filterVertexPosition(aPosition: vec2<f32>) -> vec4<f32> {
    var position = aPosition * gfu.uOutputFrame.zw + gfu.uOutputFrame.xy;
    position.x = position.x * (2.0 / gfu.uOutputTexture.x) - 1.0;
    position.y = position.y * (2.0 * gfu.uOutputTexture.z / gfu.uOutputTexture.y) - gfu.uOutputTexture.z;
    return vec4(position, 0.0, 1.0);
  }

  fn filterTextureCoord(aPosition: vec2<f32>) -> vec2<f32> {
    return aPosition * (gfu.uOutputFrame.zw * gfu.uInputSize.zw);
  }

  @vertex
  fn mainVertex(@location(0) aPosition: vec2<f32>) -> VSOutput {
    return VSOutput(filterVertexPosition(aPosition), filterTextureCoord(aPosition));
  }
`;

// ---------------------------------------------------------------------------
// Vignette
// ---------------------------------------------------------------------------
const vignetteGl = /* glsl */ `
  precision highp float;
  in vec2 vTextureCoord;

  uniform sampler2D uTexture;
  uniform vec4 uInputSize;
  uniform vec4 uOutputFrame;
  uniform float uIntensity;
  uniform float uRadius;

  void main(void)
  {
      vec4 color = texture2D(uTexture, vTextureCoord);
      vec2 screenUv = vTextureCoord * uInputSize.xy / uOutputFrame.zw;
      float d = distance(screenUv, vec2(0.5));
      float vig = smoothstep(uRadius, uRadius - 0.35, d);
      color.rgb *= mix(1.0, vig, uIntensity);
      gl_FragColor = color;
  }
`;

const vignetteWgsl = /* wgsl */ `
  ${wgslHeader}

  struct VignetteUniforms {
    uIntensity: f32,
    uRadius: f32,
  };
  @group(1) @binding(0) var<uniform> vignetteUniforms: VignetteUniforms;

  @fragment
  fn mainFragment(@location(0) uv: vec2<f32>) -> @location(0) vec4<f32> {
    var color = textureSample(uTexture, uSampler, uv);
    let screenUv = uv * gfu.uInputSize.xy / gfu.uOutputFrame.zw;
    let d = distance(screenUv, vec2<f32>(0.5, 0.5));
    let vig = smoothstep(vignetteUniforms.uRadius, vignetteUniforms.uRadius - 0.35, d);
    let mixAmount = mix(1.0, vig, vignetteUniforms.uIntensity);
    return vec4<f32>(color.rgb * mixAmount, color.a);
  }
`;

export function createVignetteFilter(intensity = 0.5, radius = 0.72): Filter {
  return new Filter({
    glProgram: GlProgram.from({ vertex: glVertex, fragment: vignetteGl, name: "vignette-filter" }),
    gpuProgram: GpuProgram.from({
      vertex: { source: vignetteWgsl, entryPoint: "mainVertex" },
      fragment: { source: vignetteWgsl, entryPoint: "mainFragment" },
    }),
    resources: {
      vignetteUniforms: {
        uIntensity: { value: intensity, type: "f32" },
        uRadius: { value: radius, type: "f32" },
      },
    },
  });
}

// ---------------------------------------------------------------------------
// Palette swap — recolors enemy sprites per tier without extra textures.
// Colors are compared in straight-alpha space (Pixi textures premultiply).
// ---------------------------------------------------------------------------
const paletteGl = /* glsl */ `
  precision highp float;
  in vec2 vTextureCoord;

  uniform sampler2D uTexture;
  uniform vec4 uSource[4];
  uniform vec4 uTarget[4];
  uniform float uTolerance;

  void main(void)
  {
      vec4 color = texture2D(uTexture, vTextureCoord);
      if (color.a > 0.001) {
          vec3 rgb = color.rgb / color.a;
          for (int i = 0; i < 4; i++) {
              if (distance(rgb, uSource[i].rgb) < uTolerance) {
                  rgb = uTarget[i].rgb;
                  break;
              }
          }
          color = vec4(rgb * color.a, color.a);
      }
      gl_FragColor = color;
  }
`;

const paletteWgsl = /* wgsl */ `
  ${wgslHeader}

  struct PaletteUniforms {
    uSource: array<vec4<f32>, 4>,
    uTarget: array<vec4<f32>, 4>,
    uTolerance: f32,
  };
  @group(1) @binding(0) var<uniform> paletteUniforms: PaletteUniforms;

  @fragment
  fn mainFragment(@location(0) uv: vec2<f32>) -> @location(0) vec4<f32> {
    var color = textureSample(uTexture, uSampler, uv);
    if (color.a > 0.001) {
      var rgb = color.rgb / color.a;
      for (var i = 0; i < 4; i++) {
        if (distance(rgb, paletteUniforms.uSource[i].rgb) < paletteUniforms.uTolerance) {
          rgb = paletteUniforms.uTarget[i].rgb;
          break;
        }
      }
      color = vec4<f32>(rgb * color.a, color.a);
    }
    return color;
  }
`;

function hexToVec(hex: number): [number, number, number] {
  return [((hex >> 16) & 0xff) / 255, ((hex >> 8) & 0xff) / 255, (hex & 0xff) / 255];
}

export function createPaletteSwapFilter(
  pairs: Array<[source: number, target: number]>,
  tolerance = 0.12,
): Filter {
  const src = new Float32Array(16);
  const dst = new Float32Array(16);
  for (let i = 0; i < 4; i++) {
    const pair = pairs[i] ?? pairs[pairs.length - 1] ?? [0, 0];
    const [sr, sg, sb] = hexToVec(pair[0]);
    const [tr, tg, tb] = hexToVec(pair[1]);
    src.set([sr, sg, sb, 1], i * 4);
    dst.set([tr, tg, tb, 1], i * 4);
  }
  return new Filter({
    glProgram: GlProgram.from({ vertex: glVertex, fragment: paletteGl, name: "palette-swap-filter" }),
    gpuProgram: GpuProgram.from({
      vertex: { source: paletteWgsl, entryPoint: "mainVertex" },
      fragment: { source: paletteWgsl, entryPoint: "mainFragment" },
    }),
    resources: {
      paletteUniforms: {
        uSource: { value: src, type: "vec4<f32>", size: 4 },
        uTarget: { value: dst, type: "vec4<f32>", size: 4 },
        uTolerance: { value: tolerance, type: "f32" },
      },
    },
  });
}

/** Tier palettes: tier 2 = cool blue "elite", tier 3 = red-hot "brute". */
export function createTierFilters(): Record<number, Filter> {
  return {
    2: createPaletteSwapFilter([
      [0xf77622, 0x2c6ff2], // walker orange body → blue
      [0xc2461e, 0x1a3fa0],
      [0x63c74d, 0x2ce8f5], // shell light green → cyan
      [0xb55088, 0x2c6ff2], // flyer purple → blue
    ]),
    3: createPaletteSwapFilter([
      [0xf77622, 0xe43b44], // → angry red
      [0xc2461e, 0xa22633],
      [0x63c74d, 0xf6757a],
      [0xb55088, 0xe43b44],
    ]),
  };
}
