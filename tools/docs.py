"""docs.py — render a parsed research document as the site's HTML.

The source Markdown in the Writeups and Breach_Reports repositories uses a
handful of conventions that this module turns into the site's components:

  * ``<details>`` blocks hold a flag or a password. They become the site's
    ``.flag`` disclosure, with any surrounding prose kept as normal text.
  * A paragraph that is only a bold label (``**Exposure path:**``) becomes a
    sub-heading.
  * A paragraph that is only inline code becomes a code block.
  * Images are copied out of the source repository and referenced from
    ``assets/images`` with the alternative text supplied in ``content.json``.
  * Tables become the site's focusable, scrollable table region.

Standard library only.
"""

from __future__ import annotations

import re

from mdparse import normalise_html, render_inline, plain_text

_SUMMARY = re.compile(r"<summary>(.*?)</summary>", re.S | re.I)
_BOLD_ONLY = re.compile(r"^\*\*(.+?)\*\*$", re.S)
_CODE_ONLY = re.compile(r"^`([^`]+)`$", re.S)
_PASSWORD_LINE = re.compile(r"^(?:Password:\s*)?<b>(.*?)</b>\s*$", re.S | re.I)
_CODE_LINE = re.compile(r"^<code>(.*?)</code>\s*$", re.S | re.I)


def _strip_tags(html):
    return re.sub(r"<[^>]+>", "", html)


def _label_text(text):
    """A bold label used as a heading: drop the trailing colon."""
    return render_inline(text).rstrip(":")


def split_details(raw):
    """Split a raw ``<details>`` block into (summary, prose_lines, secret).

    The secret is the flag or password; the prose is everything else the
    author wrote inside the disclosure.
    """
    summary_match = _SUMMARY.search(raw)
    summary = summary_match.group(1).strip() if summary_match else None

    inner = raw
    if summary_match:
        inner = raw[: summary_match.start()] + raw[summary_match.end():]
    inner = re.sub(r"</?details[^>]*>", "", inner, flags=re.I)

    prose = []
    secret = None
    for raw_line in inner.split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        if summary and line == summary:
            continue
        match = _PASSWORD_LINE.match(line) or _CODE_LINE.match(line)
        if match:
            secret = match.group(1).strip()
            continue
        prose.append(line)

    if secret is None:
        # Some disclosures hold only prose; keep the last line as the secret.
        for index in range(len(prose) - 1, -1, -1):
            candidate = _strip_tags(prose[index]).strip()
            if candidate:
                secret = candidate
                prose.pop(index)
                break

    return summary, prose, secret


def _flag_label(summary, secret):
    if summary:
        return summary
    if secret and secret.lower().startswith("osintuk{"):
        return "Click to reveal flag"
    return "Reveal password"


