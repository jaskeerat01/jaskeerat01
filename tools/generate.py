#!/usr/bin/env python3
"""generate.py — build the static portfolio from its sources.

This is an *authoring* tool, not a deploy step. It reads the research
Markdown from the public GitHub repositories plus the hand-written content in
``content.json`` and writes plain HTML files into the site root. The site that
gets published is still nothing but HTML and CSS: no JavaScript, no runtime
parser, no build step on the server.

    python3 tools/generate.py              # build using the cache, refreshing nothing
    python3 tools/generate.py --refresh    # re-download the Markdown first
    python3 tools/generate.py --offline    # build from the cache only
    python3 tools/generate.py --check      # build into a temp folder and diff

Standard library only. Python 3.8 or newer.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import docs  # noqa: E402
import sitekit  # noqa: E402
import sources  # noqa: E402
from mdparse import HARD_BREAK, parse_markdown, plain_text  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "content.json")

_warnings = []


def warn(message):
    _warnings.append(message)
    print(f"  warning: {message}", file=sys.stderr)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def load_content():
    with open(CONTENT_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def write_page(out_root, relative_path, html):
    full = os.path.join(out_root, relative_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"  wrote {relative_path}")


def field_line(line):
    """Match a `**Label:** value` metadata line."""
    match = re.match(r"^\*\*(.+?):\*\*\s*(.*)$", line)
    return (match.group(1).strip(), match.group(2).strip()) if match else None


def leading_fields(blocks):
    """Pull the `**Label:** value` fields out of a document's opening block."""
    fields = {}
    for block in blocks:
        if block["type"] == "heading" and block["level"] == 1:
            continue
        if block["type"] != "paragraph":
            break
        lines = [l for l in block["text"].split(HARD_BREAK) if l.strip()]
        parsed = [field_line(l) for l in lines]
        if not parsed or any(p is None for p in parsed):
            break
        for label, value in parsed:
            fields[label.lower()] = value
        break
    return fields


def strip_leading(blocks):
    """Drop the title, the metadata paragraph and the rule after it.

    They are shown in the page header instead of in the body.
    """
    out = []
    for index, block in enumerate(blocks):
        if index == 0 and block["type"] == "heading" and block["level"] == 1:
            continue
        if index <= 1 and block["type"] == "paragraph":
            lines = [l for l in block["text"].split(HARD_BREAK) if l.strip()]
            if lines and all(field_line(l) for l in lines):
                continue
        if not out and block["type"] == "rule":
            continue
        out.append(block)
    return out


def indent(text, spaces=8):
    """Indent a block of HTML so the generated source stays readable."""
    pad = " " * spaces
    return "\n".join(pad + line if line.strip() else line for line in text.split("\n"))


def esc(text):
    """Escape a plain-text value for use in an HTML attribute."""
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                .replace('"', "&quot;"))


def md(text):
    """Render content.json prose: escapes HTML and honours Markdown markup.

    Use this for anything that ends up as element content, so that a stray
    ampersand in the data can never break the markup. Use esc() for values
    that go into an attribute.
    """
    if text is None:
        return ""
    from mdparse import render_inline
    return render_inline(text)


def source_url(owner, repo, branch, path):
    quoted = path.replace(" ", "%20")
    return f"https://github.com/{owner}/{repo}/blob/{branch}/{quoted}"


# ---------------------------------------------------------------------------
# research archives
# ---------------------------------------------------------------------------

