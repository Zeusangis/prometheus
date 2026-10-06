"""Keep docs/project-context.md honest.

Two kinds of claim are protected:

* the generated inventory (Appendix A) must match the code, and
* the hand-written known-gaps and next-steps sections (7 and 8) must each carry a marker
  whose registered check still holds, so the document fails when the code contradicts it.
"""

from tools.generate_project_context import (
    BEGIN_MARKER,
    DOCUMENT,
    END_MARKER,
    build_app,
    build_block,
    read,
    render,
)
from tools.known_gaps import CLAIM_CHECKS, claim_ids


def test_generated_inventory_is_current():
    app = build_app()
    with app.app_context():
        block = build_block(app)
    document = read(DOCUMENT)
    assert render(document, block) == document, (
        "docs/project-context.md is stale. Run: "
        "cd talent_intelligence_backend && python -m tools.generate_project_context"
    )


def test_document_keeps_its_markers():
    document = read(DOCUMENT)
    assert document.count(BEGIN_MARKER) == 1
    assert document.count(END_MARKER) == 1
    assert document.index(BEGIN_MARKER) < document.index(END_MARKER)


def test_documented_claims_still_hold():
    """A known gap or next step must remain true, or the document must be updated."""
    document = read(DOCUMENT)
    documented = claim_ids(document)
    assert documented, "no <!-- claim: ... --> markers found in docs/project-context.md"
    unregistered = [claim_id for claim_id in documented if claim_id not in CLAIM_CHECKS]
    assert not unregistered, (
        f"documented claims have no check in tools/known_gaps.py: {unregistered}"
    )
    app = build_app()
    with app.app_context():
        for claim_id in documented:
            description, check = CLAIM_CHECKS[claim_id]
            try:
                check(app)
            except AssertionError as error:
                raise AssertionError(
                    f"docs/project-context.md claims '{claim_id}' ({description}), "
                    f"but the code contradicts it: {error}. Update the document, the marker "
                    "and tools/known_gaps.py together."
                ) from error


def test_every_registered_claim_is_documented():
    """A check with no documented claim is dead weight and would fail once the gap closes."""
    documented = set(claim_ids(read(DOCUMENT)))
    orphans = sorted(set(CLAIM_CHECKS) - documented)
    assert not orphans, (
        "these checks back no claim in docs/project-context.md; delete the check and its "
        f"registry entry once the feature ships: {orphans}"
    )
