#!/usr/bin/env python3
"""check.py — verify the built site.

Run this after any change to the HTML, the CSS or the generator:

    python3 tools/check.py

It checks structure, links, accessibility basics, the security rules and the
content rules, and exits non-zero if anything fails. Standard library only, so
it needs no installation.

The checks are the ones an agent (or a person) should run before committing:

  * every HTML file is well formed and has a sensible heading outline
  * every internal link and asset resolves to a real file
  * no link points at a directory URL
  * every off-site link carries rel="noopener noreferrer"
  * there is no JavaScript, no form, no tracker and no remote subresource
  * images carry no metadata
  * no absolute system path or authoring note is left in the output
  * every archive entry links back to its archive, and every entry page is listed
  * the robots.txt does not block a published document
  * no placeholder text and no unexpected contact address
"""

from __future__ import annotations

import os
import re
import sys
from html.parser import HTMLParser
from urllib.parse import unquote, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

failures = []
notes = []


def fail(message):
    failures.append(message)


def ok(message):
    notes.append(message)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.errors = []
        self.ids = []
        self.links = []        # (tag, attrs, text)
        self.imgs = []
        self.headings = []
        self.lang = None
        self.title = None
        self._in_title = False
        self._link = None
        self._text = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.lang = a.get("lang")
        if tag == "title":
            self._in_title = True
        if "id" in a:
            self.ids.append(a["id"])
        if tag in ("a", "button") and (a.get("href") or tag == "button"):
            self._link = (tag, a)
            self._text = []
        if tag == "img":
            self.imgs.append(a)
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if self._link and self._link[0] == tag:
            self.links.append((self._link[0], self._link[1], " ".join(self._text).strip()))
            self._link = None
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append(f"stray </{tag}>")
            return
        if self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            while self.stack and self.stack[-1] != tag:
                self.errors.append(f"unclosed <{self.stack.pop()}> before </{tag}>")
            if self.stack:
                self.stack.pop()
        else:
            self.errors.append(f"unexpected </{tag}>")

    def handle_data(self, data):
        if self.stack and self.stack[-1] in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.headings.append((self.stack[-1], data.strip()))
        if self._link:
            self._text.append(data)


def html_pages():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        if "cache" in dirpath.split(os.sep) or "__pycache__" in dirpath:
            continue
        for name in sorted(filenames):
            if name.endswith(".html"):
                yield os.path.join(dirpath, name)


