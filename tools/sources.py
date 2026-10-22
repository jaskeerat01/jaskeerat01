"""sources.py — fetch the Markdown the site is generated from.

The research content lives in public GitHub repositories:

  * Writeups      — the OSINT challenge write-ups and sourcing exercises
  * Breach_Reports — the published breach analyses

Files are cached under `tools/cache/` so the generator can be re-run offline
and so that a run is deterministic: the same cached input always produces the
same output.

Standard library only.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"
USER_AGENT = "jaskeerat-portfolio-generator (static site builder)"


def _cache_path(owner, repo, branch, path):
    safe = path.replace("/", "__")
    return os.path.join(CACHE_DIR, owner, repo, branch, safe)


def _read_cache(owner, repo, branch, path):
    full = _cache_path(owner, repo, branch, path)
    if os.path.isfile(full):
        with open(full, encoding="utf-8") as fh:
            return fh.read()
    return None


def _write_cache(owner, repo, branch, path, data):
    full = _cache_path(owner, repo, branch, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(data)


def fetch_text(owner, repo, branch, path, refresh=False, offline=False):
    """Return the raw text of `path` in `owner/repo`, using the local cache first."""
    if not refresh and not offline:
        cached = _read_cache(owner, repo, branch, path)
        if cached is not None:
            return cached
    if offline:
        cached = _read_cache(owner, repo, branch, path)
        if cached is None:
            raise FileNotFoundError(
                f"{owner}/{repo}/{branch}/{path} is not in the cache and --offline was requested"
            )
        return cached

    url = f"{RAW}/{owner}/{repo}/{branch}/{urllib.parse.quote(path)}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"could not fetch {url}: HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"could not fetch {url}: {exc.reason}") from exc
    _write_cache(owner, repo, branch, path, data)
    return data


def list_dir(owner, repo, branch, path, refresh=False, offline=False):
    """List a directory in a repository, returning a list of file names."""
    cache_file = os.path.join(
        CACHE_DIR, owner, repo, branch, f"__dir__{path.replace('/', '__')}.json"
    )
    if not refresh and os.path.isfile(cache_file):
        with open(cache_file, encoding="utf-8") as fh:
            return json.load(fh)
    if offline:
        scanned = _scan_cache(owner, repo, branch, path)
        if scanned is None:
            raise FileNotFoundError(
                f"directory listing for {owner}/{repo}/{branch}/{path} is not cached"
            )
        return scanned

    url = f"{API}/repos/{owner}/{repo}/contents/{urllib.parse.quote(path)}?ref={branch}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    names = sorted(
        entry["name"] for entry in payload
        if entry["type"] == "file" and entry["name"].lower().endswith((".md", ".markdown"))
    )
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, "w", encoding="utf-8") as fh:
        json.dump(names, fh, indent=2)
    return names


def _scan_cache(owner, repo, branch, path):
    """Reconstruct a directory listing from the files already cached."""
    base = os.path.join(CACHE_DIR, owner, repo, branch)
    if not os.path.isdir(base):
        return None
    prefix = f"{path}/" if path else ""
    names = []
    for entry in os.listdir(base):
        if not entry.endswith((".md", ".markdown")):
            continue
        # Cached file names use "__" in place of "/".
        flat = entry[:-3] if entry.lower().endswith(".md") else entry
        if flat.startswith(prefix.replace("/", "__")):
            names.append(flat.split("__")[-1] + ".md")
    if not names:
        return None
    return sorted(names)
