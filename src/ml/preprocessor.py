"""Text preprocessing for bug reports."""
import re
import string


HAS_NLTK = False
_lemmatizer = None
try:
    import nltk
    from nltk.stem import WordNetLemmatizer
    nltk.data.find("corpora/wordnet")
    _lemmatizer = WordNetLemmatizer()
    HAS_NLTK = True
except (ImportError, LookupError):
    pass


_HTML_TAG_RE = re.compile(r"<[^>]+>")
_URL_RE = re.compile(r"https?://\S+")
_JIRA_KEY_RE = re.compile(r"[A-Z]+-\d+")
_MULTI_SPACE_RE = re.compile(r"\s+")

STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during",
    "before", "after", "above", "below", "between", "out", "off", "over",
    "under", "again", "further", "then", "once", "and", "but", "or", "nor",
    "not", "so", "very", "just", "about", "up", "down", "here", "there",
    "this", "that", "these", "those", "i", "me", "my", "we", "our", "you",
    "your", "he", "him", "his", "she", "her", "it", "its", "they", "them",
}


def strip_html(text: str) -> str:
    return _HTML_TAG_RE.sub(" ", text)


def strip_urls(text: str) -> str:
    return _URL_RE.sub(" ", text)


def strip_jira_keys(text: str) -> str:
    return _JIRA_KEY_RE.sub(" ", text)


def normalize_whitespace(text: str) -> str:
    return _MULTI_SPACE_RE.sub(" ", text).strip()


def lemmatize(text: str) -> str:
    if not HAS_NLTK or _lemmatizer is None:
        return text
    return " ".join(_lemmatizer.lemmatize(w) for w in text.split())


def preprocess_text(text: str) -> str:
    if not text:
        return ""
    text = strip_html(text)
    text = strip_urls(text)
    text = strip_jira_keys(text)
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    tokens = text.split()
    tokens = [t for t in tokens if t not in STOP_WORDS and len(t) > 1]
    text = " ".join(tokens)
    text = lemmatize(text)
    text = normalize_whitespace(text)
    return text


def preprocess_bug(summary: str, description: str = "") -> str:
    combined = f"{summary} {description}"
    return preprocess_text(combined)
