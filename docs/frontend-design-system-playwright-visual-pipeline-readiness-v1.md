# Frontend Design System / Playwright Visual Pipeline Readiness v1

## Decision

Decision: FRONTEND_VISUAL_PIPELINE_READINESS_DOCUMENTED_ONLY

This sprint documents the current Aegis frontend design system and the safe future browser/Playwright visual validation pipeline. It adds no visible UI, no React component, no API endpoint, no runtime behavior, no frontend authority, no evidence, and no verifier success.

## Scope

Documented:

- current frontend application structure
- current design tokens and visual primitives
- current runtime state display boundaries
- visual state taxonomy for future provider and repo-audit surfaces
- browser/Playwright validation readiness
- future screenshot and interaction validation rules
- accessibility and reduced-motion expectations
- design tooling and plugin safety boundaries

This is a readiness document only. It does not redesign the UI, add a design system package, add Storybook, add Playwright config, add screenshots, add browser automation, or wire any future surface.

## Current Frontend Inventory

The frontend is a Next/React application under `frontend/` with Electron dev support.

Current package scripts:

- `npm run dev`: Next dev server on `127.0.0.1`
- `npm run build`: Next build
- `npm run start`: Next start
- `npm run lint`: ESLint
- `npm run electron:dev`: Next dev plus Electron
- `npm run electron:build`: build plus Electron packaging

Current primary structure:

- `frontend/src/app/page.tsx`: dashboard composition
- `frontend/src/app/layout.tsx`: root layout
- `frontend/src/app/globals.css`: base tokens and visual primitives
- `frontend/src/layouts/AppShell.tsx`: shell, sidebar, header, runtime console
- `frontend/src/components/*`: shared components such as status badges, header, runtime console, dev overlay
- `frontend/src/features/runtime/components/*`: runtime panels, maintenance scan, approval, application/tool registry, timeline
- `frontend/src/features/dashboard/components/SystemOverview.tsx`: system overview summary
- `frontend/src/features/sidebar/components/Sidebar.tsx`: navigation
- `frontend/src/store/*`: frontend state stores
- `frontend/src/lib/socket.ts`: websocket bridge
- `frontend/electron/main.js`: Electron shell entrypoint

The frontend already uses Tailwind, React, Zustand, socket.io-client, lucide-react, and framer-motion.

## Current Design System Shape

Current visual primitives are mostly Tailwind utility based:

- CSS variables for `--background`, `--foreground`, `--font-inter`, and `--font-mono`
- `glass-panel` for operational panels
- `glass-card` for contained status and data cards
- `bg-grid` for the runtime background
- `custom-scrollbar` for scrollable panels
- `StatusBadge` for status presentation
- lucide icons for operational controls and status labels
- small uppercase mono labels for telemetry, integrity, status, and system metadata

This is a practical component vocabulary, not yet a formal design-system package.

## Current Visual State Semantics

The frontend displays backend-owned state. It must not invent state, infer runtime truth, or convert missing data into success or failure.

Current state sources include:

- runtime state and integrity from the websocket bridge and runtime store
- command records, pending approvals, and pending clarifications from backend snapshots
- maintenance scan projection from backend snapshots
- application and tool registry snapshots from backend snapshots
- runtime console logs from frontend-ingested backend events and local UI bridge events

Visual display is a projection. It is not runtime authority.

## Visual State Taxonomy

Future frontend surfaces should use the following visual categories:

- `neutral_no_data`: no current projection or no observed data
- `metadata_only`: descriptive backend-owned metadata
- `candidate_only`: future candidate, not verified truth
- `informational`: visible but non-authoritative state
- `warning_attention`: needs attention but is not automatically runtime failure
- `blocked`: backend policy or readiness blocks the action
- `future_gated`: future work exists but is not active now
- `operator_review_required`: human review is required before any future action
- `unknown`: unresolved or insufficient information
- `error_from_backend`: backend explicitly reports an error or failed condition

These categories are display-only. They do not authorize actions.

## Forbidden Visual Meanings

Future UI text, colors, badges, animations, and screenshots must not imply:

