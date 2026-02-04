type AnyWidgetRenderProps = {
	el: HTMLElement;
	model: {
		get: (key: string) => unknown;
		set: (key: string, value: unknown) => void;
		save_changes: () => void;
		on: (event: string, callback: () => void) => void;
		send: (data: unknown, buffers?: ArrayBuffer[] | undefined) => void;
	};
};

import * as THREE from "three";

type GlobeInitConfig = {
	rendererConfig?: Record<string, unknown>;
	waitForGlobeReady?: boolean;
	animateIn?: boolean;
};

type GlobeLayoutConfig = {
	width?: number;
	height?: number;
	globeOffset?: [number, number];
	backgroundColor?: string;
	backgroundImageUrl?: string;
};

type GlobeLayerConfig = {
	globeImageUrl?: string | null;
	bumpImageUrl?: string | null;
	globeTileEngineUrl?: string | null;
	showGlobe?: boolean;
	showGraticules?: boolean;
	showAtmosphere?: boolean;
	atmosphereColor?: string;
	atmosphereAltitude?: number;
	globeCurvatureResolution?: number;
	globeMaterial?: unknown;
};

type PointsLayerConfig = {
	pointsData?: Array<Record<string, unknown>>;
	pointLabel?: string;
	pointLat?: number | string;
	pointLng?: number | string;
	pointColor?: string;
	pointAltitude?: number | string;
	pointRadius?: number | string;
	pointResolution?: number;
	pointsMerge?: boolean;
	pointsTransitionDuration?: number;
};

type ArcsLayerConfig = {
	arcsData?: Array<Record<string, unknown>>;
	arcLabel?: string;
	arcStartLat?: number | string;
	arcStartLng?: number | string;
	arcStartAltitude?: number | string;
	arcEndLat?: number | string;
	arcEndLng?: number | string;
	arcEndAltitude?: number | string;
	arcColor?: string | Array<string>;
	arcAltitude?: number | string | null;
	arcAltitudeAutoScale?: number | string;
	arcStroke?: number | string;
	arcCurveResolution?: number;
	arcCircularResolution?: number;
	arcDashLength?: number | string;
	arcDashGap?: number | string;
	arcDashInitialGap?: number | string;
	arcDashAnimateTime?: number | string;
	arcsTransitionDuration?: number;
};

type PolygonsLayerConfig = {
	polygonsData?: Array<Record<string, unknown>>;
	polygonLabel?: string;
	polygonGeoJsonGeometry?: string;
	polygonCapColor?: string;
	polygonCapMaterial?: unknown;
	polygonSideColor?: string;
	polygonSideMaterial?: unknown;
	polygonStrokeColor?: string;
	polygonAltitude?: number | string;
	polygonCapCurvatureResolution?: number | string;
	polygonsTransitionDuration?: number;
};

type PathsLayerConfig = {
	pathsData?: Array<Record<string, unknown>>;
	pathLabel?: string;
	pathResolution?: number;
	pathColor?: string | Array<string>;
	pathStroke?: number | string;
	pathDashLength?: number | string;
	pathDashGap?: number | string;
	pathDashInitialGap?: number | string;
	pathDashAnimateTime?: number | string;
	pathTransitionDuration?: number;
};

type HeatmapsLayerConfig = {
	heatmapsData?: Array<Record<string, unknown>>;
	heatmapPoints?: unknown;
	heatmapPointLat?: number | string;
	heatmapPointLng?: number | string;
	heatmapPointWeight?: number | string;
	heatmapBandwidth?: number | string;
	heatmapColorFn?: unknown;
	heatmapColorSaturation?: number | string;
	heatmapBaseAltitude?: number | string;
	heatmapTopAltitude?: number | string;
	heatmapsTransitionDuration?: number;
};

type HexedPolygonsLayerConfig = {
	hexPolygonsData?: Array<Record<string, unknown>>;
	hexPolygonGeoJsonGeometry?: string;
	hexPolygonColor?: string;
	hexPolygonAltitude?: number | string;
	hexPolygonResolution?: number | string;
	hexPolygonMargin?: number | string;
	hexPolygonUseDots?: boolean;
	hexPolygonCurvatureResolution?: number | string;
	hexPolygonDotResolution?: number | string;
	hexPolygonsTransitionDuration?: number;
	hexPolygonLabel?: string;
};

type TilesLayerConfig = {
	tilesData?: Array<Record<string, unknown>>;
	tileLat?: number | string;
	tileLng?: number | string;
	tileAltitude?: number | string;
	tileWidth?: number | string;
	tileHeight?: number | string;
	tileUseGlobeProjection?: boolean;
	tileMaterial?: unknown;
	tileCurvatureResolution?: number | string;
	tilesTransitionDuration?: number;
	tileLabel?: string;
};

type ParticlesLayerConfig = {
	particlesData?: Array<Record<string, unknown>>;
	particlesList?: unknown;
	particleLat?: number | string;
	particleLng?: number | string;
	particleAltitude?: number | string;
	particlesSize?: number | string;
	particlesSizeAttenuation?: boolean | string;
	particlesColor?: string;
	particlesTexture?: unknown;
	particleLabel?: string;
};

type RingsLayerConfig = {
	ringsData?: Array<Record<string, unknown>>;
	ringLat?: number | string;
	ringLng?: number | string;
	ringAltitude?: number | string;
	ringColor?: string | Array<string>;
	ringResolution?: number;
	ringMaxRadius?: number | string;
	ringPropagationSpeed?: number | string;
	ringRepeatPeriod?: number | string;
};

type LabelsLayerConfig = {
	labelsData?: Array<Record<string, unknown>>;
	labelLat?: number | string;
	labelLng?: number | string;
	labelAltitude?: number | string;
	labelRotation?: number | string;
	labelText?: string;
	labelSize?: number | string;
	labelTypeFace?: unknown;
	labelColor?: string;
	labelResolution?: number;
	labelIncludeDot?: boolean;
	labelDotRadius?: number | string;
	labelDotOrientation?: string;
	labelsTransitionDuration?: number;
	labelLabel?: string;
};

type GlobeConfig = {
	init?: GlobeInitConfig;
	layout?: GlobeLayoutConfig;
	globe?: GlobeLayerConfig;
	points?: PointsLayerConfig;
	arcs?: ArcsLayerConfig;
	polygons?: PolygonsLayerConfig;
	paths?: PathsLayerConfig;
	heatmaps?: HeatmapsLayerConfig;
	hexed_polygons?: HexedPolygonsLayerConfig;
	tiles?: TilesLayerConfig;
	particles?: ParticlesLayerConfig;
	rings?: RingsLayerConfig;
	labels?: LabelsLayerConfig;
	view?: GlobeViewConfig;
};

type PointOfView = {
	lat: number;
	lng: number;
	altitude: number;
};

type GlobeViewConfig = {
	pointOfView?: PointOfView;
	transitionMs?: number;
};

const buildMaterial = (spec: unknown): unknown => {
	if (!spec || typeof spec !== "object") {
		return spec;
	}
	if (!("type" in spec)) {
		return spec;
	}
	const { type, params } = spec as {
		type: string;
		params?: Record<string, unknown>;
	};
	const ctor = (THREE as Record<string, unknown>)[type];
	if (typeof ctor !== "function") {
		return spec;
	}
	const materialCtor = ctor as new (
		params?: Record<string, unknown>,
	) => unknown;
	return new materialCtor(params ?? {});
};

