"""MediaWiki API client for fetching and parsing Wikipedia talk pages.

Known limitations of talk page parsing:
- Unsigned comments (no ~~~~ signature) will be missed or attributed incorrectly
- Flow/StructuredDiscussions pages use a completely different format
- Deeply nested templates (e.g., {{ping}}, {{talkback}}) may confuse the parser
- Comments split across multiple lines with complex formatting may be merged/split
- Non-standard signature formats vary across wikis
"""

import re
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import unquote, urlparse

import httpx
import mwparserfromhell

from app.config import settings


@dataclass
class CommentData:
    """Parsed comment from a talk page."""

    author: Optional[str] = None
    text: str = ""
    timestamp: Optional[str] = None
    section_title: str = "General"
    indent_level: int = 0


@dataclass
class TalkPageData:
    """Result of fetching and parsing a talk page."""

    title: str = ""
    url: str = ""
    comments: list[CommentData] = field(default_factory=list)
    raw_wikitext: str = ""
    error: Optional[str] = None


def extract_title_from_url(url: str) -> str:
    """Extract the article title from a Wikipedia URL.

    Supports formats:
    - https://en.wikipedia.org/wiki/Article_Name
    - https://en.wikipedia.org/w/index.php?title=Article_Name
    - https://en.m.wikipedia.org/wiki/Article_Name
    """
    parsed = urlparse(url)
    path = parsed.path

    # Standard /wiki/ format
    if "/wiki/" in path:
        title = path.split("/wiki/", 1)[1]
        return unquote(title).replace("_", " ")

    # index.php format
    if "title=" in (parsed.query or ""):
        for param in parsed.query.split("&"):
            if param.startswith("title="):
                return unquote(param.split("=", 1)[1]).replace("_", " ")

    raise ValueError(f"Could not extract article title from URL: {url}")


def _get_talk_title(article_title: str) -> str:
    """Convert an article title to its talk page title."""
    if article_title.startswith("Talk:"):
        return article_title
    return f"Talk:{article_title}"


