# AGENTS.md — working on this portfolio

A guide for any AI agent (or person) picking up this repository. Read this
before changing anything.

---

## 1. What this project is

A personal cybersecurity portfolio for **Jaskeerat Singh**: cybersecurity
research, OSINT, threat intelligence and breach analysis.

The published site is **static HTML and one CSS file**. There is no JavaScript
on the site, no runtime Markdown parser, no bundler and no build step. The
HTML files are committed and GitHub Pages serves them exactly as they are on
disk.

The research content (write-ups and breach reports) lives as Markdown in two
public GitHub repositories. A small Python program in `tools/` converts that
Markdown into the HTML pages, so the content never has to be copied by hand.
That program is an **authoring tool**, not part of the deployed site.

---

## 2. The three commands

```sh
# Rebuild the HTML from the source repositories
python3 tools/generate.py --refresh

# Verify everything (structure, links, security, content rules)
python3 tools/check.py

# Serve it locally
python3 -m http.server 8000
```

`python3 tools/generate.py --check` rebuilds into a temporary folder and
diffs it against the committed HTML, so you can tell whether the repository is
in sync with the source repositories.

Python 3.8 or newer is all that is required. **No pip install, no virtual
environment, no Node.js, no third-party packages** — the standard library is
enough. Do not add a dependency to this repository.

---

## 3. Non-negotiable rules

These are the constraints the site is built on. Do not break them.

1. **The published site stays static.** No `<script>`, no inline event
   handlers, no `javascript:` URLs, no frameworks, no bundlers, no `package.json`,
   no `node_modules`.
2. **No build step at deploy time.** The HTML is committed. GitHub Pages must be
   able to serve the repository as-is. `tools/` is a local authoring tool and
   nothing more.
3. **No third-party resources.** No analytics, no trackers, no web fonts, no
   CDN, no embedded frames, no social widgets. A page load makes two requests:
   the HTML and the stylesheet.
4. **No directory URLs.** Every internal link names a document explicitly —
   `writeups/index.html`, never `writeups/`. A folder URL puts the site layout
   in the address bar and can expose a directory listing on some hosts.
5. **Every off-site link carries `rel="noopener noreferrer"`.** `noopener`
   stops the target reaching back through `window.opener`; `noreferrer` stops
   the referring page path from leaking to third parties.
6. **Never invent content.** No qualifications, employers, dates, skills,
   certifications, awards, metrics, findings or citations that the source does
   not support. See section 8.
7. **Every page must be usable with scripting disabled.** It already is, because
   there is no scripting.

---

## 4. Repository map

```
index.html                  Home            (generated)
resume.html                 Resume          (generated)
projects/index.html         Projects        (generated)
writeups/index.html         Archive         (generated)
writeups/<slug>.html        10 write-ups    (generated)
breach-reports/index.html   Archive         (generated)
breach-reports/<slug>.html  1 report        (generated)

assets/css/styles.css       The only stylesheet — hand-written, do not generate
assets/favicon.svg          Site icon
assets/images/*.png         Screenshots, metadata already stripped

tools/generate.py           The generator's entry point
tools/mdparse.py            Markdown-subset parser
tools/docs.py               Renders a parsed document into the site's HTML
tools/sitekit.py            The shared page shell (head, header, nav, footer)
tools/sources.py            GitHub fetch with a local cache
tools/content.json          Everything a human writes by hand
tools/check.py              The verification script
tools/cache/                Downloaded source files, recreated on demand

.htaccess  _headers  _redirects  robots.txt  .nojekyll   Server hardening
```

**`assets/css/styles.css` and `assets/favicon.svg` are hand-written.** The
generator does not touch them.

---

## 5. Adding a writeup or a breach report

There are two routes. **Use route A unless you have a reason not to.**

### Route A — through the generator (preferred)

1. Write the Markdown file in the source repository
   (`jaskeerat01/Writeups` or `jaskeerat01/Breach_Reports`).
2. Add an entry to `tools/content.json`.
3. Run `python3 tools/generate.py --refresh`.