def collect_writeups(config, site, refresh, offline):
    """Fetch, parse and describe every writeup."""
    owner = site["owner"]
    repo = site["repos"]["writeups"]
    branch = site["branches"]["writeups"]
    writeup_config = config["writeups"]
    entries = []
    index = 0

    for collection in writeup_config["collections"]:
        names = sources.list_dir(owner, repo, branch, collection["dir"],
                                 refresh=refresh, offline=offline)
        for name in names:
            path = f"{collection['dir']}/{name}"
            raw = sources.fetch_text(owner, repo, branch, path,
                                     refresh=refresh, offline=offline)
            blocks = strip_leading(parse_markdown(raw))
            fields = leading_fields(parse_markdown(raw))

            override = writeup_config["overrides"].get(path, {})
            index += 1

            title = override.get("title")
            if not title and collection.get("title_field"):
                title = fields.get(collection["title_field"].lower())
            if not title:
                heading = next(
                    (b["text"] for b in parse_markdown(raw)
                     if b["type"] == "heading" and b["level"] == 1), "")
                title = heading.title()
                if collection.get("title_template"):
                    title = collection["title_template"].format(title=title)

            standfirst = override.get("standfirst")
            if not standfirst and collection.get("standfirst_field"):
                standfirst = fields.get(collection["standfirst_field"].lower(), "")

            if collection["kind"] == "flags":
                captured = len(re.findall(r"osintuk\{", raw))
                total = captured
                status = fields.get("status", "")
                match = re.search(r"\((\d+)\s*/\s*(\d+)\s*flags", status, re.I)
                if match:
                    captured, total = int(match.group(1)), int(match.group(2))
                    if total != captured:
                        warn(f"{path}: status says {total} flags but {captured} were found")
                elif captured:
                    total = captured
                meta_value = f"{captured} / {total} captured" if total else "0 captured"
            else:
                levels = sum(1 for b in blocks
                             if b["type"] == "heading"
                             and plain_text(b["text"]).lower().startswith("level"))
                meta_value = str(levels)

            summary = override.get("summary") or docs.document_summary(blocks)
            if not summary:
                warn(f"{path}: no summary available, add one to content.json")

            entries.append({
                "collection": collection,
                "path": path,
                "slug": override.get("slug") or _slugify(name),
                "index": f"{index:02d}",
                "title": title,
                "standfirst": standfirst,
                "meta_label": collection["meta_label"],
                "meta_value": meta_value,
                "summary": summary,
                "blocks": blocks,
                "raw": raw,
                "images": override.get("images", {}),
                "source": source_url(owner, repo, branch, path),
            })
    return entries


def collect_reports(config, site, refresh, offline):
    owner = site["owner"]
    repo = site["repos"]["breach_reports"]
    branch = site["branches"]["breach_reports"]
    report_config = config["breach_reports"]
    entries = []
    index = 0

    names = sources.list_dir(owner, repo, branch, "", refresh=refresh, offline=offline)
    for name in names:
        path = name
        raw = sources.fetch_text(owner, repo, branch, path, refresh=refresh, offline=offline)
        blocks = strip_leading(parse_markdown(raw))
        override = report_config["overrides"].get(path, {})
        index += 1

        heading = next((b["text"] for b in parse_markdown(raw)
                        if b["type"] == "heading" and b["level"] == 1), name)
        title = override.get("title") or heading.replace(" Breach Report", "")

        entries.append({
            "path": path,
            "slug": override.get("slug") or _slugify(name),
            "index": f"{index:02d}",
            "title": title,
            "standfirst": override.get("standfirst", ""),
            "actor": override.get("actor", ""),
            "first_seen": override.get("first_seen", ""),
            "summary": override.get("summary") or docs.document_summary(blocks),
            "blocks": blocks,
            "preamble": override.get("preamble"),
            "observations": override.get("observations", []),
            "table_captions": override.get("table_captions", {}),
            "provenance_extra": override.get("provenance_extra", ""),
            "source": source_url(owner, repo, branch, path),
        })
    return entries


def _slugify(name):
    slug = re.sub(r"\.md$", "", name, flags=re.I)
    slug = re.sub(r"[^a-z0-9]+", "-", slug.lower()).strip("-")
    return slug


# ---------------------------------------------------------------------------
# page bodies
# ---------------------------------------------------------------------------

def writeup_page(entry):
    renderer = docs.DocumentRenderer(
        image_base="../assets/images/",
        images=entry["images"],
    )
    body = renderer.render(entry["blocks"])
    for message in renderer.warnings:
        warn(f"{entry['path']}: {message}")

    return f"""<main id="content" tabindex="-1">
  <article>
    <header class="page">
      <div class="wrap">
        <a class="crumb" href="../writeups/index.html">All writeups</a>
        <div class="page__meta">
          <span>Writeup {entry['index']} &mdash; {md(entry['collection']['name'])}</span>
          <span>{md(entry['meta_label'])} &mdash; {md(entry['meta_value'])}</span>
        </div>
        <h1 class="page__title">{md(entry['title'])}</h1>
        <p class="page__standfirst">{md(entry['standfirst'])}</p>
      </div>
    </header>

    <section class="band">
      <div class="wrap">
        <div class="prose">
{indent(body)}
        </div>

        <div class="provenance">
          <p><strong>Source:</strong>
          <a href="{entry['source']}" rel="noopener noreferrer">Writeups &rarr; {entry['path']}</a>
          on GitHub.</p>
          <p><a href="../writeups/index.html">&larr; Back to the writeups archive</a></p>
        </div>
      </div>
    </section>
  </article>
</main>"""


