from __future__ import annotations

import hashlib
import re
from difflib import SequenceMatcher
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_PREFIXES = ("utm_",)
TRACKING_PARAMS = {
    "fbclid",
    "gclid",
    "igshid",
    "mc_cid",
    "mc_eid",
    "ref",
    "spm",
}


def canonical_url(url: str) -> str:
    split = urlsplit(url.strip())
    scheme = split.scheme.lower() or "https"
    host = split.netloc.lower()
    path = re.sub(r"/+$", "", split.path) or "/"
    query = []
    for key, value in parse_qsl(split.query, keep_blank_values=False):
        lower_key = key.lower()
        if lower_key in TRACKING_PARAMS or lower_key.startswith(TRACKING_PREFIXES):
            continue
        query.append((key, value))
    return urlunsplit((scheme, host, path, urlencode(sorted(query)), ""))


def normalize_title(title: str) -> str:
    return re.sub(r"\s+", " ", title).strip().lower()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug or hashlib.sha1(value.encode("utf-8")).hexdigest()[:10]


def item_hash(title: str, url: str) -> str:
    source = f"{normalize_title(title)}|{canonical_url(url)}"
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def titles_similar(left: str, right: str, threshold: float = 0.75) -> bool:
    return SequenceMatcher(None, normalize_title(left), normalize_title(right)).ratio() >= threshold
