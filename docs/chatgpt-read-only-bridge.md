# ChatGPT Read-Only Bridge

## Purpose

The Aegis Read-Only ChatGPT Bridge lets a Custom GPT named `Aegis Architect`
inspect the current Aegis repository through a controlled local HTTP surface.

The bridge is for review and prompt planning only. It is not Aegis Ask, not
autonomous operation, not MCP, not external tool execution, and not a Codex
replacement. Codex remains the executor for code changes, validation, commits,
and pushes.

## Architecture

The bridge is implemented as an isolated FastAPI app in
`src/aegis/api/read_only_bridge.py` with a manual entrypoint at
`src/aegis/read_only_bridge.py`.

It is intentionally not mounted into the normal Aegis runtime app. Starting the
bridge does not start Socket.IO runtime workers, command execution, frontend
authority, model calls, or journal mutation.

## Security Model

The bridge is local, token-gated, read-only, and repo-root locked.

Security boundaries:

- requires `X-Aegis-Bridge-Token`
- root is locked to `C:\Users\nemes\Desktop\Aegis`
- safe path resolver blocks absolute paths, UNC paths, home-relative paths,
  traversal, symlinks, and outside-repo paths
- JSON responses only
- no write endpoints
- no command execution endpoints
- no app launch endpoints
- no model/tool/MCP endpoints
- no external network calls
- no file content in request audit logs
- no runtime log/archive exposure by default

Git metadata endpoints use fixed read-only git argument lists. They do not
accept arbitrary commands and do not return diff content.

## Endpoints

- `GET /health`: bridge status, repo root, read-only flags, denied path policy,
  and current HEAD when available.
- `GET /repo/status`: branch, HEAD, clean/dirty state, and changed file paths.
- `GET /repo/tree`: filtered repository tree with denylist and result caps.
- `GET /repo/file`: safe UTF-8 text file content with size and line count.
- `POST /repo/search`: bounded Python text search over allowlisted text files.
- `POST /repo/context-pack`: bounded snippets from explicit files or search
  results. Context packs are not permission or authority.
- `GET /repo/git-log`: recent commit metadata without diffs.

## Denied Paths

Denied by default:

- `.git`
- `.env`
- `.env.*`
- secret/token/credential/private-key/password-like file names
- `node_modules`
- `.next`
- `.venv`
- `.pytest_cache`
- `__pycache__`
- build/dist/cache artifacts
- `logs`
- `logs/archive`
- `runtime_events.jsonl`
- `.log` and `.jsonl` files
- binary/media/archive/database files

Denied paths are rejected before file content is read.

## Authentication Setup

The recommended local launcher creates a random token automatically and stores
it only in `.local/aegis-bridge-token.txt`. The `.local/` directory is ignored
by git.

Start with the Windows launcher:

```powershell
.\scripts\start-aegis-bridge.bat
```

To start the bridge and attempt to start ngrok for port `8765`:

```powershell
.\scripts\start-aegis-bridge-and-ngrok.bat
```

The launcher:

- creates `.local/` if needed
- creates `.local/aegis-bridge-token.txt` if missing
- sets `AEGIS_BRIDGE_TOKEN` for the bridge process
- starts `.\.venv\Scripts\python.exe -m aegis.read_only_bridge`
- prints the local URL, token file path, auth header name, and tunnel reminder

The bridge + ngrok launcher:

- reuses the same local token file
- starts the bridge in a separate local process
- starts `ngrok http 8765` if `ngrok` is installed and on `PATH`
- keeps bridge startup usable even when ngrok is missing
- prints the local URL, token file path, auth header name, OpenAPI schema path,
  and manual Custom GPT reminders

The normal launcher does not print the token. To intentionally display it for
Custom GPT Action setup:

```powershell
.\scripts\show-aegis-bridge-token.ps1
```

That helper requires typing `SHOW` before it prints the token.

To reset the token, stop the bridge, delete:

```text
.local/aegis-bridge-token.txt
```

Then rerun:

```powershell
.\scripts\start-aegis-bridge.bat
```

Manual token setup is still supported if needed:

```powershell
$env:AEGIS_BRIDGE_TOKEN = "replace-with-local-random-token"
```

