"""Run a local web dashboard showing fleet WireGuard status."""
from __future__ import annotations

import datetime
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import click

from porthole import config, ssh, state


def _fetch_status(network) -> list[dict[str, Any]]:
    """SSH to hub, parse wg show dump, return peer list as dicts."""
    hub_host = network.hub.endpoint.split(":")[0]
    try:
        output = ssh.ssh_run(hub_host, "wg show wg0 dump")
    except Exception as exc:
        raise RuntimeError(f"SSH to hub failed: {exc}") from exc

    key_map = {p.public_key: p for p in network.peers if p.role != "hub"}
    peers = []

    lines = output.strip().splitlines()
    for line in lines[1:]:  # skip interface line
        fields = line.split("\t")
        if len(fields) < 8:
            continue
        pubkey = fields[0]
        endpoint = fields[2] if fields[2] != "(none)" else None
        handshake_ts = int(fields[4]) if fields[4].isdigit() else 0
        tx = int(fields[5]) if fields[5].isdigit() else 0
        rx = int(fields[6]) if fields[6].isdigit() else 0

        peer = key_map.get(pubkey)
        name = peer.name if peer else f"unknown-{pubkey[:8]}"
        ip = peer.ip if peer else None
        dns = f"{name}.{getattr(network, 'domain', 'wg')}" if peer else None

        now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
        age_s = (now - handshake_ts) if handshake_ts else None

        if age_s is None:
            status = "never-seen"
        elif age_s < 180:
            status = "connected"
        elif age_s < 600:
            status = "stale"
        else:
            status = "offline"

        peers.append(
            dict(
                name=name,
                ip=ip,
                dns=dns,
                endpoint=endpoint,
                handshake_ts=handshake_ts,
                age_s=age_s,
                tx_bytes=tx,
                rx_bytes=rx,
                status=status,
            )
        )

    peers.sort(key=lambda p: p["name"])
    return peers


_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>porthole fleet dashboard</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 1100px; margin: 2rem auto; padding: 0 1rem; color: #222; }
    h1   { font-size: 1.5rem; margin-bottom: 0.5rem; }
    .toolbar { display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem; }
    button { background: #3b82f6; color: #fff; border: none; padding: 0.45rem 1.1rem;
             border-radius: 6px; cursor: pointer; font-size: 0.9rem; }
    button:hover { background: #2563eb; }
    #timestamp { color: #666; font-size: 0.85rem; }
    #error { color: #dc2626; margin-bottom: 1rem; display: none; }
    table { width: 100%; border-collapse: collapse; }
    th, td { text-align: left; padding: 0.45rem 0.65rem; border-bottom: 1px solid #e5e5e5; font-size: 0.88rem; }
    th { background: #f5f5f5; font-weight: 600; }
    .dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; }
    .connected  { background: #22c55e; }
    .stale      { background: #f59e0b; }
    .offline    { background: #ef4444; }
    .never-seen { background: #94a3b8; }
    td.mono { font-family: monospace; font-size: 0.82rem; }
  </style>
</head>
<body>
  <h1>porthole fleet dashboard</h1>
  <div class="toolbar">
    <button onclick="refresh()">Refresh</button>
    <span id="timestamp">Loading…</span>
  </div>
  <div id="error"></div>
  <table id="table">
    <thead><tr>
      <th>Status</th><th>Name</th><th>WireGuard IP</th><th>DNS</th>
      <th>Endpoint</th><th>Last Handshake</th><th>Tx</th><th>Rx</th>
    </tr></thead>
    <tbody id="tbody"></tbody>
  </table>
  <script>
    function fmtBytes(n) {
      const u = ["B","KiB","MiB","GiB"];
      for (const s of u) { if (n < 1024) return n.toFixed(1) + " " + s; n /= 1024; }
      return n.toFixed(1) + " TiB";
    }
    function fmtAge(s) {
      if (s === null) return "never";
      if (s < 60) return s + "s ago";
      if (s < 3600) return Math.floor(s/60) + "m ago";
      return Math.floor(s/3600) + "h " + Math.floor((s%3600)/60) + "m ago";
    }
    async function refresh() {
      const errEl = document.getElementById("error");
      const tsEl  = document.getElementById("timestamp");
      errEl.style.display = "none";
      tsEl.textContent = "Fetching…";
      try {
        const r = await fetch("/api/status");
        if (!r.ok) throw new Error("HTTP " + r.status);
        const peers = await r.json();
        const tb = document.getElementById("tbody");
        tb.innerHTML = "";
        for (const p of peers) {
          const dot = `<span class="dot ${p.status}"></span>`;
          const label = p.status.replace("-", " ");
          tb.innerHTML += `<tr>
            <td>${dot}${label}</td>
            <td>${p.name}</td>
            <td class="mono">${p.ip || "—"}</td>
            <td class="mono">${p.dns || "—"}</td>
            <td class="mono">${p.endpoint || "—"}</td>
            <td>${fmtAge(p.age_s)}</td>
            <td>${fmtBytes(p.tx_bytes)}</td>
            <td>${fmtBytes(p.rx_bytes)}</td>
          </tr>`;
        }
        tsEl.textContent = "Updated: " + new Date().toLocaleTimeString();
      } catch(e) {
        errEl.textContent = "Error: " + e.message;
        errEl.style.display = "";
        tsEl.textContent = "Failed.";
      }
    }
    refresh();
    setInterval(refresh, 60000);
  </script>
</body>
</html>
"""


def run_dashboard(port: int) -> None:
    """Start the fleet dashboard web server."""
    state_path = config.STATE_FILE
    if not state_path.exists():
        raise click.ClickException(f"State file not found: {state_path}")

    network = state.load_state(state_path)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):  # noqa: A002
            pass  # silence access log

        def _send(self, code: int, ctype: str, body: bytes) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/":
                self._send(200, "text/html; charset=utf-8", _HTML.encode())
            elif self.path == "/api/status":
                try:
                    peers = _fetch_status(network)
                    body = json.dumps(peers).encode()
                    self._send(200, "application/json", body)
                except RuntimeError as exc:
                    body = json.dumps({"error": str(exc)}).encode()
                    self._send(500, "application/json", body)
            else:
                self._send(404, "text/plain", b"Not Found")

    server = HTTPServer(("0.0.0.0", port), Handler)
    click.echo(f"porthole dashboard running at http://localhost:{port}/")
    click.echo("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        click.echo("\nStopped.")
