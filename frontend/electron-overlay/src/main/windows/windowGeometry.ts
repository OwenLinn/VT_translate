import { screen } from "electron";
import type {
  ActivePopover,
  OverlayBounds,
  OverlayPositionSnapshot
} from "../../shared/overlayIpcTypes";

export const WINDOW_GAP = 12;
const SCREEN_MARGIN = 16;

export const DEFAULT_SIZES = {
  subtitle: { width: 900, height: 108 },
  settingsIcon: { width: 72, height: 72 },
  controlCard: { width: 420, height: 232 },
  controlCardTuning: { width: 460, height: 720 },
  popover: { width: 260, height: 96 },
  popoverLanguage: { width: 260, height: 132 }
} as const;

export function initialSubtitleBounds(): OverlayBounds {
  const workArea = screen.getPrimaryDisplay().workArea;
  const width = Math.min(DEFAULT_SIZES.subtitle.width, workArea.width - 48);
  return clampBounds(
    {
      width,
      height: DEFAULT_SIZES.subtitle.height,
      x: workArea.x + Math.round((workArea.width - width) / 2),
      y: workArea.y + 72
    },
    true
  );
}

export function layoutFromSubtitle(
  subtitle: OverlayBounds,
  options: { tuning: boolean; rowOffset?: number; activePopover?: ActivePopover } = { tuning: false }
): OverlayPositionSnapshot {
  const subtitleBounds = clampBounds(subtitle, true);
  const settingsIcon = clampBounds({
    width: DEFAULT_SIZES.settingsIcon.width,
    height: DEFAULT_SIZES.settingsIcon.height,
    x: subtitleBounds.x + subtitleBounds.width + WINDOW_GAP,
    y: subtitleBounds.y + Math.round((subtitleBounds.height - DEFAULT_SIZES.settingsIcon.height) / 2)
  });

  const controlHeight = fitHeight(
    options.tuning ? DEFAULT_SIZES.controlCardTuning.height : DEFAULT_SIZES.controlCard.height
  );
  const controlY = anchorMenuY({
    preferredY: subtitleBounds.y,
    anchorTop: subtitleBounds.y,
    anchorBottom: subtitleBounds.y + subtitleBounds.height,
    height: controlHeight
  });
  const controlCard = clampBounds({
    width: DEFAULT_SIZES.controlCard.width,
    height: controlHeight,
    x: settingsIcon.x + settingsIcon.width + WINDOW_GAP,
    y: controlY
  });

  const popoverHeight = fitHeight(popoverHeightFor(options.activePopover));
  const rowOffset = Math.max(0, options.rowOffset ?? 58);
  const rowTop = controlCard.y + rowOffset;
  const popoverY = anchorMenuY({
    preferredY: rowTop,
    anchorTop: rowTop,
    anchorBottom: rowTop + 42,
    height: popoverHeight
  });
  const popover = clampBounds({
    width: DEFAULT_SIZES.popover.width,
    height: popoverHeight,
    x: controlCard.x + controlCard.width + WINDOW_GAP,
    y: popoverY
  });

  return { subtitle: subtitleBounds, settingsIcon, controlCard, popover };
}

export function clampBounds(bounds: OverlayBounds, preferHorizontalCenter = false): OverlayBounds {
  const workArea = screen.getPrimaryDisplay().workArea;
  const maxX = workArea.x + workArea.width - bounds.width;
  const maxY = workArea.y + workArea.height - bounds.height;

  if (preferHorizontalCenter && bounds.width > workArea.width) {
    return {
      ...bounds,
      width: workArea.width,
      x: workArea.x,
      y: clamp(bounds.y, workArea.y, Math.max(workArea.y, maxY))
    };
  }

  return {
    ...bounds,
    x: clamp(bounds.x, workArea.x, Math.max(workArea.x, maxX)),
    y: clamp(bounds.y, workArea.y, Math.max(workArea.y, maxY))
  };
}

export function popoverHeightFor(activePopover: ActivePopover | undefined): number {
  if (activePopover === "language") {
    return DEFAULT_SIZES.popoverLanguage.height;
  }
  if (activePopover === "tuning") {
    return 320;
  }
  return DEFAULT_SIZES.popover.height;
}

function fitHeight(height: number): number {
  const workArea = screen.getPrimaryDisplay().workArea;
  return Math.min(height, Math.max(120, workArea.height - SCREEN_MARGIN * 2));
}

function anchorMenuY({
  preferredY,
  anchorTop,
  anchorBottom,
  height
}: {
  preferredY: number;
  anchorTop: number;
  anchorBottom: number;
  height: number;
}): number {
  const workArea = screen.getPrimaryDisplay().workArea;
  const minY = workArea.y + SCREEN_MARGIN;
  const maxY = workArea.y + workArea.height - height - SCREEN_MARGIN;

  if (preferredY <= maxY) {
    return Math.max(minY, preferredY);
  }

  const upwardY = anchorBottom - height;
  if (upwardY >= minY) {
    return upwardY;
  }

  const aboveY = anchorTop - height - WINDOW_GAP;
  if (aboveY >= minY) {
    return aboveY;
  }

  return clamp(preferredY, minY, Math.max(minY, maxY));
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}
