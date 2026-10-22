"""sitekit.py — the shared HTML shell for the portfolio.

Every page is the same document with a different body: the same <head>, the
same header and navigation, the same footer. Keeping that in one place means
adding a navigation entry or changing a link policy is a single edit.

Standard library only.
"""

from __future__ import annotations

import re

NAV = [
    ("HOME", "home"),
    ("WRITEUPS", "writeups"),
    ("BREACH REPORTS", "breach"),
    ("PROJECTS", "projects"),
    ("RESUME", "resume"),
]

ICON_GITHUB = (
    '<svg viewBox="0 0 16 16" aria-hidden="true" focusable="false">'
    '<path fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38'
    ' 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53'
    '.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95'
    ' 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.42 7.42 0 0 1 2-.27c.68 0 1.36.09 2 .27'
    ' 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95'
    '.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8z"/>'
    "</svg>"
)

ICON_LINKEDIN = (
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
    '<path fill="currentColor" d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037'
    '-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046'
    'c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286z'
    'M5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065z'
    'm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542'
    'C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729'
    'C24 .774 23.2 0 22.225 0z"/>'
    "</svg>"
)

ICON_MAIL = (
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none"'
    ' stroke="currentColor" stroke-width="2" stroke-linecap="square">'
    '<rect x="3" y="5" width="18" height="14"/><path d="M3.5 6l8.5 6.5L20.5 6"/></svg>'
)

ICON_TOP = (
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none"'
    ' stroke="currentColor" stroke-width="2" stroke-linecap="square">'
    '<path d="M12 20V5"/><path d="M5 12l7-7 7 7"/></svg>'
)


#: An href with no scheme that looks like a host name, e.g.
#: `href=www.linkedin.com/robots.txt`. The source Markdown writes a few of
#: these; without a scheme the browser would treat them as local paths.
#:
#: The pattern is deliberately narrow so that ordinary relative links such as
#: `op-auto.html` or `writeups/index.html` are never touched: a bare host must
#: either carry a path or have at least two dots in its name.
_BARE_DOMAIN_HREF = re.compile(
    r'href="((?![A-Za-z][A-Za-z0-9+.-]*:)(?![/.#])'
    r'(?:[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+/[^\s"]*'
    r'|[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+){2,}))"',
    re.I,
)


def _fix_bare_hrefs(text):
    """Give scheme-less host names an explicit https:// scheme."""
    return _BARE_DOMAIN_HREF.sub(r'href="https://\1"', text)


def _harden_external_links(text):
    """Force rel="noopener noreferrer" on every off-site link.

    noopener stops the target page reaching back through window.opener.
    noreferrer stops the full URL of this page — which reveals the folder
    layout — from being sent to any third-party site.

    The pattern allows any attribute order, so a link that starts with
    ``class=`` is hardened just as one that starts with ``href=``.
    """

    def fix(match):
        tag = match.group(0)
        if re.search(r'\brel="', tag):
            return re.sub(r'\brel="[^"]*"', 'rel="noopener noreferrer"', tag)
        return tag[:-1] + ' rel="noopener noreferrer">'

    return re.sub(r'<a\b[^>]*href="https?://[^"]+"[^>]*>', fix, text)


def normalise_html(text):
    """Return an HTML document in a form that ignores formatting.

    Whitespace between tags, indentation, attribute wrapping and the space a
    formatter leaves before a closing tag are all normalised away, but the
    words and their order are left alone — so a real content change still
    shows up as a difference.
    """
    text = re.sub(r">\s+<", "><", text)
    text = re.sub(r"\s+<", "<", text)
    text = re.sub(r">\s+", ">", text)
    text = re.sub(r"[ \t\r\n]+", " ", text)
    text = text.replace(" />", "/>")
    return text.strip()


def nav_links(up, active):
    """Build the navigation list.

    Links always point at an explicit document (`writeups/index.html`), never
    at a folder, so the directory layout is never shown in the address bar.
    """
    targets = {
        "home": up + "index.html",
        "writeups": up + "writeups/index.html",
        "breach": up + "breach-reports/index.html",
        "projects": up + "projects/index.html",
        "resume": up + "resume.html",
    }
    items = []
    for label, key in NAV:
        current = ' aria-current="page"' if key == active else ""
        items.append(f'<li><a href="{targets[key]}"{current}>{label}</a></li>')
    return "\n            ".join(items)


def header(up, active, site):
    return f"""<header class="bar">
      <a class="bar__mark" href="{up}index.html">
        <svg class="bar__glyph" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
          <rect x="2" y="2" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5"/>
          <rect x="8" y="8" width="8" height="8" fill="currentColor"/>
        </svg>
        {site['name'].upper()}
      </a>
      <span class="bar__by">{site['alias_label']} {site['alias']}</span>
      <nav class="bar__nav" aria-label="Primary">
        <ul role="list">
            {nav_links(up, active)}
        </ul>
      </nav>
    </header>"""


def footer(up, site):
    return f"""<footer class="foot">
      <div class="wrap">
        <div class="foot__col">
          <span class="foot__mark">{site['name'].upper()}</span>
          <p>Cybersecurity research, OSINT and threat intelligence.</p>
        </div>
        <div class="foot__col foot__col--alias">
          <span>{site['alias_label']}</span>
          <span>{site['alias']}</span>
        </div>
        <div class="foot__col foot__col--icons">
          <span>Elsewhere</span>
          <div class="foot__icons">
            <a class="icon-link" href="{site['github']}" title="GitHub — {site['github']}" aria-label="GitHub profile">{ICON_GITHUB}</a>
            <a class="icon-link" href="{site['linkedin']}" title="LinkedIn — {site['linkedin']}" aria-label="LinkedIn profile">{ICON_LINKEDIN}</a>
            <a class="icon-link" href="mailto:{site['email']}" title="Email — {site['email']}" aria-label="Email {site['name']}">{ICON_MAIL}</a>
            <a class="icon-link" href="#top" title="Back to top" aria-label="Back to top">{ICON_TOP}</a>
          </div>
        </div>
      </div>
    </footer>"""


def page(*, title, description, up="", active="", site, body, extra_head=""):
    """Return a complete HTML document.

    The whole document is passed through the link hardening, not just the
    body, so the header and footer are covered too.
    """
    document = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="text-scale" content="scale">
  <meta name="description" content="{description}">
  <meta name="author" content="{site['name']}">
  <meta name="robots" content="index, follow">
  <meta name="referrer" content="strict-origin-when-cross-origin">
  <meta name="theme-color" content="#000000">
  <title>{title}</title>
  <link rel="icon" href="{up}assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="{up}assets/css/styles.css">{extra_head}
</head>
<body id="top">
  <a class="skip" href="#content">Skip to main content</a>
{header(up, active, site)}

{body}

{footer(up, site)}
</body>
</html>
"""
    return _harden_external_links(_fix_bare_hrefs(document))
