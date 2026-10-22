# Jaskeerat Singh — Personal Cybersecurity Portfolio

A static, hand-built portfolio for cybersecurity research, OSINT, threat intelligence and
breach analysis. Every page is plain HTML5 with one shared stylesheet. There is **no build
step, no package manager, no bundler and no JavaScript framework** — open `index.html` and the
site works.

The visual language is editorial rather than dashboard-like: black paper, white ink, a
monospaced display voice, hard 2px rules, small uppercase labels, numbered sections and
inverted bands used for rhythm. Long documents switch to a sans-serif reading voice so they
stay comfortable to read.

---

## Contents

- [Folder structure](#folder-structure)
- [Opening the site locally](#opening-the-site-locally)
- [Publishing with GitHub Pages](#publishing-with-github-pages)
- [Regenerating the site](#regenerating-the-site)
- [Security and privacy](#security-and-privacy)
- [Editing your details](#editing-your-details)
- [Adding a new writeup](#adding-a-new-writeup)
- [Adding a new breach report](#adding-a-new-breach-report)
- [Updating the project](#updating-the-project)
- [Editing the stylesheet](#editing-the-stylesheet)
- [Deploying to a subdirectory](#deploying-to-a-subdirectory)
- [Browser support and accessibility](#browser-support-and-accessibility)

---

## Folder structure

```
.
├── index.html                  Home
├── resume.html                 Resume (print-friendly)
├── README.md                   This file
├── AGENTS.md                   Guide for AI agents working on this repository
│
├── .htaccess                   Hardening for Apache-style hosts
├── .nojekyll                   Publish as-is on GitHub Pages (no Jekyll)
├── _headers                    Security headers for Netlify / Cloudflare Pages
├── _redirects                  Directory → document redirects
├── robots.txt                  Crawl policy
│
├── tools/                      Optional authoring tool (see tools/README.md)
│   ├── generate.py             Builds the HTML from the source repositories
│   ├── check.py                Verifies structure, links, security and content
│   ├── mdparse.py              A small Markdown-subset parser
│   ├── docs.py                 Renders a document into the site's HTML
│   ├── sitekit.py              The shared page shell
│   ├── sources.py              GitHub fetch with a local cache
│   ├── content.json            Everything you write by hand
│   └── README.md               How to use the generator
│
├── projects/
│   └── index.html              Projects archive (one project)
│
├── writeups/
│   ├── index.html              Writeups archive
│   ├── op-auto.html            Individual writeup
│   ├── op-cord.html            Individual writeup
│   ├── op-kinetic.html         Individual writeup
│   ├── sourcing-game-1.html    Individual writeup
│   ├── sourcing-game-2.html    Individual writeup
│   ├── sourcing-game-3.html    Individual writeup
│   ├── sourcing-game-4.html    Individual writeup
│   ├── sourcing-game-5.html    Individual writeup
│   ├── sourcing-game-6.html    Individual writeup
│   └── sourcing-game-7.html    Individual writeup
│
├── breach-reports/
│   ├── index.html              Breach report archive
│   └── bank-of-baroda.html     Individual report
│
└── assets/
    ├── favicon.svg             Site icon
    ├── css/
    │   └── styles.css          The only stylesheet
    └── images/
        ├── op-cord-1.png       Reference screenshot used in one writeup
        ├── op-cord-2.png
        └── op-cord-3.png
```

`assets/images/` holds only images that are actually referenced. If you add an image, put it
there and reference it with a relative path.

> The three screenshots are stored with **all metadata removed** — no EXIF, no capture
> timestamp, no timezone, no screenshot-software name. Re-save any image you add the same way
> before publishing it.

> The `tools/` folder is an **optional authoring tool**, not a build step. The site you
> publish is the plain HTML committed here, and GitHub Pages serves it with no compilation
> at all. See [Regenerating the site](#regenerating-the-site) below.

---

## Opening the site locally

**Option A — just open the file.** Double-click `index.html`, or drag it into a browser. Every
link on the site is relative, so navigation, images and the stylesheet all work straight from
the file system.

**Option B — serve the folder locally.** Some browsers restrict a few features when a page is
opened from `file://`. If you want a clean local server, Python 3 is enough:

```sh
cd jaskeerat-portfolio
python3 -m http.server 8000
```

Then open <http://localhost:8000/>.

No installation, compilation or configuration is involved in either case.

---

## Publishing with GitHub Pages

1. Create a new GitHub repository (a public one is needed for the free Pages tier).
2. Push this folder to the repository:

   ```sh
   git init
   git add .
   git commit -m "Add portfolio site"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<repo-name>.git
   git push -u origin main
   ```

3. In the repository go to **Settings → Pages**.
4. Under **Build and deployment**, set **Source** to **Deploy from a branch**, then choose
   `main` and the `/ (root)` folder. Click **Save**.
5. The site is published at `https://<your-username>.github.io/<repo-name>/` within a minute or
   two. If it does not appear, wait for the **Pages** build to finish and check the
   **Actions** tab for a `deploy-pages` job.

There is nothing to compile. GitHub Pages serves the HTML and CSS exactly as they are on disk.

To use a custom domain, add a `CNAME` file to the root of the repository containing your
domain name, then point the domain at GitHub Pages in your DNS provider.

The `.nojekyll` file stops GitHub Pages from running Jekyll over the site, so every file is
published byte-for-byte as it is on disk. This matters because the site contains files that
start with an underscore (`_headers`, `_redirects`) and files that start with a dot
(`.htaccess`), which Jekyll would otherwise skip or process.

---

## Regenerating the site

The write-ups and breach reports live as Markdown in your public repositories, and
`tools/` contains a small Python program that turns them into the HTML pages here.
It exists so the research content never has to be copied by hand.

```sh
python3 tools/generate.py --refresh     # re-download the Markdown and rebuild
python3 tools/generate.py --check        # rebuild in a temp folder and diff
python3 tools/check.py                   # verify structure, links, security, content
```

`tools/check.py` also rebuilds the site in a temporary folder and compares it
with the committed HTML. The comparison is on content, not bytes: a page whose
content has been hand-edited fails and is named, while a page an editor has
merely reformatted is only noted. Put content changes in
`tools/content.json`.

Python 3.8 or newer is all that is needed — no pip install, no virtual environment, no
Node.js, no third-party packages.

**This is not a build step for the website.** The HTML files are committed to the
repository and GitHub Pages serves them exactly as they are on disk. You only need to
run the generator when the source material changes; the site is perfectly publishable
without it, and you can always hand-edit an HTML file if you would rather.

What lives where:

| File | What it holds |
| --- | --- |
| `tools/content.json` | Your name, contact details, bio, skills, project, and the one-line summary for each archive entry |
| `tools/mdparse.py` | A Markdown-subset parser for the source format |
| `tools/docs.py` | Turns a parsed document into the site's HTML components |
| `tools/sitekit.py` | The shared page shell: head, header, navigation, footer |
| `tools/generate.py` | The command-line entry point |

`tools/README.md` has the full instructions, including how to add a writeup, a breach
report and an image.

---

## Security and privacy

The site is deliberately built so that it cannot leak anything it should not.

### What the site does not do

- **No JavaScript at all.** Not a single `<script>` tag, no inline event handlers, no
  `javascript:` URLs. That removes the entire class of cross-site-scripting problems, and it
  means the Content-Security-Policy can refuse scripts outright.
- **No third-party resources.** No analytics, no trackers, no web fonts, no CDN, no embedded
  frames, no social widgets. A page load makes exactly two requests: the HTML and the
  stylesheet.
- **No forms, cookies, storage or fingerprinting.** There is nothing to submit, nothing
  stored, and no canvas, geolocation or device APIs touched.
- **No metadata in the images.** The screenshots carry no EXIF, no capture time, no timezone
  and no screenshot-software name.
- **No absolute paths or authoring notes** anywhere in the published output.

### Directory URLs are never exposed

Every internal link points at an explicit document — `writeups/index.html`, not
`writeups/` — so the folder layout never appears in the address bar and a visitor cannot
browse the directory. Three extra layers back this up:

| Host | File | What it does |
| --- | --- | --- |
| Apache, cPanel, most VPS | `.htaccess` | `Options -Indexes` turns off directory listings; a rewrite rule 301-redirects `/writeups/` to `/writeups/index.html` |
| Netlify, Cloudflare Pages | `_headers` | Security headers for every response |
| Netlify, Cloudflare Pages | `_redirects` | The same directory → document redirects |
| GitHub Pages | `.nojekyll` | Publishes the files as-is |

`robots.txt` additionally asks crawlers to index the documents rather than the folder URLs.

### Headers that are applied

Both `.htaccess` and `_headers` set the same set of headers:

| Header | Value | Why |
| --- | --- | --- |
| `Content-Security-Policy` | `default-src 'none'; script-src 'none'; …` | Refuses all scripts and connections; the site needs neither |
| `X-Content-Type-Options` | `nosniff` | Stops a browser guessing a file's type |
| `X-Frame-Options` | `DENY` | Blocks framing and clickjacking |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Third-party sites see only the origin, never the page path |
| `Permissions-Policy` | `geolocation=(), microphone=(), camera=(), …` | Switches off browser features the site never uses |
| `Cross-Origin-Opener-Policy` | `same-origin` | Isolates the window from other origins |
| `Cross-Origin-Resource-Policy` | `same-origin` | Stops the site's files being used by other sites |
| `Strict-Transport-Security` | `max-age=31536000` | Forces HTTPS for a year |

Every off-site link also carries `rel="noopener noreferrer"`, so a third-party page cannot
reach back through `window.opener` and never learns which page you came from.

> GitHub Pages ignores `.htaccess` and does not support custom response headers. If you want
> the full header set, publish to Netlify or Cloudflare Pages instead — both read `_headers`
> and `_redirects` with no configuration. GitHub Pages is still perfectly safe to use, because
> it never generates directory listings and the site links only to explicit files.

### Keeping it that way

If you edit the site, keep these rules:

- Link to `page/index.html`, never to `page/`.
- Do not add a `<script>` tag, a tracker, a web font or a third-party embed. If you need one
  of those, the strict Content-Security-Policy will block it until you relax the policy.
- Strip metadata from any new image before adding it.
- Keep `rel="noopener noreferrer"` on external links.

---

## Editing your details

Your name, contact details and links appear in more than one place. They are all plain text in
the HTML, so use find-and-replace in your editor.

| What | Where it appears |
| --- | --- |
| Name, tagline, introduction | `index.html` — the `<header class="hero">` block |
| Email, LinkedIn, GitHub | `index.html` (contact section + footer), `resume.html` (header + links section) |
| Education, experience, skills | `resume.html`, and the matching sections of `index.html` |
| Certifications, recognition, leadership | `resume.html`, and the credentials section of `index.html` |
| Footer links and icon buttons | the `<footer class="foot">` block on **every** page |
| Site navigation | the `<nav class="bar__nav">` block on **every** page |

The navigation block is repeated in each file so that the site stays a set of plain,
independent documents. If you add a page to the navigation, add the link to all of them.

The footer icon buttons use inline SVG. If you want to remove one, delete the whole
`<a class="icon-link">…</a>` element.

---

## Adding a new writeup

The quickest route is the generator, which reads the Markdown out of your
[`Writeups`](https://github.com/jaskeerat01/Writeups) repository:

1. **Write the writeup** as a Markdown file in that repository.
2. **Add an entry to `tools/content.json`** under `writeups.overrides`, keyed by the
   file's path in the repository:

   ```json
   "Sourcing Games/GAME8.md": {
     "slug": "sourcing-game-8",
     "summary": "One sentence describing what the writeup covers.",
     "standfirst": "A short line under the title."
   }
   ```

3. **Run `python3 tools/generate.py --refresh`.**

The archive page, the numbering, the page itself and the "back to archive" link are
all rebuilt for you. See [tools/README.md](tools/README.md) for the details.

If you would rather write the HTML yourself, the steps below do the same job by hand.

1. **Write the writeup** in your
   [`Writeups`](https://github.com/jaskeerat01/Writeups) repository as a Markdown file.
2. **Create the page.** Copy an existing page, for example
   `writeups/op-auto.html`, to a new file in `writeups/` with a descriptive slug:
   `writeups/my-new-writeup.html`.
3. **Edit the new page.** Update these pieces:
   - `<title>` — e.g. `My New Writeup — Writeups — Jaskeerat Singh`
   - `<meta name="description">` — one or two sentences for search results and link previews
   - the `.page__meta` line — collection name and any status such as the flag count
   - `<h1 class="page__title">` — the writeup title
   - `<p class="page__standfirst">` — a one-line description of the target or focus
   - the `.prose` block — the body of the writeup
   - the `.provenance` block — the `Source:` link pointing at the Markdown file on GitHub

   The body uses the same components as the existing pages:

   | Component | Markup |
   | --- | --- |
   | Section heading | `<h2>1. Short title</h2>` |
   | Subsection | `<h3>Short title</h3>` |
   | Body paragraph | `<p>…</p>` |
   | Bullet list | `<ul><li>…</li></ul>` |
   | Command or output | `<pre><code>…</code></pre>` |
   | Inline code | `<code>…</code>` |
   | Reference list | `<ul><li><a href="…">Source name</a></li></ul>` |
   | Hidden flag or password | the `<details class="flag">` block already in the pages |
   | Screenshot | `<figure><img …><figcaption>…</figcaption></figure>` |

4. **Add the entry to the archive.** Open `writeups/index.html` and add a row inside the
   `<div class="rows">` block for the right collection:

   ```html
   <article class="row">
     <p class="row__index">11</p>
     <div>
       <h3 class="row__title"><a href="my-new-writeup.html">My New Writeup</a></h3>
       <p class="row__desc">One or two sentences describing what the writeup covers.</p>
     </div>
     <dl class="row__meta">
       <div><dt>Platform</dt><dd>OSINT UK</dd></div>
       <div><dt>Flags</dt><dd>4 / 4 flags captured</dd></div>
     </dl>
   </article>
   ```

   The `row__index` is the position number shown on the left. If you add a new collection
   rather than an entry to an existing one, add a new `<h3 class="rows__label">Collection
   name</h3>` followed by its own `<div class="rows">` block.

5. **Check the links.** The archive uses links relative to the `writeups/` folder
   (`my-new-writeup.html`), and each writeup page links back with `../writeups/index.html`.
   Keep those two forms and everything stays correct in a repository subdirectory — and no
   folder URL is ever exposed.

---

## Adding a new breach report

The same three steps, with two differences.

1. **Create the page** in `breach-reports/`, copying `breach-reports/bank-of-baroda.html` as a
   template. Name it after the incident, for example `breach-reports/example-incident.html`.
2. **Keep claims and facts separate.** A breach report usually mixes three different things:
   what a threat actor claims, what they published, and what can actually be read from the
   exposed evidence. Label them. A short note at the top of the `.prose` block, like the one on
   the Bank of Baroda page, is usually enough:

   ```html
   <p class="note"><strong>How to read this report.</strong> …</p>
   ```

   Do not turn an unverified claim into a confirmed incident, and do not add incident dates,
   affected record counts, financial impact or conclusions that the source does not support.
3. **Add the entry to `breach-reports/index.html`** with the same `.row` markup as the
   writeups archive. The breach archive keeps its own distinct page header, so the two archives
   stay visually separate while sharing the same design system.
4. **Reference the source** in the `.provenance` block at the bottom of the page, linking to
   the Markdown file in the
   [`Breach_Reports`](https://github.com/jaskeerat01/Breach_Reports) repository.

---

## Updating the project

The projects page is `projects/index.html`. It currently contains exactly one project.

- **Title and summary** — the `.rows` entry at the top of section `01`.
- **Problem, overview, capabilities, technologies, what is not built yet, and scope** — the
  `.prose` block in section `01`.
- **GitHub link** — the `View on GitHub` button and the `page__meta` line.
- **Alert mock-up** — the `.telegram` block in section `02`. It is a static illustration and
  must stay labelled `Illustrative preview — not a live alert`. Do not point it at a real
  channel or present it as a real alert.
- **Feature list and technology table** — the `FEATURES` and `TECH` content lives directly in
  the HTML, as `<li>` elements and table rows. Edit them in place.

If you add a second project, add another `.row` to the `.rows` block and give each project its
own `<section class="band">` with the detail sections inside it.

---

## Editing the stylesheet

Everything visual lives in `assets/css/styles.css`, organised into numbered sections:

| Section | Contents |
| --- | --- |
| 01 | Design tokens — colours, rules, metrics, type scale |
| 02 | Reset and base elements |
| 03 | Typography |
| 04 | Layout primitives |
| 05 | Skip link, header and navigation |
| 06 | Hero and buttons |
| 07 | Bands (numbered sections) |
| 08 | Editorial rows and archive lists |
| 09 | Grids, tags, notes and tables |
| 10 | Document pages (writeups and reports) |
| 11 | Resume |
| 12 | Project page |
| 13 | Footer |
| 14 | Utilities |
| 15 | Print |

Reusable values are CSS custom properties on `:root`, so a global change is a one-line edit:

```css
:root {
  --paper:      #0c0b09;   /* warm near-black paper */
  --ink:        #f4f2ec;   /* warm off-white */
  --dim:        #8f897d;   /* secondary text */
  --paper-light: #f4f2ec;  /* the inverted band */
  --paper-warm:  #ece7dc;  /* the breach-report archive */
  --accent:     #e05a3c;   /* ember — used sparingly */
  --accent-ink: #9e3a20;   /* ember, for the light surfaces */
  --rule:       2px;
  --pad:        clamp(1.125rem, 4vw, 3rem);
  --maxw:       1160px;
}
```

The two inverted band styles are `.band--invert` (the warm off-white) and `.band--warm`
(the deeper cream, which gives the breach-report archive its own identity). The light bands
override `--accent` with `--accent-ink`, so anything written as `var(--accent)` is legible
on both the dark and the light surfaces. The print rules are in section 15 and are easy to
extend.

---

## Deploying to a subdirectory

The site works unchanged under `https://<user>.github.io/<repo>/` because every internal link
and asset path is relative. Two rules keep it that way:

- Links between top-level pages name the document explicitly: `writeups/index.html`,
  `breach-reports/index.html`, `projects/index.html` and `resume.html`.
- Pages inside a subfolder use `../` as their prefix, for example `../writeups/index.html`
  and `../assets/css/styles.css`.

Do not convert any of these to absolute paths beginning with `/`, do not link to a folder
(`writeups/`), and do not add a `<base>` tag.

---

## Browser support and accessibility

The site uses baseline, widely supported CSS: custom properties, `clamp()`, flexbox, grid,
container queries, `@layer`, `:focus-visible` and `text-wrap`. It is tested to work in current
Chrome, Edge, Firefox and Safari, and degrades gracefully where container queries are not
available.

Accessibility work already in place:

- Semantic landmarks (`header`, `nav`, `main`, `article`, `footer`) and a skip link to the
  main content.
- One `<h1>` per page and a correct heading order.
- A visible `:focus-visible` outline on every interactive element, plus a `:hover` state that
  inverts rather than relying on colour alone.
- `alt` text on every image, including the reference screenshots.
- Tables use `<caption>`, `<th scope="col">` and `<th scope="row">`, and are wrapped in a
  focusable scroll region so they can be read with a keyboard.
- Native `<details>` elements for flags and passwords — no JavaScript, fully keyboard
  operable.
- The site opts into operating-system text scaling with
  `<meta name="text-scale" content="scale">`, and all sizing is in `rem` so text can be
  resized to 200% without losing content.
- The resume has a dedicated print stylesheet. Use your browser's print function and choose
  *Save as PDF* to export it.

There is no JavaScript on the site at all, so every page and every piece of content is
available with scripting disabled.
