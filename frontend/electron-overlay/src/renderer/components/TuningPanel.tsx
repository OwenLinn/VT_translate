import { cleanDark } from "../presets/cleanDark";
import { debugStrong } from "../presets/debugStrong";
import { elegantGlass } from "../presets/elegantGlass";
import { ultraCleanDark } from "../presets/ultraCleanDark";
import { useTuningStore, type GlassTuning, type PresetName } from "../state/tuningStore";
import { copyPresetToml } from "../utils/copyPreset";
import { GlassCard } from "./GlassCard";
import { GlassSlider } from "./GlassSlider";
import { SegmentedControl } from "./SegmentedControl";

const presets: Record<PresetName, Partial<GlassTuning>> = {
  cleanDark,
  ultraCleanDark,
  elegantGlass,
  debugStrong
};

export function TuningPanel(): JSX.Element {
  const tuning = useTuningStore();
  const applyPreset = useTuningStore((state) => state.applyPreset);
  const setValue = useTuningStore((state) => state.setValue);

  return (
    <GlassCard className="tuning-panel" dense>
      <div className="tuning-panel__header">
        <div>
          <h2>Liquid Glass Tuning</h2>
          <p>Phase 2 visual prototype only.</p>
        </div>
        <button
          className="text-button no-drag"
          type="button"
          onClick={() => {
            void copyPresetToml(tuning).then((text) => console.info(text));
          }}
        >
          Copy Parameters
        </button>
      </div>
      <SegmentedControl<PresetName>
        value={tuning.presetName}
        options={[
          { label: "Clean", value: "cleanDark" },
          { label: "Ultra", value: "ultraCleanDark" },
          { label: "Elegant", value: "elegantGlass" },
          { label: "Debug", value: "debugStrong" }
        ]}
        onChange={(value) => applyPreset(value, presets[value])}
      />
      <div className="tuning-panel__grid">
        <GlassSlider label="Subtitle opacity" value={tuning.subtitleOpacity} min={0.25} max={0.95} step={0.01} onChange={(value) => setValue("subtitleOpacity", value)} />
        <GlassSlider label="Card opacity" value={tuning.cardOpacity} min={0.15} max={0.85} step={0.01} onChange={(value) => setValue("cardOpacity", value)} />
        <GlassSlider label="Panel tint" value={tuning.panelTintOpacity} min={0} max={0.7} step={0.01} onChange={(value) => setValue("panelTintOpacity", value)} />
        <GlassSlider label="Corner radius" value={tuning.cornerRadius} min={12} max={44} step={1} display={(value) => `${Math.round(value)} px`} onChange={(value) => setValue("cornerRadius", value)} />
        <GlassSlider label="Edge width" value={tuning.edgeWidth} min={0.5} max={4} step={0.1} display={(value) => `${value.toFixed(1)} px`} onChange={(value) => setValue("edgeWidth", value)} />
        <GlassSlider label="Edge opacity" value={tuning.edgeOpacity} min={0.05} max={0.9} step={0.01} onChange={(value) => setValue("edgeOpacity", value)} />
        <GlassSlider label="RGB split" value={tuning.rgbShift} min={0} max={0.5} step={0.01} onChange={(value) => setValue("rgbShift", value)} />
        <GlassSlider label="Iridescence" value={tuning.iridescenceOpacity} min={0} max={0.8} step={0.01} onChange={(value) => setValue("iridescenceOpacity", value)} />
        <GlassSlider label="Highlight" value={tuning.highlightOpacity} min={0.05} max={0.7} step={0.01} onChange={(value) => setValue("highlightOpacity", value)} />
        <GlassSlider label="Shadow" value={tuning.shadowOpacity} min={0} max={0.8} step={0.01} onChange={(value) => setValue("shadowOpacity", value)} />
        <GlassSlider label="Shadow blur" value={tuning.shadowBlur} min={8} max={60} step={1} display={(value) => `${Math.round(value)} px`} onChange={(value) => setValue("shadowBlur", value)} />
        <GlassSlider label="Font scale" value={tuning.fontScale} min={0.82} max={1.26} step={0.01} onChange={(value) => setValue("fontScale", value)} />
        <GlassSlider label="Motion" value={tuning.motionMs} min={80} max={360} step={10} display={(value) => `${Math.round(value)} ms`} onChange={(value) => setValue("motionMs", value)} />
        <GlassSlider label="Thumb stretch" value={tuning.thumbStretch} min={1} max={1.2} step={0.01} onChange={(value) => setValue("thumbStretch", value)} />
      </div>
    </GlassCard>
  );
}
