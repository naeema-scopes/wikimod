"""Tests for the Wikipedia client using mocked HTTP responses."""

import json

import httpx
import pytest
import pytest_asyncio

from app.services.wikipedia import WikipediaClient, extract_title_from_url, CommentData


# --- URL parsing tests ---

def test_extract_title_standard_url():
    url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
    assert extract_title_from_url(url) == "Python (programming language)"


def test_extract_title_index_php_url():
    url = "https://en.wikipedia.org/w/index.php?title=Python_(programming_language)"
    assert extract_title_from_url(url) == "Python (programming language)"


def test_extract_title_mobile_url():
    url = "https://en.m.wikipedia.org/wiki/Climate_change"
    assert extract_title_from_url(url) == "Climate change"


def test_extract_title_invalid_url():
    with pytest.raises(ValueError):
        extract_title_from_url("https://example.com/page")


# --- Talk page fetching tests ---

MOCK_WIKITEXT = """
== Article quality ==
I think the article needs more references. [[User:Alice|Alice]] ([[User talk:Alice|talk]]) 14:30, 15 January 2024 (UTC)
:I agree, especially the introduction. [[User:Bob|Bob]] ([[User talk:Bob|talk]]) 15:00, 15 January 2024 (UTC)

== Neutrality concerns ==
This article has a clear bias. [[User:Charlie|Charlie]] ([[User talk:Charlie|talk]]) 10:00, 16 January 2024 (UTC)
:You are completely wrong about that, stop being an idiot. [[User:Dave|Dave]] ([[User talk:Dave|talk]]) 11:00, 16 January 2024 (UTC)
::Please keep the discussion civil. [[User:Eve|Eve]] ([[User talk:Eve|talk]]) 12:00, 16 January 2024 (UTC)
"""


@pytest.mark.asyncio
async def test_fetch_talk_page(httpx_mock):
    """Test fetching a talk page returns parsed data."""
    # Mock DiscussionTools API returning an error (fallback to wikitext)
    httpx_mock.add_response(
        url=httpx.URL(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "discussiontoolspageinfo",
                "page": "Talk:Python (programming language)",
                "format": "json",
                "prop": "threaditemshtml",
            },
        ),
        json={"error": {"code": "missingtitle"}},
    )

    # Mock wikitext parse API
    httpx_mock.add_response(
        url=httpx.URL(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "parse",
                "page": "Talk:Python (programming language)",
                "prop": "wikitext",
                "format": "json",
            },
        ),
        json={
            "parse": {
                "title": "Talk:Python (programming language)",
                "wikitext": {"*": MOCK_WIKITEXT},
            }
        },
    )

    client = WikipediaClient(http_client=httpx.AsyncClient())
    result = await client.fetch_talk_page("https://en.wikipedia.org/wiki/Python_(programming_language)")

    assert result.error is None
    assert result.title == "Talk:Python (programming language)"
    assert len(result.comments) > 0


@pytest.mark.asyncio
async def test_parse_comments():
    """Test parsing comments from wikitext."""
    client = WikipediaClient()
    comments = client.parse_comments(MOCK_WIKITEXT)

    assert len(comments) >= 4  # At least 4 signed comments
    # Check sections are identified
    sections = {c.section_title for c in comments}
    assert "Article quality" in sections
    assert "Neutrality concerns" in sections


@pytest.mark.asyncio
async def test_extract_sections():
    """Test that sections are correctly extracted from wikitext."""
    client = WikipediaClient()
    comments = client.parse_comments(MOCK_WIKITEXT)

    quality_comments = [c for c in comments if c.section_title == "Article quality"]
    neutrality_comments = [c for c in comments if c.section_title == "Neutrality concerns"]

    assert len(quality_comments) >= 2
    assert len(neutrality_comments) >= 3


@pytest.mark.asyncio
async def test_handles_article_without_talk_page(httpx_mock):
    """Test handling an article that has no talk page."""
    httpx_mock.add_response(
        url=httpx.URL(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "discussiontoolspageinfo",
                "page": "Talk:Nonexistent Article 12345",
                "format": "json",
                "prop": "threaditemshtml",
            },
        ),
        json={"error": {"code": "missingtitle"}},
    )

    httpx_mock.add_response(
        url=httpx.URL(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "parse",
                "page": "Talk:Nonexistent Article 12345",
                "prop": "wikitext",
                "format": "json",
            },
        ),
        json={"error": {"code": "missingtitle", "info": "The page you specified doesn't exist."}},
    )

    client = WikipediaClient(http_client=httpx.AsyncClient())
    result = await client.fetch_talk_page("https://en.wikipedia.org/wiki/Nonexistent_Article_12345")

    assert result.error is not None
    assert len(result.comments) == 0


@pytest.mark.asyncio
async def test_extracts_author_and_timestamp():
    """Test that author and timestamp are parsed from signatures."""
    client = WikipediaClient()
    wikitext = "I think this needs work. [[User:TestUser|TestUser]] ([[User talk:TestUser|talk]]) 14:30, 15 January 2024 (UTC)"
    comments = client.parse_comments(f"== Discussion ==\n{wikitext}")

    assert len(comments) >= 1
    comment = comments[0]
    assert comment.author == "TestUser"
    assert "14:30" in (comment.timestamp or "")


@pytest.mark.asyncio
async def test_parse_empty_wikitext():
    """Test parsing empty wikitext returns no comments."""
    client = WikipediaClient()
    comments = client.parse_comments("")
    assert comments == []

    comments = client.parse_comments("   ")
    assert comments == []