def report_page(entry):
    renderer = docs.DocumentRenderer(
        image_base="../assets/images/",
        table_captions=entry["table_captions"],
        observations=entry["observations"],
    )
    body = renderer.render(entry["blocks"])
    for message in renderer.warnings:
        warn(f"{entry['path']}: {message}")

    preamble = ""
    if entry["preamble"]:
        label = entry["preamble"].get("label", "")
        text = entry["preamble"].get("text", "")
        preamble = (f'<p class="note"><strong>{label}</strong> '
                    f'{_mini_markdown(text)}</p>\n')

    meta_left = f"Report {entry['index']}"
    if entry["actor"]:
        meta_left += f" &mdash; Actor &mdash; {esc(entry['actor'])}"
    meta_right = ""
    if entry["first_seen"]:
        meta_right = f"Actor first seen &mdash; {esc(entry['first_seen'])}"

    extra = ""
    if entry["provenance_extra"]:
        extra = f"\n          <p>{entry['provenance_extra']}</p>"

    return f"""<main id="content" tabindex="-1">
  <article>
    <header class="page band--warm">
      <div class="wrap">
        <a class="crumb" href="../breach-reports/index.html">All breach reports</a>
        <div class="page__meta">
          <span>{meta_left}</span>
          <span>{meta_right}</span>
        </div>
        <h1 class="page__title">{md(entry['title'])}</h1>
        <p class="page__standfirst">{md(entry['standfirst'])}</p>
      </div>
    </header>

    <section class="band">
      <div class="wrap">
        <div class="prose">
{indent(preamble + body)}
        </div>

        <div class="provenance">
          <p><strong>Source:</strong>
          <a href="{entry['source']}" rel="noopener noreferrer">Breach_Reports &rarr; {entry['path']}</a>
          on GitHub.</p>{extra}
          <p><a href="../breach-reports/index.html">&larr; Back to the breach reports archive</a></p>
        </div>
      </div>
    </section>
  </article>
</main>"""


def _mini_markdown(text):
    """Render a short string of Markdown inline (bold and italics only)."""
    from mdparse import render_inline
    return render_inline(text)


def writeups_index_page(entries, config, site):
    groups = []
    for collection in config["writeups"]["collections"]:
        items = [e for e in entries if e["collection"]["name"] == collection["name"]]
        rows = "\n".join(_archive_row(e) for e in items)
        groups.append(
            f'      <h3 class="rows__label">{md(collection["name"])}</h3>\n'
            f"      <div class=\"rows\">\n{rows}\n      </div>"
        )

    repo = f'https://github.com/{site["owner"]}/{site["repos"]["writeups"]}'
    return f"""<main id="content" tabindex="-1">

  <header class="page">
    <div class="wrap">
      <div class="page__meta">
        <span>Archive &mdash; {len(entries)} documents</span>
        <span>Source &mdash; github.com/{site['owner']}/{site['repos']['writeups']}</span>
      </div>
      <h1 class="page__title">Writeups</h1>
      <p class="page__standfirst">{md(config['writeups']['standfirst'])}</p>
    </div>
  </header>

  <section class="band">
    <div class="wrap">
      <div class="band__head">
        <span class="sec">01</span>
        <h2>Collections</h2>
      </div>
{chr(10).join(groups)}
    </div>
  </section>

  <section class="band band--invert">
    <div class="wrap">
      <div class="band__head">
        <span class="sec">02</span>
        <h2>Repository</h2>
      </div>
      <p class="band__lede">Every writeup on this page is published in full in my public
      Writeups repository. Read the originals there if you want the raw source.</p>
      <p><a class="btn" href="{repo}" rel="noopener noreferrer">Open the repository</a></p>
    </div>
  </section>

</main>"""


def _archive_row(entry):
    return f"""        <article class="row">
          <p class="row__index">{entry['index']}</p>
          <div>
            <h3 class="row__title"><a href="{entry['slug']}.html">{md(entry['title'])}</a></h3>
            <p class="row__desc">{md(entry['summary'])}</p>
          </div>
          <dl class="row__meta">
            <div><dt>Platform</dt><dd>{md(entry['collection']['name'])}</dd></div>
            <div><dt>{entry['meta_label']}</dt><dd>{md(entry['meta_value'])}</dd></div>
          </dl>
        </article>"""


