import { command } from "../bridge/wsClient";
import { useOverlayStore } from "../state/overlayStore";
import { GlassCard } from "./GlassCard";
import { SegmentedControl } from "./SegmentedControl";
import { SettingRow } from "./SettingRow";
import { StatusBadge } from "./StatusBadge";

interface ControlHubCardProps {
  sendCommand: (message: ReturnType<typeof command>) => boolean;
  openPopover?: (kind: "display" | "language" | "model", rowOffset: number) => void;
  forceVisible?: boolean;
}

export function ControlHubCard({ sendCommand, openPopover, forceVisible = false }: ControlHubCardProps): JSX.Element {
  const {
    controlOpen,
    status,
    displayMode,
    targetLang,
    sourceLang,
    translationModel,
    popover,
    setRunning,
    setPopover
  } = useOverlayStore();

  const running = status === "running";

  if (!controlOpen && !forceVisible) {
    return <></>;
  }

  const togglePopover = (kind: "display" | "language" | "model", rowOffset: number): void => {
    if (openPopover) {
      openPopover(kind, rowOffset);
      return;
    }
    setPopover(popover === kind ? null : kind);
  };

  return (
    <div className="control-stack">
      <GlassCard className="control-card" dense>
        <div className="control-card__header">
          <StatusBadge />
          <SegmentedControl
            value={running ? "running" : "idle"}
            options={[
              { label: "Start", value: "running" },
              { label: "Stop", value: "idle" }
            ]}
            onChange={(value) => {
              const nextRunning = value === "running";
              setRunning(nextRunning);
              sendCommand(command(nextRunning ? "start" : "stop"));
            }}
          />
        </div>
        <SettingRow
          label="Display"
          value={displayMode}
          onClick={() => togglePopover("display", 62)}
        />
        <SettingRow
          label="Language"
          value={`${sourceLang} -> ${targetLang}`}
          onClick={() => togglePopover("language", 108)}
        />
        <SettingRow
          label="DeepSeek"
          value={translationModel.replace("deepseek-", "")}
          onClick={() => togglePopover("model", 154)}
        />
      </GlassCard>
    </div>
  );
}