- fake runtime health
- fake provider health
- fake model availability
- fake source truth
- fake repo read
- fake evidence
- fake verifier success
- fake policy approval
- fake lease or capability grant
- fake execution permission
- fake compliance proof
- fake developer passport proof
- fake cleanup, deletion, archive, or repair
- frontend authority

Green or success styling should be reserved for backend-verified success states. Metadata candidates should remain neutral or informational.

## Provider Probe Display Rules

Future local-provider probe UI must preserve the existing provider probe display contracts:

- `no_projection_available` means no current durable projection, not provider failure
- `not_observed` means no probe observed, not provider health or unhealth proof
- `metadata_candidate` means metadata only
- `model_list_candidate` is not model availability proof
- `empty_model_list_candidate` is not runtime failure
- negative candidates are warning candidates, not runtime health mutation
- retry guidance remains operator-gated and not frontend-authorized

Provider probe UI must not call providers, poll endpoints, send prompts, read model files, or mark provider/model health verified.

## Repo Audit Dry-Run Display Rules

Future repo-audit dry-run UI must preserve the existing source-plan and surface display contracts:

- no projection means neutral no-data
- dry-run not observed means no observed projection, not failure
- candidate sources are candidate metadata only
- exclusions are policy metadata, not cleanup or deletion
- blockers remain blocked
- future gates remain unavailable now
- operator review does not authorize run, fetch, clone, report, or file read

Repo-audit UI must not call GitHub, fetch URLs, clone repos, read local files, create context packages, generate reports, create evidence, or claim verifier success.

## Playwright / Browser Validation Readiness

No committed Playwright workflow is present in the frontend package today. The safe future pipeline should be added deliberately and should validate rendered behavior without creating committed screenshots or fake pass artifacts.

Recommended future validation stages:

1. Start backend and frontend through normal dev commands.
2. Open the app at the exact intended URL, usually `http://127.0.0.1:3000` or `http://localhost:3000`.
3. Verify page identity with URL and title.
4. Verify the page is not blank and no framework error overlay is visible.
5. Capture console errors and warnings.
6. Capture one desktop screenshot and one practical mobile screenshot.
7. Exercise at least one visible interaction.
8. Verify hover, click, focus, scroll, and websocket state where relevant.
9. Wait long enough for delayed overlays, reconnects, or runtime snapshots.
10. Record what was validated and what remains unvalidated.

Browser validation is UI evidence for a rendered state. It is not backend evidence, verifier success, runtime health, provider health, source truth, or execution permission.

## Suggested Future Playwright Smoke Matrix

Future tests should be narrow and state-preserving:

- first screen renders without framework overlay
- sidebar navigation changes visible panels
- Runtime Console remains visible and scrollable
- Maintenance Scan button remains clickable when present
- pending approval controls are disabled or enabled only according to backend snapshot
- `no_projection_available` provider/repo-audit states render neutral no-data
- candidate metadata renders as candidate metadata
- blocked/future-gated/operator-review states preserve wording
- viewport checks cover desktop and one mobile size
- hidden overlays do not intercept clicks
- z-index and pointer-events rules do not block primary controls

These tests should not mutate journal, evidence, replay, runtime state, provider state, repo sources, or model state.

## Screenshot And Artifact Rules

Future screenshots, traces, and visual reports should be generated outside the repository unless explicitly requested as committed artifacts.

Do not stage:

- screenshots
- traces
- browser output
- generated reports
- temporary Playwright scripts
- cache files
- model files
- dataset files
- vector database files
- API keys
- secrets
- tokens

Screenshots can support UI QA claims, but they do not create backend evidence or verifier success.

## Accessibility And Reduced-Motion Notes

Future visual hardening should check:

- keyboard focus visibility
- tab order for sidebar, panels, buttons, and inputs
- accessible labels for icon-only buttons
- disabled controls have both visual and semantic disabled states
- status badges are readable without relying on color alone
- panel text does not clip at desktop or mobile sizes
- scroll containers are reachable by keyboard
- reduced-motion handling for framer-motion animation
- high-contrast readability for warning, danger, unknown, and blocked states

