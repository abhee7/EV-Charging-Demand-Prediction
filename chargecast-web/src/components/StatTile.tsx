interface Props {
  label: string;
  value: string;
  hint?: string;
}

export function StatTile({ label, value, hint }: Props) {
  return (
    <div className="rounded-xl border border-black/[0.08] bg-black/[0.025] px-3.5 py-3">
      <p className="text-2xs text-muted">{label}</p>
      <p className="tnum mt-1 font-display text-lg font-semibold">{value}</p>
      {hint && <p className="mt-0.5 text-2xs text-muted">{hint}</p>}
    </div>
  );
}
