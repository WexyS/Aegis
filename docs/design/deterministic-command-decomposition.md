# Deterministic Command Decomposition Design
**Goal:** Define how natural-language commands become explicit, ordered primitive intents before execution.

**Decision:** Decomposition must happen before execution. A generic or compound user command must never reach the executor as a malformed single action.

This design is intentionally implementation-free. It does not change parser, executor, tools, frontend, replay, timeline, LLM routing, memory, vision, or voice.

---

## Why This Exists

Evidence gates can only prove the action they were asked to execute. If the parser turns:

```text
"brave açıp python nedir ara"
```

into:

```python
{"intent": "search_web", "params": {"query": "brave açıp python nedir"}}
```

then verification may correctly prove the wrong action. Command decomposition is therefore a foundation dependency for click, browser workflows, type workflows, and maintenance actions.

Rule: normalize first, execute second.

---

## Pipeline

```text
user text
-> normalization
-> language/pattern detection
-> primitive intent candidates
-> ambiguity detection
-> risk classification
-> normalized plan
-> guard validation
-> execution
```

### 1. Normalization

Normalize input without changing meaning:

- trim whitespace
- lowercase only for pattern matching, preserving original spans for parameters
- normalize Turkish apostrophes and suffix-like app references
- normalize common connectors:
  - Turkish: `ve`, `sonra`, `ardından`, `açıp`, `aç ve`, `yaz`, `ara`
  - English: `and`, `then`, `open and`, `type`, `search`
- preserve quoted strings as literal text/query candidates

### 2. Language And Pattern Detection

Detect deterministic patterns before any LLM proposal:

- app open phrase
- app focus phrase
- type/write phrase
- search phrase
- URL phrase
- click phrase
- coordinate phrase
- destructive phrase

The rule-based layer should handle known high-confidence patterns in Turkish and English.

### 3. Primitive Intent Candidates

Convert detected spans into candidate primitive intents:

- `open_app`
- `focus_app`
- `type`
- `open_url`
- `search_web`
- future `browser_click`
- future `desktop_click`
- `clarification_required`
- `approval_required`

Candidates are not executable until ambiguity and guard validation pass.

### 4. Ambiguity Detection

Detect unresolved targets before execution:

- unknown app
- unknown browser target
- generic click target
- browser-vs-desktop click ambiguity
- missing type text
- missing search query
- destructive action without explicit approval route

Ambiguous commands should become `clarification_required` or `approval_required`, not a guessed action.

### 5. Risk Classification

Risk is assigned to each primitive intent and to the plan as a whole:

- low: read-only or low-risk browser navigation
- medium: typing, browser search, non-destructive app interaction
- high: desktop click, system settings, file mutation
- critical: destructive/system-sensitive action, blocked unless an approved policy exists

The plan risk is at least the maximum primitive risk.

### 6. Normalized Plan

The output is an ordered list of primitive intents plus plan metadata:

```python
{
    "plan_kind": "deterministic_decomposition",
    "language": "tr" | "en" | "unknown",
    "source_text": "...",
    "status": "ready" | "clarification_required" | "approval_required" | "blocked",
    "risk": "low" | "medium" | "high" | "critical",
    "steps": [
        {
            "intent": "open_app",
            "params": {"app": "notepad"},
            "source_span": "not defterini aç",
            "risk": "low"
        }
    ],
    "ambiguities": [],
    "guard_notes": []
}
```

Only `status="ready"` plans may execute automatically, and only when risk policy allows it.

---

## Supported Compound Patterns

### Open App + Type

Supported:

- `not defterini aç ve merhaba yaz`
- `notepad açıp merhaba yaz`
- `open notepad and type hello`

Expected primitives:

```python
[
    {"intent": "open_app", "params": {"app": "notepad"}},
    {"intent": "type", "params": {"text": "merhaba", "_require_focus": "notepad"}},
]
```

### Open App + Search Web

Supported:

- `brave açıp python nedir ara`
- `chrome aç ve aegis runtime search`
- `open brave and search what is python`

Expected primitives:

```python
[
    {"intent": "open_app", "params": {"app": "brave"}},
    {"intent": "search_web", "params": {"query": "python nedir", "browser": "brave"}},
]
```

Important: app name must not be merged into the query.

### Open URL + Search Or Query

Supported:

- `example.com aç`
- `https://example.com aç ve python ara`
- `open https://example.com then search docs`

Expected primitives:

```python
[
    {"intent": "open_url", "params": {"url": "https://example.com"}},
    {"intent": "search_web", "params": {"query": "docs"}},
]
```

If the second action depends on a site-local search box, that is future target resolution, not deterministic search.

### Focus App + Type

Supported:

- `notepad'e odaklan ve merhaba yaz`
- `focus notepad and type hello`

Expected primitives:

```python
[
    {"intent": "focus_app", "params": {"app": "notepad"}},
    {"intent": "type", "params": {"text": "merhaba", "_require_focus": "notepad"}},
]
```

### Browser Context + First Result Click

Future placeholder only.

```python
[
    {"intent": "search_web", "params": {"query": "python nedir", "browser": "brave"}},
    {"intent": "clarification_required", "params": {"reason": "browser_click target resolution not implemented"}}
]
```

Do not emit executable `browser_click` until target resolution exists.

### Explicit Coordinate Click