For a writeup, under `writeups.overrides`, keyed by the file's path in the
repository:

```json
"Sourcing Games/GAME8.md": {
  "slug": "sourcing-game-8",
  "summary": "One sentence describing what the writeup covers.",
  "standfirst": "A short line under the title."
}
```

- `slug` becomes the file name of the generated page: `writeups/sourcing-game-8.html`.
- `summary` is the one-line description on the archive page.
- `standfirst` is the line under the title on the page itself.

For a breach report, under `breach_reports.overrides`:

```json
{
  "slug": "example-incident",
  "title": "Example Incident",
  "standfirst": "Breach analysis — threat actor profile and exposed material",
  "actor": "Some Group",
  "first_seen": "Month Year",
  "summary": "One sentence for the archive page.",
  "preamble": {
    "label": "How to read this report.",
    "text": "The note that appears at the top of the report."
  },
  "table_captions": { "Victim Date": "The caption for that table." },
  "observations": [
    {
      "code_contains": "a snippet of the code block",
      "lead": "A paragraph placed before that code block.",
      "note": "A paragraph placed after it."
    }
  ]
}
```

**Keep the `preamble`.** It is what separates the threat actor's own claims
from what the listing actually shows, and it is the reason the archive is worth
reading. Never state an unverified claim as a confirmed incident.

The generator rebuilds the archive page, the numbering, the page itself and
the "back to archive" link. There is no other file to edit.

If the new file is in a brand-new collection, add that collection to
`writeups.collections` first, with a `name`, a `dir` and a `kind` of either
`flags` or `levels`.

### Route B — writing the HTML by hand

Sometimes you need a page that does not come from a repository, or you need to
tweak a generated page. If you hand-write, follow **all** of this.

#### The page skeleton

Every page shares the same shell. Copy an existing page rather than starting
from scratch — `writeups/op-auto.html` for a document, `breach-reports/index.html`
for an archive.

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="text-scale" content="scale">
  <meta name="description" content="…">
  <meta name="author" content="Jaskeerat Singh">
  <meta name="robots" content="index, follow">
  <meta name="referrer" content="strict-origin-when-cross-origin">
  <meta name="theme-color" content="#000000">
  <title>…</title>
  <link rel="icon" href="../assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="../assets/css/styles.css">
</head>
<body id="top">
  <a class="skip" href="#content">Skip to main content</a>
  <!-- header and footer are in tools/sitekit.py -->
  <main id="content" tabindex="-1"> … </main>
</body>
</html>
```

The `<header class="bar">` and `<footer class="foot">` come from
`tools/sitekit.py`. If you hand-write a page, copy them from an existing one
and keep them identical. **Do not** add a `<script>` or any third-party
`<link>`.

#### The document page

```html
<main id="content" tabindex="-1">
  <article>
    <header class="page">
      <div class="wrap">
        <a class="crumb" href="../writeups/index.html">All writeups</a>
        <div class="page__meta">
          <span>Writeup 04 — OSINT UK</span>
          <span>Flags — 4 / 4 captured</span>
        </div>
        <h1 class="page__title">Operation Auto</h1>
        <p class="page__standfirst">Vehicle Intelligence &amp; Infrastructure Enumeration</p>
      </div>
    </header>

    <section class="band">
      <div class="wrap">
        <div class="prose">
          <!-- the document -->
        </div>

        <div class="provenance">
          <p><strong>Source:</strong>
          <a href="https://github.com/…/blob/master/…md" rel="noopener noreferrer">Writeups &rarr; OSINT UK/Op_Auto.md</a>
          on GitHub.</p>
          <p><a href="../writeups/index.html">&larr; Back to the writeups archive</a></p>
        </div>
      </div>
    </section>
  </article>
