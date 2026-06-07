# Benchmarks

Standalone performance harnesses. Not part of the shipped package or the test
suite.

## `frontend_python_bench.mjs`

Measures the throughput of the frontend-Python (MicroPython) callback bridge
used by data-driven accessors such as the heatmap `heatmap_color_fn` and the hex
bin colour/altitude callbacks. It replicates pyglobegl's exact callback wrapping
(`__pyglobegl_wrap_callback` plus the JSON argument round-trip) and reports
per-call cost against a native-JS baseline.

It runs under Node, so it works in WSL (no WebGL is involved — only the
JS-to-WASM boundary cost, which is engine-bound).

```bash
cd frontend && pnpm install   # one-time: provides the MicroPython runtime
cd .. && node bench/frontend_python_bench.mjs
```

The harness exists to answer one question: are MicroPython colour callbacks fast
enough? globe.gl invokes these accessors at data-change time (heatmaps bake 100
colour samples per heatmap; arcs sample the curve resolution per arc; dash
animation runs in the shader), not per animation frame, so the relevant bar is
"hundreds of calls on data change" rather than "thousands per frame".
