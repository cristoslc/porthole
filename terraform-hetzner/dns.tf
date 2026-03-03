# ---------------------------------------------------------------------------
# dns.tf — DNS A record for the hub hostname via Hetzner DNS API
#
# Hetzner DNS is a separate service from Hetzner Cloud; both use the same
# API token (hcloud_token / HETZNER_DNS_API_TOKEN).
#
# Prerequisite: the parent domain (e.g. "example.com") must already exist
# as a Hetzner-managed DNS zone.
#
# Implementation note: the hetznerdns Terraform provider only exists in the
# Terraform registry, not the OpenTofu registry. This resource uses
# null_resource + local-exec calling the Hetzner DNS REST API directly via
# Python stdlib, with idempotent upsert logic (update if record exists,
# create otherwise).
# ---------------------------------------------------------------------------

locals {
  hostname_parts = split(".", var.hub_hostname)
  subdomain      = local.hostname_parts[0]
  domain_name    = join(".", slice(local.hostname_parts, 1, length(local.hostname_parts)))
}

resource "null_resource" "dns_record" {
  # Re-runs whenever the server IP changes (e.g. after destroy + apply).
  triggers = {
    hub_ip    = hcloud_server.hub.ipv4_address
    subdomain = local.subdomain
    domain    = local.domain_name
  }

  provisioner "local-exec" {
    interpreter = ["python3", "-c"]
    command     = <<-PYTHON
import json, sys, urllib.request, urllib.error

token     = "${var.hcloud_token}"
subdomain = "${local.subdomain}"
domain    = "${local.domain_name}"
ip        = "${hcloud_server.hub.ipv4_address}"

BASE = "https://dns.hetzner.com/api/v1"
headers = {"Auth-API-Token": token, "Content-Type": "application/json"}

def api(method, path, body=None):
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} {method} {path}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)

# Look up zone
zones = api("GET", f"/zones?name={domain}").get("zones", [])
if not zones:
    print(f"ERROR: DNS zone '{domain}' not found in Hetzner DNS.", file=sys.stderr)
    print("Create the zone in Hetzner DNS console and re-run terraform apply.", file=sys.stderr)
    sys.exit(1)
zone_id = zones[0]["id"]

# Upsert A record
records = api("GET", f"/records?zone_id={zone_id}").get("records", [])
existing = [r for r in records if r["name"] == subdomain and r["type"] == "A"]
payload  = {"value": ip, "ttl": 300, "type": "A", "name": subdomain, "zone_id": zone_id}

if existing:
    rid = existing[0]["id"]
    api("PUT", f"/records/{rid}", payload)
    print(f"Updated A record: {subdomain}.{domain} -> {ip}")
else:
    api("POST", "/records", payload)
    print(f"Created A record: {subdomain}.{domain} -> {ip}")
    PYTHON
  }
}
