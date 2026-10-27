"""Unit tests for SourceCreate validation (app/models/source.py).

Focus: cross-field rules (year vs published_date, fields required by type).
No database needed.
"""

from datetime import date

import pytest
from pydantic import ValidationError

from app.models import SourceCreate
from app.models.source import SourceType


def make(**overrides) -> SourceCreate:
    fields = {"type": "book", "title": "QED", "authors": "Feynman, Richard"}
    fields.update(overrides)
    return SourceCreate.model_validate(fields)


# --- Required and optional fields --------------------------------------------
def test_minimal_book_is_valid():
    source = make()

    assert source.type is SourceType.book
    assert source.year is None
    assert source.editors is None


@pytest.mark.parametrize("missing", ["type", "title", "authors"])
def test_required_field(missing):
    fields = {"type": "book", "title": "QED", "authors": "Feynman, Richard"}
    del fields[missing]

    with pytest.raises(ValidationError):
        SourceCreate.model_validate(fields)


def test_unknown_type_is_rejected():
    with pytest.raises(ValidationError):
        make(type="thesis")


@pytest.mark.parametrize(
    ("field", "max_length"),
    [("title", 1024), ("authors", 1024), ("editors", 1024), ("pages", 64), ("url", 2048)],
)
def test_length_limits(field, max_length):
    make(**{field: "x" * max_length})
    with pytest.raises(ValidationError):
        make(**{field: "x" * (max_length + 1)})


# --- year and published_date -------------------------------------------------
def test_year_is_taken_from_published_date():
    source = make(published_date="1985-06-01")

    assert source.year == 1985


def test_matching_year_and_published_date():
    source = make(year=1985, published_date=date(1985, 6, 1))

    assert source.year == 1985


def test_year_must_match_published_date():
    with pytest.raises(ValidationError, match="year must match published_date"):
        make(year=1990, published_date="1985-06-01")


def test_undated_source():
    assert make(year=None).year is None


# --- Fields required by type -------------------------------------------------
@pytest.mark.parametrize(
    ("type", "required", "value"),
    [
        ("journal_article", "container_title", "Physical Review"),
        ("book_chapter", "container_title", "The Feynman Lectures"),
        ("web_page", "url", "https://example.org"),
    ],
)
def test_type_requires_field(type, required, value):
    make(type=type, **{required: value})
    with pytest.raises(ValidationError, match=f"{type} requires {required}"):
        make(type=type)


# Fields that satisfy each type's rules, authors aside
VALID_BY_TYPE = {
    "book": {},
    "journal_article": {"container_title": "Physical Review"},
    "book_chapter": {"container_title": "The Feynman Lectures"},
    "web_page": {"url": "https://example.org"},
    "other": {},
}


@pytest.mark.parametrize("type", ["book", "journal_article", "book_chapter", "web_page"])
@pytest.mark.parametrize("absent", ["missing", "null"])
def test_type_requires_authors(type, absent):
    fields = {"type": type, "title": "QED", **VALID_BY_TYPE[type]}
    if absent == "null":
        fields["authors"] = None

    with pytest.raises(ValidationError, match=f"{type} requires authors"):
        SourceCreate.model_validate(fields)


# --- other type ---------------------------------------------------------------
def test_other_needs_only_a_title():
    source = SourceCreate.model_validate({"type": "other", "title": "Conversation with Alice"})

    assert source.type is SourceType.other
    assert source.authors is None


def test_other_accepts_authors():
    assert make(type="other", authors="Alice").authors == "Alice"


# --- note ---------------------------------------------------------------------
@pytest.mark.parametrize("type", list(VALID_BY_TYPE))
def test_note_is_accepted_on_every_type(type):
    source = make(type=type, note="Why it matters", **VALID_BY_TYPE[type])

    assert source.note == "Why it matters"


def test_note_defaults_to_none():
    assert make().note is None