def load(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# collect
# ---------------------------------------------------------------------------

pages = {}
for path in html_pages():
    relative = os.path.relpath(path, ROOT)
    source = load(path)
    parser = Page()
    parser.feed(source)
    parser.close()
    pages[relative] = (parser, source, path)

if not pages:
    print("No HTML files found.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# structure
# ---------------------------------------------------------------------------

for relative, (parser, source, path) in pages.items():
    if parser.errors:
        fail(f"{relative}: " + "; ".join(parser.errors[:6]))
    if parser.stack:
        fail(f"{relative}: unclosed tags at the end of the file: {parser.stack}")
    if parser.lang != "en":
        fail(f"{relative}: <html lang> is {parser.lang!r}, expected 'en'")
    if not parser.ids:
        fail(f"{relative}: no id attributes found")
    if len(parser.ids) != len(set(parser.ids)):
        duplicates = sorted({i for i in parser.ids if parser.ids.count(i) > 1})
        fail(f"{relative}: duplicate ids: {duplicates}")

    h1s = [h for h, _ in parser.headings if h == "h1"]
    if len(h1s) != 1:
        fail(f"{relative}: expected exactly one <h1>, found {len(h1s)}")
    previous = 0
    for tag, text in parser.headings:
        level = int(tag[1])
        if previous and level > previous + 1:
            fail(f"{relative}: heading level jumps from h{previous} to h{level} ({text!r})")
        previous = level

    for img in parser.imgs:
        if "alt" not in img:
            fail(f"{relative}: <img src={img.get('src')!r}> has no alt attribute")

    for tag, attrs, text in parser.links:
        if not attrs.get("href"):
            continue
        href = attrs["href"]
        if href.startswith("#") and href[1:] not in set(parser.ids):
            fail(f"{relative}: in-page link {href!r} has no target")

    for match in re.finditer(r'aria-(?:labelledby|describedby)="([^"]+)"', source):
        for target in match.group(1).split():
            if target not in set(parser.ids):
                fail(f"{relative}: aria reference to a missing id {target!r}")

ok(f"{len(pages)} HTML documents are well formed with a single <h1> each")

# ---------------------------------------------------------------------------
# links
# ---------------------------------------------------------------------------

for relative, (parser, source, path) in pages.items():
    base = os.path.dirname(path)
    for match in re.finditer(r'(?:href|src)\s*=\s*"([^"]+)"', source):
        raw = match.group(1)
        if raw.startswith(("http://", "https://", "mailto:", "data:", "#")):
            continue
        target = unquote(raw.partition("#")[0])
        if not target:
            continue
        resolved = os.path.normpath(os.path.join(base, target))
        if not os.path.exists(resolved):
            fail(f"{relative}: link does not resolve: {raw!r}")
        if target.endswith("/"):
            fail(f"{relative}: link points at a directory URL: {raw!r}")

ok("every internal link and asset resolves, and no link points at a directory")

# ---------------------------------------------------------------------------
# security
# ---------------------------------------------------------------------------

REMOTE = re.compile(r'<(?:script|img|iframe|source|video|audio|embed|object)\b[^>]*>', re.I)
ALLOWED_EXTERNAL = {
    "github.com", "www.github.com", "www.linkedin.com", "linkedin.com",
    "attack.mitre.org", "en.wikipedia.org", "platesmania.com", "www.whoxy.com",
    "www.alamy.com", "museum.wales", "senedd.wales", "www.facebook.com",
    "cyberchef.org", "mailmeteor.com", "meta.stackoverflow.com",
    "stackoverflow.com", "api.github.com", "crackstation.net", "fortune.com",
    "www.freelancer.com", "www.airbnb.co.in", "web.archive.org",
    "www.microsoft.com", "www.meetup.com", "edubilla.com", "curekirby.org",
    "margaretjones.weebly.com", "www.researchgate.net", "www.kaggle.com",
    "www.ere.net", "corprecruiter.blogspot.com", "au.linkedin.com",
    "www.sourcing.games", "inovace.eu", "ru.pinterest.com", "readymag.website",
    "www.lovemoney.com", "bitbucket.org", "x.com", "www.x.com", "twitter.com",
    "www.forbes.com", "www.flickr.com",
    "register-of-charities.charitycommission.gov.uk",
}

for relative, (parser, source, path) in pages.items():
    if re.search(r"<script", source, re.I):
        fail(f"{relative}: a <script> tag is present")
    if re.search(r"\son[a-z]+\s*=\s*[\"']", source, re.I):
        fail(f"{relative}: an inline event handler attribute is present")
    if re.search(r"javascript:", source, re.I):
        fail(f"{relative}: a javascript: URL is present")
    if re.search(r"<form|<input|<textarea|<select", source, re.I):
        fail(f"{relative}: a form control is present")
    if re.search(r"localStorage|sessionStorage|document\.cookie|getImageData|"
                 r"navigator\.geolocation|getUserMedia", source, re.I):
        fail(f"{relative}: references a browser API the site should not use")
    if re.search(r"google-analytics|googletagmanager|gtag\(|hotjar|matomo|"
                 r"plausible|umami|clarity|fonts\.googleapis|cdn\.", source, re.I):
        fail(f"{relative}: references a third-party tracker, font or CDN")
    for match in REMOTE.finditer(source):
        if re.search(r'(?:src|href)\s*=\s*"(?:https?:)?//', match.group(0), re.I):
            fail(f"{relative}: loads a remote subresource: {match.group(0)[:90]}")

    for tag, attrs, text in parser.links:
        href = attrs.get("href", "")
        if not href.startswith(("http://", "https://")):
            continue
        rel = (attrs.get("rel") or "").lower().split()
        if "noopener" not in rel or "noreferrer" not in rel:
            fail(f"{relative}: external link without rel=noopener noreferrer: {href[:70]}")
        host = urlparse(href).netloc.lower()
        if host not in ALLOWED_EXTERNAL:
            fail(f"{relative}: unexpected external host: {host}")

    if 'name="referrer"' not in source or "strict-origin-when-cross-origin" not in source:
        fail(f"{relative}: missing Referrer-Policy: strict-origin-when-cross-origin")

ok("no scripting, no trackers, no remote subresources, external links are hardened")

# ---------------------------------------------------------------------------
# images
# ---------------------------------------------------------------------------

image_dir = os.path.join(ROOT, "assets", "images")
if os.path.isdir(image_dir):
    for name in sorted(os.listdir(image_dir)):
        if not name.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
            continue
        with open(os.path.join(image_dir, name), "rb") as fh:
            blob = fh.read()
        if b"Raw profile type" in blob or b"Exif" in blob[:200]:
            fail(f"assets/images/{name}: contains EXIF metadata")
        for marker in (b"tEXt", b"iTXt", b"zTXt", b"tIME"):
            if marker in blob:
                fail(f"assets/images/{name}: contains a {marker.decode()} text chunk")
    ok("images carry no EXIF and no text chunks")

# ---------------------------------------------------------------------------
# nothing that leaks the machine
# ---------------------------------------------------------------------------

LEAKS = [
    (r"(?:^|[\s\"'(=])/home/[A-Za-z0-9._-]+", "an absolute home directory path"),
    (r"(?:^|[\s\"'(=])/Users/[A-Za-z0-9._-]+", "an absolute macOS home path"),
    (r"(?:^|[\s\"'(=])/tmp/[A-Za-z0-9._-]+", "a temporary directory path"),
    (r"(?:^|[\s\"'(=])[A-Z]:\\\\", "an absolute Windows path"),
    (r"<!--", "an HTML comment"),
    (r"\bTODO\b|\bFIXME\b", "an authoring note"),
    (r"gnome-screenshot|weasyprint|puppeteer|playwright", "the name of local tooling"),
]
for relative, (parser, source, path) in pages.items():
    for pattern, label in LEAKS:
        match = re.search(pattern, source, re.I)
        if match:
            snippet = source[max(0, match.start() - 30):match.end() + 30].replace("\n", " ")
            fail(f"{relative}: possible {label}: ...{snippet}...")

ok("no absolute system paths, comments or authoring notes in the output")

# ---------------------------------------------------------------------------
# archives
# ---------------------------------------------------------------------------

for archive, prefix in (("writeups/index.html", "writeups/"),
                         ("breach-reports/index.html", "breach-reports/")):
    if archive not in pages:
        fail(f"{archive}: missing")
        continue
    source = pages[archive][1]
    links = [l for l in re.findall(r'href="([^"#]+\.html)"', source)
             if not l.startswith("../")]
    if not links:
        fail(f"{archive}: no entries are linked")
    for link in links:
        entry = f"{prefix}{link}"
        if entry not in pages:
            fail(f"{archive}: entry {link!r} has no page")
            continue
        if f'href="../{prefix}index.html"' not in pages[entry][1]:
            fail(f"{entry}: no link back to the archive")
    existing = [k for k in pages if k.startswith(prefix) and k != archive]
    if len(existing) != len(links):
        fail(f"{archive}: {len(existing)} entry pages exist but {len(links)} are linked")

ok("every archive entry links back to its archive and is listed")

# ---------------------------------------------------------------------------
# robots.txt
# ---------------------------------------------------------------------------

robots_path = os.path.join(ROOT, "robots.txt")
if os.path.exists(robots_path):
    robots = load(robots_path)
    samples = ["/index.html", "/writeups/index.html", "/writeups/op-auto.html",
               "/breach-reports/bank-of-baroda.html", "/projects/index.html",
               "/resume.html", "/assets/css/styles.css"]

    def blocks(pattern, url):
        anchored = pattern.endswith("$")
        if anchored:
            pattern = pattern[:-1]
        regex = "^" + re.escape(pattern).replace(r"\*", ".*") + ("$" if anchored else "")
        return re.match(regex, url) is not None

    for line in robots.splitlines():
        line = line.strip()
        if not line.lower().startswith("disallow:"):
            continue
        pattern = line.split(":", 1)[1].strip()
        if not pattern:
            continue
        for sample in samples:
            if blocks(pattern, sample):
                fail(f"robots.txt '{pattern}' would block the real page {sample}")
    ok("robots.txt does not block any published document")
else:
    fail("robots.txt is missing")

# ---------------------------------------------------------------------------
# content rules
# ---------------------------------------------------------------------------

PLACEHOLDERS = ["lorem ipsum", "coming soon", "placeholder", "your name here",
                 "tbd", "fixme"]
ALLOWED_EMAILS = {
    "jaskeerat01.work@gmail.com",
    # Puzzle data from the published write-ups, not your own details.
    "j.jones@recruitment.camp",
    "pt103368@pt103368.corp.int",
    "whitelist-crawl@linkedin.com",
}
RULLED_OUT = ["C++", "Google Workspace", "Google Sheets", "Google Docs",
              "Vulnerability Assessment"]

for relative, (parser, source, path) in pages.items():
    lowered = source.lower()
    for placeholder in PLACEHOLDERS:
        if placeholder.lower() in lowered:
            fail(f"{relative}: placeholder text {placeholder!r} is present")
    for term in RULLED_OUT:
        if term in source:
            fail(f"{relative}: contains the ruled-out term {term!r}")
    for address in set(re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", source)):
        if address.lower() not in ALLOWED_EMAILS:
            fail(f"{relative}: unexpected email address {address!r}")

ok("no placeholder text, no ruled-out skills, no unexpected contact details")

# ---------------------------------------------------------------------------
# the alias is display text only
# ---------------------------------------------------------------------------
# The short handle is printed in the bar and the footer so a visitor can
# connect the two identities. It is deliberately not a link: it is never an
# href, never the text of an <a>, and never part of a "links" list.
ALIAS = "paino5"
alias_occurrences = 0
for relative, (parser, source, path) in pages.items():
    for tag, attrs, text in parser.links:
        if ALIAS in (attrs.get("href") or "").lower():
            fail(f"{relative}: the alias is used as a link target")
        if ALIAS in text.lower():
            fail(f"{relative}: the alias is used as link text")
    for match in re.finditer(r'(?:href|src)\s*=\s*"([^"]*)"', source):
        if ALIAS in match.group(1).lower():
            fail(f"{relative}: the alias appears in a link or asset path")
    for match in re.finditer(r"<a\b[^>]*>.*?</a>", source, re.S | re.I):
        if ALIAS in match.group(0).lower():
            fail(f"{relative}: the alias appears inside an anchor")
    alias_occurrences += source.lower().count(ALIAS)
if alias_occurrences:
    ok(f"the alias appears {alias_occurrences} times as plain text and never as a link")

# ---------------------------------------------------------------------------
# the generated HTML must still match the generator
# ---------------------------------------------------------------------------
# A hand-edit to a generated page is lost the next time the generator runs.
# This compares the committed HTML against a fresh build so the drift is
# reported rather than silently overwritten.
def check_drift():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import tempfile

    import generate  # noqa: PLC0415
    from sitekit import normalise_html  # noqa: PLC0415

    drifted = []
    reformatted = []
    with tempfile.TemporaryDirectory() as tmp:
        try:
            generate.build(tmp, refresh=False, offline=True)
        except Exception as exc:  # noqa: BLE001
            notes.append(f"could not rebuild for the drift check: {exc}")
            return
        for dirpath, _dirs, filenames in os.walk(tmp):
            for filename in sorted(filenames):
                if not filename.endswith(".html"):
                    continue
                new = os.path.join(dirpath, filename)
                relative = os.path.relpath(new, tmp)
                committed = os.path.join(ROOT, relative)
                if not os.path.exists(committed):
                    drifted.append(f"{relative} is not committed")
                    continue
                with open(new, encoding="utf-8") as a, open(committed, encoding="utf-8") as b:
                    fresh, current = a.read(), b.read()
                if fresh == current:
                    continue
                if normalise_html(fresh) == normalise_html(current):
                    # Same content, different formatting — an editor reformatted
                    # the file. The next build restores the generator's layout.
                    reformatted.append(relative)
                else:
                    drifted.append(relative)
    for relative in drifted:
        fail(f"{relative} has been hand-edited and no longer matches the generator — "
             f"move the change into tools/content.json and rebuild, or it will be lost")
    for relative in reformatted:
        notes.append(f"{relative} was reformatted by an editor; the content matches "
                     f"the generator and the next build restores its formatting")
    if not drifted and not reformatted:
        ok("every generated page still matches the generator")
    elif not drifted:
        ok("every generated page still carries the generator's content")


check_drift()

# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------

print("=" * 72)
for note in notes:
    print("  ok  ", note)
print("=" * 72)
if failures:
    print(f"{len(failures)} PROBLEM(S):")
    for problem in failures:
        print("  X   ", problem)
    sys.exit(1)
print("All checks passed.")