class DocumentRenderer:
    """Render a parsed block list into the site's `.prose` HTML."""

    def __init__(self, *, image_base="", images=None, table_captions=None,
                 observations=None, figure_base=""):
        self.image_base = image_base
        self.images = images or {}
        self.table_captions = table_captions or {}
        self.observations = observations or []
        self.figure_base = figure_base
        self.warnings = []
        self._last_heading = 2

    # -- blocks ------------------------------------------------------------

    def render(self, blocks):
        out = []
        for block in blocks:
            out.append(self._render_block(block))
        return "\n".join(piece for piece in out if piece)

    def _render_block(self, block, top_level=True):
        kind = block["type"]
        if kind == "heading":
            return self._render_heading(block)
        if kind == "paragraph":
            return self._render_paragraph(block["text"], top_level)
        if kind == "list":
            return self._render_list(block)
        if kind == "quote":
            return f'<blockquote><p>{render_inline(block["text"])}</p></blockquote>'
        if kind == "rule":
            return '<hr>'
        if kind == "table":
            return self._render_table(block)
        if kind == "html":
            return self._render_html(block["text"])
        return ""

    def _render_heading(self, block):
        level = min(block["level"], 4)
        # The source's level-1 title is the page title, not part of the body.
        if level == 1:
            return ""
        self._last_heading = level
        return f"<h{level}>{render_inline(block['text'])}</h{level}>"

    def _render_paragraph(self, text, top_level=True):
        stripped = text.strip()
        lines = [line.strip() for line in re.split(r"\n|\x00", stripped) if line.strip()]

        # A bold label on its own line, followed by more content: the label
        # becomes a heading and the rest is rendered beneath it.
        if len(lines) > 1 and top_level:
            label = _BOLD_ONLY.match(lines[0])
            if label:
                rest = "\n".join(lines[1:])
                code = _CODE_ONLY.match(rest)
                if code:
                    return (f"<h3>{_label_text(label.group(1))}</h3>\n"
                            + self._code_block(code.group(1)))
                return (f"<h3>{_label_text(label.group(1))}</h3>\n"
                        + self._render_lines(lines[1:]))

        if len(lines) == 1:
            # A paragraph that is only a bold label becomes a heading. This
            # only applies at the top level: inside a list the same markup is
            # a label for the item, not a heading. A label that follows a
            # sub-heading is one level deeper, so it reads as a label rather
            # than a sibling.
            match = _BOLD_ONLY.match(stripped)
            if match and top_level:
                level = 4 if self._last_heading >= 3 else 3
                return f"<h{level}>{render_inline(match.group(1))}</h{level}>"

            # A paragraph that is only inline code becomes a code block.
            match = _CODE_ONLY.match(stripped)
            if match:
                return self._code_block(match.group(1))

        return self._render_lines(lines)

    def _render_lines(self, lines):
        """Render the lines of a paragraph, turning lone images into figures."""
        parts = []
        for line in lines:
            image = re.match(r"^!\[([^\]]*)\]\(([^)\s]+)\)$", line)
            if image:
                figure = self._render_figure(image.group(1), image.group(2))
                if figure:
                    parts.append(figure)
                continue
            parts.append(f"<p>{render_inline(line)}</p>")
        return "\n".join(parts)

    def _code_block(self, code):
        lead = ""
        note = ""
        for observation in self.observations:
            marker = observation.get("code_contains")
            if marker and marker in code:
                if observation.get("lead"):
                    lead = f"<p>{render_inline(observation['lead'])}</p>\n"
                if observation.get("note"):
                    note = f"\n<p>{render_inline(observation['note'])}</p>"
        escaped = (code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        return f'{lead}<pre><code>{escaped}</code></pre>{note}'

    def _render_list(self, block):
        tag = "ol" if block["ordered"] else "ul"
        items = []
        for item in block["items"]:
            items.append(self._render_item(item))
        return f"<{tag}>\n" + "\n".join(items) + f"\n</{tag}>"

    def _render_item(self, item):
        if item["blocks"]:
            inner = "\n".join(self._render_block(b, top_level=False) for b in item["blocks"])
            inner = "\n".join(line for line in inner.split("\n") if line.strip())
            inner = "\n".join("  " + line if line.strip() else line
                              for line in inner.split("\n"))
            return f"<li>\n{inner}\n</li>"
        rendered = self._render_paragraph(item["text"], top_level=False)
        # A single simple paragraph stays unwrapped inside the list item.
        if rendered.count("<p>") == 1 and rendered.startswith("<p>") and rendered.endswith("</p>"):
            rendered = rendered[3:-4]
        return f"<li>{rendered}</li>"

    def _render_table(self, block):
        caption = self.table_captions.get(
            " ".join(block["header"]), "Data from the source report"
        )
        caption_id = "table-caption"
        head = "".join(f"<th scope=\"col\">{render_inline(c)}</th>" for c in block["header"])
        rows = []
        for row in block["rows"]:
            cells = "".join(f"<td>{render_inline(c)}</td>" for c in row)
            rows.append(f"<tr>{cells}</tr>")
        return (
            f'<div class="table-wrap" tabindex="0" role="region" aria-labelledby="{caption_id}">\n'
            f'  <table class="rubric">\n'
            f'    <caption id="{caption_id}">{render_inline(caption)}</caption>\n'
            f"    <thead>\n      <tr>{head}</tr>\n    </thead>\n"
            f"    <tbody>\n" + "\n".join(rows) + "\n    </tbody>\n"
            f"  </table>\n</div>"
        )

    def _render_html(self, raw):
        if re.match(r"^\s*<details", raw, re.I):
            return self._render_details(raw)
        if re.match(r"^\s*<img", raw, re.I):
            match = re.search(r'src="([^"]+)"', raw)
            alt = re.search(r'alt="([^"]*)"', raw)
            if match:
                return self._render_figure(alt.group(1) if alt else "", match.group(1))
        return normalise_html(raw)

    def _render_details(self, raw):
        summary, prose, secret = split_details(raw)
        label = _flag_label(summary, secret)

        parts = []
        if prose:
            joined = "<br>\n".join(render_inline(line) for line in prose)
            parts.append(f"<p>{joined}</p>")
        if secret is not None:
            escaped = (secret.replace("&", "&amp;").replace("<", "&lt;")
                       .replace(">", "&gt;"))
            parts.append(
                '<details class="flag">\n'
                f"  <summary>{label}</summary>\n"
                f'  <div class="flag__body"><code>{escaped}</code></div>\n'
                "</details>"
            )
        if not parts:
            self.warnings.append("a <details> block held no password or flag")
        return "\n".join(parts)

    def _render_figure(self, alt, src):
        override = self.images.get(src)
        if override:
            local = f"{self.image_base}{override['local']}"
            caption = override.get("caption", "")
            alt_text = override.get("alt", alt)
        else:
            self.warnings.append(f"no image entry for {src!r}")
            return ""
        caption_html = f"\n  <figcaption>{caption}</figcaption>" if caption else ""
        return (
            "<figure>\n"
            f'  <img src="{local}" alt="{alt_text}" loading="lazy">'
            f"{caption_html}\n"
            "</figure>"
        )


def document_summary(blocks, max_length=220):
    """Derive a one-line summary from a document's own opening prose."""
    for block in blocks:
        if block["type"] == "heading" and block["level"] == 2:
            if plain_text(block["text"]).lower() in ("challenge summary", "summary"):
                continue
        if block["type"] == "paragraph":
            text = plain_text(block["text"])
            if text:
                if len(text) > max_length:
                    text = text[: max_length - 1].rsplit(" ", 1)[0] + "…"
                return text
    return ""
