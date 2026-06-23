#!/usr/bin/env python3
"""Pull rack/device inventory from NetBox and write docs/netbox.json.

Env vars:
  NETBOX_URL     Base URL, e.g. https://coreweave.cloud.netboxapp.com
  NETBOX_TOKEN   API token from /user/api-tokens/
  NETBOX_SITES   Comma-separated list of site slugs (e.g. "evi01,evi02"). Home
                 site is the first entry — UI treats it as the default site.
  NETBOX_SITE    Single-site shortcut. Used only when NETBOX_SITES is unset.

Output shape (multi-site):
  {
    "fetched_at": "...",
    "source": "...",
    "home_site": "evi01",
    "sites": {
      "evi01": { "slug": "evi01", "fetched_at": "...", "locations": {...} },
      "evi02": { "slug": "evi02", "fetched_at": "...", "locations": {...} }
    }
  }

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
NETBOX_SITES_ENV = os.environ.get("NETBOX_SITES", "").strip()
NETBOX_SITE = os.environ.get("NETBOX_SITE", "evi01").strip()

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "docs", "netbox.json")

MANUAL_LOCATIONS = {"l3-optics-cage", "l3 optics cage", "l3opticscage"}

# Slugs to skip entirely (rollup / parent locations we don't expose in the UI).
# Keys are site slug (lowercase); values are sets of location slugs.
SKIP_LOCATIONS_BY_SITE = {
    "evi01": {"us-evi01"},
}

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


def fetch_site(site_slug):
    """Fetch one site's locations/racks/devices. Returns a dict with locations,
    or None if the site slug doesn't exist on this NetBox instance."""
    site_match = api_get("dcim/sites/", {"slug": site_slug, "limit": 1})
    if not site_match.get("results"):
        print(f"  ! site slug '{site_slug}' not found on this instance — skipped", file=sys.stderr)
        return None

    locations = api_paginate("dcim/locations/", {"site": site_slug})
    print(f"  found {len(locations)} location(s) under site {site_slug}")

    skip_locs = SKIP_LOCATIONS_BY_SITE.get(site_slug.lower(), set())
    out_locations = {}
    total_racks = 0
    total_devices = 0

    for loc in locations:
        slug = loc["slug"]
        name = loc["name"]
        if slug.lower() in MANUAL_LOCATIONS:
            print(f"    - {name} ({slug}): skipped (manual entry)")
            continue
        if slug.lower() in skip_locs:
            print(f"    - {name} ({slug}): skipped (rollup / not exposed in UI)")
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
        print(f"    - {label} ({slug}): {len(rack_map)} rack(s), {loc_device_count} device(s)")

    return {
        "slug": site_slug,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "totals": {"locations": len(out_locations), "racks": total_racks, "devices": total_devices},
        "locations": out_locations,
    }


def main():
    if not NETBOX_TOKEN:
        print("ERROR: NETBOX_TOKEN env var is required", file=sys.stderr)
        sys.exit(1)

    if NETBOX_SITES_ENV:
        site_slugs = [s.strip().lower() for s in NETBOX_SITES_ENV.split(",") if s.strip()]
    else:
        site_slugs = [NETBOX_SITE.lower()]

    if not site_slugs:
        print("ERROR: no sites configured (set NETBOX_SITES or NETBOX_SITE)", file=sys.stderr)
        sys.exit(1)

    home_site = site_slugs[0]
    print(f"NetBox: {NETBOX_URL}  home={home_site}  sites={site_slugs}")

    sites_out = {}
    grand_locations = 0
    grand_racks = 0
    grand_devices = 0
    for slug in site_slugs:
        print(f"\n--- site: {slug} ---")
        site_data = fetch_site(slug)
        if not site_data:
            continue
        sites_out[slug] = site_data
        grand_locations += site_data["totals"]["locations"]
        grand_racks += site_data["totals"]["racks"]
        grand_devices += site_data["totals"]["devices"]

    if not sites_out:
        print("\nERROR: no sites fetched successfully — aborting", file=sys.stderr)
        sys.exit(2)

    if home_site not in sites_out:
        # Fall back to the first successfully fetched site as home.
        home_site = next(iter(sites_out.keys()))

    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": NETBOX_URL,
        "home_site": home_site,
        "sites": sites_out,
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    # Compact separators shrink the file by ~40% on disk (page download is gzipped
    # by GitHub Pages anyway). One site is ~700 KB, six sites ~4 MB on disk.
    with open(OUTPUT_PATH, "w") as f:
        json.dump(payload, f, separators=(",", ":"))

    size = os.path.getsize(OUTPUT_PATH)
    print(f"\nWrote {OUTPUT_PATH}  ({size/1024:.0f} KB)")
    print(f"  {len(sites_out)} site(s), {grand_locations} location(s), {grand_racks} rack(s), {grand_devices} device(s)")


if __name__ == "__main__":
    main()
