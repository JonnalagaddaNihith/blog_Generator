import os
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

    def save_image(self, image_data: bytes, prefix: str = "img") -> str:
        """
        Save image data to storage.
        Returns the relative path to the saved image.
        """
        filename = f"{prefix}_{uuid.uuid4().hex}.png"
        filepath = self.images_path / filename

        try:
            with open(filepath, "wb") as f:
                f.write(image_data)
            logger.info(f"Saved image to: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Error saving image: {e}")
            raise

    def save_pdf(self, pdf_data: bytes, prefix: str = "blog") -> str:
        """
        Save PDF data to storage.
        Returns the relative path to the saved PDF.
        """
        filename = f"{prefix}_{uuid.uuid4().hex}.pdf"
        filepath = self.pdfs_path / filename

        try:
            with open(filepath, "wb") as f:
                f.write(pdf_data)
            logger.info(f"Saved PDF to: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Error saving PDF: {e}")
            raise

    def get_image_path(self, filename: str) -> str:
        """Get full path for an image file."""
        return str(self.images_path / filename)

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

    def delete_file(self, filepath: str) -> bool:
        """
        Delete a file from storage.
        Returns True if successful, False otherwise.
        """
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Deleted file: {filepath}")
                return True
            logger.warning(f"File not found for deletion: {filepath}")
            return False
        except Exception as e:
            logger.error(f"Error deleting file {filepath}: {e}")
            return False

    def file_exists(self, filepath: str) -> bool:
        """Check if a file exists."""
        return os.path.exists(filepath)

    def generate_image_filename(self, prefix: str = "img") -> str:
        """Generate a unique filename for an image."""
        return f"{prefix}_{uuid.uuid4().hex}.png"

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
