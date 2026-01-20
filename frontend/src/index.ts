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

type GlobeConfig = {
	init?: GlobeInitConfig;
	layout?: GlobeLayoutConfig;
	globe?: GlobeLayerConfig;
	points?: PointsLayerConfig;
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

export function render({ el, model }: AnyWidgetRenderProps): () => void {
	el.style.width = "100%";
	el.style.height = "auto";
	el.style.display = "flex";
	el.style.justifyContent = "center";
	el.style.alignItems = "center";

	ensureWebGPUShaderStage();

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

		model.on("msg:custom", (msg: unknown) => {
			if (
				typeof msg === "object" &&
				msg !== null &&
				"type" in msg &&
				(msg as { type: string }).type === "globe_tile_engine_clear_cache"
			) {
				globe.globeTileEngineClearCache();
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
