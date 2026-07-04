import { motion } from "framer-motion";
import { useTuningStore } from "../state/tuningStore";

interface LiquidThumbProps {
  index: number;
  count: number;
}

export function LiquidThumb({ index, count }: LiquidThumbProps): JSX.Element {
  const tuning = useTuningStore();
  return (
    <motion.div
      className="liquid-thumb"
      animate={{
        left: `${(100 / count) * index}%`,
        width: `${100 / count}%`,
        scaleX: tuning.thumbStretch
      }}
      transition={{
        type: "spring",
        stiffness: 420,
        damping: 34,
        mass: 0.7
      }}
    />
  );
}
