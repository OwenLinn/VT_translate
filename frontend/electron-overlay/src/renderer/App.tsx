import { useCallback, useEffect, useMemo, useRef } from "react";
import { AnimatePresence } from "framer-motion";
import { startMockEvents } from "./bridge/mockEvents";
import { connectOverlaySocket, type OverlaySocket } from "./bridge/wsClient";
import type { CommandMessage } from "./bridge/messageTypes";
import type { OverlayWindowType } from "../shared/overlayIpcTypes";
import { ControlHubCard } from "./components/ControlHubCard";
import { OptionPopoverCard } from "./components/OptionPopoverCard";
import { SettingsIconButton } from "./components/SettingsIconButton";
import { SubtitleBar } from "./components/SubtitleBar";
import { TuningPanel } from "./components/TuningPanel";
import { useOverlayStore } from "./state/overlayStore";
import "./styles/tokens.css";
import "./styles/glass.css";
import "./styles/layout.css";
import "./styles/animations.css";

type OverlayMode = "mock" | "tuning";

function readMode(): OverlayMode {
  const mode = new URLSearchParams(window.location.search).get("mode");
  return mode === "tuning" ? "tuning" : "mock";
}

function readWindowType(): OverlayWindowType | "single" {
  const value = new URLSearchParams(window.location.search).get("window");
  if (
    value === "subtitle" ||
    value === "settings-icon" ||
    value === "control-card" ||
    value === "popover"
  ) {
    return value;
  }
  return "single";
}

export function App(): JSX.Element {
  const mode = useMemo(readMode, []);
  const windowType = useMemo(readWindowType, []);

  if (windowType !== "single") {
    return <MultiWindowApp mode={mode} windowType={windowType} />;
  }

  return <SingleLegacyApp mode={mode} />;
}

function SingleLegacyApp({ mode }: { mode: OverlayMode }): JSX.Element {
  const applyEvent = useOverlayStore((state) => state.applyEvent);
  const socketRef = useRef<OverlaySocket | null>(null);
  const popover = useOverlayStore((state) => state.popover);

  const sendCommand = useCallback((message: CommandMessage): boolean => {
    return socketRef.current?.sendCommand(message) ?? false;
  }, []);

  useEffect(() => {
    const socket = connectOverlaySocket(applyEvent);
    socketRef.current = socket;
    const stopMock = startMockEvents(applyEvent);
    window.electronOverlay?.setInteractive(true).catch(() => undefined);
    return () => {
      stopMock();
      socket.close();
      socketRef.current = null;
    };
  }, [applyEvent]);

  return (
    <main className={`overlay-shell overlay-shell--${mode}`}>
      <section className="overlay-stage drag-region">
        <SubtitleBar />
        <ControlHubCard sendCommand={sendCommand} />
        <AnimatePresence>
          {popover && <OptionPopoverCard key={popover} kind={popover} sendCommand={sendCommand} />}
        </AnimatePresence>
      </section>
      <AnimatePresence>{mode === "tuning" && <TuningPanel />}</AnimatePresence>
    </main>
  );
}

function MultiWindowApp({
  mode,
  windowType
}: {
  mode: OverlayMode;
  windowType: OverlayWindowType;
}): JSX.Element {
  const applyUiState = useOverlayStore((state) => state.applyUiState);
  const controlOpen = useOverlayStore((state) => state.controlOpen);
  const popover = useOverlayStore((state) => state.popover);

  useEffect(() => {
    let cleanupState = (): void => undefined;
    let cleanupPosition = (): void => undefined;
    console.log(`[renderer:${windowType}] mounting, requesting initial state`);
    window.electronOverlay
      ?.getState()
      .then((state) => {
        console.log(
          `[renderer:${windowType}] got initial state: status=${state.runtimeStatus} connected=${state.backendConnected} controlOpen=${state.showControlCard}`
        );
        applyUiState(state);
      })
      .catch((err) => console.error(`[renderer:${windowType}] getState failed:`, err));
    cleanupState =
      window.electronOverlay?.onStateUpdated((state) => {
        console.log(
          `[renderer:${windowType}] stateUpdated: status=${state.runtimeStatus} subtitle="${state.subtitle.translatedText.slice(0, 40)}"`
        );
        applyUiState(state);
      }) ?? cleanupState;
    cleanupPosition =
      window.electronOverlay?.onPositionUpdated(() => {
        return undefined;
      }) ?? cleanupPosition;
    return () => {
      cleanupState();
      cleanupPosition();
    };
  }, [windowType]);

  const sendCommand = useCallback((message: CommandMessage): boolean => {
    if (message.command === "start" || message.command === "stop") {
      void window.electronOverlay?.settingSelected({
        key: "running",
        value: message.command === "start"
      });
      return true;
    }
    if (message.command === "setDisplayMode") {
      void window.electronOverlay?.settingSelected({ key: "displayMode", value: String(message.value) });
      return true;
    }
    if (message.command === "setSourceLanguage") {
      void window.electronOverlay?.settingSelected({ key: "sourceLanguage", value: String(message.value) });
      return true;
    }
    if (message.command === "setTargetLanguage") {
      void window.electronOverlay?.settingSelected({ key: "targetLanguage", value: String(message.value) });
      return true;
    }
    if (message.command === "setTranslationModel") {
      void window.electronOverlay?.settingSelected({ key: "deepseekModel", value: String(message.value) });
      return true;
    }
    return false;
  }, []);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent): void => {
      if (event.key === "Escape") {
        void window.electronOverlay?.escape();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  if (windowType === "subtitle") {
    return (
      <main className="overlay-window overlay-window--subtitle drag-region">
        <SubtitleBar showSettingsButton={false} />
      </main>
    );
  }

  if (windowType === "settings-icon") {
    return (
      <main className="overlay-window overlay-window--settings-icon">
        <SettingsIconButton
          open={controlOpen}
          onClick={() => {
            console.log("[renderer:settings-icon] toggleControlCard clicked");
            window.electronOverlay
              ?.toggleControlCard()
              .then((state) => {
                console.log(
                  `[renderer:settings-icon] toggleControlCard result: showControlCard=${state.showControlCard}`
                );
              })
              .catch((err) => console.error("[renderer:settings-icon] toggleControlCard failed:", err));
          }}
        />
      </main>
    );
  }

  if (windowType === "control-card") {
    return (
      <main className={`overlay-window overlay-window--control-card overlay-window--${mode}`}>
        <ControlHubCard
          forceVisible
          sendCommand={sendCommand}
          openPopover={(kind, rowOffset) => {
            void window.electronOverlay?.openPopover({ popover: kind, rowOffset });
          }}
        />
        <AnimatePresence>{mode === "tuning" && <TuningPanel />}</AnimatePresence>
      </main>
    );
  }

  return (
    <main className="overlay-window overlay-window--popover">
      <AnimatePresence>
        {popover && <OptionPopoverCard key={popover} kind={popover} sendCommand={sendCommand} />}
      </AnimatePresence>
      {!popover && (
        <OptionPopoverCard
          kind="display"
          sendCommand={(message) => {
            sendCommand(message);
            return true;
          }}
        />
      )}
    </main>
  );
}
