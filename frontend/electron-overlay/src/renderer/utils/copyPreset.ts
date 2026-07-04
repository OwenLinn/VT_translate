import type { GlassTuning } from "../state/tuningStore";

export function buildPresetToml(tuning: GlassTuning): string {
  return [
    "[electron_overlay.glass]",
    `preset = "${tuning.presetName}"`,
    `subtitle_opacity = ${tuning.subtitleOpacity.toFixed(2)}`,
    `card_opacity = ${tuning.cardOpacity.toFixed(2)}`,
    `panel_tint_opacity = ${tuning.panelTintOpacity.toFixed(2)}`,
    `corner_radius = ${Math.round(tuning.cornerRadius)}`,
    `edge_width = ${tuning.edgeWidth.toFixed(2)}`,
    `edge_opacity = ${tuning.edgeOpacity.toFixed(2)}`,
    `rgb_shift = ${tuning.rgbShift.toFixed(2)}`,
    `iridescence_opacity = ${tuning.iridescenceOpacity.toFixed(2)}`,
    `highlight_opacity = ${tuning.highlightOpacity.toFixed(2)}`,
    `shadow_opacity = ${tuning.shadowOpacity.toFixed(2)}`,
    `shadow_blur = ${Math.round(tuning.shadowBlur)}`,
    "",
    "[electron_overlay.animation]",
    `motion_ms = ${Math.round(tuning.motionMs)}`,
    `thumb_stretch = ${tuning.thumbStretch.toFixed(2)}`
  ].join("\n");
}

export async function copyPresetToml(tuning: GlassTuning): Promise<string> {
  const toml = buildPresetToml(tuning);
  if (window.electronOverlay) {
    await window.electronOverlay.copyText(toml);
  } else if (navigator.clipboard) {
    await navigator.clipboard.writeText(toml);
  }
  return toml;
}
