#!/usr/bin/env python3
"""Builds repo.json (a Dalamud custom plugin repository) from GitHub releases.

For every plugin listed in plugins.json:
  * the newest non-prerelease release that has latest.zip + <InternalName>.json is "stable";
  * a newer prerelease (if any) becomes the "testing" build.
The plugin manifest produced by DalamudPackager is taken from the release and
extended with the download links and stats Dalamud expects.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.github.com"
TOKEN = os.environ.get("GITHUB_TOKEN")


def get(url: str, accept: str = "application/vnd.github+json"):
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": "yona-xiv-repo"})
    if TOKEN and url.startswith(API):
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8-sig"))


def asset(release: dict, name: str) -> dict | None:
    return next((a for a in release.get("assets", []) if a["name"] == name), None)


def version_tuple(v: str) -> tuple[int, ...]:
    parts = [int(p) for p in v.split(".") if p.isdigit()]
    return tuple(parts + [0] * (4 - len(parts)))


def timestamp(iso: str) -> int:
    return int(datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp())


def build_entry(plugin: dict) -> dict | None:
    repo, name = plugin["repo"], plugin["internalName"]
    releases = get(f"{API}/repos/{repo}/releases?per_page=50")

    usable = [r for r in releases
              if not r.get("draft") and asset(r, "latest.zip") and asset(r, f"{name}.json")]
    if not usable:
        print(f"{repo}: no releases with latest.zip + {name}.json yet, skipping")
        return None

    stable = next((r for r in usable if not r["prerelease"]), None)
    testing = next((r for r in usable if r["prerelease"]), None)

    def manifest_of(release: dict) -> dict:
        return get(asset(release, f"{name}.json")["browser_download_url"], accept="application/octet-stream")

    base_release = stable or testing
    manifest = manifest_of(base_release)
    zip_url = asset(base_release, "latest.zip")["browser_download_url"]

    entry = dict(manifest)
    entry.update({
        "RepoUrl": manifest.get("RepoUrl") or f"https://github.com/{repo}",
        "DownloadLinkInstall": zip_url,
        "DownloadLinkUpdate": zip_url,
        "DownloadLinkTesting": zip_url,
        "IsTestingExclusive": stable is None,
        "LastUpdate": timestamp(base_release["published_at"]),
        "DownloadCount": sum(asset(r, "latest.zip")["download_count"] for r in usable),
        "Changelog": (base_release.get("body") or "").strip(),
    })
    if plugin.get("iconUrl"):
        entry["IconUrl"] = plugin["iconUrl"]

    if stable and testing and version_tuple(testing["tag_name"].lstrip("v").split("-")[0]) > version_tuple(manifest["AssemblyVersion"]):
        test_manifest = manifest_of(testing)
        entry["TestingAssemblyVersion"] = test_manifest["AssemblyVersion"]
        entry["TestingDalamudApiLevel"] = test_manifest.get("DalamudApiLevel", manifest.get("DalamudApiLevel"))
        entry["DownloadLinkTesting"] = asset(testing, "latest.zip")["browser_download_url"]
    elif stable is None:
        entry["TestingAssemblyVersion"] = manifest["AssemblyVersion"]

    print(f"{repo}: stable={stable and stable['tag_name']} testing={entry.get('TestingAssemblyVersion')}")
    return entry


def main() -> int:
    plugins = json.loads((ROOT / "plugins.json").read_text(encoding="utf-8"))
    entries = []
    failed = False
    for plugin in plugins:
        try:
            entry = build_entry(plugin)
            if entry:
                entries.append(entry)
        except Exception as exc:  # keep other plugins listed if one repo fails
            failed = True
            print(f"{plugin.get('repo')}: ERROR {exc}", file=sys.stderr)

    if failed:
        print("Not writing repo.json because at least one plugin failed.", file=sys.stderr)
        return 1

    out = ROOT / "repo.json"
    out.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(entries)} plugin(s) to {out.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
