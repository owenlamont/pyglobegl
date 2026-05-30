# Goals & Roadmap

## Goals

- Provide a modern anywidget-based globe.gl wrapper for Jupyter, JupyterLab,
  Colab, VS Code, and marimo.
- Ship a prebuilt JupyterLab extension via `pip install` (no separate lab
  build / extension install).
- Keep the Python API friendly for spatial-data workflows.

## Roadmap

### Near term

Expose globe.gl APIs in order, by section:

- [x] Initialisation
- [x] Container layout
- [x] Globe layer
- [x] Points layer
- [x] Arcs layer
- [x] Polygons layer
- [x] Paths layer
- [x] Heatmaps layer
- [x] Hex bin layer
- [x] Hexed polygons layer
- [x] Tiles layer
- [x] Particles layer
- [x] Rings layer
- [x] Labels layer
- [ ] HTML elements layer
- [ ] 3D objects layer
- [ ] Custom layer
- [ ] Render control
- [ ] Utility options

Alongside the layer work:

- Prioritise strongly typed, overload-heavy Python APIs with flexible input
  unions (for example, accept Pillow images, NumPy arrays, or remote URLs
  anywhere globe.gl accepts textures/images).
- Solidify a CRS-first API: detect CRS on inputs and auto-reproject to
  EPSG:4326 before emitting lat/lng data for globe.gl layers.

### Mid term

- GeoPandas adapter: map geometry types to globe.gl layers with sensible
  defaults and schema validation.
- MovingPandas trajectories (static): accept trajectory/segment outputs and
  render via paths/arcs without time animation in v1.
- Geometry-only inputs: accept bare geometry collections (Shapely or
  GeoJSON-like) as a convenience layer when CRS metadata is explicit.

### Long term / research

- GeoPolars exploration: track maturity and define an adapter plan once CRS
  metadata and extension types are stable upstream.
- Raster feasibility: investigate mapping rasters to globe.gl via tiles,
  heatmaps, or sampled grids; document constraints and recommended workflows.
