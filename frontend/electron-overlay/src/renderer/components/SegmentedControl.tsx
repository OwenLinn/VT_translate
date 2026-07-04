import { LiquidThumb } from "./LiquidThumb";

interface Option<T extends string> {
  label: string;
  value: T;
}

interface SegmentedControlProps<T extends string> {
  value: T;
  options: Array<Option<T>>;
  onChange: (value: T) => void;
}

export function SegmentedControl<T extends string>({
  value,
  options,
  onChange
}: SegmentedControlProps<T>): JSX.Element {
  const index = Math.max(0, options.findIndex((option) => option.value === value));

  return (
    <div className="segmented no-drag">
      <LiquidThumb index={index} count={options.length} />
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          className={option.value === value ? "segmented__button segmented__button--active" : "segmented__button"}
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
