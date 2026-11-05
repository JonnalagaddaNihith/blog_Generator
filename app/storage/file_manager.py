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
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure storage directories exist."""
        self.images_path.mkdir(parents=True, exist_ok=True)
        self.pdfs_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Storage directories ensured: {self.images_path}, {self.pdfs_path}")

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


file_manager = FileManager()