def breach_index_page(entries, config, site):
    rows = "\n".join(
        f"""        <article class="row">
          <p class="row__index">{entry['index']}</p>
          <div>
            <h3 class="row__title"><a href="{entry['slug']}.html">{md(entry['title'])}</a></h3>
            <p class="row__desc">{md(entry['summary'])}</p>
          </div>
          <dl class="row__meta">
            <div><dt>Actor</dt><dd>{md(entry['actor'])}</dd></div>
            <div><dt>First seen</dt><dd>{md(entry['first_seen'])}</dd></div>
          </dl>
        </article>"""
        for entry in entries
    )
    repo = f'https://github.com/{site["owner"]}/{site["repos"]["breach_reports"]}'
    return f"""<main id="content" tabindex="-1">

  <header class="page band--warm">
    <div class="wrap">
      <div class="page__meta">
        <span>Archive &mdash; {len(entries)} report{'s' if len(entries) != 1 else ''}</span>
        <span>Source &mdash; github.com/{site['owner']}/{site['repos']['breach_reports']}</span>
      </div>
      <h1 class="page__title">Breach reports</h1>
      <p class="page__standfirst">{md(config['breach_reports']['standfirst'])}</p>
    </div>
  </header>

  <section class="band">
    <div class="wrap">
      <div class="band__head">
        <span class="sec">01</span>
        <h2>Reports</h2>
      </div>
      <div class="rows">
{rows}
      </div>
    </div>
  </section>

  <section class="band band--warm">
    <div class="wrap">
      <div class="band__head">
        <span class="sec">02</span>
        <h2>Method</h2>
      </div>
      <p class="band__lede">{md(config['breach_reports']['method_lede'])}</p>
      <p><a class="btn" href="{repo}" rel="noopener noreferrer">Open the repository</a></p>
    </div>
  </section>

</main>"""


# ---------------------------------------------------------------------------
# profile pages
# ---------------------------------------------------------------------------

def _hero_figure(items):
    return "\n".join(
        f'            <span class="dim">{item["text"]}</span>' if item.get("dim")
        else f'            <span>{item["text"]}</span>'
        for item in items
    )


def _hero_buttons(items):
    out = []
    for item in items:
        classes = "btn btn--ghost" if item.get("ghost") else "btn"
        out.append(f'            <a class="{classes}" href="{item["href"]}">{item["label"]}</a>')
    return "\n".join(out)


def _role_line(entry, dates_on_new_line=False):
    """One line for a role: org, optional arrangement, then the dates."""
    parts = [f"<strong>{md(entry['org'])}</strong>"]
    if entry.get("arrangement"):
        parts.append(f"&mdash; {md(entry['arrangement'])}")
    parts.append(f"&mdash; {md(entry['dates'])}")
    if dates_on_new_line:
        return f'<p>{" ".join(parts)}</p>'
    return f'<p>{" ".join(parts)}</p>'


def _skill_groups(groups, indent=8):
    pad = " " * indent
    out = []
    for group in groups:
        out.append(f'{pad}<div class="spec__key">{group["label"]}</div>')
        out.append(f'{pad}<div class="spec__val">')
        out.append(f'{pad}  <ul class="chips" role="list">')
        for item in group["items"]:
            out.append(f"{pad}    <li>{item}</li>")
        out.append(f"{pad}  </ul>")
        out.append(f"{pad}</div>")
    return "\n".join(out)


