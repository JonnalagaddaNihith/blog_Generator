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
