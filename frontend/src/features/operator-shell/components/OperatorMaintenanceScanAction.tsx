"use client";

import React from 'react';
import { Activity, Wrench } from 'lucide-react';

import { dictionaryFor } from '@/i18n';
import { fetchMaintenanceScan } from '@/lib/api';
import { useRuntimeStore } from '@/store/useRuntimeStore';
import { useUIStore } from '@/store/useUIStore';
import type { OperatorDecisionPreview } from '@/types/operator';
import type { MaintenanceScanReport } from '@/types/runtime';

type MaintenanceRequestStatus = 'idle' | 'requesting' | 'received' | 'unavailable';

const BOUNDED_MAINTENANCE_SCAN_REQUESTS = new Set([
  'maintenance scan',
  'run maintenance scan',
  'bakim taramasi',
  'bakim taramasini calistir',
]);

export const OperatorMaintenanceScanAction = ({
  decision,
}: {
  decision: OperatorDecisionPreview;
}) => {
  const language = useUIStore((state) => state.language);
  const t = dictionaryFor(language).operatorShell;
  const setMaintenanceScan = useRuntimeStore((state) => state.setMaintenanceScan);
  const [requestStatus, setRequestStatus] = React.useState<MaintenanceRequestStatus>('idle');
  const [requestResult, setRequestResult] = React.useState<MaintenanceScanReport | null>(null);

  if (!isEligibleMaintenanceScanDecision(decision)) return null;

  const requestMaintenanceScan = async () => {
    setRequestStatus('requesting');
    setRequestResult(null);
    try {
      const report = await fetchMaintenanceScan();
      setRequestResult(report);
      setMaintenanceScan(report);
      setRequestStatus('received');
    } catch {
      setRequestResult(null);
      setRequestStatus('unavailable');
    }
  };

  const diagnosticStatus = requestResult?.summary.status;
  const findingCount = requestResult?.summary.finding_count;
  const attentionCount = Array.isArray(requestResult?.summary.attention)
    ? requestResult.summary.attention.length
    : undefined;

  return (
    <section
      aria-labelledby="operator-maintenance-scan-title"
      className="mt-5 rounded-lg border border-[#3a3834] bg-[#1b1a18] p-4 sm:p-5"
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h2
            id="operator-maintenance-scan-title"
            className="flex items-center gap-2 text-sm font-semibold text-[#ece9e2]"
          >
            <Wrench size={16} aria-hidden="true" className="shrink-0 text-[#f4bf4f]" />
            {t.maintenanceScanActionTitle}
          </h2>
          <p className="mt-2 max-w-2xl text-xs leading-5 text-[#918d86]">
            {t.maintenanceScanActionCopy}
          </p>
        </div>
        <button
          type="button"
          onClick={() => { void requestMaintenanceScan(); }}
          disabled={requestStatus === 'requesting'}
          className="inline-flex min-h-10 shrink-0 items-center justify-center gap-2 rounded-md border border-[#6d5b31] bg-[#29241a] px-3 text-xs font-semibold text-[#f4bf4f] hover:border-[#967c3f] hover:bg-[#332b1d] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#f4bf4f] disabled:cursor-wait disabled:opacity-55"
        >
          <Activity size={14} aria-hidden="true" />
          {requestStatus === 'requesting' ? t.maintenanceScanRequesting : t.maintenanceScanRequest}
        </button>
      </div>

      {requestStatus === 'idle' && (
        <p className="mt-3 text-[11px] leading-5 text-[#77736d]">{t.maintenanceScanIdle}</p>
      )}
      {requestStatus === 'requesting' && (
        <p className="mt-3 text-[11px] leading-5 text-[#aaa69e]" role="status" aria-live="polite">
          {t.maintenanceScanWaiting}
        </p>
      )}
      {requestStatus === 'unavailable' && (
        <p className="mt-3 text-[11px] leading-5 text-[#d7a660]" role="status" aria-live="polite">
          {t.maintenanceScanNoResult}
        </p>
      )}
      {requestStatus === 'received' && requestResult && diagnosticStatus && (
        <div className="mt-4 border-t border-[#34322f] pt-4" role="status" aria-live="polite">
          <p className="text-xs font-medium text-[#c9c5bc]">{t.maintenanceScanResultReceived}</p>
          <dl className="mt-3 grid gap-3 text-xs sm:grid-cols-2">
            <ResultField label={t.maintenanceScanDiagnosticStatus} value={diagnosticStatus} />
            <ResultField label={t.maintenanceScanVersion} value={requestResult.scan_version} />
            <ResultField label={t.maintenanceScanMode} value={t.maintenanceScanReadOnly} />
            {typeof findingCount === 'number' && (
              <ResultField label={t.maintenanceScanFindingCount} value={String(findingCount)} />
            )}
            {typeof attentionCount === 'number' && (
              <ResultField label={t.maintenanceScanAttentionCount} value={String(attentionCount)} />
            )}
          </dl>
          <p className="mt-3 text-[11px] leading-5 text-[#77736d]">{t.maintenanceScanAdvancedCopy}</p>
        </div>
      )}

      <p className="mt-3 text-[10px] leading-5 text-[#6f6b64]">{t.maintenanceScanBoundary}</p>
    </section>
  );
};

const ResultField = ({ label, value }: { label: string; value: string }) => (
  <div className="min-w-0">
    <dt className="text-[#716d66]">{label}</dt>
    <dd className="mt-1 break-words font-medium text-[#c9c5bc]">{value}</dd>
  </div>
);

function isEligibleMaintenanceScanDecision(decision: OperatorDecisionPreview): boolean {
  return decision.previewSource === 'backend_contract'
    && decision.backendPreviewAvailable
    && decision.routeId === 'status_explainer'
    && decision.capabilityAssessment?.classification === 'observe_only'
    && BOUNDED_MAINTENANCE_SCAN_REQUESTS.has(normalizeMaintenanceRequest(decision.request));
}

function normalizeMaintenanceRequest(value: string): string {
  return value
    .toLowerCase()
    .replace(/\u0131/g, 'i')
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/[.!?]+$/, '');
}