def home_page(config, site):
    home = config["home"]
    hero = home["hero"]
    site_links = {
        "github": site["github"],
        "linkedin": site["linkedin"],
        "email": site["email"],
    }
    fine = hero["fine"].format(**site_links)

    interest_cells = "\n".join(
        f'        <article class="cell">\n'
        f'          <h3>{md(cell["title"])}</h3>\n'
        f'          <p>{md(cell["body"])}</p>\n'
        f"        </article>"
        for cell in home["interest"]["cells"]
    )

    experience = "\n".join(
        f'        <div class="spec__key">{md(entry["role"])}</div>\n'
        f'        <div class="spec__val">\n'
        f"          {_role_line(entry)}\n"
        f'          <ul class="bullets">\n'
        + "\n".join(f"            <li>{md(bullet)}</li>" for bullet in entry["bullets"])
        + "\n          </ul>\n        </div>"
        for entry in home["experience"]["entries"]
    )

    credential_cells = "\n".join(
        f'        <article class="cell">\n'
        f'          <span class="cell__meta">{md(cell["meta"])}</span>\n'
        f'          <h3>{md(cell["title"])}</h3>\n'
        f'          <p>{md(cell["body"])}</p>\n'
        f"        </article>"
        for cell in home["credentials"]["cells"]
    )

    leadership = home["credentials"]["leadership"]
    leadership_roles = "\n".join(
        f'          <p><strong>{md(role["title"])}</strong> &mdash; {md(role["org"])}</p>'
        for role in leadership["roles"]
    )

    work_rows = "\n".join(
        f"""        <article class="row">
          <p class="row__index">{row['index']}</p>
          <div>
            <h3 class="row__title"><a href="{row['href']}">{md(row['title'])}</a></h3>
            <p class="row__desc">{md(row['desc'])}</p>
          </div>
          <dl class="row__meta">
{chr(10).join(f'            <div><dt>{md(m["label"])}</dt><dd>{md(m["value"])}</dd></div>' for m in row['meta'])}
          </dl>
        </article>"""
        for row in home["work"]["rows"]
    )

    contact = "\n".join(
        f'        <div class="spec__key">{md(link["label"])}</div>\n'
        f'        <div class="spec__val"><a href="{link["href"]}">{md(link["value"])}</a></div>'
        for link in home["contact"]["links"]
    )

    return f"""<main id="content" tabindex="-1">

  <header class="hero">
    <div class="wrap">
      <h1 class="hero__title">{site['name']}</h1>
      <p class="hero__full">{hero['tagline']}</p>
      <div class="hero__grid">
        <div class="hero__main">
          <p class="hero__lede">{md(hero['lede'])}</p>
          <div class="hero__cta">
{_hero_buttons(hero['buttons'])}
          </div>
          <p class="hero__fine">{md(fine)}</p>
        </div>
        <div class="hero__fig">
          <p class="herotri">
{_hero_figure(hero['figure'])}
          </p>
        </div>
      </div>
    </div>
  </header>

  <section class="band" id="profile" aria-labelledby="profile-title">
    <div class="wrap">
      <div class="band__head">
        <span class="sec">01</span>
        <h2 id="profile-title">Profile</h2>
      </div>
      <p class="band__lede">{md(home['profile']['lede'])}</p>
      <div class="band__body">
        <div class="prose">
{chr(10).join(f"          <p>{md(p.replace('{grade}', config['resume']['education']['grade_number']))}</p>" for p in home['profile']['paragraphs'])}
        </div>
      </div>
    </div>
  </section>

  <section class="band band--invert" id="interest" aria-labelledby="interest-title">
    <div class="wrap">
      <div class="band__head">
        <span class="sec">02</span>
        <h2 id="interest-title">Areas of interest</h2>
      </div>
      <p class="band__lede">{md(home['interest']['lede'])}</p>
      <div class="cells">
{interest_cells}
      </div>
    </div>
  </section>

  <section class="band" id="experience" aria-labelledby="experience-title">
    <div class="wrap">
      <div class="band__head">
        <span class="sec">03</span>
        <h2 id="experience-title">Selected experience</h2>
      </div>
      <p class="band__lede">{md(home['experience']['lede'])}</p>
      <div class="spec">
{experience}
      </div>
    </div>
  </section>

  <section class="band band--invert" id="skills" aria-labelledby="skills-title">
    <div class="wrap">
      <div class="band__head">
        <span class="sec">04</span>
        <h2 id="skills-title">Technical skills</h2>
      </div>
      <p class="band__lede">{md(home['skills']['lede'])}</p>
      <div class="spec">
{_skill_groups(home['skills']['groups'])}
      </div>
    </div>
  </section>

  <section class="band" id="credentials" aria-labelledby="credentials-title">
    <div class="wrap">
      <div class="band__head">
        <span class="sec">05</span>
        <h2 id="credentials-title">Certifications &amp; recognition</h2>
      </div>
      <div class="cells cells--wide">
{credential_cells}
      </div>

      <div class="spec mt-lg">
        <div class="spec__key">{md(leadership['label'])}</div>
        <div class="spec__val">
{leadership_roles}
          <p class="muted">{md(leadership['note'])}</p>
        </div>
      </div>
    </div>
  </section>

  <section class="band" id="work" aria-labelledby="work-title">
    <div class="wrap">
      <div class="band__head">
        <span class="sec">06</span>
        <h2 id="work-title">{md(home['work'].get('title', 'Selected work'))}</h2>
      </div>
      <div class="rows">
{work_rows}
      </div>
    </div>
  </section>

  <section class="band band--invert" id="contact" aria-labelledby="contact-title">
    <div class="wrap">
      <div class="band__head">
        <span class="sec">07</span>
        <h2 id="contact-title">Contact</h2>
      </div>
      <p class="band__lede">{md(home['contact']['lede'])}</p>
      <div class="spec">
{contact}
      </div>
    </div>
  </section>

</main>"""


