"""Keep docs/project-context.md honest: the generated inventory must match the code."""

from tools.generate_project_context import (
    BEGIN_MARKER,
    DOCUMENT,
    END_MARKER,
    build_app,
    build_block,
    read,
    render,
)


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
