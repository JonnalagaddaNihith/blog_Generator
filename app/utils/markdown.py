import re
import markdown
from bs4 import BeautifulSoup

_BLOCK_TAGS = {
    "address", "article", "aside", "blockquote", "br", "dd", "div", "dl",
    "dt", "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2",
    "h3", "h4", "h5", "h6", "header", "hr", "li", "main", "nav", "ol",
    "p", "pre", "section", "table", "td", "th", "tr", "ul",
}


def markdown_to_plain_text(text: str) -> str:
    """
    Convert Markdown to plain text for grammar/readability checks.

    Fenced code blocks are dropped (code is not prose); inline code keeps
    its text. Falls back to the raw input if conversion fails.
    """
    if not text:
        return ""
    try:
        html = markdown.markdown(text, extensions=["fenced_code", "tables"])
        soup = BeautifulSoup(html, "html.parser")
        for pre in soup.find_all("pre"):
            pre.decompose()
        for el in soup.find_all(_BLOCK_TAGS):
            el.append("\n")
        plain = soup.get_text("")
    except Exception:
        plain = text
    plain = re.sub(r"~~(.*?)~~", r"\1", plain)
    return re.sub(r"\n{3,}", "\n\n", plain).strip()