def resume_page(config, site):
    home = config["home"]
    resume = config["resume"]
    experience = "\n".join(
        f'        <div class="spec__key">{md(entry["role"])}</div>\n'
        f'        <div class="spec__val">\n'
        f"          {_role_line(entry, dates_on_new_line=True)}\n"
        f'          <ul class="bullets">\n'
        + "\n".join(f"            <li>{md(bullet)}</li>" for bullet in entry["bullets"])
        + "\n          </ul>\n        </div>"
        for entry in home["experience"]["entries"]
    )
    links = "\n".join(
        f'        <div class="spec__key">{md(link["label"])}</div>\n'
        f'        <div class="spec__val"><a href="{link["href"]}">{md(link["value"])}</a></div>'
        for link in home["contact"]["links"]
    )
    education = resume["education"]
    return f"""<main id="content" tabindex="-1">

  <header class="page">
    <div class="wrap">
      <div class="page__meta">
        <span>Resume &mdash; {site['name']}</span>
        <span>Updated &mdash; {site['year']}</span>
      </div>
      <h1 class="page__title">{site['name']}</h1>
      <p class="resume__intro">{md(resume['intro'])}</p>
      <div class="resume__contact">
        <a href="mailto:{site['email']}">{site['email']}</a>
        <a href="{site['linkedin']}" rel="noopener noreferrer">linkedin.com/in/jaskeerat01</a>
        <a href="{site['github']}" rel="noopener noreferrer">github.com/jaskeerat01</a>
      </div>
    </div>
  </header>

  <section class="band band--tight" id="education" aria-labelledby="education-title">
    <div class="wrap">
      <div class="band__head">
        <span class="sec">01</span>
        <h2 id="education-title">Education</h2>
      </div>
      <div class="spec">
        <div class="spec__key">{md(education['key'])}</div>
        <div class="spec__val">
          <p>{md(education['org'])}</p>
          <p>{md(education['grade'])}</p>
        </div>
      </div>
    </div>
  </section>

  <section class="band band--tight" id="experience" aria-labelledby="experience-title">
    <div class="wrap">
      <div class="band__head">
        <span class="sec">02</span>
        <h2 id="experience-title">Professional experience</h2>
      </div>
      <div class="spec">
{experience}
      </div>
    </div>
  </section>

  <section class="band band--tight" id="skills" aria-labelledby="skills-title">
    <div class="wrap">
      <div class="band__head">
        <span class="sec">03</span>
        <h2 id="skills-title">Technical skills</h2>
      </div>
      <div class="spec">
{_skill_groups(home['skills']['groups'])}
      </div>
    </div>
  </section>

  <section class="band band--tight" id="certifications" aria-labelledby="certifications-title">
    <div class="wrap">
      <div class="band__head">
        <span class="sec">04</span>
        <h2 id="certifications-title">Certifications</h2>
      </div>
      <div class="spec">
        <div class="spec__key">CSEDP</div>
        <div class="spec__val">
          <p>Certified Social Engineering Defense Practitioner with Merit &mdash; February 2026</p>
          <p>Phishing, vishing, impersonation defence and email security protocols.</p>
        </div>
        <div class="spec__key">Google Cybersecurity</div>
        <div class="spec__val">
          <p>Google Cybersecurity Professional Certificate &mdash; June 2025 to January 2026</p>
        </div>
      </div>
    </div>
  </section>

  <section class="band band--tight" id="recognition" aria-labelledby="recognition-title">
    <div class="wrap">
      <div class="band__head">
        <span class="sec">05</span>
        <h2 id="recognition-title">Recognition &amp; awards</h2>
      </div>
      <div class="spec">
        <div class="spec__key">CTRL-ALT-ACT</div>
        <div class="spec__val">
          <p>Award for Excellence in Cybersecurity Training &mdash; Cyber Secured India</p>
          <p>Recognition of OSINT performance.</p>
        </div>
        <div class="spec__key">Code With DCG</div>
        <div class="spec__val">
          <p>Award for Excellence in Hackathon &mdash; DTU Consulting Group and Geekroom GTBIT</p>
        </div>
      </div>
    </div>
  </section>

  <section class="band band--tight" id="leadership" aria-labelledby="leadership-title">
    <div class="wrap">
      <div class="band__head">
        <span class="sec">06</span>
        <h2 id="leadership-title">Leadership</h2>
      </div>
      <div class="spec">
        <div class="spec__key">CyberSec Lead</div>
        <div class="spec__val">
          <p>Geekroom GTBIT</p>
        </div>
        <div class="spec__key">Design Co-Lead</div>
        <div class="spec__val">
          <p>GDG GTBIT</p>
        </div>
      </div>
    </div>
  </section>

  <section class="band band--tight" id="links" aria-labelledby="links-title">
    <div class="wrap">
      <div class="band__head">
        <span class="sec">07</span>
        <h2 id="links-title">Links</h2>
      </div>
      <div class="spec">
{links}
      </div>
      <p class="print-hint no-print">Use your browser&rsquo;s print function to save this page
      as a PDF.</p>
    </div>
  </section>

</main>"""