Reduced motion must not hide runtime truth or remove required status labels.

## Performance / Responsiveness Notes

Existing frontend state already caps runtime console logs at 100 entries. Future visual QA should additionally watch for:

- repeated websocket snapshots causing full-page re-render churn
- large registry or maintenance arrays rendered without stable keys
- hidden fixed overlays intercepting clicks
- unbounded animation loops or expensive derived state
- Electron DevTools focus side effects
- panel scroll traps
- layout shift from long status labels

Any optimization should preserve backend truth and should not drop pending approvals, blockers, maintenance findings, historical labels, unknown states, or negative candidates.

## Design Tooling And Plugin Safety

Future use of Figma, Canva, screenshots, image generation, or other design tooling must remain presentation-only.

Design assets and prototypes cannot:

- define runtime authority
- mark backend health
- prove provider availability
- prove repo source truth
- create evidence
- create verifier success
- grant approval, lease, capability, or execution permission
- override policy or context boundaries

Visual polish is allowed only when it preserves truthful state and backend-owned authority.

## Relationship To Runtime / Evidence / Verifier

Frontend display consumes backend projections. It does not own runtime truth.

The visual pipeline cannot:

- create runtime events
- mutate journal, evidence, replay, or snapshots
- verify actions
- hide replay or historical debt
- turn dispatch success into verification success
- turn evidence existence into verifier success
- downgrade backend failures into neutral display states

If backend reports fail, unknown, blocked, or future-gated, the UI must preserve that meaning.

## Relationship To Mission Control

Future Mission Control visuals may use richer layout, motion, and ambient dashboard elements. Those elements must remain subordinate to backend state.

Mission Control UI can improve comprehension, but it cannot make model output, context packages, source candidates, tool simulation, dry-run metadata, or plugin metadata authoritative.

## Relationship To Provider / Model Readiness

Provider and model readiness metadata remains metadata. Frontend display cannot prove:

- model loaded
- model available
- model healthy
- endpoint reachable
- Auto Mode selected
- provider authenticated
- context safely delivered
- model output truthful

Any future local or cloud model display must keep model output proposal-only.

## Relationship To Repo Audit / Source Intelligence

Repo Audit, GitHub Source Connector, Web Research Gateway, Source Intake, Source Plan, and Dry-Run display metadata remain candidate or projection metadata unless a future approved runner creates backend-owned evidence and verifier checks.

Frontend display cannot authorize:

- GitHub API calls
- URL fetches
- repo clones
- local repo reads
- file list/stat/hash/read
- context packages
- source records
- reports

## Intentionally Not Done

This sprint did not:

- add Playwright config or tests
- start the frontend or backend
- run browser automation
- capture screenshots
- change React components
- change Tailwind or design tokens
- add a design-system package
- add Storybook
- add frontend routes
- add provider probe UI
- add repo-audit dry-run UI
- change websocket behavior
- change runtime, backend, API, policy, approval, evidence, verifier, journal, or replay behavior
- stage or modify generated frontend files

## Future Implementation Notes

Recommended next frontend pipeline steps:

1. Add a minimal committed Playwright configuration only when a UI-changing sprint needs repeatable rendered validation.
2. Keep screenshots and traces out of the repository by default.
3. Add no-data/candidate/blocked/future-gated/operator-review visual fixtures using synthetic data only.
4. Add regression checks for pointer-event overlays and clickability after delayed websocket snapshots.
5. Add reduced-motion and keyboard-focus checks for primary panels.
6. Add provider/repo-audit surface tests only after the display contracts are wired into visible components.

## Remaining Risks

- No committed Playwright workflow exists yet.
- Current frontend design primitives are useful but not formalized as a typed design-system package.
- Existing panels rely heavily on Tailwind utility conventions, so visual consistency depends on reviewer discipline.
- Electron-specific focus/click behavior still requires manual validation when shell behavior changes.
- Future premium motion work could accidentally obscure truth labels unless reduced-motion and state-label tests are added.
- Browser screenshots can prove rendered UI state but cannot prove backend truth, evidence, verifier success, provider health, or source truth.
