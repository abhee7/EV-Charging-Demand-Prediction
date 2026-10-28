interface Props {
  title: string;
  hint?: string;
  right?: React.ReactNode;
}

export function SectionHeading({ title, hint, right }: Props) {
  return (
    <div className="mb-4 mt-8 flex flex-wrap items-baseline gap-x-3 gap-y-1 border-b border-black/[0.08] pb-2 first:mt-0">
      <h2 className="font-display text-lg font-semibold">{title}</h2>
      {hint && <p className="text-xs text-muted">{hint}</p>}
      {right && <div className="ml-auto">{right}</div>}
    </div>
  );
}