</main>
```

`aria-labelledby` is not needed here: the `<h1>` is the first thing in
`<main>`. Use `aria-labelledby` only when a `<section>` has a heading that is
not its first child.

#### The components

Everything in the body lives inside `<div class="prose">`. Use these and
nothing else:

| Purpose | Markup |
| --- | --- |
| Section heading | `<h2>1. Short title</h2>` |
| Sub-heading | `<h3>Short title</h3>` — and `<h4>` under an `<h3>` |
| Body paragraph | `<p>…</p>` |
| Bullet list | `<ul><li>…</li></ul>`, nested `<ul>` inside a `<li>` |
| Ordered list | `<ol><li>…</li></ol>` |
| Command or output | `<pre><code>…</code></pre>` |
| Inline code | `<code>…</code>` |
| Reference list | `<ul><li><a href="…">Source name</a></li></ul>` |
| Quote | `<blockquote><p>…</p></blockquote>` |
| Thin rule | `<hr>` |
| Screenshot | `<figure><img src="../assets/images/x.png" alt="…"><figcaption>…</figcaption></figure>` |
| Hidden flag or password | the `<details class="flag">` block below |

The flag disclosure:

```html
<details class="flag">
  <summary>Click to reveal flag</summary>
  <div class="flag__body"><code>osintuk{GERK436}</code></div>
</details>
```

Use `<summary>Click to reveal flag</summary>` for flags and
`<summary>Reveal password</summary>` for passwords. Native `<details>` needs no
JavaScript and is keyboard-operable. **Never put a heading inside a
`<summary>`** — it disappears from the screen-reader heading list.

#### A table

```html
<div class="table-wrap" tabindex="0" role="region" aria-labelledby="victims-caption">
  <table class="rubric">
    <caption id="victims-caption">Victims and dates, as published by the actor</caption>
    <thead>
      <tr><th scope="col">Victim</th><th scope="col">Date</th></tr>
    </thead>
    <tbody>
      <tr><th scope="row">Law Offices US</th><td>13 June 2026</td></tr>
    </tbody>
  </table>
</div>
```

The wrapper is what makes the table scrollable on a narrow screen and
keyboard-scrollable. `tabindex="0"` is required. The `aria-labelledby` must
point at the `<caption>`'s id.

#### The archive page

```html
<div class="rows">
  <article class="row">
    <p class="row__index">01</p>
    <div>
      <h3 class="row__title"><a href="op-auto.html">Operation Auto</a></h3>
      <p class="row__desc">One or two sentences describing the entry.</p>
    </div>
    <dl class="row__meta">
      <div><dt>Platform</dt><dd>OSINT UK</dd></div>
      <div><dt>Flags</dt><dd>4 / 4 captured</dd></div>
    </dl>
  </article>
</div>
```

`<dl>` children must be wrapped in a `<div>` so each `<dt>` pairs with its
`<dd>`.

#### Things to keep in mind while hand-writing

These are the mistakes that actually happen. Each one has been made and caught
in this repository.

- **Escape your text.** `&` becomes `&amp;`, `<` becomes `&lt;`. If you copy
  prose from the source Markdown, it is raw text and must be escaped. Inside
  an attribute, `"` must be escaped too.
- **One `<h1>` per page, and no heading level jumps.** `<h1>` → `<h2>` → `<h3>`
  → `<h4>`. Going `<h2>` straight to `<h4>` fails the check.
- **Every `<img>` needs `alt`.** Describe what the image shows for someone who
  cannot see it. Decorative images take `alt=""`.
- **Every link must resolve.** Relative to the page's own folder. From
  `writeups/`, the stylesheet is `../assets/css/styles.css`.
- **Never link to a folder.** `../writeups/index.html`, not `../writeups/`.
- **Every off-site link needs `rel="noopener noreferrer"`.**
- **Do not add a `style` attribute.** The stylesheet already covers
  everything; a hard-coded style is how the design drifts.
- **Do not invent a component.** If you need something new, add it to
  `assets/css/styles.css` in the right numbered section, using the existing
  custom properties. Do not introduce a new colour, font or spacing value.
- **Do not add a shadow, a radius or a gradient.** The design is flat with hard
  2px rules.
- **Do not add a new colour.** The palette is the warm near-black, the warm
  off-white, the warm grey, and one ember accent. If you need another tone,
  you need a different design, not another hex value.
