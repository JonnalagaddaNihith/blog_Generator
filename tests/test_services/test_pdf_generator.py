import pytest
import os
from app.services.pdf_generator import pdf_generator


@pytest.mark.asyncio
async def test_pdf_generation():
    """Test PDF generation."""
    import tempfile

    # Create a temporary file for the PDF
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        output_path = tmp.name

    try:
        result_path = pdf_generator.generate_pdf(
            output_path=output_path,
            title="Test Blog Post",
            content="# Introduction\n\nThis is a test blog post.\n\n## Main Section\n\nHere is some content.",
            author="Test Author",
            meta_description="A test blog post for testing PDF generation.",
        )

        assert result_path == output_path
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0

    finally:
        # Clean up
        if os.path.exists(output_path):
            os.remove(output_path)


def test_inline_markdown_formats_basic_syntax():
    result = pdf_generator._inline_markdown(
        "A **bold** and `code` [link](https://example.com)."
    )

    assert result == (
        "A <b>bold</b> and "
        "<font name=\"Courier\" size=\"9\">code</font> "
        "<a href=\"https://example.com\" color=\"#1a0dab\"><u>link</u></a>."
    )


def test_add_content_renders_markdown_blocks():
    story = []
    pdf_generator._add_content(
        story,
        "## Main Heading\n\n"
        "Intro with **bold** and [source](https://example.com).\n\n"
        "* First item\n"
        "* Second item\n\n"
        "1. First step\n"
        "2. Second step",
    )

    texts = [getattr(item, "text", "") for item in story]

    assert "Main Heading" in texts
    assert any("<b>bold</b>" in text and "<a href=" in text for text in texts)
    assert any(text.startswith("• First item") for text in texts)
    assert any(text.startswith("1. First step") for text in texts)
    assert not any("##" in text or "**" in text or "[source](" in text for text in texts)
