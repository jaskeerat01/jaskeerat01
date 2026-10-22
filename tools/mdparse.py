"""mdparse.py — a small, dependency-free Markdown parser.

The portfolio's research content lives as Markdown in public GitHub
repositories. This module turns that Markdown into a simple document model so
`generate.py` can render it as the same static HTML the site ships today.

It is deliberately a *subset* parser covering exactly the constructs the source
files use, rather than a general Markdown implementation:

  * ATX headings            # ## ### ...
  * paragraphs (with "  " hard line breaks)
  * bullet lists            -  *  +   (nested by indentation)
  * ordered lists           1. 2. 3.
  * block quotes            > text
  * horizontal rules        ---  ***  ___
  * pipe tables             | a | b |  with a |---|---| row
  * raw HTML blocks         <details>…</details>
  * inline formatting       **bold**, *italic*, `code`, [text](url), ![alt](src)
  * inline raw HTML         <br>, <b>…</b>

The site itself remains plain HTML and CSS: this is an authoring tool that runs
on your machine, not something the browser ever executes.

Standard library only.
"""

from __future__ import annotations

import re

__all__ = ["parse_markdown", "render_inline", "Block"]


# ---------------------------------------------------------------------------
# Block level
# ---------------------------------------------------------------------------

_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_RULE = re.compile(r"^\s*([-*_])(\s*\1){2,}\s*$")
_ITEM = re.compile(r"^(\s*)([*+-]|\d{1,9}[.)])\s+(.*)$")
_QUOTE = re.compile(r"^\s*>\s?(.*)$")
_TABLE_DELIM = re.compile(r"^\s*\|?[\s:|-]+\|[\s:|-]*$")
_HTML_OPEN = re.compile(r"^\s*</?([A-Za-z][\w-]*)")

#: HTML elements that are treated as opaque blocks rather than inline text.
_RAW_BLOCK_TAGS = {"details", "table", "div", "img", "p", "br", "figure"}


class Block(dict):
    """A parsed block. A dict subclass so blocks stay easy to serialise."""

    @property
    def type(self):
        return self["type"]


def _indent_of(line):
    return len(line) - len(line.lstrip())


def _strip_blank(lines):
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def _collect_raw_html(lines, start):
    """Collect a raw HTML block starting at `lines[start]`.

    Returns (html_text, next_index). For paired tags the block runs to the
    matching close tag; for a single tag it runs to the end of the paragraph.
    """
    first = lines[start]
    m = _HTML_OPEN.match(first)
    tag = m.group(1).lower() if m else None
    if tag in ("img", "br", "hr"):
        return first.strip(), start + 1

    out = [first]
    depth = 0
    if tag:
        # Count the tags on the opening line so the depth starts balanced.
        for tm in re.finditer(r"<(/?)([A-Za-z][\w-]*)", first):
            if tm.group(2).lower() == tag:
                depth += -1 if tm.group(1) else 1
    idx = start + 1
    if tag:
        while idx < len(lines):
            line = lines[idx]
            out.append(line)
            for tm in re.finditer(r"<(/?)([A-Za-z][\w-]*)", line):
                if tm.group(2).lower() != tag:
                    continue
                depth += -1 if tm.group(1) else 1
            idx += 1
            if depth <= 0:
                break
        return "\n".join(out), idx

    # Unknown tag: consume until a blank line.
    idx = start + 1
    while idx < len(lines) and lines[idx].strip():
        out.append(lines[idx])
        idx += 1
    return "\n".join(out), idx


def _parse_list(lines, start):
    """Parse a (possibly nested) list starting at `lines[start]`.

    Returns (list_block, next_index).
    """
    ordered = bool(re.match(r"^\s*\d{1,9}[.)]\s", lines[start]))
    items = []
    idx = start

    while idx < len(lines):
        line = lines[idx]
        if not line.strip():
            # A blank line ends the list unless the next line continues it.
            nxt = idx + 1
            while nxt < len(lines) and not lines[nxt].strip():
                nxt += 1
            if nxt >= len(lines):
                break
            cont = _ITEM.match(lines[nxt])
            if cont and len(cont.group(1)) >= 1:
                idx = nxt
                continue
            if _indent_of(lines[nxt]) > 0 and not _ITEM.match(lines[nxt]):
                idx = nxt
                continue
            break

        m = _ITEM.match(line)
        if not m:
            break

        indent = len(m.group(1))
        marker = m.group(2)
        marker_len = len(m.group(1)) + len(marker)
        rest = m.group(3)

        # Content starts after the marker plus the run of spaces after it.
        spaces = len(rest) - len(rest.lstrip())
        content_indent = marker_len + spaces
        first_text = rest.lstrip()

        # Gather the item's own lines (continuations and nested content).
        item_lines = [first_text]
        idx += 1
        while idx < len(lines):
            nxt = lines[idx]
            if not nxt.strip():
                break
            if _indent_of(nxt) < content_indent:
                break
            item_lines.append(nxt[content_indent:])
            idx += 1

        items.append(_parse_item(item_lines, ordered))

    return {"type": "list", "ordered": ordered, "items": items}, idx