- **Keep the `<details>` disclosure for flags and passwords.** Collapsing them
  into visible text changes the source's presentation.
- **Preserve the source's meaning.** Do not tidy up a write-up's wording, do not
  "fix" a command, and do not add a conclusion the author did not write.
- **Keep the `provenance` block** with a link to the original source and a link
  back to the archive. It is required by the check script.

---

## 6. The design system

`assets/css/styles.css` is organised into numbered sections and uses CSS custom
properties on `:root`. Read the file before changing anything.

**Tokens** (section 01): `--paper` (warm near-black), `--ink` (warm off-white),
`--dim` (warm grey), `--paper-light` and `--paper-warm` (the two light surfaces),
`--accent` and `--accent-ink` (the ember accent and its dark variant for light
surfaces), `--rule` (2px), `--rule-hair` (1px), `--pad`, `--maxw` (1160px), the
`--step-*` type scale, the `--track-*` letter-spacing scale, and the two font
stacks (`--font-mono` for the display voice, `--font-sans` for long-form
reading).

**The hero figure.** The list of practice areas in the right-hand column of the home page
is a ranked list, not a set of equal items. Three sizes carry the hierarchy: the lead
area is set largest, the two other primary domains sit a step below, and the three
supporting areas are set small, indented and grey. All three primaries are set in the
ink colour, each preceded by a small accent marker that echoes the mark in the
favicon. The block is deliberately unframed — no rule above it, and none below the
last line — so it reads as a list rather than a panel. If you add or reorder an area,
keep the tiers: the lead area first, primaries in the odd positions, supporting areas
in the even ones.

**The hero has no "Fig." label.** The hero opens straight into the name. The
numbered sections start at `01` with Profile, so every page's section badges count
from one. Do not reintroduce a figure number above the hero — there is no figure
there to number, and it left the first band looking like it was missing something.

**The alias.** `site.alias` in `tools/content.json` holds the short handle
(`paino5`). It is rendered in the bar next to the name and in the footer, and
it is the only place the old "Cybersecurity Research — Portfolio 2026" chrome
used to be. If the handle changes, change it in `content.json` and rebuild.

**The alias is display text only.** It is never a link: not an `href`, not the
text of an `<a>`, and never part of a "links" list, on any page. It appears
in exactly two places — the bar and the footer's own column — and both are
plain `<span>`s. `tools/check.py` fails the build if the alias ever turns up
inside an anchor, an `href`, or a `src`. Do not link it, even to a profile you
are sure of; if a link to it is ever wanted, it is a decision for the site
owner, not a default.

**The colour system.** Four values, not two: a warm near-black paper, a warm
off-white ink, a warm grey for secondary text, and a single ember accent. The
accent is used for the alias, the focus ring, the current page in the
navigation, the section-number badges, the row indices, the credential
metadata, the flag disclosure, and link underlines. It is a second channel of
hierarchy, never a replacement for the type scale.

When you need the accent on a light surface, do not pick a third colour: the
light bands already override `--accent` with `--accent-ink`, so anything that
uses `var(--accent)` is correct on both.

> **Trap:** a rule that reads `background: var(--ink)` inside `.band--invert`
> will resolve to the *overridden* `--ink` and the band will stay dark. That is
> why the light surfaces have their own tokens, `--paper-light` and
> `--paper-warm`. Do not reintroduce the trap.

**Bands.** `.band` is a full-width section with a 2px rule under it.
`.band--invert` turns it to the warm off-white; `.band--warm` turns it to the
deeper cream and is used to give the breach-report archive its own identity.
`.band--tight` reduces the vertical padding.

**Sections.** Every band opens with:

```html
<div class="band__head">
  <span class="sec">01</span>
  <h2 id="…-title">Profile</h2>
</div>
```

The `sec` badge is the section number. Each page counts its own sections from one,
so the home page runs 01 Profile through 07 Contact. Keep them in order and in step
with each other.

