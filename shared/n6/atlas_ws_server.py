#!/usr/bin/env python3
# @hexa-first-exempt — websockets lib + asyncio binary stream required; hexa stage1 lacks async WS.
# ═══════════════════════════════════════════════════════════
# atlas_ws_server.py — ATLAS-P3-1 WebSocket live bridge
#
# Local WebSocket server on ws://127.0.0.1:8765.
# Tails atlas.n6 (or a scratch file in --probe-lag mode) for new
# @X / @E / @P / @C / @L / @F / @R / @S records and JSON edge lines,
# broadcasts them as {type:"node"|"edge", id, ts} to all connected clients.
#
# MODES
#   default          serve until SIGTERM; polls target mtime every ~250ms
#   --probe-lag      one-shot self-test: server tails a scratch file,
#                    a local client connects, 10 appends are made and
#                    round-trip lag measured server→client. Emits JSON
#                    summary (avg_lag_ms, max_lag_ms, samples[]).
#
# CONSTRAINTS
#   - atlas.n6 is L0 read-only. This script NEVER writes atlas.n6.
#   - --probe-lag uses a scratch file in /tmp, never atlas.n6.
#   - No hooks triggered; single-process, clean shutdown on SIGTERM.
# ═══════════════════════════════════════════════════════════

import argparse
import asyncio
import json
import os
import re
import signal
import sys
import tempfile
import time
from pathlib import Path

try:
    import websockets
except ImportError:
    print("error: websockets module required. pip install websockets", file=sys.stderr)
    sys.exit(1)


HOST = "127.0.0.1"
PORT = 8765
POLL_INTERVAL = 0.25  # 250ms
NEXUS = Path(os.environ.get("NEXUS", "/Users/ghost/Dev/nexus"))
DEFAULT_ATLAS = NEXUS / "shared" / "n6" / "atlas.n6"

# Atlas text-node line pattern (e.g., "@X CS-... = expr :: domain [grade]")
NODE_LINE_RE = re.compile(r"^@([PCLFRSXE\?])\s+([A-Za-z0-9_\-\.]+)")
# Edge line can be JSON object with "type":"edge"
JSON_EDGE_RE = re.compile(r'"type"\s*:\s*"edge"')
JSON_NODE_RE = re.compile(r'"type"\s*:\s*"node"')
JSON_ID_RE = re.compile(r'"(?:id|from|to)"\s*:\s*"([^"]+)"')


