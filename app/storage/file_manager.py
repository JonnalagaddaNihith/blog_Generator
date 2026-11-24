import uuid
from pathlib import Path
from typing import Optional
from app.config import settings
from app.utils.logger import logger


class FileManager:
    def __init__(self):
        self.images_path = Path(settings.storage_images_path)
        self.pdfs_path = Path(settings.storage_pdfs_path)
        self.docx_path = Path(settings.storage_pdfs_path).parent / "docx"
        self.txt_path = Path(settings.storage_pdfs_path).parent / "txt"
        self.html_path = Path(settings.storage_pdfs_path).parent / "html"
        self.md_path = Path(settings.storage_pdfs_path).parent / "md"
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure storage directories exist."""
        self.images_path.mkdir(parents=True, exist_ok=True)
        self.pdfs_path.mkdir(parents=True, exist_ok=True)
        self.docx_path.mkdir(parents=True, exist_ok=True)
        self.txt_path.mkdir(parents=True, exist_ok=True)
        self.html_path.mkdir(parents=True, exist_ok=True)
        self.md_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Storage directories ensured: {self.images_path}, {self.pdfs_path}, {self.docx_path}, {self.txt_path}, {self.html_path}, {self.md_path}")

    def save_image(self, image_data: bytes, prefix: str = "img", image_format: str = "png") -> str:
        """
        Save image data to storage.
        Returns the relative path to the saved image.
        """
        filename = f"{prefix}_{uuid.uuid4().hex}.{image_format}"
        filepath = self.images_path / filename

        try:
            with open(filepath, "wb") as f:
                f.write(image_data)
            logger.info(f"Saved image to: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Error saving image: {e}")
            raise

    def get_pdf_path(self, filename: str) -> str:
        """Get full path for a PDF file."""
        return str(self.pdfs_path / filename)

    def get_docx_path(self, filename: str) -> str:
        """Get full path for a DOCX file."""
        return str(self.docx_path / filename)

    def get_txt_path(self, filename: str) -> str:
        """Get full path for a TXT file."""
        return str(self.txt_path / filename)

    def get_html_path(self, filename: str) -> str:
        """Get full path for an HTML file."""
        return str(self.html_path / filename)

    def get_md_path(self, filename: str) -> str:
        """Get full path for an MD file."""
        return str(self.md_path / filename)

    def generate_pdf_filename(self, prefix: str = "blog") -> str:
        """Generate a unique filename for a PDF."""
        return f"{prefix}_{uuid.uuid4().hex}.pdf"

    def generate_docx_filename(self, prefix: str = "blog") -> str:
        """Generate a unique filename for a DOCX."""
        return f"{prefix}_{uuid.uuid4().hex}.docx"

    def generate_txt_filename(self, prefix: str = "blog") -> str:
        """Generate a unique filename for a TXT."""
        return f"{prefix}_{uuid.uuid4().hex}.txt"

    def generate_html_filename(self, prefix: str = "blog") -> str:
        """Generate a unique filename for an HTML."""
        return f"{prefix}_{uuid.uuid4().hex}.html"

    def generate_md_filename(self, prefix: str = "blog") -> str:
        """Generate a unique filename for an MD."""
        return f"{prefix}_{uuid.uuid4().hex}.md"


file_manager = FileManager()
