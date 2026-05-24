"use client";

import React from 'react';
import { CircleDashed } from 'lucide-react';

type EmptyStateProps = {
  title: string;
  detail?: string;
  icon?: React.ReactNode;
  className?: string;
};

export const EmptyState = ({ title, detail, icon, className = '' }: EmptyStateProps) => (
  <div className={`rounded-lg border border-white/10 bg-black/20 p-4 ${className}`}>
    <div className="flex items-start gap-3">
      <div className="mt-0.5 text-foreground/25">
        {icon ?? <CircleDashed size={15} />}
      </div>
      <div className="min-w-0">
        <div className="text-[11px] font-medium text-foreground/45">{title}</div>
        {detail && <div className="mt-1 text-[10px] font-mono leading-relaxed text-foreground/30">{detail}</div>}
      </div>
    </div>
  </div>
);
