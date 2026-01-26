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

type GlobeConfig = {
	init?: GlobeInitConfig;
	layout?: GlobeLayoutConfig;
	globe?: GlobeLayerConfig;
	points?: PointsLayerConfig;
	arcs?: ArcsLayerConfig;
	polygons?: PolygonsLayerConfig;
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

		const materialProps = new Set([
			"globeMaterial",
			"polygonCapMaterial",
			"polygonSideMaterial",
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
				} else if (type === "points_prop") {
					applyLayerProp(pointProps, payload?.prop, payload?.value);
				} else if (type === "arcs_prop") {
					applyLayerProp(arcProps, payload?.prop, payload?.value);
				} else if (type === "polygons_prop") {
					applyLayerProp(polygonProps, payload?.prop, payload?.value);
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
