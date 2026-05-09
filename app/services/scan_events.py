"""In-memory pub/sub for scan WebSocket streams."""

import asyncio
import json
from collections import defaultdict

from fastapi import WebSocket

from app.schemas.scan import StreamEvent


class ScanEventBroker:
    def __init__(self) -> None:
        self._subs: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, scan_id: str, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._subs[scan_id].add(ws)

    async def disconnect(self, scan_id: str, ws: WebSocket) -> None:
        async with self._lock:
            self._subs[scan_id].discard(ws)
            if not self._subs[scan_id]:
                del self._subs[scan_id]

    async def publish(self, scan_id: str, event: StreamEvent) -> None:
        raw = json.dumps(event.model_dump(), default=str)
        async with self._lock:
            targets = list(self._subs.get(scan_id, ()))
        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_text(raw)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(scan_id, ws)


broker = ScanEventBroker()
