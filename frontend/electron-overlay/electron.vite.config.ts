import { resolve } from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig, externalizeDepsPlugin } from "electron-vite";

export default defineConfig({
  main: {
    plugins: [externalizeDepsPlugin()]
  },
  preload: {
    plugins: [externalizeDepsPlugin()],
    build: {
      rollupOptions: {
        input: resolve("src/preload/preload.ts"),
        output: {
          format: "cjs",
          entryFileNames: "[name].cjs"
        }
      }
    }
  },
  renderer: {
    root: ".",
    resolve: {
      alias: {
        "@renderer": resolve("src/renderer")
      }
    },
    plugins: [react()],
    build: {
      rollupOptions: {
        input: resolve("index.html")
      }
    }
  }
});
