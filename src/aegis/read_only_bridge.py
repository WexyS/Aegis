from __future__ import annotations

import os

import uvicorn

from aegis.api.read_only_bridge import create_bridge_app


app = create_bridge_app()


def main() -> None:
    host = os.getenv("AEGIS_BRIDGE_HOST", "127.0.0.1")
    port = int(os.getenv("AEGIS_BRIDGE_PORT", "8765"))
    uvicorn.run("aegis.read_only_bridge:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