**Two-column data rows** use `.spec`: a `.spec__key` column of small uppercase
labels and a `.spec__val` column of content. Below 40rem it collapses to one
column, and a key plus its value then read as a single group: the key gives up
its hairline and the value's bottom border is the only divider between groups.
Keep it that way. If the key keeps its own rule in one-column mode, it sits
flush against the first bordered chip and the two 1px lines merge into a
heavier 2px line — the collision this rule exists to prevent.

**Chip lists** use `<ul class="chips" role="list">` with `<li>` items. The
`role="list"` restores the list semantics that Safari drops when a list is
unstyled or flexed.

**The header stays on the page column.** `.bar` is full-bleed by design — the
2px rule has to run edge to edge — but its *contents* must line up with `.wrap`,
which is centred once the viewport is wider than `--maxw`. That is why its
inline padding is

```css
padding-inline: calc(max(0px, (100% - var(--maxw)) / 2) + var(--pad));
```

Do not put `padding-inline: var(--pad)` back: on a 1440px screen that leaves the
wordmark 92px to the left of the first heading, and it is the only element on
the site that would not share the content column.

**The breakpoint ladder.** The stylesheet moves in steps, and each step has one
job. Add to the existing step rather than inventing a new one:

| Width | What changes |
| --- | --- |
| 64rem | `.cells` drops from three columns to two |
| 54rem | the alias byline leaves the bar; the nav keeps the wordmark's row |
| 52rem | the hero becomes one column and the practice-area list sits below |
| 43rem | the nav is set a step smaller (0.72rem) but keeps its row |
| 41rem | the nav drops beneath the wordmark, full width and left-aligned; bar padding tightens; `scroll-padding-top` grows to 7rem |
| 40rem | `.cells` and `.spec` become one column; the tagline tracking tightens |
| 26rem | the nav tightens again (0.68rem); the hero actions become one full-width column; `scroll-padding-top` grows to 8rem |

**The sticky bar has a height budget.** The bar is sticky, so every pixel it
takes is gone from every screen. On a phone it is two rows and ~88px — the
wordmark on one, the navigation on the next. Keep it there. Three rows of
navigation (~118px) at 320px is the floor, not the target. The
`scroll-padding-top` values in section 02 of the stylesheet track the bar
heights; if you make the bar taller, raise them too, or an anchor jump will
land the heading behind it.


**Do not add new colours.** The palette is a warm near-black, a warm
off-white, a warm grey and a single ember accent. There is no second accent,
and there should not be one. On the light bands the accent automatically
becomes its darker variant, so anything written as `var(--accent)` is correct
on both.

---

## 7. Security rules

`tools/check.py` enforces most of these, but know why they exist.

- **Directory URLs must never appear.** `.htaccess` sets `Options -Indexes` and
  301-redirects `/writeups/` to `/writeups/index.html`; `_redirects` does the
  same for Netlify and Cloudflare Pages; `robots.txt` asks crawlers to index
  the documents rather than the folders. On GitHub Pages, `.htaccess` and
  `_headers` are ignored, but GitHub never generates a directory listing and
  the site only ever links to explicit files.
- **The `Referrer-Policy` meta tag must stay.** It is what stops the page path
  reaching third parties even if a link is missing its `rel`.
- **`robots.txt` must use `Disallow: /*/$`.** The `$` anchors the pattern to
  the end of the URL. Without it, `Disallow: /*/` matches *every* URL on the
  site and blocks the whole thing from search engines. This mistake was made
  here and Lighthouse caught it.
- **Strip metadata from every image you add.** A screenshot can carry the
  capture time, your timezone and the name of the screenshot tool. The three
  images in `assets/images/` were cleaned this way; the check script fails if
  any EXIF or text chunk appears.
- **No absolute paths, no comments, no authoring notes** in the published
  output. A stray `<!-- TODO -->` or `/home/you/...` is a leak.
- **Only the intended contact details may appear.** Your email, GitHub and
  LinkedIn, plus the three puzzle email addresses that belong to the published
  write-ups themselves.
- **The alias is never a link.** It is printed, never linked. The check script
  fails the build if it appears in an anchor or in a URL.

