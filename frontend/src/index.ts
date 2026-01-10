import earthTextureUrl from "./assets/earth-day.jpg";

type AnyWidgetRenderProps = {
	el: HTMLElement;
	model: {
		get: (key: string) => unknown;
		set: (key: string, value: unknown) => void;
		save_changes: () => void;
		on: (event: string, callback: () => void) => void;
	};
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

export function render({ el }: AnyWidgetRenderProps): void {
	el.style.width = "100%";
	el.style.height = "500px";
	el.style.minHeight = "500px";

	ensureWebGPUShaderStage();

	void import("globe.gl").then(({ default: Globe }) => {
		const globe = Globe()(el);
		globe.pointOfView({ lat: 0, lng: 0, altitude: 2 }, 0);
		globe.globeImageUrl(earthTextureUrl);
	});
}

export default { render };
