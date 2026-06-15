#!/usr/bin/env python3
"""Pull rack/device inventory from NetBox and write docs/netbox.json.

Env vars:
  NETBOX_URL    Base URL, e.g. https://coreweave.cloud.netboxapp.com
  NETBOX_TOKEN  API token from /user/api-tokens/
  NETBOX_SITE   Site slug to pull (default: evi01)

Locations matching MANUAL_LOCATIONS are skipped (kept as manual entry in the UI).
"""

import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

NETBOX_URL = os.environ.get("NETBOX_URL", "https://coreweave.cloud.netboxapp.com").rstrip("/")
NETBOX_TOKEN = os.environ.get("NETBOX_TOKEN", "")
NETBOX_SITE = os.environ.get("NETBOX_SITE", "evi01")

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "docs", "netbox.json")

MANUAL_LOCATIONS = {"l3-optics-cage", "l3 optics cage", "l3opticscage"}

# Slugs to skip entirely (rollup / parent locations we don't expose in the UI).
SKIP_LOCATIONS = {"us-evi01"}

# Map NetBox Location slugs → UI labels used by the DailyTasks form.
UI_LABEL_OVERRIDES = {
    "data-hall-1": "DH1", "data-hall-2": "DH2",
    "data-hall-3": "DH3", "data-hall-4": "DH4",
    "data-hall-5": "DH5", "data-hall-6": "DH6",
    # Legacy short-form slugs kept in case NetBox is reorganized later
    "dh1": "DH1", "dh2": "DH2", "dh3": "DH3",
    "dh4": "DH4", "dh5": "DH5", "dh6": "DH6",
}


def api_get(path, params=None):
    url = f"{NETBOX_URL}/api/{path.lstrip('/')}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "Authorization": f"Token {NETBOX_TOKEN}",
        "Accept": "application/json",
        "User-Agent": "DailyTasks-fetch-netbox/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            pass
        print(f"\nHTTP {e.code} {e.reason}  for  {url}", file=sys.stderr)
        if body:
            print(f"Response body: {body}", file=sys.stderr)
        raise


def api_paginate(path, params=None):
    params = dict(params or {})
    params.setdefault("limit", 200)
    results = []
    next_url = None
    while True:
        if next_url:
            req = urllib.request.Request(next_url, headers={
                "Authorization": f"Token {NETBOX_TOKEN}",
                "Accept": "application/json",
            })
            with urllib.request.urlopen(req, timeout=60) as resp:
                page = json.loads(resp.read())
        else:
            page = api_get(path, params)
        results.extend(page.get("results", []))
        next_url = page.get("next")
        if not next_url:
            break
    return results


def label_for(loc_slug, loc_name):
    if loc_slug in UI_LABEL_OVERRIDES:
        return UI_LABEL_OVERRIDES[loc_slug]
    return loc_name


def main():
    if not NETBOX_TOKEN:
        print("ERROR: NETBOX_TOKEN env var is required", file=sys.stderr)
        sys.exit(1)

    print(f"NetBox: {NETBOX_URL}  site={NETBOX_SITE}")

    # Verify the site slug exists before pulling locations — otherwise NetBox
    # 400s with an unhelpful filter error. Look up by slug directly (a full
    # listing would time out on large instances).
    site_match = api_get("dcim/sites/", {"slug": NETBOX_SITE, "limit": 1})
    if not site_match.get("results"):
        print(f"\nERROR: site slug '{NETBOX_SITE}' not found on this instance.", file=sys.stderr)
        print(f"Hint: try a case variant or search for it:", file=sys.stderr)
        print(f"  curl -sS -H 'Authorization: Token $NETBOX_TOKEN' \\", file=sys.stderr)
        print(f"    '{NETBOX_URL}/api/dcim/sites/?q={NETBOX_SITE}&limit=20' | \\", file=sys.stderr)
        print(f"    python3 -c \"import json,sys;[print(s['slug'],'—',s['name']) for s in json.load(sys.stdin)['results']]\"", file=sys.stderr)
        sys.exit(2)

    locations = api_paginate("dcim/locations/", {"site": NETBOX_SITE})
    print(f"  found {len(locations)} location(s) under site")

    out_locations = {}
    total_racks = 0
    total_devices = 0

    for loc in locations:
        slug = loc["slug"]
        name = loc["name"]
        if slug.lower() in MANUAL_LOCATIONS:
            print(f"  - {name} ({slug}): skipped (manual entry)")
            continue
        if slug.lower() in SKIP_LOCATIONS:
            print(f"  - {name} ({slug}): skipped (rollup / not exposed in UI)")
            continue

        label = label_for(slug, name)
        racks = api_paginate("dcim/racks/", {"location_id": loc["id"]})
        rack_map = {}
        loc_device_count = 0

        for rack in racks:
            devices = api_paginate("dcim/devices/", {"rack_id": rack["id"]})
            dev_list = []
            for d in devices:
                dev_list.append({
                    "name": d.get("name") or "",
                    "position": d.get("position"),
                    "u_height": (d.get("device_type") or {}).get("u_height"),
                    "role": ((d.get("role") or d.get("device_role") or {}) or {}).get("name"),
                    "status": (d.get("status") or {}).get("value"),
                })
            dev_list.sort(key=lambda x: (x.get("position") is None, x.get("position") or 0, x.get("name") or ""))
            rack_map[rack["name"]] = {
                "id": rack["id"],
                "u_height": rack.get("u_height"),
                "devices": dev_list,
            }
            loc_device_count += len(dev_list)

        out_locations[label] = {
            "slug": slug,
            "netbox_name": name,
            "racks": rack_map,
        }
        total_racks += len(rack_map)
        total_devices += loc_device_count
        print(f"  - {label} ({slug}): {len(rack_map)} rack(s), {loc_device_count} device(s)")

    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": NETBOX_URL,
        "site": NETBOX_SITE,
        "locations": out_locations,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"\nWrote {OUTPUT_PATH}")
    print(f"  {len(out_locations)} location(s), {total_racks} rack(s), {total_devices} device(s)")


if __name__ == "__main__":
    main()
