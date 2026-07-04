import { command } from "../bridge/wsClient";
import { useOverlayStore, type DisplayMode, type PopoverKind } from "../state/overlayStore";
import { GlassCard } from "./GlassCard";
import { SegmentedControl } from "./SegmentedControl";

interface OptionPopoverCardProps {
  kind: Exclude<PopoverKind, null>;
  sendCommand: (message: ReturnType<typeof command>) => boolean;
}

export function OptionPopoverCard({ kind, sendCommand }: OptionPopoverCardProps): JSX.Element {
  const {
    displayMode,
    targetLang,
    sourceLang,
    translationModel,
    setDisplayMode,
    setTargetLang,
    setSourceLang,
    setTranslationModel
  } = useOverlayStore();

  return (
    <GlassCard className="option-popover" dense>
      {kind === "display" && (
        <SegmentedControl<DisplayMode>
          value={displayMode}
          options={[
            { label: "Trans", value: "translation" },
            { label: "Both", value: "source-translation" },
            { label: "Source", value: "source" }
          ]}
          onChange={(value) => {
            setDisplayMode(value);
            sendCommand(command("setDisplayMode", value));
          }}
        />
      )}
      {kind === "language" && (
        <div className="popover-grid">
          <SegmentedControl
            value={sourceLang}
            options={[
              { label: "Auto", value: "auto" },
              { label: "EN", value: "en" },
              { label: "JA", value: "ja" }
            ]}
            onChange={(value) => {
              setSourceLang(value);
              sendCommand(command("setSourceLanguage", value));
            }}
          />
          <SegmentedControl
            value={targetLang}
            options={[
              { label: "TW", value: "zh-TW" },
              { label: "CN", value: "zh-CN" }
            ]}
            onChange={(value) => {
              setTargetLang(value);
              sendCommand(command("setTargetLanguage", value));
            }}
          />
        </div>
      )}
      {kind === "model" && (
        <SegmentedControl
          value={translationModel}
          options={[
            { label: "Flash", value: "deepseek-v4-flash" },
            { label: "Pro", value: "deepseek-v4-pro" }
          ]}
          onChange={(value) => {
            setTranslationModel(value);
            sendCommand(command("setTranslationModel", value));
          }}
        />
      )}
    </GlassCard>
  );
}
