# tools/ — the site generator

This folder is an **authoring tool**. It is not part of the published site and the
browser never runs any of it. The site is plain HTML and CSS, and the HTML files are
committed to the repository, so GitHub Pages serves them directly with no build step.

The generator exists so that the research content does not have to be copied by hand.
The write-ups and breach reports live as Markdown in your public repositories; this
tool reads them, parses them and writes the matching HTML pages.

```
tools/
├── generate.py     the command-line entry point
├── check.py        verifies the built site
├── mdparse.py      a small Markdown-subset parser
├── docs.py         renders a parsed document into the site's HTML
├── sitekit.py      the shared page shell: head, header, navigation, footer
├── sources.py      GitHub fetch with a local cache
├── content.json    everything you write by hand
└── cache/          downloaded source files (created on first run, safe to delete)
```

## Requirements

Python 3.8 or newer. **Nothing else** — no pip install, no virtual environment, no
Node.js, no third-party packages. The standard library is enough.

## Usage

```sh
cd tools
python3 generate.py              # build the site using the cached source files
python3 generate.py --refresh    # re-download the Markdown first
python3 generate.py --offline    # build using only the cache, no network
python3 generate.py --check      # build into a temporary folder and diff
python3 generate.py --out ../somewhere-else   # write the output elsewhere
python3 check.py                 # verify the built site
```

Run it from anywhere; the paths are resolved relative to the script.

`--check` is the useful one before a commit: it builds into a temporary folder and
tells you which committed files no longer match the source. If it says the output
matches exactly, the repository is in sync with the repositories.

`check.py` verifies the built site: that every document is well formed with a
single `<h1>` and a correct heading outline, that every link and asset resolves,
that no link points at a folder, that every off-site link is hardened, that
there is no scripting or tracking, that the images carry no metadata, that the
archives link back correctly, and that no placeholder text or unexpected contact
detail has crept in. It exits non-zero on failure.

## What it does

1. Reads `content.json` — your name, contact details, bio, skills, project and the
   one-line summaries for each archive entry.
2. Lists the folders of the `Writeups` and `Breach_Reports` repositories through the
   GitHub API, then downloads each Markdown file.
3. Parses each file with `mdparse.py` into a small document model.
4. Renders the model with `docs.py` into the site's `.prose` HTML, turning the source
   conventions into the site's components:

   | In the Markdown | On the page |
   | --- | --- |
   | `**Operation:** …` | the page title, read from the field name in `content.json` |
   | `## 1. Something` | a section heading with a rule under it |
   | `**Label:**` on its own | a sub-heading |
   | `` `some command` `` | a code block |
   | `<details>` with a flag or password | the "Click to reveal flag" disclosure |
   | `![alt](path.png)` | a figure, with the local image and its alternative text |
   | `\| a \| b \|` | the focusable, scrollable table region |
   | `> quote` | a block quote |
   | a bare `https://…` | a link |

5. Writes the 16 HTML files into the site root.

The tool prints a warning if the source changes shape in a way it does not recognise —
for example if a flag count in the source no longer matches the number of flags found.
Warnings go to stderr and never fail the build.

## Adding a writeup

1. Add the Markdown file to your `Writeups` repository.
2. Add an entry to `content.json` under `writeups.overrides`, keyed by its path in the
   repository:

   ```json
   "Sourcing Games/GAME8.md": {
     "slug": "sourcing-game-8",
     "summary": "One sentence describing what the write-up covers.",
     "standfirst": "A short line under the title."
   }
   ```

   The `summary` is the one-line description on the archive page and the `standfirst`
   is the line under the title on the write-up page. The slug is the file name of the
   generated page.
3. Run `python3 generate.py --refresh`.

The archive page, the numbering and the "back to archive" links are all rebuilt for
you. There is no other file to edit.

If the new file is in a brand-new collection, add that collection to
`writeups.collections` first, with a `name`, a `dir` and a `kind` of either `flags` or
`levels`.

## Adding a breach report

The same three steps, with the entry in `breach_reports.overrides` instead. A report
also accepts:

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
  "table_captions": { "Victim Date": "The caption for the table." },
  "observations": [
    {
      "code_contains": "a snippet of the code block",
      "lead": "A paragraph placed before that code block.",
      "note": "A paragraph placed after it."
    }
  ]
}
```

Keep the `preamble`. It is what separates the threat actor's own claims from what the
listing actually shows, and it is the reason the archive is worth reading.

## Editing the profile pages

`index.html`, `resume.html` and `projects/index.html` are built from `content.json`
too, so you never have to edit HTML by hand:

| Section of `content.json` | What it produces |
| --- | --- |
| `site` | name, email, links, repository names, the year in the header |
| `home` | the whole homepage, section by section |
| `resume` | the resume introduction and education |
| `project` | the featured project: overview, features, technologies, scope |
| `writeups` | the archive standfirst, the collections and the per-entry overrides |
| `breach_reports` | the archive standfirst, the method note and the per-report overrides |

Text in `content.json` may use a little Markdown: `**bold**`, `*italic*`, `` `code` ``
and `[link text](https://example.com)`. Everything is escaped, so an ampersand in your
text cannot break the markup.

## Adding an image

Put the file in `assets/images/`, then list it in the write-up's `images` block:

```json
"images": {
  "reference_img/op-cord-1.png": {
    "local": "op-cord-1.png",
    "alt": "What the image shows, for someone who cannot see it.",
    "caption": "The caption under the image."
  }
}
```

The key is the path the image has in the source repository; `local` is the file name
inside `assets/images/`.

Strip the metadata from any image you add before publishing it — a screenshot can
carry the capture time, your timezone and the name of the screenshot tool. The three
images already in the repository were cleaned this way.

## The cache

`cache/` holds the downloaded Markdown and the directory listings. It is created on
the first run and can be deleted at any time; the tool re-downloads what it needs.
It is not needed to serve the site and is safe to leave out of version control.
