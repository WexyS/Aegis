# Aegis UI Notes

The active user interface now lives in `frontend/`.

This `ui/` directory is kept only for historical notes and should not be treated as the active UI contract.

## Active UI Source

- `frontend/src/app/page.tsx`
- `frontend/src/lib/socket.ts`
- `frontend/src/store/useRuntimeStore.ts`
- `frontend/src/features/runtime/components/`
- `frontend/src/contracts/protocol.ts`

## Contract Rule

The UI must render backend-derived state only:

- protocol events
- runtime snapshots
- event journal projections
- tool registry snapshots
- app registry snapshots
- evidence audit reports
- maintenance scan reports

Do not add fake telemetry, fake verification, or frontend-only runtime truth.
