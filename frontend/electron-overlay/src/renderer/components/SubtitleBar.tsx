import type { CSSProperties } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useOverlayStore } from "../state/overlayStore";
import { useTuningStore } from "../state/tuningStore";
import { GlassCard } from "./GlassCard";
import { SettingsIconButton } from "./SettingsIconButton";

export function SubtitleBar({ showSettingsButton = true }: { showSettingsButton?: boolean }): JSX.Element {
  const {
    source,
    translation,
    subtitleKind,
    showSource,
    showTranslation,
    latencyMs,
    segmentId,
    setControlOpen,
    controlOpen
  } = useOverlayStore();
  const tuning = useTuningStore();

  return (
    <GlassCard className="subtitle-bar">
      <div
        className="subtitle-bar__body"
        style={
          {
            "--subtitle-opacity": tuning.subtitleOpacity,
            "--font-scale": tuning.fontScale
          } as CSSProperties
        }
      >
        <AnimatePresence mode="popLayout">
          <motion.div
            key={`${segmentId}-${subtitleKind}`}
            className={`subtitle-text subtitle-text--${subtitleKind}`}
            initial={{ opacity: 0, y: 10, filter: "blur(6px)" }}
            animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
            exit={{ opacity: 0, y: -6, filter: "blur(4px)" }}
            transition={{ duration: tuning.motionMs / 1000 }}
          >
            {showSource && <div className="subtitle-source">{source}</div>}
            {showTranslation && <div className="subtitle-translation">{translation}</div>}
          </motion.div>
        </AnimatePresence>
      </div>
      <div className="subtitle-bar__meta">
        <span>{subtitleKind}</span>
        <span>{latencyMs === null ? "--" : `${latencyMs} ms`}</span>
      </div>
      {showSettingsButton && (
        <SettingsIconButton open={controlOpen} onClick={() => setControlOpen(!controlOpen)} />
      )}
    </GlassCard>
  );
}
