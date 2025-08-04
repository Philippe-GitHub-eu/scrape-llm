from selectolax.parser import HTMLParser
import trafilatura

def readable_text(html: str) -> str:
    out = trafilatura.extract(html, include_comments=False, include_tables=False)
    return out or ""

def select_text(html: str, css: str) -> str:
    tree = HTMLParser(html)
    node = tree.css_first(css)
    return node.text(strip=True) if node else ""
