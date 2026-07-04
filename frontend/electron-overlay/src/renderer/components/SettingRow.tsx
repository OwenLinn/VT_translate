import type { PropsWithChildren } from "react";

interface SettingRowProps extends PropsWithChildren {
  label: string;
  value?: string;
  onClick?: () => void;
}

export function SettingRow({ label, value, onClick, children }: SettingRowProps): JSX.Element {
  const content = (
    <>
      <span className="setting-row__label">{label}</span>
      <span className="setting-row__value">{value}</span>
      {children}
    </>
  );

  if (onClick) {
    return (
      <button className="setting-row setting-row--button no-drag" type="button" onClick={onClick}>
        {content}
      </button>
    );
  }

  return <div className="setting-row">{content}</div>;
}
