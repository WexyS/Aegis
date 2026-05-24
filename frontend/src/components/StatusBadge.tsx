"use client";

import React from 'react';

type StatusTone = 'success' | 'info' | 'warning' | 'danger' | 'unknown';

const TONE_STYLES: Record<StatusTone, string> = {
  success: 'border-success/30 bg-success/10 text-success',
  info: 'border-accent/30 bg-accent/10 text-accent',
  warning: 'border-warning/30 bg-warning/10 text-warning',
  danger: 'border-danger/35 bg-danger/10 text-danger',
  unknown: 'border-white/10 bg-white/[0.03] text-foreground/45',
};

type StatusBadgeProps = {
  label?: React.ReactNode;
  tone?: StatusTone;
  icon?: React.ReactNode;
  className?: string;
};

export const StatusBadge = ({
  label,
  tone = 'unknown',
  icon,
  className = '',
}: StatusBadgeProps) => (
  <span
    className={`inline-flex max-w-full items-center gap-1.5 rounded-md border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${TONE_STYLES[tone]} ${className}`}
  >
    {icon}
    <span className="truncate">{label ?? 'unknown'}</span>
  </span>
);
