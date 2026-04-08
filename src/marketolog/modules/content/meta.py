"""Meta generation tool — produces a structured brief for title/description/H1 suggestions."""
from __future__ import annotations

_PREVIEW_LENGTH = 500


def run_generate_meta(text: str, keywords: list[str] | None = None) -> str:
    """Return a structured Markdown brief asking Claude to generate SEO meta tags.

    Args:
        text: Source content to base meta tags on.
        keywords: Optional list of target keywords to include in meta tags.

    Returns:
        A Markdown-formatted brief string with requirements for Title,
        Meta Description, and H1 — 3 variants each.
    """
    preview = text.strip()[:_PREVIEW_LENGTH]

    keywords_section = ""
    if keywords:
        kw_list = "\n".join(f"- {kw}" for kw in keywords)
        keywords_section = f"\n## Target Keywords\n\n{kw_list}\n"

    brief = f"""\
# Meta Generation Brief

## Source Content Preview

```
{preview}
```
{keywords_section}
## Requirements

### Title
- Length: 50–60 characters
- Place the primary keyword as close to the start as possible
- Provide **3 variants**

### Meta Description
- Length: 140–160 characters
- Must include the primary keyword and a clear call-to-action (CTA)
- Provide **3 variants**

### H1
- Must include the primary keyword
- Must differ from the Title (more informative / conversational)
- Provide **3 variants**

## Output Format

Return the variants in the following structure:

**Title**
1. ...
2. ...
3. ...

**Description**
1. ...
2. ...
3. ...

**H1**
1. ...
2. ...
3. ...
"""
    return brief
