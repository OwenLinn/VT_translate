import { create } from "zustand";
import { cleanDark } from "../presets/cleanDark";

export type PresetName = "cleanDark" | "ultraCleanDark" | "elegantGlass" | "debugStrong";

export interface GlassTuning {
  presetName: PresetName;
  subtitleOpacity: number;
  cardOpacity: number;
  panelTintOpacity: number;
  cornerRadius: number;
  edgeWidth: number;
  edgeOpacity: number;
  rgbShift: number;
  iridescenceOpacity: number;
  highlightOpacity: number;
  shadowOpacity: number;
  shadowBlur: number;
  fontScale: number;
  motionMs: number;
  thumbStretch: number;
}

interface TuningState extends GlassTuning {
  setValue: <K extends keyof GlassTuning>(key: K, value: GlassTuning[K]) => void;
  applyPreset: (presetName: PresetName, preset: Partial<GlassTuning>) => void;
}

export const useTuningStore = create<TuningState>((set) => ({
  ...cleanDark,
  setValue: (key, value) => set({ [key]: value } as Partial<TuningState>),
  applyPreset: (presetName, preset) =>
    set({
      ...preset,
      presetName
    })
}));