def projects_page(config, site):
    project = config["project"]
    features = "\n".join(
        f"            <li><strong>{md(f['title'])}.</strong> {md(f['body'])}</li>"
        for f in project["features"]
    )
    tech_rows = "\n".join(
        f'                <tr><th scope="row">{md(t["category"])}</th>'
        f'<td>{md(t["technology"])}</td><td>{md(t["purpose"])}</td></tr>'
        for t in project["technologies"]
    )
    proposed = "\n".join(f"            <li>{md(item)}</li>" for item in project["not_built"]["items"])
    repo = f'https://github.com/{site["owner"]}/{site["repos"]["project"]}'
    alert_body = project["alert"]["body"].replace("&", "&amp;").replace("<", "&lt;")
    return f"""<main id="content" tabindex="-1">

  <header class="page">
    <div class="wrap">
      <div class="page__meta">
        <span>Projects &mdash; 1</span>
        <span>Source &mdash; github.com/{site['owner']}/{site['repos']['project']}</span>
      </div>
      <h1 class="page__title">Projects</h1>
      <p class="page__standfirst">One project, built because the research work kept needing the
      same thing: a way to watch the sources I care about without re-reading them by hand every
      time.</p>
    </div>
  </header>

  <section class="band" id="project" aria-labelledby="project-title">
    <div class="wrap">
      <div class="band__head">
        <span class="sec">01</span>
        <h2 id="project-title">Featured project</h2>
      </div>

      <div class="rows">
        <article class="row">
          <p class="row__index">01</p>
          <div>
            <h3 class="row__title">{md(project['title'])}</h3>
            <p class="row__desc">A background collector for Tor hidden services that filters
            posts for relevance, extracts indicators of compromise, summarises threats with a
            local model, stores the results and pushes the matches to a chat channel.</p>
          </div>
          <dl class="row__meta">
            <div><dt>Status</dt><dd>{project['status']}</dd></div>
            <div><dt>Stack</dt><dd>{project['stack']}</dd></div>
          </dl>
        </article>
      </div>

      <div class="band__body band__body--wide mt-lg">
        <div class="prose">
          <h3>The problem</h3>
          <p>{md(project['problem'])}</p>

          <h3>What it does</h3>
          <p>{md(project['overview'])}</p>

          <h3>Verified capabilities</h3>
          <ul>
{features}
          </ul>

          <h3>Technologies</h3>
          <div class="table-wrap" tabindex="0" role="region" aria-labelledby="tech-caption">
            <table class="rubric">
              <caption id="tech-caption">Components used by the engine</caption>
              <thead>
                <tr>
                  <th scope="col">Category</th>
                  <th scope="col">Technology</th>
                  <th scope="col">Purpose</th>
                </tr>
              </thead>
              <tbody>
{tech_rows}
              </tbody>
            </table>
          </div>

          <h3>Running it</h3>
          <p>{md(project['running'])}</p>

          <h3>Not built yet</h3>
          <p>{md(project['not_built']['lede'])}</p>
          <ul>
{proposed}
          </ul>

          <h3>Scope and intended use</h3>
          <p>{md(project['scope'])}</p>
        </div>
      </div>

      <div class="band__foot">
        <a class="btn" href="{repo}" rel="noopener noreferrer">View on GitHub</a>
      </div>
    </div>
  </section>

  <section class="band band--invert" id="alert" aria-labelledby="alert-title">
    <div class="wrap">
      <div class="band__head">
        <span class="sec">02</span>
        <h2 id="alert-title">Alert format</h2>
      </div>
      <p class="band__lede">{md(project['alert']['lede'])}</p>

      <p class="flagged">Illustrative preview &mdash; not a live alert</p>

      <div class="telegram">
        <div class="telegram__bar">
          <span>Telegram &mdash; example layout</span>
        </div>
        <div class="telegram__body">
          <p class="telegram__title">&#9888; Threat alert &mdash; example</p>
          <p class="telegram__msg">{alert_body}</p>
          <p class="telegram__stamp">Illustrative preview &mdash; not a live alert</p>
        </div>
      </div>
    </div>
  </section>

</main>"""


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def build(out_root, refresh=False, offline=False):
    config = load_content()
    site = config["site"]

    print("Fetching sources...")
    writeups = collect_writeups(config, site, refresh, offline)
    reports = collect_reports(config, site, refresh, offline)
    print(f"  {len(writeups)} writeups, {len(reports)} breach reports")

    print("Writing pages...")
    write_page(out_root, "index.html", sitekit.page(
        title=site.get("home_title") or f"{site['name']} — Cybersecurity Research, OSINT & Threat Intelligence",
        description=(
            f"Portfolio of {site['name']}, a computer science student working in cybersecurity "
            "research, open-source intelligence, threat intelligence and breach analysis. "
            "Writeups, breach analysis reports, a dark web threat intelligence tool and a "
            "printable resume."
        ),
        up="", active="home", site=site, body=home_page(config, site),
    ))

    write_page(out_root, "resume.html", sitekit.page(
        title=f"Resume — {site['name']} — Cybersecurity Research & OSINT",
        description=(
            f"Resume of {site['name']}: education, professional experience in OSINT and "
            "open-source mentorship, technical skills, certifications, recognition and leadership."
        ),
        up="", active="resume", site=site, body=resume_page(config, site),
    ))

    write_page(out_root, "projects/index.html", sitekit.page(
        title=f"Projects — {config['project']['title']} — {site['name']}",
        description=(
            f"The {config['project']['title']}: an automated collector for Tor hidden services "
            "that filters posts, extracts indicators of compromise, summarises threats with a "
            "local model and stores findings."
        ),
        up="../", active="projects", site=site, body=projects_page(config, site),
    ))

    write_page(out_root, "writeups/index.html", sitekit.page(
        title=f"Writeups — {site['name']}",
        description=(
            "OSINT challenge writeups and sourcing exercises by Jaskeerat Singh, with the "
            "method, sources and result behind every step."
        ),
        up="../", active="writeups", site=site,
        body=writeups_index_page(writeups, config, site),
    ))
    for entry in writeups:
        write_page(out_root, f"writeups/{entry['slug']}.html", sitekit.page(
            title=f"{entry['title']} — Writeups — {site['name']}",
            description=f"{entry['title']} — {entry['standfirst']}. Research writeup by {site['name']}.",
            up="../", active="writeups", site=site, body=writeup_page(entry),
        ))

    write_page(out_root, "breach-reports/index.html", sitekit.page(
        title=f"Breach Reports — {site['name']}",
        description=(
            "Publicly reported breach analyses by Jaskeerat Singh, separating threat actor "
            "claims from confirmed evidence."
        ),
        up="../", active="breach", site=site,
        body=breach_index_page(reports, config, site),
    ))
    for entry in reports:
        write_page(out_root, f"breach-reports/{entry['slug']}.html", sitekit.page(
            title=f"{entry['title']} — Breach Report — {site['name']}",
            description=(
                f"Breach analysis of published material attributed to the {entry['actor']} "
                "ransomware group: actor profile, ATT&CK techniques and the exposed document "
                "categories."
            ),
            up="../", active="breach", site=site, body=report_page(entry),
        ))

    if _warnings:
        print(f"\n{len(_warnings)} warning(s) during the build.", file=sys.stderr)


