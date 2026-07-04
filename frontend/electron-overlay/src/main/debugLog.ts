import { appendFileSync, mkdirSync } from "node:fs";
import { dirname } from "node:path";

export function appendDebugLog(scope: string, message: string): void {
  const logPath = process.env.OVERLAY_FRONTEND_DEBUG_LOG;
  if (!logPath) {
    return;
  }
  try {
    mkdirSync(dirname(logPath), { recursive: true });
    const timestamp = new Date().toISOString();
    appendFileSync(logPath, `[${timestamp}] [${scope}] ${message}\n`, "utf8");
  } catch (error) {
    console.error(`[debug-log] failed to append frontend debug log: ${String(error)}`);
  }
}
