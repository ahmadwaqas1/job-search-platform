from app.integrations.job_sources.base import NormalizedJobPosting
from app.services.job_ingestion_service import _content_hash


def _posting(**overrides) -> NormalizedJobPosting:
    defaults = dict(external_id="abc123", title="Backend Engineer", company="Acme", location="Remote", description_text="Do stuff.")
    defaults.update(overrides)
    return NormalizedJobPosting(**defaults)


def test_content_hash_stable_for_identical_postings():
    assert _content_hash(_posting()) == _content_hash(_posting())


def test_content_hash_changes_when_description_changes():
    h1 = _content_hash(_posting())
    h2 = _content_hash(_posting(description_text="Do different stuff."))
    assert h1 != h2


def test_content_hash_changes_when_salary_changes():
    h1 = _content_hash(_posting(salary_min=100_000))
    h2 = _content_hash(_posting(salary_min=120_000))
    assert h1 != h2


def test_content_hash_ignores_external_id():
    # external_id is the upsert key itself, not part of the change-detection
    # hash - two postings that differ only by external_id should still hash
    # the same since their content is identical.
    h1 = _content_hash(_posting(external_id="id-1"))
    h2 = _content_hash(_posting(external_id="id-2"))
    assert h1 == h2
