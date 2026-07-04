import type { CSSProperties, PropsWithChildren } from "react";
import { motion } from "framer-motion";
import { useTuningStore } from "../state/tuningStore";
import { GlassEdge } from "./GlassEdge";
import { GlassHighlight } from "./GlassHighlight";

interface GlassCardProps extends PropsWithChildren {
  className?: string;
  dense?: boolean;
}

export function GlassCard({ children, className = "", dense = false }: GlassCardProps): JSX.Element {
  const tuning = useTuningStore();
  const style = {
    "--glass-radius": `${tuning.cornerRadius}px`,
    "--glass-card-opacity": tuning.cardOpacity,
    "--glass-panel-tint": tuning.panelTintOpacity,
    "--glass-edge-width": `${tuning.edgeWidth}px`,
    "--glass-edge-opacity": tuning.edgeOpacity,
    "--glass-rgb-shift": `${tuning.rgbShift}px`,
    "--glass-iridescence": tuning.iridescenceOpacity,
    "--glass-highlight": tuning.highlightOpacity,
    "--glass-shadow-opacity": tuning.shadowOpacity,
    "--glass-shadow-blur": `${tuning.shadowBlur}px`
  } as CSSProperties;

  return (
    <motion.section
      className={`glass-card ${dense ? "glass-card--dense" : ""} ${className}`}
      style={style}
      initial={{ opacity: 0, scale: 0.97, y: 10 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.98, y: 6 }}
      transition={{ duration: tuning.motionMs / 1000, ease: [0.2, 0.85, 0.25, 1] }}
    >
      <GlassEdge />
      <GlassHighlight />
      <div className="glass-card__content">{children}</div>
    </motion.section>
  );
}
