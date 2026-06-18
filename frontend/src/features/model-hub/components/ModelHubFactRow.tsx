export const ModelHubFactRow = ({ label, value }: { label: string; value: string }) => (
  <div className="flex min-w-0 items-center justify-between gap-3 rounded-lg border border-white/10 bg-white/[0.025] px-3 py-2">
    <span className="shrink-0 text-xs text-foreground/52">{label}</span>
    <span className="min-w-0 break-all text-right text-xs font-semibold leading-5 text-foreground/82" title={value}>
      {value}
    </span>
  </div>
);
