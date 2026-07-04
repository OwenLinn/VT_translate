import type { BackendEvent, SubtitleEvent } from "./messageTypes";

const mockLines: Array<Pick<SubtitleEvent, "source" | "translation" | "kind" | "latencyMs">> = [
  {
    kind: "partial",
    source: "The live streamer is setting up the next match...",
    translation: "主播正在準備下一場對戰...",
    latencyMs: 1180
  },
  {
    kind: "final",
    source: "The live streamer is setting up the next match and checking chat.",
    translation: "主播正在準備下一場對戰，順便看聊天室。",
    latencyMs: 1740
  },
  {
    kind: "partial",
    source: "This boss phase looks dangerous.",
    translation: "這個 Boss 階段看起來很危險。",
    latencyMs: 1320
  },
  {
    kind: "final",
    source: "This boss phase looks dangerous, but the timing is clean.",
    translation: "這個 Boss 階段看起來很危險，但節奏抓得很漂亮。",
    latencyMs: 2030
  }
];

export function startMockEvents(onEvent: (event: BackendEvent) => void): () => void {
  let index = 0;
  onEvent({ type: "status", status: "running", backendConnected: false });

  const emit = (): void => {
    const line = mockLines[index % mockLines.length];
    onEvent({
      type: "subtitle",
      segmentId: index + 1,
      kind: line.kind,
      source: line.source,
      translation: line.translation,
      sourceLang: "auto",
      targetLang: "zh-TW",
      latencyMs: line.latencyMs,
      timestampMs: Date.now()
    });
    index += 1;
  };

  emit();
  const timer = window.setInterval(emit, 2600);
  return () => window.clearInterval(timer);
}
