interface Props {
  title: string;
  lede: string;
  meta?: string;
}

export function PageHeader({ title, lede, meta }: Props) {
  return (
    <header className="mb-7 border-b border-black/[0.08] pb-5">
      <h1 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">
        {title}
      </h1>
      <p className="mt-2 max-w-3xl text-base text-ink/90">{lede}</p>
      {meta && <p className="mt-1 text-sm text-muted">{meta}</p>}
    </header>
  );
}