Future placeholder only.

```python
[
    {"intent": "clarification_required", "params": {"reason": "desktop_click is not enabled"}}
]
```

Do not turn raw coordinates into executable desktop clicks until the desktop click evidence contract exists.

---

## Normalized Intent Examples

### Turkish Open + Type

Input:

```text
not defterini aç ve merhaba yaz
```

Output:

```python
[
    {"intent": "open_app", "params": {"app": "notepad"}},
    {"intent": "type", "params": {"text": "merhaba", "_require_focus": "notepad"}},
]
```

### Turkish Open + Search

Input:

```text
brave açıp python nedir ara
```

Output:

```python
[
    {"intent": "open_app", "params": {"app": "brave"}},
    {"intent": "search_web", "params": {"query": "python nedir", "browser": "brave"}},
]
```

### English Open + Type

Input:

```text
open notepad and type hello world
```

Output:

```python
[
    {"intent": "open_app", "params": {"app": "notepad"}},
    {"intent": "type", "params": {"text": "hello world", "_require_focus": "notepad"}},
]
```

### English Open + Search

Input:

```text
open chrome and search python tutorial
```

Output:

```python
[
    {"intent": "open_app", "params": {"app": "chrome"}},
    {"intent": "search_web", "params": {"query": "python tutorial", "browser": "chrome"}},
]
```

### Ambiguous Click

Input:

```text
click that button
```

Output:

```python
[
    {
        "intent": "clarification_required",
        "params": {
            "reason": "click target is ambiguous",
            "needed": "browser target, desktop target, or explicit resolved target"
        }
    }
]
```

### Destructive Action

Input:

```text
delete this file
```

Output:

```python
[
    {
        "intent": "approval_required",
        "params": {
            "reason": "destructive action requires explicit proposal and approval"
        }
    }
]
```

---

## Ambiguity Rules

- If target app is unknown, return `clarification_required` unless an explicit fallback policy exists.
- If app alias is known but not installed/resolvable, return `clarification_required` or a verified registry miss, not a guessed app.
- If command says `click that`, `şuna tıkla`, `bu butona tıkla`, or similar unresolved target language, return `clarification_required`.
- If command asks click but target resolution is not possible, no dispatch.
- If browser target vs desktop target is ambiguous, return `clarification_required`.
- If command includes destructive action, return `approval_required`.
- If a command contains multiple actions, preserve order exactly.
- If a later step depends on earlier context, encode that dependency explicitly, for example `_require_focus`.
- If a phrase can be app name or query text, prefer app name only when it matches a known app alias; otherwise ask clarification.
- Do not silently turn unknown app text into search query.

---

## Parser And LLM Boundary

Rule-based deterministic decomposition runs first.

### Rule-Based Layer

Owns:

- known Turkish/English compound patterns
- app alias matching
- URL detection
- search query extraction
- type text extraction
- explicit ambiguity detection
- risk/guard classification for known primitives

### LLM Layer

May only propose normalized plans.

LLM output must pass:

- schema validation
- known intent validation
- known parameter validation
- risk policy validation
- app/tool registry validation where applicable
- ambiguity guard validation
- no direct executor bypass

The LLM cannot:

- call tools directly
- bypass approval
- invent new tool names
- bypass evidence gates
- turn ambiguous click commands into executable clicks
- mark a plan verified

### Guard Layer

The guard accepts only:

- valid primitive intents
- known params
- valid risk route
- explicit status: `ready`, `clarification_required`, `approval_required`, or `blocked`

Invalid LLM output becomes `clarification_required` or `blocked`.

---

## Tests Required Before Code

- Turkish open+type decomposes into `open_app`, then `type`.
- Turkish open+search decomposes into `open_app`, then `search_web`.
- English open+type decomposes into `open_app`, then `type`.
- English open+search decomposes into `open_app`, then `search_web`.
- App name is separated from search query.
- Unknown app does not become search query accidentally.
- Ambiguous click becomes `clarification_required`.
- Generic click never reaches executor as raw `click`.
- Multi-step order is preserved.
- Type step carries `_require_focus` from app/focus step.
- Search step carries browser/app context when present.
- Destructive action becomes `approval_required`.
- LLM proposal with unknown intent is rejected.
- LLM proposal with executable click before target resolution is rejected.

---

## Future Implementation Slices

1. Decomposition schema and tests
   - Define normalized plan shape.
   - Add schema validation.
   - No executor changes.

2. Rule-based Turkish/English open+type
   - Tests first.
   - Emits ordered `open_app` + `type`.

3. Rule-based Turkish/English open+search
   - Tests first.
   - Separates app name from query.

4. Focus+type decomposition
   - Tests first.
   - Emits `focus_app` + `type` with `_require_focus`.

5. Ambiguity and guard validation
   - Unknown app, generic click, destructive action.
   - No dispatch for unresolved click.

6. LLM proposal boundary
   - LLM proposes normalized plan only.
   - Guard validates or rejects.

7. Target Resolution Layer Design
   - Separate design sprint after decomposition design is stable.

---

## Out Of Scope

Do not implement in this design sprint:

- parser changes
- executor changes
- tool changes
- click implementation
- target resolution implementation
- LLM planner implementation
- memory
- vision
- voice
- frontend changes
- replay/timeline changes
- schema versioning