class AtlasTailer:
    """Tails a file, yielding parsed events (node/edge) for lines appended since start."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.offset = 0
        self.last_mtime = 0.0
        self._lock = asyncio.Lock()

    def seek_to_end(self):
        try:
            self.offset = self.path.stat().st_size
            self.last_mtime = self.path.stat().st_mtime
        except FileNotFoundError:
            self.offset = 0
            self.last_mtime = 0.0

    async def poll_once(self):
        """Return list of (type, id, ts) events for any new lines since last call."""
        events = []
        try:
            st = self.path.stat()
        except FileNotFoundError:
            return events
        if st.st_mtime == self.last_mtime and st.st_size == self.offset:
            return events
        # File changed; read new bytes
        async with self._lock:
            try:
                with open(self.path, "rb") as f:
                    f.seek(self.offset)
                    new_bytes = f.read()
            except FileNotFoundError:
                return events
            self.offset = st.st_size
            self.last_mtime = st.st_mtime
            # Decode tolerantly
            try:
                text = new_bytes.decode("utf-8", errors="replace")
            except Exception:
                return events
            ts_now = time.time()
            for line in text.splitlines():
                ev = self._parse_line(line, ts_now)
                if ev is not None:
                    events.append(ev)
        return events

    @staticmethod
    def _parse_line(line: str, ts: float):
        s = line.strip()
        if not s:
            return None
        # atlas text node
        m = NODE_LINE_RE.match(s)
        if m:
            return {"type": "node", "id": m.group(2), "ts": ts, "kind": m.group(1)}
        # JSON edge
        if JSON_EDGE_RE.search(s):
            # try to parse JSON and get from/to
            try:
                obj = json.loads(s)
                eid = f"{obj.get('from','?')}->{obj.get('to','?')}"
                return {"type": "edge", "id": eid, "ts": ts,
                        "from": obj.get("from"), "to": obj.get("to"),
                        "edge_type": obj.get("edge_type")}
            except Exception:
                ids = JSON_ID_RE.findall(s)
                return {"type": "edge", "id": "->".join(ids[:2]) if ids else "?", "ts": ts}
        # JSON node
        if JSON_NODE_RE.search(s):
            try:
                obj = json.loads(s)
                return {"type": "node", "id": obj.get("id", "?"), "ts": ts,
                        "kind": "json"}
            except Exception:
                ids = JSON_ID_RE.findall(s)
                return {"type": "node", "id": ids[0] if ids else "?", "ts": ts}
        return None


class WSHub:
    """Tracks connected clients and broadcasts events."""

    def __init__(self):
        self.clients = set()

    async def register(self, ws):
        self.clients.add(ws)

    async def unregister(self, ws):
        self.clients.discard(ws)

    async def broadcast(self, msg: dict):
        if not self.clients:
            return
        encoded = json.dumps(msg)
        dead = []
        for c in list(self.clients):
            try:
                await c.send(encoded)
            except Exception:
                dead.append(c)
        for d in dead:
            self.clients.discard(d)


async def handle_client(ws, hub: WSHub):
    await hub.register(ws)
    try:
        # Send a hello
        await ws.send(json.dumps({"type": "hello", "ts": time.time(),
                                   "source": "atlas_ws_server"}))
        # Keep the connection open; listen for optional client pings
        async for msg in ws:
            # we accept but ignore client messages (subscribe is implicit)
            pass
    except Exception:
        pass
    finally:
        await hub.unregister(ws)


async def tail_loop(tailer: AtlasTailer, hub: WSHub, stop_event: asyncio.Event):
    while not stop_event.is_set():
        try:
            events = await tailer.poll_once()
            for ev in events:
                await hub.broadcast(ev)
        except Exception as e:
            print(f"tail error: {e}", file=sys.stderr)
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=POLL_INTERVAL)
        except asyncio.TimeoutError:
            pass


async def serve_main(atlas_path: Path):
    hub = WSHub()
    tailer = AtlasTailer(atlas_path)
    tailer.seek_to_end()

    stop_event = asyncio.Event()

    def _stop():
        stop_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _stop)
        except NotImplementedError:
            pass

    async with websockets.serve(lambda ws: handle_client(ws, hub), HOST, PORT):
        print(f"atlas_ws_server: listening on ws://{HOST}:{PORT}  target={atlas_path}",
              file=sys.stderr)
        tail_task = asyncio.create_task(tail_loop(tailer, hub, stop_event))
        await stop_event.wait()
        tail_task.cancel()
        try:
            await tail_task
        except asyncio.CancelledError:
            pass
    print("atlas_ws_server: shutdown", file=sys.stderr)


async def probe_lag(n_samples: int = 10) -> dict:
    """Self-test: tail a scratch file, append lines, measure round-trip server→client."""
    scratch = Path(tempfile.gettempdir()) / f"atlas_ws_probe_{os.getpid()}.n6"
    scratch.write_text("", encoding="utf-8")

    hub = WSHub()
    tailer = AtlasTailer(scratch)
    tailer.seek_to_end()

    # Record server-observed emit timestamp and client-observed receive timestamp.
    # We cannot trivially stamp messages on broadcast entry (events are per-line),
    # so we stamp send-time here and compare to client arrival.
    emit_times = {}   # msg_id -> ts at broadcast
    samples_ms = []

    async def stamped_tail(tailer, hub, stop_event):
        while not stop_event.is_set():
            events = await tailer.poll_once()
            for ev in events:
                msg_id = ev.get("id", "?")
                emit_ts = time.time()
                emit_times[msg_id] = emit_ts
                # attach server emit timestamp so client can measure
                payload = dict(ev)
                payload["server_emit_ts"] = emit_ts
                await hub.broadcast(payload)
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=POLL_INTERVAL)
            except asyncio.TimeoutError:
                pass

    stop_event = asyncio.Event()

    server = await websockets.serve(
        lambda ws: handle_client(ws, hub), HOST, PORT
    )
    tail_task = asyncio.create_task(stamped_tail(tailer, hub, stop_event))

    # connect a local client
    try:
        async with websockets.connect(f"ws://{HOST}:{PORT}") as client:
            # drain the hello
            try:
                hello = await asyncio.wait_for(client.recv(), timeout=2.0)
                _ = json.loads(hello)
            except Exception:
                pass

            for i in range(n_samples):
                node_id = f"PROBE-{i:03d}"
                # Append to scratch file (this is NOT atlas.n6)
                append_line = f"@X {node_id} = 1 :: probe [10*]\n"
                t0 = time.time()
                with open(scratch, "a", encoding="utf-8") as f:
                    f.write(append_line)
                    f.flush()
                    os.fsync(f.fileno())
                # Wait for client to receive
                try:
                    while True:
                        raw = await asyncio.wait_for(client.recv(), timeout=5.0)
                        msg = json.loads(raw)
                        if msg.get("id") == node_id and msg.get("type") == "node":
                            t1 = time.time()
                            lag_ms = (t1 - t0) * 1000.0
                            samples_ms.append(round(lag_ms, 3))
                            break
                except asyncio.TimeoutError:
                    samples_ms.append(float("inf"))
                # spacing between samples so polling window doesn't coalesce
                await asyncio.sleep(0.4)
    finally:
        stop_event.set()
        tail_task.cancel()
        try:
            await tail_task
        except asyncio.CancelledError:
            pass
        server.close()
        await server.wait_closed()
        try:
            scratch.unlink()
        except FileNotFoundError:
            pass

    finite = [x for x in samples_ms if x != float("inf")]
    avg = sum(finite) / len(finite) if finite else float("inf")
    mx = max(finite) if finite else float("inf")
    return {
        "lag_samples_ms": samples_ms,
        "avg_lag_ms": round(avg, 3) if finite else None,
        "max_lag_ms": round(mx, 3) if finite else None,
        "n_samples": len(samples_ms),
        "poll_interval_ms": int(POLL_INTERVAL * 1000),
        "target_met": bool(finite and mx < 1000.0),
    }


def parse_args():
    p = argparse.ArgumentParser(
        description="atlas.n6 → WebSocket live bridge (ATLAS-P3-1)"
    )
    p.add_argument("--atlas", default=str(DEFAULT_ATLAS),
                   help="atlas file to tail (default: shared/n6/atlas.n6)")
    p.add_argument("--probe-lag", action="store_true",
                   help="run self-test lag measurement and exit")
    p.add_argument("--samples", type=int, default=10,
                   help="probe-lag sample count (default: 10)")
    return p.parse_args()


def main():
    args = parse_args()
    if args.probe_lag:
        result = asyncio.run(probe_lag(args.samples))
        print(json.dumps(result, indent=2))
        sys.exit(0 if result.get("target_met") else 2)
    asyncio.run(serve_main(Path(args.atlas)))


if __name__ == "__main__":
    main()
