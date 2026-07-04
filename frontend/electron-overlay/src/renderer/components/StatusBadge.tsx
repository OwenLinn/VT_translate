import { useOverlayStore } from "../state/overlayStore";

export function StatusBadge(): JSX.Element {
  const { status, backendConnected } = useOverlayStore();
  return (
    <div className={`status-badge status-badge--${status}`}>
      <span className="status-badge__dot" />
      <span>{backendConnected ? "Bridge" : "Mock"}</span>
      <strong>{status}</strong>
    </div>
  );
}
