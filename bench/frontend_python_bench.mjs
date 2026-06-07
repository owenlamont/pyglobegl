// Microbenchmark for the frontend-Python (MicroPython) callback bridge.
//
// Replicates pyglobegl's exact wrapping (__pyglobegl_wrap_callback + JSON
// round-trip from frontend/src/index.ts) and measures callback throughput.
// Runs under Node (the WASM-boundary cost is engine-bound and browser
// independent; no WebGL is involved), so it works in WSL.
//
// Context: globe.gl invokes these colour accessors at geometry-build /
// data-change time, not per animation frame (heatmaps bake NUM_COLORS=100
// samples per heatmap; arcs sample arcCurveResolution+1 per arc; dash
// animation is shader-side). So the relevant bar is "hundreds of calls on
// data change", which these numbers comfortably clear.
//
// Usage (install frontend deps first: `cd frontend && pnpm install`):
//   node bench/frontend_python_bench.mjs
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const pkgDir = join(
  here,
  "../frontend/node_modules/@micropython/micropython-webassembly-pyscript",
);
const { loadMicroPython } = await import(join(pkgDir, "micropython.mjs"));
const wasmUrl = join(pkgDir, "micropython.wasm");

const hr = () => Number(process.hrtime.bigint()) / 1e6; // ms

// Exact copy of pyglobegl's runtime helpers (frontend/src/index.ts).
const RUNTIME_HELPERS = `
import json
import js

def __pyglobegl_to_python(value):
    try:
        serialized = js.JSON.stringify(value)
    except Exception:
        return value
    if serialized is None:
        return None
    try:
        return json.loads(str(serialized))
    except Exception:
        return value

def __pyglobegl_wrap_callback(callback):
    def _wrapped(*args):
        converted_args = [__pyglobegl_to_python(arg) for arg in args]
        return callback(*converted_args)
    return _wrapped
`;

// A representative heatmap-style colormap (t in [0, 1] -> 'rgb(...)').
const COLOR_FN_SRC = `
def colormap(t):
    r = int(255 * min(1.0, max(0.0, 1.5 * t)))
    g = int(255 * min(1.0, max(0.0, 1.0 - abs(t - 0.5) * 2)))
    b = int(255 * min(1.0, max(0.0, 1.5 * (1.0 - t))))
    return "rgb(" + str(r) + "," + str(g) + "," + str(b) + ")"
`;

// The same logic in native JS, for a baseline.
const colormapJs = (t) => {
  const r = Math.round(255 * Math.min(1, Math.max(0, 1.5 * t)));
  const g = Math.round(255 * Math.min(1, Math.max(0, 1 - Math.abs(t - 0.5) * 2)));
  const b = Math.round(255 * Math.min(1, Math.max(0, 1.5 * (1 - t))));
  return `rgb(${r},${g},${b})`;
};

// Hexbin-style object-argument callback (the existing pattern).
const HEX_FN_SRC = `
def hex_color(b):
    w = b.get("sumWeight", 0)
    return "rgb(" + str(min(255, int(w))) + ",0,0)"
`;

const time = (label, n, fn) => {
  const t0 = hr();
  let sink;
  for (let i = 0; i < n; i++) sink = fn(i);
  const dt = hr() - t0;
  const perCall = (dt / n) * 1000; // microseconds
  console.log(
    `${label.padEnd(46)} ${n.toString().padStart(8)} calls  ${dt
      .toFixed(1)
      .padStart(9)} ms  ${perCall.toFixed(2).padStart(8)} us/call  ${Math.round(
      n / (dt / 1000),
    )
      .toLocaleString()
      .padStart(13)} calls/s`,
  );
  return sink;
};

const tInit0 = hr();
const mp = await loadMicroPython({ url: wasmUrl });
console.log(`MicroPython init: ${(hr() - tInit0).toFixed(1)} ms\n`);

const tCompile0 = hr();
mp.runPython(RUNTIME_HELPERS);
mp.runPython(COLOR_FN_SRC);
console.log(
  `runPython(helpers + colormap source): ${(hr() - tCompile0).toFixed(
    1,
  )} ms (one-time per callback)\n`,
);

const main = mp.pyimport("__main__");
const wrappedColor = main.__pyglobegl_wrap_callback(main.colormap);
const directColor = main.colormap;

mp.runPython(HEX_FN_SRC);
const main2 = mp.pyimport("__main__");
const wrappedHex = main2.__pyglobegl_wrap_callback(main2.hex_color);

for (let i = 0; i < 1000; i++) {
  wrappedColor(i / 1000);
  colormapJs(i / 1000);
}

console.log("Scalar (t)=>color  — heatmap/arc/path/ring gradient pattern:");
time("  native JS baseline", 1_000_000, (i) => colormapJs((i % 100) / 99));
time("  MicroPython wrapped (JSON round-trip)", 200_000, (i) =>
  wrappedColor((i % 100) / 99),
);
time("  MicroPython direct (no round-trip wrap)", 200_000, (i) =>
  directColor((i % 100) / 99),
);

console.log("\nObject (bin)=>color — the existing hexbin pattern:");
const bin = {
  sumWeight: 42,
  points: [{ a: 1 }, { a: 2 }],
  center: { lat: 1, lng: 2 },
};
time("  MicroPython wrapped (JSON round-trip)", 200_000, () => wrappedHex(bin));

console.log(
  "\nReal-world invocation profiles (build/data-change time, NOT per frame):",
);
time("  1 heatmap rebuild (NUM_COLORS=100 calls)", 1000, () => {
  for (let i = 0; i < 100; i++) wrappedColor(i / 99);
});
time("  1 arc gradient (arcCurveResolution=64+1)", 1000, () => {
  for (let i = 0; i < 65; i++) wrappedColor(i / 64);
});
