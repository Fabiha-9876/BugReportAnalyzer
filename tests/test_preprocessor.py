"""Tests for ML preprocessor."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ml.preprocessor import (
    preprocess_text, preprocess_bug, strip_html, strip_urls, strip_jira_keys,
)


class TestPreprocessor:
    def test_strip_html(self):
        assert strip_html("<p>Hello <b>world</b></p>") == " Hello  world  "

    def test_strip_urls(self):
        result = strip_urls("Check https://example.com for details")
        assert "https://example.com" not in result

    def test_strip_jira_keys(self):
        result = strip_jira_keys("See PROJ-123 for details")
        assert "PROJ-123" not in result

    def test_preprocess_text_basic(self):
        result = preprocess_text("The LOGIN button IS not WORKING!")
        assert "the" not in result
        assert "is" not in result
        assert "login" in result or "button" in result

    def test_preprocess_empty(self):
        assert preprocess_text("") == ""
        assert preprocess_text(None) == ""

    def test_preprocess_bug_combines(self):
        result = preprocess_bug("Login fails", "Steps: enter credentials")
        assert "login" in result
        assert "fail" in result or "fails" in result

    def test_stop_words_removed(self):
        result = preprocess_text("The application is very slow and the page does not load")
        assert "the" not in result.split()
        assert "is" not in result.split()
        assert "very" not in result.split()

    def test_short_words_removed(self):
        result = preprocess_text("I a am in it to go so")
        # All 1-2 char stop words should be removed
        assert result.strip() == "" or all(len(w) > 1 for w in result.split())
