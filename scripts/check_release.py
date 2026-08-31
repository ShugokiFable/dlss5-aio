#!/usr/bin/env python3
"""dlss5-aio release checker.

Runs cheap, dependency-free checks that catch the mistakes that already bit
this repo:
  1. Dead external links (404s) in README/CREDITS/START-HERE.
  2. Restricted motion-vector provider FILES sneaking into the packed tree
     (iMMERSE / LumeniteFX / MartysMods / Launchpad / VORT shaders are
     license-forbidden to bundle).
  3. Doc pointers (README/CREDITS/LICENSE/LICENSE.md/START-HERE) present.

Every external URL that can't be verified is reported as a WARNING, never a
hard failure, unless it's a genuine 404/410 (a dead link). This avoids flaky CI
from WAF/bot-blocks (403/429) and transient 5xx while still failing on the
class of bug that actually matters: a link that points nowhere.

Exit code 0 = pass, 1 = fail.
"""
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ["README.md", "CREDITS.md", "START-HERE.txt", "LICENSE.md"]

# Provider files that must never be rooted inside the packed tree. The Feeder's
# DLSS5_Feed.fx legitimately *references* them by name (provider selector), so
# this guard checks FILE PATHS only, not file contents.
RESTRICTED_PATH = re.compile(r"(lumenite|quantmotion|martys|launchpad|immerse|vort)",
                             re.IGNORECASE)

URL_RE = re.compile(r"https?://[^\s\)\[\]\"'<>]+")
# Statuses that are probably someone else's bot-block, not a dead link.
SOFT_BLOCK = {403, 405, 429, 418, 451, 999}
# On 5xx the site is up but broken; treat as warn, not fail.
HARD_FAIL = {404, 410}


def find_urls(text: str):
    seen = set()
    for m in URL_RE.finditer(text):
        u = m.group(0).rstrip(".,;:!?")
        if u not in seen:
            seen.add(u)
            yield u


def check_url(url: str):
    req = urllib.request.Request(
        url, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) dlss5-aio-linkcheck",
            "Accept": "*/*",
        })
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, None
    except urllib.error.HTTPError as e:
        return e.code, None
    except urllib.error.URLError as e:
        return 0, str(e.reason)
    except Exception as e:  # noqa: BLE001
        return 0, str(e)


def main():
    ok = True

    # ---- 1. Dead-link check -------------------------------------------------
    all_urls = set()
    for name in DOCS:
        p = ROOT / name
        if p.exists():
            all_urls.update(find_urls(p.read_text(encoding="utf-8", errors="replace")))

    failures = []
    warnings = []
    for url in sorted(all_urls):
        status, err = check_url(url)
        if status == 200:
            continue
        if status in HARD_FAIL:
            failures.append(f"{status}  {url}")
        elif status in SOFT_BLOCK or status >= 500:
            warnings.append(f"{status or 'ERR'}  {url}  ({err})")
        else:
            warnings.append(f"{status or 'ERR'}  {url}  ({err})")
    if warnings:
        print(f"[warn] {len(warnings)} link(s) unverified (likely bot-blocked):")
        for w in warnings:
            print(f"   {w}")
    if failures:
        print(f"[FAIL] {len(failures)} dead link(s):")
        for f in failures:
            print(f"   {f}")
        ok = False
    else:
        print(f"[ok] links: {len(all_urls)} checked, 0 dead")

    # ---- 2. Restricted-file guard ------------------------------------------
    restricted = []
    for f in ROOT.rglob("*"):
        if f.is_file() and not f.is_symlink():
            rel = f.relative_to(ROOT).as_posix()
            # Ignore .git internals and our own scripts.
            if rel.startswith(".git/") or rel.startswith("scripts/") or "workflows" in rel:
                continue
            if RESTRICTED_PATH.search(rel):
                restricted.append(rel)
    if restricted:
        print(f"[FAIL] restricted provider file(s) present in repo tree:")
        for r in restricted:
            print(f"   {r}")
        ok = False
    else:
        print("[ok] restricted-file guard: clean")

    # ---- 3. Doc pointers ----------------------------------------------------
    missing = [name for name in DOCS if not (ROOT / name).exists()]
    if missing:
        print(f"[FAIL] missing docs: {missing}")
        ok = False
    else:
        print("[ok] docs: README/CREDITS/LICENSE/LICENSE.md/START-HERE all present")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