Do not commit or paste the real token into docs, prompts, screenshots, issue
comments, or OpenAPI examples.

## Run Locally

From the Aegis repo:

```powershell
.\scripts\start-aegis-bridge.bat
```

Direct module startup remains available for advanced/manual use:

```powershell
$env:AEGIS_BRIDGE_TOKEN = "replace-with-local-random-token"
.\.venv\Scripts\python.exe -m aegis.read_only_bridge
```

Default URL:

```text
http://127.0.0.1:8765
```

Optional host/port:

```powershell
$env:AEGIS_BRIDGE_HOST = "127.0.0.1"
$env:AEGIS_BRIDGE_PORT = "8765"
```

## Custom GPT Action Setup

Use `docs/aegis-read-only-bridge-openapi.yaml` as the Custom GPT Action schema.

Configure API key auth:

- header name: `X-Aegis-Bridge-Token`
- value: the local operator-provided token from
  `.local/aegis-bridge-token.txt`

Use `scripts\show-aegis-bridge-token.ps1` when you intentionally need to copy
the token. Do not paste the token into prompts or committed files.

To show and copy the current ngrok HTTPS URL after the tunnel starts:

```powershell
.\scripts\show-aegis-ngrok-url.ps1
```

To copy a small Custom GPT Action setup summary without printing the token:

```powershell
.\scripts\copy-aegis-bridge-action-values.ps1
```

Recommended first calls:

1. `GET /health`
2. `GET /repo/status`
3. `GET /repo/tree`
4. `GET /repo/file` for specific safe files
5. `POST /repo/search` for bounded lookup
6. `POST /repo/context-pack` for compact review context

## Tunnel Notes

Prefer local-only use. Custom GPT Actions normally need an HTTPS URL, so if a
tunnel is required, configure it manually with your chosen local tunnel provider.
The bridge does not require ngrok, Cloudflare, or any paid service.

For the common ngrok path:

```powershell
.\scripts\start-aegis-bridge-and-ngrok.bat
```

Then:

```powershell
.\scripts\show-aegis-ngrok-url.ps1
```

Paste the returned HTTPS URL into the OpenAPI `servers.url` field in the Custom
GPT Action setup. The default OpenAPI file stays committed with localhost;
operator-specific tunnel URLs should not be committed.

Free ngrok URLs may change each time the tunnel starts. A static tunnel can be
configured later if the operator has one, but static domains are not required.
Use a short-lived tunnel bound to the bridge port, keep the token private, and
shut the tunnel down after the review session.

Do not expose the bridge without token auth. Do not expand the bridge to include
write, execute, shell, app-launch, model-call, or external API endpoints.

Stop the bridge and ngrok by closing their process windows or pressing Ctrl+C in
each process.

## Recommended Workflow

1. Codex implements changes, runs tests, commits, and pushes.
2. Aegis Architect inspects the repo through the bridge.
3. Aegis Architect verifies Codex reports against files where possible.
4. The user/operator approves the next direction.
5. Codex receives the next scoped implementation prompt.

## Threat Model

Primary risks:

- accidental secret exposure
- reading ignored runtime logs or archives
- path traversal outside the repo
- treating bridge context as evidence or authority
- turning the bridge into a command execution surface
- leaving a tunnel open longer than needed

Controls:

- denylist and safe path resolver
- token header
- local host default
- size and result caps
- binary rejection
- no write/execute endpoints
- no normal runtime integration
- no frontend authority
- no model/tool/MCP execution

## Limitations

- The bridge reads safe text files only.
- Large files are rejected.
- Runtime logs, archives, `.git`, `.env`, caches, generated artifacts, and
  secret-like paths are denied.
- Context pack output is convenience context, not permission, evidence, verifier
  success, approval, lease, or capability.
- Git status/log metadata is read-only and does not include diffs.
- The bridge is not a security boundary for untrusted public exposure.

## Remaining Risks

- A tunnel provider could add exposure risk if misconfigured.
- Denylist naming cannot prove a safe file has no sensitive content.
- The bridge does not replace human review before using any snippet in a prompt.
- Future expansions must keep write/execute/model/tool/MCP/network operations
  out of this bridge.