def _parse_item(item_lines, ordered):
    """Turn the lines belonging to one list item into blocks."""
    blocks = []
    pending = []

    def flush():
        if pending:
            text = "\n".join(pending).strip()
            if text:
                blocks.append({"type": "paragraph", "text": text})
            pending.clear()

    i = 0
    while i < len(item_lines):
        line = item_lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        m = _HTML_OPEN.match(stripped)
        if m and m.group(1).lower() in _RAW_BLOCK_TAGS:
            flush()
            raw, i = _collect_raw_html(item_lines, i)
            blocks.append({"type": "html", "text": raw})
            continue

        if _ITEM.match(line):
            flush()
            sub, i = _parse_list(item_lines, i)
            blocks.append(sub)
            continue

        pending.append(line)
        i += 1

    flush()

    if len(blocks) == 1 and blocks[0]["type"] == "paragraph":
        return {"text": blocks[0]["text"], "blocks": []}
    return {"text": "", "blocks": blocks}


def _parse_table(lines, start):
    """Parse a pipe table starting at `lines[start]`.

    Returns (table_block, next_index) or (None, start) if it is not a table.
    """
    header = _split_row(lines[start])
    if header is None or start + 1 >= len(lines):
        return None, start
    if not _TABLE_DELIM.match(lines[start + 1]):
        return None, start

    align = []
    for cell in _split_row(lines[start + 1]):
        cell = cell.strip()
        if cell.startswith(":") and cell.endswith(":"):
            align.append("center")
        elif cell.endswith(":"):
            align.append("right")
        else:
            align.append("left")

    rows = []
    idx = start + 2
    while idx < len(lines) and lines[idx].strip() and "|" in lines[idx]:
        cells = _split_row(lines[idx])
        if cells is None:
            break
        cells = (cells + [""] * len(header))[: len(header)]
        rows.append(cells)
        idx += 1

    return {
        "type": "table",
        "header": header,
        "align": align,
        "rows": rows,
    }, idx


