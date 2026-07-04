/// <reference types="vite/client" />

import type { OverlayRendererApi } from "../shared/overlayIpcTypes";

declare global {
  interface Window {
    electronOverlay?: OverlayRendererApi;
  }
}
