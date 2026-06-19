export const ModelHubFactRow = ({ label, value }: { label: string; value: string }) => (
  <div className="flex min-w-0 flex-col gap-1 rounded-lg border border-white/10 bg-white/[0.025] px-3 py-2 sm:flex-row sm:items-center sm:justify-between sm:gap-3">
    <span className="shrink-0 text-xs text-foreground/52">{label}</span>
    <span className="min-w-0 max-w-full break-words text-left text-xs font-semibold leading-5 text-foreground/82 sm:text-right" title={value}>
      {value}
    </span>
  </div>
);