const isMaterial = (value: unknown): boolean =>
	!!value &&
	typeof value === "object" &&
	"isMaterial" in (value as { isMaterial?: boolean }) &&
	(value as { isMaterial?: boolean }).isMaterial === true;

const isTexture = (value: unknown): boolean =>
	!!value &&
	typeof value === "object" &&
	"isTexture" in (value as { isTexture?: boolean }) &&
	(value as { isTexture?: boolean }).isTexture === true;

const materialFromSpec = (value: unknown): unknown => {
	if (!value) {
		return value;
	}
	if (isMaterial(value)) {
		return value;
	}
	return buildMaterial(value);
};

const textureLoader = new THREE.TextureLoader();

const textureFromSpec = (value: unknown): unknown => {
	if (!value) {
		return value;
	}
	if (isTexture(value)) {
		return value;
	}
	if (typeof value === "string") {
		return textureLoader.load(value);
	}
	return value;
};

function ensureWebGPUShaderStage(): void {
	const globalScope = globalThis as {
		GPUShaderStage?: { VERTEX: number; FRAGMENT: number; COMPUTE: number };
	};

	if (globalScope.GPUShaderStage) {
		return;
	}

	globalScope.GPUShaderStage = {
		VERTEX: 1,
		FRAGMENT: 2,
		COMPUTE: 4,
	};
}

const TOOLTIP_STYLE = `.float-tooltip-kap {
  position: absolute;
  width: max-content;
  max-width: max(50%, 150px);
  padding: 3px 5px;
  border-radius: 3px;
  font: 12px sans-serif;
  color: #eee;
  background: rgba(0,0,0,0.6);
  pointer-events: none;
}
`;

function ensureTooltipStyles(el: HTMLElement): void {
	const root = el.getRootNode();
	const styleParent =
		root instanceof ShadowRoot
			? root
			: (document.head ?? document.documentElement);
	if (
		!styleParent ||
		styleParent.querySelector?.('[data-pyglobegl-tooltip="1"]')
	) {
		return;
	}
	const style = document.createElement("style");
	style.dataset.pyglobeglTooltip = "1";
	style.textContent = TOOLTIP_STYLE;
	styleParent.appendChild(style);
}

