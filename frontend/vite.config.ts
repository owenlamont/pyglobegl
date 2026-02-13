import anywidget from "@anywidget/vite";
import { defineConfig } from "vite";

export default defineConfig({
	plugins: [anywidget()],
	build: {
		outDir: "../src/pyglobegl/_static",
		emptyOutDir: true,
		target: "esnext",
		rollupOptions: {
			output: {
				banner:
					"if (globalThis.GPUShaderStage === undefined) { globalThis.GPUShaderStage = { VERTEX: 1, FRAGMENT: 2, COMPUTE: 4 }; }",
				inlineDynamicImports: true,
			},
		},
		lib: {
			entry: "src/index.ts",
			formats: ["es"],
			fileName: "index",
		},
	},
});
