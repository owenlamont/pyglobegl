type AnyWidgetRenderProps = {
	el: HTMLElement;
	model: {
		get: (key: string) => unknown;
		set: (key: string, value: unknown) => void;
		save_changes: () => void;
		on: (event: string, callback: () => void) => void;
	};
};

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

type GlobeConfig = {
	init?: GlobeInitConfig;
	layout?: GlobeLayoutConfig;
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
		const globe = new Globe(mount, initialConfig?.init);
		globe.pointOfView({ lat: 0, lng: 0, altitude: 2.8 }, 0);
		globe.atmosphereAltitude(0.05);

		const outputArea = el.closest(".output-area") as HTMLElement | null;

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
			const hasExplicitSize = applyLayoutSizing(layout);
			if (hasExplicitSize) {
				disableAutoResize();
			} else {
				enableAutoResize();
			}
			applyLayoutProps(layout);
		};

		applyConfig(initialConfig);

		model.on("change:config", () => {
			applyConfig(getConfig());
		});
	});

	return () => {
		resizeObserver?.disconnect();
	};
}

export default { render };