class WikipediaClient:
    """Client for fetching and parsing Wikipedia talk pages."""

    API_URL = "https://en.wikipedia.org/w/api.php"

    def __init__(self, http_client: Optional[httpx.AsyncClient] = None):
        self._client = http_client

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is not None:
            return self._client
        return httpx.AsyncClient(
            headers={"User-Agent": settings.wikipedia_api_user_agent},
            timeout=30.0,
        )

    async def fetch_talk_page(self, article_url: str) -> TalkPageData:
        """Fetch the talk page for a Wikipedia article URL."""
        try:
            title = extract_title_from_url(article_url)
        except ValueError as e:
            return TalkPageData(error=str(e))

        talk_title = _get_talk_title(title)
        client = await self._get_client()
        should_close = self._client is None

        try:
            # First try DiscussionTools API for structured data
            comments = await self._try_discussion_tools(client, talk_title)

            if comments is None:
                # Fall back to raw wikitext parsing
                wikitext = await self._fetch_wikitext(client, talk_title)
                if wikitext is None:
                    return TalkPageData(
                        title=talk_title,
                        url=article_url,
                        error="Talk page not found",
                    )
                comments = self.parse_comments(wikitext)
                return TalkPageData(
                    title=talk_title,
                    url=article_url,
                    comments=comments,
                    raw_wikitext=wikitext,
                )

            return TalkPageData(
                title=talk_title,
                url=article_url,
                comments=comments,
            )
        except httpx.HTTPStatusError as e:
            return TalkPageData(title=talk_title, url=article_url, error=f"HTTP error: {e.response.status_code}")
        except httpx.RequestError as e:
            return TalkPageData(title=talk_title, url=article_url, error=f"Request error: {str(e)}")
        finally:
            if should_close:
                await client.aclose()

    async def _try_discussion_tools(
        self, client: httpx.AsyncClient, talk_title: str
    ) -> Optional[list[CommentData]]:
        """Try to get structured comment data from the DiscussionTools API."""
        params = {
            "action": "discussiontoolspageinfo",
            "page": talk_title,
            "format": "json",
            "prop": "threaditemshtml",
        }
        try:
            resp = await client.get(self.API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

            if "error" in data or "discussiontoolspageinfo" not in data:
                return None

            page_info = data["discussiontoolspageinfo"]
            if "threaditemshtml" not in page_info:
                return None

            comments = []
            thread_items = page_info["threaditemshtml"]

            for item in thread_items:
                if item.get("type") != "comment":
                    continue
                comment = CommentData(
                    author=item.get("author", None),
                    text=self._strip_html(item.get("html", item.get("bodyhtml", ""))),
                    timestamp=item.get("timestamp", None),
                    section_title=item.get("heading", {}).get("plaintext", "General")
                    if isinstance(item.get("heading"), dict) else "General",
                    indent_level=item.get("level", 0),
                )
                if comment.text.strip():
                    comments.append(comment)

            return comments if comments else None
        except (httpx.HTTPError, KeyError):
            return None

    async def _fetch_wikitext(self, client: httpx.AsyncClient, talk_title: str) -> Optional[str]:
        """Fetch raw wikitext of a talk page."""
        params = {
            "action": "parse",
            "page": talk_title,
            "prop": "wikitext",
            "format": "json",
        }
        resp = await client.get(self.API_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

        if "error" in data:
            return None

        return data.get("parse", {}).get("wikitext", {}).get("*", None)

    def parse_comments(self, wikitext: str) -> list[CommentData]:
        """Parse comments from raw wikitext using mwparserfromhell.

        Uses indentation patterns (colons ':') and signature patterns (~~~~)
        to identify individual comments.
        """
        if not wikitext or not wikitext.strip():
            return []

        comments = []
        current_section = "General"

        # Split into lines for processing
        lines = wikitext.split("\n")
        current_comment_lines: list[str] = []
        current_indent = 0
        current_author: Optional[str] = None
        current_timestamp: Optional[str] = None

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Detect section headings
            heading_match = re.match(r"^(={2,})\s*(.+?)\s*\1\s*$", stripped)
            if heading_match:
                # Flush any pending comment
                if current_comment_lines:
                    text = self._clean_comment_text("\n".join(current_comment_lines))
                    if text.strip():
                        comments.append(CommentData(
                            author=current_author,
                            text=text,
                            timestamp=current_timestamp,
                            section_title=current_section,
                            indent_level=current_indent,
                        ))
                    current_comment_lines = []
                    current_author = None
                    current_timestamp = None

                current_section = heading_match.group(2).strip()
                continue

            # Count indentation level (colons at start)
            indent_match = re.match(r"^(:+)", stripped)
            indent_level = len(indent_match.group(1)) if indent_match else 0

            # Remove leading colons
            content = re.sub(r"^:+", "", stripped).strip()

            # Check for signature (indicates end of a comment)
            has_signature = bool(re.search(
                r"\[\[User[_ ]?(?:talk)?:([^\]|]+)(?:\|[^\]]+)?\]\].*?"
                r"(\d{1,2}:\d{2},\s+\d{1,2}\s+\w+\s+\d{4}\s+\(UTC\))",
                content,
                re.IGNORECASE,
            )) or "~~~~" in content

            if has_signature:
                # Extract author and timestamp from signature
                author, timestamp = self._extract_signature(content)
                # Remove signature from text
                clean_text = self._remove_signature(content)

                if current_comment_lines:
                    current_comment_lines.append(clean_text)
                    full_text = self._clean_comment_text("\n".join(current_comment_lines))
                else:
                    full_text = self._clean_comment_text(clean_text)

                if full_text.strip():
                    comments.append(CommentData(
                        author=author or current_author,
                        text=full_text,
                        timestamp=timestamp or current_timestamp,
                        section_title=current_section,
                        indent_level=indent_level,
                    ))

                current_comment_lines = []
                current_author = None
                current_timestamp = None
            else:
                # Continuation of a multi-line comment
                if indent_level != current_indent and current_comment_lines:
                    # Indentation changed, flush previous comment
                    text = self._clean_comment_text("\n".join(current_comment_lines))
                    if text.strip():
                        comments.append(CommentData(
                            author=current_author,
                            text=text,
                            timestamp=current_timestamp,
                            section_title=current_section,
                            indent_level=current_indent,
                        ))
                    current_comment_lines = []
                    current_author = None
                    current_timestamp = None

                current_comment_lines.append(content)
                current_indent = indent_level

        # Flush any remaining comment
        if current_comment_lines:
            text = self._clean_comment_text("\n".join(current_comment_lines))
            if text.strip():
                comments.append(CommentData(
                    author=current_author,
                    text=text,
                    timestamp=current_timestamp,
                    section_title=current_section,
                    indent_level=current_indent,
                ))

        return comments

    def _extract_signature(self, text: str) -> tuple[Optional[str], Optional[str]]:
        """Extract author and timestamp from a MediaWiki signature."""
        # Match [[User:Username|...]] ... timestamp (UTC)
        sig_match = re.search(
            r"\[\[User[_ ]?(?:talk)?:([^\]|]+)(?:\|[^\]]+)?\]\].*?"
            r"(\d{1,2}:\d{2},\s+\d{1,2}\s+\w+\s+\d{4}\s+\(UTC\))",
            text,
            re.IGNORECASE,
        )
        if sig_match:
            return sig_match.group(1).strip(), sig_match.group(2).strip()

        # Try simpler timestamp pattern
        ts_match = re.search(r"(\d{1,2}:\d{2},\s+\d{1,2}\s+\w+\s+\d{4}\s+\(UTC\))", text)
        if ts_match:
            return None, ts_match.group(1).strip()

        return None, None

    def _remove_signature(self, text: str) -> str:
        """Remove the signature portion from a comment line."""
        # Remove [[User:...]] links and timestamp
        text = re.sub(
            r"\[\[User[_ ]?(?:talk)?:[^\]]+\]\]\s*(?:\([^\)]*\)\s*)?",
            "",
            text,
            flags=re.IGNORECASE,
        )
        # Remove timestamps
        text = re.sub(r"\d{1,2}:\d{2},\s+\d{1,2}\s+\w+\s+\d{4}\s+\(UTC\)", "", text)
        # Remove ~~~~
        text = re.sub(r"~{3,5}", "", text)
        return text.strip()

    def _clean_comment_text(self, text: str) -> str:
        """Clean wikitext markup from comment text."""
        try:
            parsed = mwparserfromhell.parse(text)
            # Strip wikitext markup but keep the text
            clean = parsed.strip_code()
        except Exception:
            clean = text

        # Additional cleanup
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean

    @staticmethod
    def _strip_html(html: str) -> str:
        """Strip HTML tags from text."""
        return re.sub(r"<[^>]+>", "", html).strip()