def check(out_root):
    """Build into a temporary folder and diff against the committed HTML."""
    from sitekit import normalise_html

    config = load_content()
    site = config["site"]
    with tempfile.TemporaryDirectory() as tmp:
        build(tmp, refresh=False, offline=False)
        differences = []
        reformatted = []
        for dirpath, _dirs, filenames in os.walk(tmp):
            for filename in filenames:
                if not filename.endswith(".html"):
                    continue
                new = os.path.join(dirpath, filename)
                relative = os.path.relpath(new, tmp)
                old = os.path.join(ROOT, relative)
                if not os.path.exists(old):
                    differences.append(f"new file: {relative}")
                    continue
                with open(new, encoding="utf-8") as a, open(old, encoding="utf-8") as b:
                    fresh, current = a.read(), b.read()
                if fresh == current:
                    continue
                if normalise_html(fresh) == normalise_html(current):
                    reformatted.append(relative)
                else:
                    differences.append(f"differs: {relative}")
        if not differences and not reformatted:
            print("The committed HTML matches the generator output exactly.")
            return 0
        if reformatted and not differences:
            print("The committed HTML carries the generator's content, but an editor "
                  "reformatted:")
            for line in reformatted:
                print(f"  - {line}")
            print("Run 'generate.py' to restore the generator's formatting.")
            return 0
        print("Differences between the committed HTML and the generator output:")
        for line in differences:
            print("  -", line)
        for line in reformatted:
            print(f"  - {line} (formatting only)")
        return 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true",
                        help="re-download the source Markdown before building")
    parser.add_argument("--offline", action="store_true",
                        help="build using only the cached Markdown")
    parser.add_argument("--check", action="store_true",
                        help="build into a temporary folder and diff against the site")
    parser.add_argument("--out", default=ROOT, help="output directory (default: the site root)")
    args = parser.parse_args()

    if args.check:
        return check(args.out)

    build(args.out, refresh=args.refresh, offline=args.offline)
    return 0


if __name__ == "__main__":
    sys.exit(main())
