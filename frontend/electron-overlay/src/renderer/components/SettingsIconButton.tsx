import { motion } from "framer-motion";

interface SettingsIconButtonProps {
  open: boolean;
  onClick: () => void;
}

export function SettingsIconButton({ open, onClick }: SettingsIconButtonProps): JSX.Element {
  return (
    <motion.button
      className="settings-icon no-drag"
      type="button"
      aria-label="Toggle overlay controls"
      title="Overlay controls"
      onClick={onClick}
      whileHover={{ scale: 1.04 }}
      whileTap={{ scale: 0.94 }}
    >
      <span className={open ? "settings-icon__glyph settings-icon__glyph--open" : "settings-icon__glyph"} />
    </motion.button>
  );
}
