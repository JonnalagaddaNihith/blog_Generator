from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib import colors
from typing import Optional
from app.utils.logger import logger
import os


class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the PDF."""
        # Update existing styles or add new ones if they don't exist
        if 'CustomTitle' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#2c3e50'),
            ))

        if 'CustomHeading2' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='CustomHeading2',
                parent=self.styles['Heading2'],
                fontSize=18,
                spaceAfter=12,
                spaceBefore=20,
                textColor=colors.HexColor('#34495e'),
            ))

        if 'CustomHeading3' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='CustomHeading3',
                parent=self.styles['Heading3'],
                fontSize=14,
                spaceAfter=10,
                spaceBefore=15,
                textColor=colors.HexColor('#34495e'),
            ))

        # Update existing BodyText style
        self.styles['BodyText'].fontSize = 11
        self.styles['BodyText'].spaceAfter = 12
        self.styles['BodyText'].alignment = TA_JUSTIFY
        self.styles['BodyText'].leading = 14

        if 'MetaInfo' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='MetaInfo',
                parent=self.styles['Normal'],
                fontSize=9,
                spaceAfter=6,
                textColor=colors.gray,
            ))

    def generate_pdf(
        self,
        output_path: str,
        title: str,
        content: str,
        author: Optional[str] = None,
        image_path: Optional[str] = None,
        meta_description: Optional[str] = None,
    ) -> str:
        """
        Generate a PDF from blog content.
        Returns the path to the generated PDF.
        """
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18,
            )

            story = []

            # Add title
            story.append(Paragraph(title, self.styles['CustomTitle']))
            story.append(Spacer(1, 0.3 * inch))

            # Add featured image if provided
            if image_path and os.path.exists(image_path):
                try:
                    img = Image(image_path, width=5 * inch, height=3 * inch)
                    img.hAlign = 'CENTER'
                    story.append(img)
                    story.append(Spacer(1, 0.3 * inch))
                except Exception as e:
                    logger.warning(f"Failed to add image to PDF: {e}")

            # Add meta info
            if author:
                story.append(Paragraph(f"Author: {author}", self.styles['MetaInfo']))
            if meta_description:
                story.append(Paragraph(f"Description: {meta_description}", self.styles['MetaInfo']))
            story.append(Spacer(1, 0.2 * inch))

            # Add content (parse markdown-like headers)
            self._add_content(story, content)

            # Build PDF
            doc.build(story)
            logger.info(f"Successfully generated PDF at: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            raise

    def _add_content(self, story: list, content: str):
        """
        Parse content and add to story with proper formatting.
        Handles headings (##, ###) and paragraphs.
        """
        lines = content.split('\n')
        current_paragraph = []

        for line in lines:
            line = line.strip()

            if not line:
                if current_paragraph:
                    paragraph_text = ' '.join(current_paragraph)
                    story.append(Paragraph(paragraph_text, self.styles['BodyText']))
                    story.append(Spacer(1, 0.1 * inch))
                    current_paragraph = []
                continue

            # Check for headers
            if line.startswith('### '):
                if current_paragraph:
                    paragraph_text = ' '.join(current_paragraph)
                    story.append(Paragraph(paragraph_text, self.styles['BodyText']))
                    story.append(Spacer(1, 0.1 * inch))
                    current_paragraph = []
                heading = line[4:].strip()
                story.append(Paragraph(heading, self.styles['CustomHeading3']))
            elif line.startswith('## '):
                if current_paragraph:
                    paragraph_text = ' '.join(current_paragraph)
                    story.append(Paragraph(paragraph_text, self.styles['BodyText']))
                    story.append(Spacer(1, 0.1 * inch))
                    current_paragraph = []
                heading = line[3:].strip()
                story.append(Paragraph(heading, self.styles['CustomHeading2']))
            elif line.startswith('# '):
                if current_paragraph:
                    paragraph_text = ' '.join(current_paragraph)
                    story.append(Paragraph(paragraph_text, self.styles['BodyText']))
                    story.append(Spacer(1, 0.1 * inch))
                    current_paragraph = []
                heading = line[2:].strip()
                story.append(Paragraph(heading, self.styles['CustomTitle']))
            else:
                current_paragraph.append(line)

        # Add remaining paragraph
        if current_paragraph:
            paragraph_text = ' '.join(current_paragraph)
            story.append(Paragraph(paragraph_text, self.styles['BodyText']))


pdf_generator = PDFGenerator()