---

## 8. Content rules

The profile is the source of truth, and it is short. Do not pad it.

- **Never invent** a qualification, employer, date, skill, certification,
  award, client, metric, statistic or finding. If it is not in `content.json`
  or in the source repository, it does not go on the site.
- **Never present an interest as expertise.** The areas-of-interest section is
  explicitly framed as "the subjects I am actively studying and practising",
  with a line saying it is not a claim of professional specialisation. Keep
  that framing.
- **Distinguish claims from facts.** In a breach report, say plainly that the
  actor profile and the techniques are the group's own characterisation, and
  that the exposed material is what they published. Never turn an unverified
  claim into a confirmed incident, and never invent incident dates, affected
  record counts, attack methods, financial impact or conclusions.
- **Do not add skills that were not supplied.** No C++, no Google Workspace,
  no Google Docs, no vulnerability assessment. The check script fails on the
  ruled-out list.
- **No proficiency bars or percentages.** Tools are listed; levels are not
  claimed.
- **No statistics that are not supported.** "More than 20 OSINT
  investigations" is supported; "threats detected" is not.

---

## 9. Accessibility

The site is checked with Lighthouse and currently scores 100 on accessibility,
best practices and SEO. Keep it there.

- Semantic landmarks: `header`, `nav`, `main`, `article`, `footer`. A skip
  link as the first element, pointing at `<main id="content" tabindex="-1">`.
- One `<h1>` per page, and a correct heading order.
- `:focus-visible` outlines are styled; do not remove them.
- Native `<details>` for disclosures, not ARIA-built ones.
- Tables use `<caption>`, `<th scope="col">` and `<th scope="row">`.
- All sizing is in `rem`; the root font size is never overridden.
- `<meta name="text-scale" content="scale">` opts into OS text scaling. Do not
  set a root font size to undo it.

---

## 10. How the generator reads the source

So you can extend it without guessing.

**OSINT UK files** look like this:

```markdown
# OSINT UK CTF Challenge Writeup
**Operation:** Operation Auto  
**Target Focus:** Vehicle Intelligence & Infrastructure Enumeration  
**Status:** Completed (4/4 Flags Captured)

---

## 1. Background Vehicle Ingress Identification
*   **Methodology:** Analyzed …
*   **Verification Sources:**
    *   [PlatesMania …](https://platesmania.com/de/foto31990210)
*   **Flag Data:** 
    <details>
    <summary>Click to reveal flag</summary>
    <code>osintuk{GERK436}</code>
    </details>
```

- `**Operation:**` becomes the page title; `**Target Focus:**` the standfirst.
  The field names are configurable per collection in `content.json`.
- `**Status:**` supplies the flag count, and the generator cross-checks it
  against the flags it actually found. A mismatch prints a warning.
- `## N. Title` becomes a section heading; `---` becomes a thin rule.
- A `<details>` holding a `<code>` becomes a flag disclosure.
- `*   ` bullets nest by indentation.

**Sourcing Games files** look like this:

```markdown
# GAME 1
## Level 1
Checked the source code of the web page **(Ctrl + U)**
<details>
Password: <b>games42</b>
</details>
```

- The title comes from the `#` heading, via the collection's `title_template`.
- `## Level N` headings are counted for the "Levels" metadata.
- A `<details>` with `Password: <b>…</b>` becomes a password disclosure, and
  any prose before the password is kept as normal text.

**Breach reports** use headings, bullets, `**Label:**` paragraphs, pipe tables
and a `---` rule.

**Conventions the renderer applies:**

| In the source | On the page |
| --- | --- |
| A paragraph that is only `**Label:**` | a heading — `<h3>`, or `<h4>` if it follows an `<h3>` |
| A paragraph that is only a bold label followed by more content | the label becomes a heading, the rest renders beneath it |
| A paragraph that is only `` `code` `` | a `<pre><code>` block |
| A paragraph that is only an image | a `<figure>` with the local image and its alternative text |
| A bare `https://…` in running text | a link |
| A link written without a scheme, e.g. `href=www.example.com` | given an explicit `https://` |
| An attribute written without quotes | quoted |