export function render({ el, model }: AnyWidgetRenderProps): () => void {
	el.style.width = "100%";
	el.style.height = "auto";
	el.style.display = "flex";
	el.style.justifyContent = "center";
	el.style.alignItems = "center";

	ensureWebGPUShaderStage();
	ensureTooltipStyles(el);

	let resizeObserver: ResizeObserver | undefined;

	void import("globe.gl").then(({ default: Globe }) => {
		const mount = document.createElement("div");
		el.replaceChildren(mount);

		const getConfig = (): GlobeConfig | undefined =>
			model.get("config") as GlobeConfig | undefined;

		const initialConfig = getConfig();
		(
			globalThis as { __pyglobegl_init_config?: GlobeInitConfig }
		).__pyglobegl_init_config = initialConfig?.init;
		const globe = new Globe(mount, initialConfig?.init);
		globe.pointOfView({ lat: 0, lng: 0, altitude: 2.8 }, 0);
		globe.atmosphereAltitude(0.05);

		const outputArea = el.closest(".output-area") as HTMLElement | null;

		globe.onGlobeReady(() => {
			(
				globalThis as { __pyglobegl_globe_ready?: boolean }
			).__pyglobegl_globe_ready = true;
			(
				globalThis as {
					__pyglobegl_renderer_attributes?: WebGLContextAttributes | null;
				}
			).__pyglobegl_renderer_attributes = globe
				.renderer()
				.getContext()
				.getContextAttributes();
			model.send({ type: "globe_ready" });
		});

		globe.onGlobeClick((coords: { lat: number; lng: number }) => {
			model.send({ type: "globe_click", payload: coords });
		});

		globe.onGlobeRightClick((coords: { lat: number; lng: number }) => {
			model.send({ type: "globe_right_click", payload: coords });
		});

		globe.onPointClick(
			(
				point: Record<string, unknown>,
				_event: unknown,
				coords: { lat: number; lng: number; altitude: number },
			) => {
				model.send({ type: "point_click", payload: { point, coords } });
			},
		);

		globe.onPointRightClick(
			(
				point: Record<string, unknown>,
				_event: unknown,
				coords: { lat: number; lng: number; altitude: number },
			) => {
				model.send({ type: "point_right_click", payload: { point, coords } });
			},
		);

		const hoverBindings: Record<string, boolean> = {
			point: false,
			arc: false,
			polygon: false,
			path: false,
			heatmap: false,
			hexPolygon: false,
			tile: false,
			particle: false,
			label: false,
		};

		const getEventConfig = (): Record<string, boolean> => {
			const value = model.get("event_config");
			if (!value || typeof value !== "object") {
				return {};
			}
			return value as Record<string, boolean>;
		};

		const maybeBindHoverHandlers = (): void => {
			const config = getEventConfig();
			if (config.pointHover && !hoverBindings.point) {
				globe.onPointHover(
					(
						point: Record<string, unknown> | null,
						prevPoint: Record<string, unknown> | null,
					) => {
						model.send({
							type: "point_hover",
							payload: { point, prev_point: prevPoint },
						});
					},
				);
				hoverBindings.point = true;
			}
			if (config.arcHover && !hoverBindings.arc) {
				globe.onArcHover(
					(
						arc: Record<string, unknown> | null,
						prevArc: Record<string, unknown> | null,
					) => {
						model.send({
							type: "arc_hover",
							payload: { arc, prev_arc: prevArc },
						});
					},
				);
				hoverBindings.arc = true;
			}
			if (config.polygonHover && !hoverBindings.polygon) {
				globe.onPolygonHover(
					(
						polygon: Record<string, unknown> | null,
						prevPolygon: Record<string, unknown> | null,
					) => {
						model.send({
							type: "polygon_hover",
							payload: { polygon, prev_polygon: prevPolygon },
						});
					},
				);
				hoverBindings.polygon = true;
			}
			if (config.pathHover && !hoverBindings.path) {
				globe.onPathHover(
					(
						path: Record<string, unknown> | null,
						prevPath: Record<string, unknown> | null,
					) => {
						model.send({
							type: "path_hover",
							payload: { path, prev_path: prevPath },
						});
					},
				);
				hoverBindings.path = true;
			}
			if (config.heatmapHover && !hoverBindings.heatmap) {
				globe.onHeatmapHover(
					(
						heatmap: Record<string, unknown> | null,
						prevHeatmap: Record<string, unknown> | null,
					) => {
						model.send({
							type: "heatmap_hover",
							payload: { heatmap, prev_heatmap: prevHeatmap },
						});
					},
				);
				hoverBindings.heatmap = true;
			}
			if (config.hexPolygonHover && !hoverBindings.hexPolygon) {
				globe.onHexPolygonHover(
					(
						hexPolygon: Record<string, unknown> | null,
						prevHexPolygon: Record<string, unknown> | null,
					) => {
						model.send({
							type: "hex_polygon_hover",
							payload: {
								hex_polygon: hexPolygon,
								prev_hex_polygon: prevHexPolygon,
							},
						});
					},
				);
				hoverBindings.hexPolygon = true;
			}
			if (config.tileHover && !hoverBindings.tile) {
				globe.onTileHover(
					(
						tile: Record<string, unknown> | null,
						prevTile: Record<string, unknown> | null,
					) => {
						model.send({
							type: "tile_hover",
							payload: { tile, prev_tile: prevTile },
						});
					},
				);
				hoverBindings.tile = true;
			}
			if (config.particleHover && !hoverBindings.particle) {
				globe.onParticleHover(
					(
						particle: Record<string, unknown> | null,
						prevParticle: Record<string, unknown> | null,
					) => {
						model.send({
							type: "particle_hover",
							payload: { particle, prev_particle: prevParticle },
						});
					},
				);
				hoverBindings.particle = true;
			}
			if (config.labelHover && !hoverBindings.label) {
				globe.onLabelHover(
					(
						label: Record<string, unknown> | null,
						prevLabel: Record<string, unknown> | null,
					) => {
						model.send({
							type: "label_hover",
							payload: { label, prev_label: prevLabel },
						});
					},
				);
				hoverBindings.label = true;
			}
		};

		globe.onArcClick(
			(
				arc: Record<string, unknown>,
				_event: unknown,
				coords: { lat: number; lng: number; altitude: number },
			) => {
				model.send({ type: "arc_click", payload: { arc, coords } });
			},
		);

		globe.onArcRightClick(
			(
				arc: Record<string, unknown>,
				_event: unknown,
				coords: { lat: number; lng: number; altitude: number },
			) => {
				model.send({ type: "arc_right_click", payload: { arc, coords } });
			},
		);

		globe.onPolygonClick(
			(
				polygon: Record<string, unknown>,
				_event: unknown,
				coords: { lat: number; lng: number; altitude: number },
			) => {
				model.send({ type: "polygon_click", payload: { polygon, coords } });
			},
		);

		globe.onPolygonRightClick(
			(
				polygon: Record<string, unknown>,
				_event: unknown,
				coords: { lat: number; lng: number; altitude: number },
			) => {
				model.send({
					type: "polygon_right_click",
					payload: { polygon, coords },
				});
			},
		);

		globe.onPathClick(
			(
				path: Record<string, unknown>,
				_event: unknown,
				coords: { lat: number; lng: number; altitude: number },
			) => {
				model.send({ type: "path_click", payload: { path, coords } });
			},
		);

		globe.onPathRightClick(
			(
				path: Record<string, unknown>,
				_event: unknown,
				coords: { lat: number; lng: number; altitude: number },
			) => {
				model.send({ type: "path_right_click", payload: { path, coords } });
			},
		);

		globe.onHeatmapClick(
			(
				heatmap: Record<string, unknown>,
				_event: unknown,
				coords: { lat: number; lng: number; altitude: number },
			) => {
				model.send({ type: "heatmap_click", payload: { heatmap, coords } });
			},
		);

		globe.onHeatmapRightClick(
			(
				heatmap: Record<string, unknown>,
				_event: unknown,
				coords: { lat: number; lng: number; altitude: number },
			) => {
				model.send({
					type: "heatmap_right_click",
					payload: { heatmap, coords },
				});
			},
		);

		globe.onHexPolygonClick(
			(
				hexPolygon: Record<string, unknown>,
				_event: unknown,
				coords: { lat: number; lng: number; altitude: number },
			) => {
				model.send({
					type: "hex_polygon_click",
					payload: { hex_polygon: hexPolygon, coords },
				});
			},
		);

		globe.onHexPolygonRightClick(
			(
				hexPolygon: Record<string, unknown>,
				_event: unknown,
				coords: { lat: number; lng: number; altitude: number },
			) => {
				model.send({
					type: "hex_polygon_right_click",
					payload: { hex_polygon: hexPolygon, coords },
				});
			},
		);

		globe.onTileClick(
			(
				tile: Record<string, unknown>,
				_event: unknown,
				coords: { lat: number; lng: number; altitude: number },
			) => {
				model.send({ type: "tile_click", payload: { tile, coords } });
			},
		);

		globe.onTileRightClick(
			(
				tile: Record<string, unknown>,
				_event: unknown,
				coords: { lat: number; lng: number; altitude: number },
			) => {
				model.send({
					type: "tile_right_click",
					payload: { tile, coords },
				});
			},
		);

		globe.onParticleClick(
			(
				particle: Record<string, unknown>,
				_event: unknown,
				coords: { lat: number; lng: number; altitude: number },
			) => {
				model.send({
					type: "particle_click",
					payload: { particle, coords },
				});
			},
		);

		globe.onParticleRightClick(
			(
				particle: Record<string, unknown>,
				_event: unknown,
				coords: { lat: number; lng: number; altitude: number },
			) => {
				model.send({
					type: "particle_right_click",
					payload: { particle, coords },
				});
			},
		);

		globe.onLabelClick(
			(
				label: Record<string, unknown>,
				_event: unknown,
				coords: { lat: number; lng: number; altitude: number },
			) => {
				model.send({ type: "label_click", payload: { label, coords } });
			},
		);

		globe.onLabelRightClick(
			(
				label: Record<string, unknown>,
				_event: unknown,
				coords: { lat: number; lng: number; altitude: number },
			) => {
				model.send({
					type: "label_right_click",
					payload: { label, coords },
				});
			},
		);

		maybeBindHoverHandlers();
		model.on("change:event_config", maybeBindHoverHandlers);

		const defaultPathPoints = (datum: unknown): unknown => {
			if (datum && typeof datum === "object" && "path" in datum) {
				return (datum as { path?: unknown }).path ?? datum;
			}
			return datum;
		};

		const defaultPathPointAlt = (point: unknown): number => {
			if (Array.isArray(point)) {
				const alt = point[2];
				return typeof alt === "number" ? alt : 0.001;
			}
			return 0.001;
		};

		globe.pathPoints(defaultPathPoints);
		globe.pathPointAlt(defaultPathPointAlt);

		const globeProps = new Set([
			"globeImageUrl",
			"bumpImageUrl",
			"globeTileEngineUrl",
			"showGlobe",
			"showGraticules",
			"showAtmosphere",
			"atmosphereColor",
			"atmosphereAltitude",
			"globeCurvatureResolution",
			"globeMaterial",
		]);

		const pointProps = new Set([
			"pointLabel",
			"pointLat",
			"pointLng",
			"pointColor",
			"pointAltitude",
			"pointRadius",
			"pointResolution",
			"pointsMerge",
			"pointsTransitionDuration",
		]);

		const arcProps = new Set([
			"arcStartLat",
			"arcStartLng",
			"arcStartAltitude",
			"arcEndLat",
			"arcEndLng",
			"arcEndAltitude",
			"arcColor",
			"arcAltitude",
			"arcAltitudeAutoScale",
			"arcStroke",
			"arcCurveResolution",
			"arcCircularResolution",
			"arcDashLength",
			"arcDashGap",
			"arcDashInitialGap",
			"arcDashAnimateTime",
			"arcsTransitionDuration",
			"arcLabel",
		]);

		const polygonProps = new Set([
			"polygonLabel",
			"polygonGeoJsonGeometry",
			"polygonCapColor",
			"polygonCapMaterial",
			"polygonSideColor",
			"polygonSideMaterial",
			"polygonStrokeColor",
			"polygonAltitude",
			"polygonCapCurvatureResolution",
			"polygonsTransitionDuration",
		]);

		const pathProps = new Set([
			"pathLabel",
			"pathResolution",
			"pathColor",
			"pathStroke",
			"pathDashLength",
			"pathDashGap",
			"pathDashInitialGap",
			"pathDashAnimateTime",
			"pathTransitionDuration",
		]);

		const heatmapProps = new Set([
			"heatmapPoints",
			"heatmapPointLat",
			"heatmapPointLng",
			"heatmapPointWeight",
			"heatmapBandwidth",
			"heatmapColorFn",
			"heatmapColorSaturation",
			"heatmapBaseAltitude",
			"heatmapTopAltitude",
			"heatmapsTransitionDuration",
		]);

		const hexPolygonProps = new Set([
			"hexPolygonGeoJsonGeometry",
			"hexPolygonColor",
			"hexPolygonAltitude",
			"hexPolygonResolution",
			"hexPolygonMargin",
			"hexPolygonUseDots",
			"hexPolygonCurvatureResolution",
			"hexPolygonDotResolution",
			"hexPolygonsTransitionDuration",
			"hexPolygonLabel",
		]);

		const tilesProps = new Set([
			"tileLat",
			"tileLng",
			"tileAltitude",
			"tileWidth",
			"tileHeight",
			"tileUseGlobeProjection",
			"tileMaterial",
			"tileCurvatureResolution",
			"tilesTransitionDuration",
			"tileLabel",
		]);

		const particlesProps = new Set([
			"particlesList",
			"particleLat",
			"particleLng",
			"particleAltitude",
			"particlesSize",
			"particlesSizeAttenuation",
			"particlesColor",
			"particlesTexture",
			"particleLabel",
		]);

		const ringsProps = new Set([
			"ringLat",
			"ringLng",
			"ringAltitude",
			"ringColor",
			"ringResolution",
			"ringMaxRadius",
			"ringPropagationSpeed",
			"ringRepeatPeriod",
		]);

		const labelsProps = new Set([
			"labelLat",
			"labelLng",
			"labelAltitude",
			"labelRotation",
			"labelText",
			"labelSize",
			"labelTypeFace",
			"labelColor",
			"labelResolution",
			"labelIncludeDot",
			"labelDotRadius",
			"labelDotOrientation",
			"labelsTransitionDuration",
			"labelLabel",
		]);

		const materialProps = new Set([
			"globeMaterial",
			"polygonCapMaterial",
			"polygonSideMaterial",
		]);

		const constantAccessorProps = new Set([
			"hexTopColor",
			"hexSideColor",
			"hexAltitude",
		]);

		const applyLayerProp = (
			props: Set<string>,
			prop: unknown,
			value: unknown,
		): void => {
			if (typeof prop !== "string" || !props.has(prop)) {
				return;
			}
			const setter = (globe as Record<string, unknown>)[prop];
			if (typeof setter === "function") {
				const nextValue = materialProps.has(prop)
					? buildMaterial(value)
					: constantAccessorProps.has(prop)
						? () => value
						: value;
				(setter as (arg: unknown) => void)(nextValue);
			}
		};

		const patchLayerData = (
			getter: () => Array<Record<string, unknown>> | undefined,
			setter: (data: Array<Record<string, unknown>>) => void,
			patches: Array<Record<string, unknown>>,
		): void => {
			const data = getter() ?? [];
			const index = new Map(
				data
					.map((datum) => {
						const id = datum.id;
						if (id === undefined || id === null) {
							return null;
						}
						return [String(id), datum] as const;
					})
					.filter(
						(entry): entry is [string, Record<string, unknown>] =>
							entry !== null,
					),
			);
			for (const patch of patches) {
				if (!patch || typeof patch !== "object") {
					continue;
				}
				const patchId = patch.id;
				if (patchId === undefined || patchId === null) {
					continue;
				}
				const target = index.get(String(patchId));
				if (!target) {
					continue;
				}
				Object.assign(target, patch);
			}
			setter(data);
		};

		const normalizeTilesData = (
			data: Array<Record<string, unknown>> | undefined,
		): Array<Record<string, unknown>> => {
			if (!data) {
				return [];
			}
			return data.map((entry) => {
				if (!entry || typeof entry !== "object") {
					return entry;
				}
				const material = materialFromSpec(
					(entry as { material?: unknown }).material,
				);
				return { ...entry, material };
			});
		};

		const normalizeParticlesData = (
			data: Array<Record<string, unknown>> | undefined,
		): Array<Record<string, unknown>> => {
			if (!data) {
				return [];
			}
			return data.map((entry) => {
				if (!entry || typeof entry !== "object") {
					return entry;
				}
				if (Array.isArray(entry)) {
					return entry;
				}
				const particles = (entry as { particles?: unknown }).particles;
				if (Array.isArray(particles)) {
					const list = particles as Array<Record<string, unknown>>;
					Object.entries(entry).forEach(([key, value]) => {
						if (key === "particles") {
							return;
						}
						let nextValue = value;
						if (key === "texture") {
							nextValue = textureFromSpec(value);
						}
						(list as unknown as Record<string, unknown>)[key] = nextValue;
					});
					return list as unknown as Record<string, unknown>;
				}
				const texture = textureFromSpec(
					(entry as { texture?: unknown }).texture,
				);
				return { ...entry, texture };
			});
		};

		model.on("msg:custom", (msg: unknown) => {
			if (
				typeof msg === "object" &&
				msg !== null &&
				"type" in msg &&
				(msg as { type: string }).type === "globe_tile_engine_clear_cache"
			) {
				globe.globeTileEngineClearCache();
			}
			if (
				typeof msg === "object" &&
				msg !== null &&
				"type" in msg &&
				"payload" in msg
			) {
				const { type, payload } = msg as {
					type: string;
					payload?: {
						data?: Array<Record<string, unknown>>;
						patches?: Array<Record<string, unknown>>;
						prop?: unknown;
						value?: unknown;
					};
				};
				if (type === "points_set_data") {
					globe.pointsData(payload?.data ?? []);
				} else if (type === "arcs_set_data") {
					globe.arcsData(payload?.data ?? []);
				} else if (type === "polygons_set_data") {
					globe.polygonsData(payload?.data ?? []);
				} else if (type === "paths_set_data") {
					globe.pathsData(payload?.data ?? []);
				} else if (type === "heatmaps_set_data") {
					globe.heatmapsData(payload?.data ?? []);
				} else if (type === "hex_polygons_set_data") {
					globe.hexPolygonsData(payload?.data ?? []);
				} else if (type === "tiles_set_data") {
					globe.tilesData(normalizeTilesData(payload?.data));
				} else if (type === "particles_set_data") {
					globe.particlesData(normalizeParticlesData(payload?.data));
				} else if (type === "rings_set_data") {
					globe.ringsData(payload?.data ?? []);
				} else if (type === "labels_set_data") {
					globe.labelsData(payload?.data ?? []);
				} else if (type === "points_patch_data") {
					patchLayerData(
						() => globe.pointsData() ?? [],
						(data) => globe.pointsData(data),
						payload?.patches ?? [],
					);
				} else if (type === "arcs_patch_data") {
					patchLayerData(
						() => globe.arcsData() ?? [],
						(data) => globe.arcsData(data),
						payload?.patches ?? [],
					);
				} else if (type === "polygons_patch_data") {
					patchLayerData(
						() => globe.polygonsData() ?? [],
						(data) => globe.polygonsData(data),
						payload?.patches ?? [],
					);
				} else if (type === "paths_patch_data") {
					patchLayerData(
						() => globe.pathsData() ?? [],
						(data) => globe.pathsData(data),
						payload?.patches ?? [],
					);
				} else if (type === "heatmaps_patch_data") {
					patchLayerData(
						() => globe.heatmapsData() ?? [],
						(data) => globe.heatmapsData(data),
						payload?.patches ?? [],
					);
				} else if (type === "hex_polygons_patch_data") {
					patchLayerData(
						() => globe.hexPolygonsData() ?? [],
						(data) => globe.hexPolygonsData(data),
						payload?.patches ?? [],
					);
				} else if (type === "tiles_patch_data") {
					patchLayerData(
						() => globe.tilesData() ?? [],
						(data) => globe.tilesData(normalizeTilesData(data)),
						payload?.patches ?? [],
					);
				} else if (type === "particles_patch_data") {
					patchLayerData(
						() => globe.particlesData() ?? [],
						(data) => globe.particlesData(normalizeParticlesData(data)),
						payload?.patches ?? [],
					);
				} else if (type === "rings_patch_data") {
					patchLayerData(
						() => globe.ringsData() ?? [],
						(data) => globe.ringsData(data),
						payload?.patches ?? [],
					);
				} else if (type === "labels_patch_data") {
					patchLayerData(
						() => globe.labelsData() ?? [],
						(data) => globe.labelsData(data),
						payload?.patches ?? [],
					);
				} else if (type === "points_prop") {
					applyLayerProp(pointProps, payload?.prop, payload?.value);
				} else if (type === "arcs_prop") {
					applyLayerProp(arcProps, payload?.prop, payload?.value);
				} else if (type === "polygons_prop") {
					applyLayerProp(polygonProps, payload?.prop, payload?.value);
				} else if (type === "paths_prop") {
					applyLayerProp(pathProps, payload?.prop, payload?.value);
				} else if (type === "heatmaps_prop") {
					applyLayerProp(heatmapProps, payload?.prop, payload?.value);
				} else if (type === "hex_polygons_prop") {
					applyLayerProp(hexPolygonProps, payload?.prop, payload?.value);
				} else if (type === "tiles_prop") {
					applyLayerProp(tilesProps, payload?.prop, payload?.value);
				} else if (type === "particles_prop") {
					applyLayerProp(particlesProps, payload?.prop, payload?.value);
				} else if (type === "rings_prop") {
					applyLayerProp(ringsProps, payload?.prop, payload?.value);
				} else if (type === "labels_prop") {
					applyLayerProp(labelsProps, payload?.prop, payload?.value);
				} else if (type === "globe_prop") {
					applyLayerProp(globeProps, payload?.prop, payload?.value);
				}
			}
		});

		const resize = () => {
			const { width } = el.getBoundingClientRect();
			if (width <= 0) {
				return;
			}

			const container = (outputArea || el.parentElement) as HTMLElement | null;
			let containerHeight = container ? container.clientHeight : 0;
			let containerPadding = 0;
			let maxHeight = 0;
			if (container) {
				const style = window.getComputedStyle(container);
				const paddingTop = Number.parseFloat(style.paddingTop);
				const paddingBottom = Number.parseFloat(style.paddingBottom);
				containerPadding = paddingTop + paddingBottom;
				const parsedMaxHeight = Number.parseFloat(style.maxHeight);
				if (Number.isFinite(parsedMaxHeight)) {
					maxHeight = parsedMaxHeight;
				}
				if (containerHeight > 0) {
					containerHeight = Math.max(0, containerHeight - containerPadding);
				}
			}
			const effectiveHeight =
				maxHeight > 0
					? Math.max(0, maxHeight - containerPadding)
					: containerHeight;
			const viewportHeight = window.innerHeight || 0;
			const rawSize = Math.min(
				width,
				effectiveHeight > 0 ? effectiveHeight : width,
				viewportHeight > 0 ? viewportHeight : width,
			);
			const size = Math.max(0, Math.floor(rawSize * 0.75));

			el.style.width = "100%";
			el.style.height = `${effectiveHeight > 0 ? effectiveHeight : size}px`;
			el.style.margin = "0";
			mount.style.width = `${size}px`;
			mount.style.height = `${size}px`;
			globe.width(size).height(size);
		};

		const applyLayoutSizing = (layout?: GlobeLayoutConfig): boolean => {
			const width = layout?.width;
			const height = layout?.height;
			const hasWidth = typeof width === "number" && Number.isFinite(width);
			const hasHeight = typeof height === "number" && Number.isFinite(height);

			if (!hasWidth && !hasHeight) {
				return false;
			}

			if (hasWidth) {
				mount.style.width = `${width}px`;
				globe.width(width);
			}
			if (hasHeight) {
				mount.style.height = `${height}px`;
				el.style.height = `${height}px`;
				globe.height(height);
			}

			if (hasWidth && !hasHeight) {
				mount.style.height = `${width}px`;
				el.style.height = `${width}px`;
				globe.height(width);
			}

			if (hasHeight && !hasWidth) {
				mount.style.width = `${height}px`;
				globe.width(height);
			}

			return true;
		};

		const applyLayoutProps = (layout?: GlobeLayoutConfig): void => {
			if (!layout) {
				return;
			}
			if (layout.globeOffset) {
				globe.globeOffset(layout.globeOffset);
			}
			if (layout.backgroundColor) {
				globe.backgroundColor(layout.backgroundColor);
			}
			if (layout.backgroundImageUrl) {
				globe.backgroundImageUrl(layout.backgroundImageUrl);
			}
		};

		const applyGlobeProps = (globeConfig?: GlobeLayerConfig): void => {
			if (!globeConfig) {
				return;
			}
			if (globeConfig.globeImageUrl !== undefined) {
				globe.globeImageUrl(globeConfig.globeImageUrl ?? null);
			}
			if (globeConfig.bumpImageUrl !== undefined) {
				globe.bumpImageUrl(globeConfig.bumpImageUrl ?? null);
			}
			if (globeConfig.globeTileEngineUrl !== undefined) {
				const template = globeConfig.globeTileEngineUrl;
				if (template) {
					globe.globeTileEngineUrl((x: number, y: number, l: number) =>
						template
							.replaceAll("{x}", String(x))
							.replaceAll("{y}", String(y))
							.replaceAll("{l}", String(l))
							.replaceAll("{z}", String(l)),
					);
				} else {
					globe.globeTileEngineUrl(null);
				}
			}
			if (globeConfig.showGlobe !== undefined) {
				globe.showGlobe(globeConfig.showGlobe);
			}
			if (globeConfig.showGraticules !== undefined) {
				globe.showGraticules(globeConfig.showGraticules);
			}
			if (globeConfig.showAtmosphere !== undefined) {
				globe.showAtmosphere(globeConfig.showAtmosphere);
			}
			if (globeConfig.atmosphereColor !== undefined) {
				globe.atmosphereColor(globeConfig.atmosphereColor);
			}
			if (globeConfig.atmosphereAltitude !== undefined) {
				globe.atmosphereAltitude(globeConfig.atmosphereAltitude);
			}
			if (globeConfig.globeCurvatureResolution !== undefined) {
				globe.globeCurvatureResolution(globeConfig.globeCurvatureResolution);
			}
			if (globeConfig.globeMaterial !== undefined) {
				const material = buildMaterial(globeConfig.globeMaterial);
				globe.globeMaterial(material);
			}
		};

		const applyPointsProps = (pointsConfig?: PointsLayerConfig): void => {
			if (!pointsConfig) {
				return;
			}
			if (pointsConfig.pointsData !== undefined) {
				globe.pointsData(pointsConfig.pointsData ?? []);
			}
			if (pointsConfig.pointLabel !== undefined) {
				globe.pointLabel(pointsConfig.pointLabel ?? null);
			}
			if (pointsConfig.pointLat !== undefined) {
				globe.pointLat(pointsConfig.pointLat ?? null);
			}
			if (pointsConfig.pointLng !== undefined) {
				globe.pointLng(pointsConfig.pointLng ?? null);
			}
			if (pointsConfig.pointColor !== undefined) {
				globe.pointColor(pointsConfig.pointColor ?? null);
			}
			if (pointsConfig.pointAltitude !== undefined) {
				globe.pointAltitude(pointsConfig.pointAltitude ?? null);
			}
			if (pointsConfig.pointRadius !== undefined) {
				globe.pointRadius(pointsConfig.pointRadius ?? null);
			}
			if (pointsConfig.pointResolution !== undefined) {
				globe.pointResolution(pointsConfig.pointResolution);
			}
			if (pointsConfig.pointsMerge !== undefined) {
				globe.pointsMerge(pointsConfig.pointsMerge);
			}
			if (pointsConfig.pointsTransitionDuration !== undefined) {
				globe.pointsTransitionDuration(pointsConfig.pointsTransitionDuration);
			}
		};

		const applyArcsProps = (arcsConfig?: ArcsLayerConfig): void => {
			if (!arcsConfig) {
				return;
			}
			if (arcsConfig.arcsData !== undefined) {
				globe.arcsData(arcsConfig.arcsData ?? []);
			}
			if (arcsConfig.arcLabel !== undefined) {
				globe.arcLabel(arcsConfig.arcLabel ?? null);
			}
			if (arcsConfig.arcStartLat !== undefined) {
				globe.arcStartLat(arcsConfig.arcStartLat ?? null);
			}
			if (arcsConfig.arcStartLng !== undefined) {
				globe.arcStartLng(arcsConfig.arcStartLng ?? null);
			}
			if (arcsConfig.arcStartAltitude !== undefined) {
				globe.arcStartAltitude(arcsConfig.arcStartAltitude ?? null);
			}
			if (arcsConfig.arcEndLat !== undefined) {
				globe.arcEndLat(arcsConfig.arcEndLat ?? null);
			}
			if (arcsConfig.arcEndLng !== undefined) {
				globe.arcEndLng(arcsConfig.arcEndLng ?? null);
			}
			if (arcsConfig.arcEndAltitude !== undefined) {
				globe.arcEndAltitude(arcsConfig.arcEndAltitude ?? null);
			}
			if (arcsConfig.arcColor !== undefined) {
				globe.arcColor(arcsConfig.arcColor ?? null);
			}
			if (arcsConfig.arcAltitude !== undefined) {
				globe.arcAltitude(arcsConfig.arcAltitude ?? null);
			}
			if (arcsConfig.arcAltitudeAutoScale !== undefined) {
				globe.arcAltitudeAutoScale(arcsConfig.arcAltitudeAutoScale ?? null);
			}
			if (arcsConfig.arcStroke !== undefined) {
				globe.arcStroke(arcsConfig.arcStroke ?? null);
			}
			if (arcsConfig.arcCurveResolution !== undefined) {
				globe.arcCurveResolution(arcsConfig.arcCurveResolution);
			}
			if (arcsConfig.arcCircularResolution !== undefined) {
				globe.arcCircularResolution(arcsConfig.arcCircularResolution);
			}
			if (arcsConfig.arcDashLength !== undefined) {
				globe.arcDashLength(arcsConfig.arcDashLength ?? null);
			}
			if (arcsConfig.arcDashGap !== undefined) {
				globe.arcDashGap(arcsConfig.arcDashGap ?? null);
			}
			if (arcsConfig.arcDashInitialGap !== undefined) {
				globe.arcDashInitialGap(arcsConfig.arcDashInitialGap ?? null);
			}
			if (arcsConfig.arcDashAnimateTime !== undefined) {
				globe.arcDashAnimateTime(arcsConfig.arcDashAnimateTime ?? null);
			}
			if (arcsConfig.arcsTransitionDuration !== undefined) {
				globe.arcsTransitionDuration(arcsConfig.arcsTransitionDuration);
			}
		};

		const applyPolygonsProps = (polygonsConfig?: PolygonsLayerConfig): void => {
			if (!polygonsConfig) {
				return;
			}
			if (polygonsConfig.polygonsData !== undefined) {
				globe.polygonsData(polygonsConfig.polygonsData ?? []);
			}
			if (polygonsConfig.polygonLabel !== undefined) {
				globe.polygonLabel(polygonsConfig.polygonLabel ?? null);
			}
			if (polygonsConfig.polygonGeoJsonGeometry !== undefined) {
				globe.polygonGeoJsonGeometry(
					polygonsConfig.polygonGeoJsonGeometry ?? null,
				);
			}
			if (polygonsConfig.polygonCapColor !== undefined) {
				globe.polygonCapColor(polygonsConfig.polygonCapColor ?? null);
			}
			if (polygonsConfig.polygonCapMaterial !== undefined) {
				globe.polygonCapMaterial(
					buildMaterial(polygonsConfig.polygonCapMaterial),
				);
			}
			if (polygonsConfig.polygonSideColor !== undefined) {
				globe.polygonSideColor(polygonsConfig.polygonSideColor ?? null);
			}
			if (polygonsConfig.polygonSideMaterial !== undefined) {
				globe.polygonSideMaterial(
					buildMaterial(polygonsConfig.polygonSideMaterial),
				);
			}
			if (polygonsConfig.polygonStrokeColor !== undefined) {
				globe.polygonStrokeColor(polygonsConfig.polygonStrokeColor ?? null);
			}
			if (polygonsConfig.polygonAltitude !== undefined) {
				globe.polygonAltitude(polygonsConfig.polygonAltitude ?? null);
			}
			if (polygonsConfig.polygonCapCurvatureResolution !== undefined) {
				globe.polygonCapCurvatureResolution(
					polygonsConfig.polygonCapCurvatureResolution ?? null,
				);
			}
			if (polygonsConfig.polygonsTransitionDuration !== undefined) {
				globe.polygonsTransitionDuration(
					polygonsConfig.polygonsTransitionDuration,
				);
			}
		};

		const applyPathsProps = (pathsConfig?: PathsLayerConfig): void => {
			if (!pathsConfig) {
				return;
			}
			if (pathsConfig.pathsData !== undefined) {
				globe.pathsData(pathsConfig.pathsData ?? []);
			}
			if (pathsConfig.pathLabel !== undefined) {
				globe.pathLabel(pathsConfig.pathLabel ?? null);
			}
			if (pathsConfig.pathResolution !== undefined) {
				globe.pathResolution(pathsConfig.pathResolution);
			}
			if (pathsConfig.pathColor !== undefined) {
				globe.pathColor(pathsConfig.pathColor ?? null);
			}
			if (pathsConfig.pathStroke !== undefined) {
				globe.pathStroke(pathsConfig.pathStroke ?? null);
			}
			if (pathsConfig.pathDashLength !== undefined) {
				globe.pathDashLength(pathsConfig.pathDashLength ?? null);
			}
			if (pathsConfig.pathDashGap !== undefined) {
				globe.pathDashGap(pathsConfig.pathDashGap ?? null);
			}
			if (pathsConfig.pathDashInitialGap !== undefined) {
				globe.pathDashInitialGap(pathsConfig.pathDashInitialGap ?? null);
			}
			if (pathsConfig.pathDashAnimateTime !== undefined) {
				globe.pathDashAnimateTime(pathsConfig.pathDashAnimateTime ?? null);
			}
			if (pathsConfig.pathTransitionDuration !== undefined) {
				globe.pathTransitionDuration(pathsConfig.pathTransitionDuration);
			}
		};

		const applyHeatmapsProps = (heatmapsConfig?: HeatmapsLayerConfig): void => {
			if (!heatmapsConfig) {
				return;
			}
			if (heatmapsConfig.heatmapsData !== undefined) {
				globe.heatmapsData(heatmapsConfig.heatmapsData ?? []);
			}
			if (heatmapsConfig.heatmapPoints !== undefined) {
				globe.heatmapPoints(heatmapsConfig.heatmapPoints ?? null);
			}
			if (heatmapsConfig.heatmapPointLat !== undefined) {
				globe.heatmapPointLat(heatmapsConfig.heatmapPointLat ?? null);
			}
			if (heatmapsConfig.heatmapPointLng !== undefined) {
				globe.heatmapPointLng(heatmapsConfig.heatmapPointLng ?? null);
			}
			if (heatmapsConfig.heatmapPointWeight !== undefined) {
				globe.heatmapPointWeight(heatmapsConfig.heatmapPointWeight ?? null);
			}
			if (heatmapsConfig.heatmapBandwidth !== undefined) {
				globe.heatmapBandwidth(heatmapsConfig.heatmapBandwidth ?? null);
			}
			if (heatmapsConfig.heatmapColorFn !== undefined) {
				globe.heatmapColorFn(heatmapsConfig.heatmapColorFn ?? null);
			}
			if (heatmapsConfig.heatmapColorSaturation !== undefined) {
				globe.heatmapColorSaturation(
					heatmapsConfig.heatmapColorSaturation ?? null,
				);
			}
			if (heatmapsConfig.heatmapBaseAltitude !== undefined) {
				globe.heatmapBaseAltitude(heatmapsConfig.heatmapBaseAltitude ?? null);
			}
			if (heatmapsConfig.heatmapTopAltitude !== undefined) {
				globe.heatmapTopAltitude(heatmapsConfig.heatmapTopAltitude ?? null);
			}
			if (heatmapsConfig.heatmapsTransitionDuration !== undefined) {
				globe.heatmapsTransitionDuration(
					heatmapsConfig.heatmapsTransitionDuration,
				);
			}
		};

		const applyHexedPolygonsProps = (
			hexPolygonsConfig?: HexedPolygonsLayerConfig,
		): void => {
			if (!hexPolygonsConfig) {
				return;
			}
			if (hexPolygonsConfig.hexPolygonsData !== undefined) {
				globe.hexPolygonsData(hexPolygonsConfig.hexPolygonsData ?? []);
			}
			if (hexPolygonsConfig.hexPolygonGeoJsonGeometry !== undefined) {
				globe.hexPolygonGeoJsonGeometry(
					hexPolygonsConfig.hexPolygonGeoJsonGeometry ?? null,
				);
			}
			if (hexPolygonsConfig.hexPolygonColor !== undefined) {
				globe.hexPolygonColor(hexPolygonsConfig.hexPolygonColor ?? null);
			}
			if (hexPolygonsConfig.hexPolygonAltitude !== undefined) {
				globe.hexPolygonAltitude(hexPolygonsConfig.hexPolygonAltitude ?? null);
			}
			if (hexPolygonsConfig.hexPolygonResolution !== undefined) {
				globe.hexPolygonResolution(
					hexPolygonsConfig.hexPolygonResolution ?? null,
				);
			}
			if (hexPolygonsConfig.hexPolygonMargin !== undefined) {
				globe.hexPolygonMargin(hexPolygonsConfig.hexPolygonMargin ?? null);
			}
			if (hexPolygonsConfig.hexPolygonUseDots !== undefined) {
				globe.hexPolygonUseDots(hexPolygonsConfig.hexPolygonUseDots);
			}
			if (hexPolygonsConfig.hexPolygonCurvatureResolution !== undefined) {
				globe.hexPolygonCurvatureResolution(
					hexPolygonsConfig.hexPolygonCurvatureResolution ?? null,
				);
			}
			if (hexPolygonsConfig.hexPolygonDotResolution !== undefined) {
				globe.hexPolygonDotResolution(
					hexPolygonsConfig.hexPolygonDotResolution ?? null,
				);
			}
			if (hexPolygonsConfig.hexPolygonsTransitionDuration !== undefined) {
				globe.hexPolygonsTransitionDuration(
					hexPolygonsConfig.hexPolygonsTransitionDuration,
				);
			}
			if (hexPolygonsConfig.hexPolygonLabel !== undefined) {
				globe.hexPolygonLabel(hexPolygonsConfig.hexPolygonLabel ?? null);
			}
		};

		const applyTilesProps = (tilesConfig?: TilesLayerConfig): void => {
			if (!tilesConfig) {
				return;
			}
			if (tilesConfig.tilesData !== undefined) {
				globe.tilesData(normalizeTilesData(tilesConfig.tilesData));
			}
			if (tilesConfig.tileLat !== undefined) {
				globe.tileLat(tilesConfig.tileLat ?? null);
			}
			if (tilesConfig.tileLng !== undefined) {
				globe.tileLng(tilesConfig.tileLng ?? null);
			}
			if (tilesConfig.tileAltitude !== undefined) {
				globe.tileAltitude(tilesConfig.tileAltitude ?? null);
			}
			if (tilesConfig.tileWidth !== undefined) {
				globe.tileWidth(tilesConfig.tileWidth ?? null);
			}
			if (tilesConfig.tileHeight !== undefined) {
				globe.tileHeight(tilesConfig.tileHeight ?? null);
			}
			if (tilesConfig.tileUseGlobeProjection !== undefined) {
				globe.tileUseGlobeProjection(tilesConfig.tileUseGlobeProjection);
			}
			if (tilesConfig.tileMaterial !== undefined) {
				globe.tileMaterial(tilesConfig.tileMaterial ?? null);
			}
			if (tilesConfig.tileCurvatureResolution !== undefined) {
				globe.tileCurvatureResolution(
					tilesConfig.tileCurvatureResolution ?? null,
				);
			}
			if (tilesConfig.tilesTransitionDuration !== undefined) {
				globe.tilesTransitionDuration(tilesConfig.tilesTransitionDuration);
			}
			if (tilesConfig.tileLabel !== undefined) {
				globe.tileLabel(tilesConfig.tileLabel ?? null);
			}
		};

		const applyParticlesProps = (
			particlesConfig?: ParticlesLayerConfig,
		): void => {
			if (!particlesConfig) {
				return;
			}
			if (particlesConfig.particlesData !== undefined) {
				globe.particlesData(
					normalizeParticlesData(particlesConfig.particlesData),
				);
			}
			if (particlesConfig.particlesList !== undefined) {
				globe.particlesList(particlesConfig.particlesList ?? null);
			}
			if (particlesConfig.particleLat !== undefined) {
				globe.particleLat(particlesConfig.particleLat ?? null);
			}
			if (particlesConfig.particleLng !== undefined) {
				globe.particleLng(particlesConfig.particleLng ?? null);
			}
			if (particlesConfig.particleAltitude !== undefined) {
				globe.particleAltitude(particlesConfig.particleAltitude ?? null);
			}
			if (particlesConfig.particlesSize !== undefined) {
				globe.particlesSize(particlesConfig.particlesSize ?? null);
			}
			if (particlesConfig.particlesSizeAttenuation !== undefined) {
				globe.particlesSizeAttenuation(
					particlesConfig.particlesSizeAttenuation ?? null,
				);
			}
			if (particlesConfig.particlesColor !== undefined) {
				globe.particlesColor(particlesConfig.particlesColor ?? null);
			}
			if (particlesConfig.particlesTexture !== undefined) {
				globe.particlesTexture(particlesConfig.particlesTexture ?? null);
			}
			if (particlesConfig.particleLabel !== undefined) {
				globe.particleLabel(particlesConfig.particleLabel ?? null);
			}
		};

		const applyRingsProps = (ringsConfig?: RingsLayerConfig): void => {
			if (!ringsConfig) {
				return;
			}
			if (ringsConfig.ringsData !== undefined) {
				globe.ringsData(ringsConfig.ringsData ?? []);
			}
			if (ringsConfig.ringLat !== undefined) {
				globe.ringLat(ringsConfig.ringLat ?? null);
			}
			if (ringsConfig.ringLng !== undefined) {
				globe.ringLng(ringsConfig.ringLng ?? null);
			}
			if (ringsConfig.ringAltitude !== undefined) {
				globe.ringAltitude(ringsConfig.ringAltitude ?? null);
			}
			if (ringsConfig.ringColor !== undefined) {
				globe.ringColor(ringsConfig.ringColor ?? null);
			}
			if (ringsConfig.ringResolution !== undefined) {
				globe.ringResolution(ringsConfig.ringResolution);
			}
			if (ringsConfig.ringMaxRadius !== undefined) {
				globe.ringMaxRadius(ringsConfig.ringMaxRadius ?? null);
			}
			if (ringsConfig.ringPropagationSpeed !== undefined) {
				globe.ringPropagationSpeed(ringsConfig.ringPropagationSpeed ?? null);
			}
			if (ringsConfig.ringRepeatPeriod !== undefined) {
				globe.ringRepeatPeriod(ringsConfig.ringRepeatPeriod ?? null);
			}
		};

		const applyLabelsProps = (labelsConfig?: LabelsLayerConfig): void => {
			if (!labelsConfig) {
				return;
			}
			if (labelsConfig.labelsData !== undefined) {
				globe.labelsData(labelsConfig.labelsData ?? []);
			}
			if (labelsConfig.labelLat !== undefined) {
				globe.labelLat(labelsConfig.labelLat ?? null);
			}
			if (labelsConfig.labelLng !== undefined) {
				globe.labelLng(labelsConfig.labelLng ?? null);
			}
			if (labelsConfig.labelAltitude !== undefined) {
				globe.labelAltitude(labelsConfig.labelAltitude ?? null);
			}
			if (labelsConfig.labelRotation !== undefined) {
				globe.labelRotation(labelsConfig.labelRotation ?? null);
			}
			if (labelsConfig.labelText !== undefined) {
				globe.labelText(labelsConfig.labelText ?? null);
			}
			if (labelsConfig.labelSize !== undefined) {
				globe.labelSize(labelsConfig.labelSize ?? null);
			}
			if (labelsConfig.labelTypeFace !== undefined) {
				globe.labelTypeFace(labelsConfig.labelTypeFace ?? null);
			}
			if (labelsConfig.labelColor !== undefined) {
				globe.labelColor(labelsConfig.labelColor ?? null);
			}
			if (labelsConfig.labelResolution !== undefined) {
				globe.labelResolution(labelsConfig.labelResolution);
			}
			if (labelsConfig.labelIncludeDot !== undefined) {
				globe.labelIncludeDot(labelsConfig.labelIncludeDot);
			}
			if (labelsConfig.labelDotRadius !== undefined) {
				globe.labelDotRadius(labelsConfig.labelDotRadius ?? null);
			}
			if (labelsConfig.labelDotOrientation !== undefined) {
				globe.labelDotOrientation(labelsConfig.labelDotOrientation ?? null);
			}
			if (labelsConfig.labelsTransitionDuration !== undefined) {
				globe.labelsTransitionDuration(labelsConfig.labelsTransitionDuration);
			}
			if (labelsConfig.labelLabel !== undefined) {
				globe.labelLabel(labelsConfig.labelLabel ?? null);
			}
		};

		const applyViewProps = (viewConfig?: GlobeViewConfig): void => {
			if (!viewConfig || !viewConfig.pointOfView) {
				return;
			}
			const transitionMs = viewConfig.transitionMs ?? 0;
			globe.pointOfView(viewConfig.pointOfView, transitionMs);
			(globalThis as { __pyglobegl_pov?: PointOfView }).__pyglobegl_pov =
				globe.pointOfView();
		};

		const enableAutoResize = () => {
			if (resizeObserver) {
				return;
			}
			resize();
			resizeObserver = new ResizeObserver(resize);
			resizeObserver.observe(el);
		};

		const disableAutoResize = () => {
			resizeObserver?.disconnect();
			resizeObserver = undefined;
		};

		const applyConfig = (config?: GlobeConfig) => {
			const layout = config?.layout;
			const globeConfig = config?.globe;
			const pointsConfig = config?.points;
			const arcsConfig = config?.arcs;
			const polygonsConfig = config?.polygons;
			const pathsConfig = config?.paths;
			const heatmapsConfig = config?.heatmaps;
			const hexPolygonsConfig = config?.hexed_polygons;
			const tilesConfig = config?.tiles;
			const particlesConfig = config?.particles;
			const ringsConfig = config?.rings;
			const labelsConfig = config?.labels;
			const viewConfig = config?.view;
			const hasExplicitSize = applyLayoutSizing(layout);
			if (hasExplicitSize) {
				disableAutoResize();
			} else {
				enableAutoResize();
			}
			applyLayoutProps(layout);
			applyGlobeProps(globeConfig);
			applyPointsProps(pointsConfig);
			applyArcsProps(arcsConfig);
			applyPolygonsProps(polygonsConfig);
			applyPathsProps(pathsConfig);
			applyHeatmapsProps(heatmapsConfig);
			applyHexedPolygonsProps(hexPolygonsConfig);
			applyTilesProps(tilesConfig);
			applyParticlesProps(particlesConfig);
			applyRingsProps(ringsConfig);
			applyLabelsProps(labelsConfig);
			applyViewProps(viewConfig);
		};

		applyConfig(initialConfig);

		model.on("change:config", () => {
			applyConfig(getConfig());
		});
	});

	return () => {
		resizeObserver?.disconnect();
		const globalScope = globalThis as {
			__pyglobegl_globe_ready?: boolean;
			__pyglobegl_renderer_attributes?: WebGLContextAttributes | null;
			__pyglobegl_init_config?: GlobeInitConfig;
			__pyglobegl_pov?: PointOfView;
		};
		delete globalScope.__pyglobegl_globe_ready;
		delete globalScope.__pyglobegl_renderer_attributes;
		delete globalScope.__pyglobegl_init_config;
		delete globalScope.__pyglobegl_pov;
	};
}

export default { render };
