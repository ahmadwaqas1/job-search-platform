"""Strip HTML markup from job descriptions returned by several source APIs
(Remotive, Greenhouse, Lever, The Muse all return HTML content blobs).
Deliberately minimal - a dependency-free regex strip is plenty for turning
"description HTML" into "readable plain text for embeddings/LLM prompts",
which is all this is used for.
"""
import html
import re

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t]+")
_BLANK_LINES_RE = re.compile(r"\n{3,}")


def strip_html(raw: str) -> str:
    if not raw:
        return ""
    text = re.sub(r"(?i)</p>|<br\s*/?>", "\n", raw)
    text = _TAG_RE.sub("", text)
    text = html.unescape(text)
    text = _WS_RE.sub(" ", text)
    text = _BLANK_LINES_RE.sub("\n\n", text)
    return text.strip()