If the source changes shape in a way the parser does not recognise, the
generator prints a warning to stderr. Warnings never fail the build — read
them.

---

## 11. Common mistakes

Each of these happened in this repository and was caught by a check.

| Symptom | Cause | Fix |
| --- | --- | --- |
| An `&` breaks the layout or shows as `&` | text copied from Markdown was not escaped | escape it, or use `md()` in the generator |
| A link points at a file that does not exist | a relative path written from the wrong folder | paths are relative to the page's own folder |
| The page 404s on the server | a link to a folder instead of a document | use `index.html` explicitly |
| Lighthouse SEO drops to 63 | `robots.txt` disallows every URL | anchor the pattern: `Disallow: /*/$` |
| An icon renders as a solid black square | a CSS `fill` overriding the SVG's `fill="none"` | set fill on the path, not in CSS |
| Chrome logs an SVG path error | a malformed path in an inline SVG | render the SVG standalone and check it |
| The footer links lack `rel` | the hardening pass did not cover the footer | harden the whole document, not just the body |
| A source link 404s on your own site | a scheme-less `href` treated as a local path | add the scheme during parsing |
| The generator and the committed HTML differ | the HTML was edited by hand | run `python3 tools/generate.py --check` and reconcile |
| `generate.py --check` reports a difference that is only whitespace | an editor reformatted the file on save | regenerate the file, and turn off format-on-save for this folder |

---

## 12. Before you commit

```sh
python3 tools/generate.py --check     # is the repository in sync with the sources?
python3 tools/check.py                # structure, links, security, content, drift
```

`tools/check.py` also rebuilds the site in a temporary folder and compares it
with the committed HTML. The comparison is on content, not bytes: a page whose
content has been hand-edited fails and is named, while a page an editor has
merely reformatted is only noted. Put content changes in
`tools/content.json`.

If you changed the CSS, also load the site in a browser at four widths, because
each one catches a different failure: **1920px** (is the bar still on the page
column?), **1440px**, **768px** (the two-column hero and the three-column rows
are at their tightest here) and **390px** (the two-row bar, one-column grids and
stacked actions). Add **320px** if you touched the navigation. Check the page you
changed, and check that nothing scrolls sideways.

**Turn off format-on-save for this folder** if your editor has it. A formatter
will rewrite the generated HTML into its own style, and the next build will
overwrite it again, so the two will disagree in the diff. `generate.py --check`
will point at the file.

**Chrome DevTools MCP is available in this environment.** It is configured in
`~/.config/opencode/opencode.jsonc` with `--executablePath` pointing at a
Chromium build, `--headless` and `--isolated`. Use it to:

- confirm there are no console messages: `list_console_messages`
- confirm the page loads only local resources: `list_network_requests`
- run a Lighthouse audit: `lighthouse_audit`
- check the page at a phone width: `emulate` with
  `viewport: "390x844x3,mobile,touch"`
- check the navigation: click each item and read the resulting URL

If a page you edited is not in the list, open it with `navigate_page` first.

---

## 13. Style of work

- **Read before you write.** Open `assets/css/styles.css` and an existing page
  before inventing a new pattern.
- **Change one thing at a time** and re-run `tools/check.py` after each.
- **Prefer the generator** to hand-editing generated HTML. A hand-edit to a
  generated page is lost the next time the generator runs. `tools/check.py`
  compares every committed page against a fresh build and compares the
  *content*, not the bytes, so it separates the two cases:

  - the content differs → it **fails**, naming the file. Move the change into
    `tools/content.json` and rebuild, or it will be overwritten.
  - only the formatting differs (an editor reformatted the file) → it
    **notes** it and passes. Nothing is lost; the next build restores the
    generator's layout.
- **Say what you did not do.** If a check could not be run, say so rather than
  implying it passed.
- **Keep the tone.** The writing is plain, specific and free of marketing
  language. "I would rather publish a small finding I can defend than a large
  one I cannot" is the register to match.
