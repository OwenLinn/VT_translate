import type { CSSProperties } from "react";
import { clamp } from "../utils/clamp";

interface GlassSliderProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  display?: (value: number) => string;
  onChange: (value: number) => void;
}

export function GlassSlider({ label, value, min, max, step, display, onChange }: GlassSliderProps): JSX.Element {
  const pct = ((value - min) / (max - min)) * 100;

  return (
    <label className="glass-slider no-drag">
      <span className="glass-slider__top">
        <span>{label}</span>
        <strong>{display ? display(value) : value.toFixed(2)}</strong>
      </span>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        style={{ "--slider-pct": `${clamp(pct, 0, 100)}%` } as CSSProperties}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </label>
  );
}