def _split_row(line):
    line = line.strip()
    if "|" not in line:
        return None
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def parse_markdown(text):
    """Parse Markdown text into a list of block dictionaries."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    blocks = []
    idx = 0

    while idx < len(lines):
        line = lines[idx]

        if not line.strip():
            idx += 1
            continue

        # Horizontal rule
        if _RULE.match(line):
            blocks.append({"type": "rule"})
            idx += 1
            continue

        # Heading
        m = _HEADING.match(line)
        if m:
            blocks.append({
                "type": "heading",
                "level": len(m.group(1)),
                "text": m.group(2).strip(),
            })
            idx += 1
            continue

        # Block quote
        m = _QUOTE.match(line)
        if m:
            quote_lines = []
            while idx < len(lines):
                qm = _QUOTE.match(lines[idx])
                if qm:
                    quote_lines.append(qm.group(1))
                    idx += 1
                elif (lines[idx].strip() and quote_lines
                      and not _HTML_OPEN.match(lines[idx].strip())):
                    quote_lines.append(lines[idx])
                    idx += 1
                else:
                    break
            blocks.append({"type": "quote", "text": "\n".join(quote_lines).strip()})
            continue

        # Table
        table, next_idx = _parse_table(lines, idx)
        if table is not None:
            blocks.append(table)
            idx = next_idx
            continue

        # Raw HTML block
        m = _HTML_OPEN.match(line)
        if m and m.group(1).lower() in _RAW_BLOCK_TAGS:
            raw, idx = _collect_raw_html(lines, idx)
            blocks.append({"type": "html", "text": raw})
            continue

        # List
        if _ITEM.match(line):
            lst, idx = _parse_list(lines, idx)
            blocks.append(lst)
            continue

        # Paragraph: run until a blank line or the start of another block.
        para = []
        hard = []
        while idx < len(lines):
            cur = lines[idx]
            if not cur.strip():
                break
            if para and (_HEADING.match(cur) or _RULE.match(cur)
                         or _QUOTE.match(cur) or _ITEM.match(cur)):
                break
            if para and _HTML_OPEN.match(cur.strip()):
                break
            # Two trailing spaces mean a hard line break in Markdown.
            hard.append(cur.endswith("  "))
            para.append(cur.strip())
            idx += 1
        if para:
            text_para = "".join(
                line + (HARD_BREAK if is_hard else "\n")
                for line, is_hard in zip(para, hard)
            ).strip()
            blocks.append({"type": "paragraph", "text": text_para})

    return blocks


# ---------------------------------------------------------------------------
# Inline level
# ---------------------------------------------------------------------------

_INLINE_CODE = re.compile(r"`([^`]+)`")
_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_BOLD = re.compile(r"\*\*(.+?)\*\*", re.S)
_ITALIC = re.compile(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?![*\w])", re.S)
_RAW_INLINE = re.compile(r"</?[A-Za-z][\w-]*[^>]*>")
#: A bare URL in running text, as GitHub-flavoured Markdown links automatically.
_BARE_URL = re.compile(r"(?<![\"'=(\w])(https?://[^\s<>\"')]+)")
_HREF = re.compile(r"href=(?:\"([^\"]*)\"|'([^']*)'|([^\s>]+))", re.I)
#: An attribute written without quotes, e.g. ``href=https://example.com``.
_UNQUOTED_ATTR = re.compile(r"\b(href|src)=([^\s\"'=<>]+)", re.I)

_ESCAPES = {
    "\\": "&#92;",
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
}

#: Sentinel used inside paragraph text to mark a Markdown hard line break.
HARD_BREAK = "\x00"


def escape(text):
    """Escape text for HTML output."""
    out = []
    for ch in text:
        out.append(_ESCAPES.get(ch, ch))
    return "".join(out)


def _tokenise_inline(text):
    """Split inline text into a list of (kind, value) tokens.

    Kinds: "text", "code", "link", "image", "html", "bold", "italic".
    """
    tokens = []
    pattern = re.compile(
        r"(?P<code>`[^`]+`)"
        r"|(?P<image>!\[[^\]]*\]\([^)\s]+(?:\s+\"[^\"]*\")?\))"
        r"|(?P<link>\[[^\]]*\]\([^)\s]+(?:\s+\"[^\"]*\")?\))"
        r"|(?P<bold>\*\*.+?\*\*)"
        r"|(?P<italic>(?<![*\w])\*(?!\s).+?(?<!\s)\*(?![*\w]))"
        r"|(?P<html></?[A-Za-z][\w-]*[^>]*>)",
        re.S,
    )
    pos = 0
    for m in pattern.finditer(text):
        if m.start() > pos:
            tokens.append(("text", text[pos:m.start()]))
        kind = m.lastgroup
        tokens.append((kind, m.group(kind)))
        pos = m.end()
    if pos < len(text):
        tokens.append(("text", text[pos:]))
    return tokens


def render_inline(text):
    """Render inline Markdown to HTML."""
    out = []
    for kind, value in _tokenise_inline(text):
        if kind == "text":
            out.append(_link_bare_urls(escape(value).replace(HARD_BREAK, "<br>\n")))
        elif kind == "code":
            out.append(f"<code>{escape(value[1:-1])}</code>")
        elif kind == "image":
            m = _IMAGE.match(value)
            alt = escape(m.group(1))
            src = m.group(2)
            out.append(f'<img src="{escape(src)}" alt="{alt}">')
        elif kind == "link":
            m = _LINK.match(value)
            label = render_inline(m.group(1))
            href = m.group(2)
            out.append(f'<a href="{escape(href)}">{label}</a>')
        elif kind == "bold":
            out.append(f"<strong>{render_inline(value[2:-2])}</strong>")
        elif kind == "italic":
            out.append(f"<em>{render_inline(value[1:-1])}</em>")
        elif kind == "html":
            out.append(normalise_html(value))
    return "".join(out)


def _link_bare_urls(escaped_text):
    """Turn bare URLs in running text into links."""
    return _BARE_URL.sub(
        lambda m: f'<a href="{m.group(1)}">{m.group(1)}</a>', escaped_text
    )


def normalise_html(raw):
    """Repair raw HTML that came from the source Markdown.

    The source writes a few links without a scheme, for example
    ``<a href=www.linkedin.com/robots.txt>``, and some without quotes, for
    example ``<a href=https://example.com>``. Left alone the browser would
    treat the first as a path on this site, so a host name is given an
    explicit ``https://`` scheme and every attribute is quoted.
    """
    raw = _UNQUOTED_ATTR.sub(lambda m: f'{m.group(1)}="{m.group(2)}"', raw)

    def fix(match):
        value = match.group(1) or match.group(2) or match.group(3) or ""
        if not value or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", value):
            return match.group(0)
        if value.startswith(("/", "#", ".")) or "." not in value.split("/")[0]:
            return match.group(0)
        return f'href="https://{value}"'

    return _HREF.sub(fix, raw)


def plain_text(text):
    """Strip inline markup down to plain text (used for summaries and titles)."""
    out = []
    for kind, value in _tokenise_inline(text):
        if kind == "text":
            out.append(value)
        elif kind == "code":
            out.append(value[1:-1])
        elif kind == "image":
            out.append(_IMAGE.match(value).group(1))
        elif kind == "link":
            out.append(_LINK.match(value).group(1))
        elif kind == "bold":
            out.append(value[2:-2])
        elif kind == "italic":
            out.append(value[1:-1])
        elif kind == "html":
            out.append(" ")
    return re.sub(r"\s+", " ", "".join(out).replace(HARD_BREAK, " ")).strip()
