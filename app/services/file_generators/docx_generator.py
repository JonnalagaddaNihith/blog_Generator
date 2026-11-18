from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from typing import Optional
import os
import re
from app.utils.logger import logger


class DocxGenerator:
    def __init__(self):
        pass

    def generate_docx(
        self,
        output_path: str,
        title: str,
        content: str,
        author: Optional[str] = None,
        image_path: Optional[str] = None,
        meta_description: Optional[str] = None,
    ) -> str:
        """
        Generate a DOCX file from blog content.
        Returns the path to the generated DOCX file.
        """
        try:
            doc = Document()

            # Add title
            title_heading = doc.add_heading(title, level=1)
            title_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER

            # Add featured image if provided
            if image_path and os.path.exists(image_path):
                try:
                    doc.add_picture(image_path, width=Inches(5))
                    last_paragraph = doc.paragraphs[-1]
                    last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                except Exception as e:
                    logger.warning(f"Failed to add image to DOCX: {e}")

            # Add meta info
            if author:
                para = doc.add_paragraph()
                run = para.add_run(f"Author: {author}")
                run.font.size = Pt(9)
                run.font.color.rgb = RGBColor(128, 128, 128)

            if meta_description:
                para = doc.add_paragraph()
                run = para.add_run(f"Description: {meta_description}")
                run.font.size = Pt(9)
                run.font.color.rgb = RGBColor(128, 128, 128)

            doc.add_paragraph()  # Add spacing

            # Add content (render Markdown as formatted DOCX content)
            self._add_content(doc, content)

            # Save document
            doc.save(output_path)
            logger.info(f"Successfully generated DOCX at: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error generating DOCX: {e}")
            raise

    def _add_content(self, doc: Document, content: str):
        """
        Parse Markdown content and add formatted paragraphs to the document.
        """
        in_code_block = False
        code_lines = []

        for raw_line in content.splitlines():
            if in_code_block:
                if raw_line.strip().startswith('```'):
                    # End code block
                    if code_lines:
                        para = doc.add_paragraph('\n'.join(code_lines))
                        para.style = 'No Spacing'
                        run = para.runs[0]
                        run.font.name = 'Courier New'
                        run.font.size = Pt(9)
                    code_lines = []
                    in_code_block = False
                else:
                    code_lines.append(raw_line)
                continue

            line = raw_line.strip()

            if not line:
                doc.add_paragraph()
                continue

            if line.startswith('```'):
                in_code_block = True
                code_lines = []
                continue

            # Check for headings
            heading_match = re.match(r'^(#{1,6})\s+(.*)$', line)
            if heading_match:
                level = len(heading_match.group(1))
                heading_text = heading_match.group(2).strip()
                doc.add_heading(heading_text, level=min(level, 3))
                continue

            # Check for horizontal rule
            if re.match(r'^([-*_])\1{2,}$', line):
                doc.add_paragraph('_' * 50)
                continue

            # Check for lists
            unordered_match = re.match(r'^(\s*)[-*+]\s+(.*)$', raw_line)
            ordered_match = re.match(r'^(\s*)(\d+)[.)]\s+(.*)$', raw_line)

            if unordered_match or ordered_match:
                if unordered_match:
                    item_text = unordered_match.group(2)
                    prefix = '• '
                else:
                    item_text = ordered_match.group(3)
                    prefix = f"{ordered_match.group(2)}. "
                para = doc.add_paragraph(prefix + item_text)
                continue

            # Check for blockquote
            quote_match = re.match(r'^\s*>\s?(.*)$', raw_line)
            if quote_match:
                para = doc.add_paragraph(quote_match.group(1))
                run = para.runs[0]
                run.italic = True
                para.paragraph_format.left_indent = Inches(0.25)
                continue

            # Regular paragraph with inline formatting
            para = doc.add_paragraph()
            self._add_inline_markdown(para, line)

        # Handle unclosed code block
        if in_code_block and code_lines:
            para = doc.add_paragraph('\n'.join(code_lines))
            para.style = 'No Spacing'
            run = para.runs[0]
            run.font.name = 'Courier New'
            run.font.size = Pt(9)

    def _add_inline_markdown(self, paragraph, text: str):
        """
        Add text with inline markdown formatting (bold, italic, code, links).
        """
        import re

        # Simple implementation - can be enhanced
        # Process code spans first
        parts = re.split(r'`([^`]+)`', text)
        for i, part in enumerate(parts):
            if i % 2 == 1:  # Code span
                run = paragraph.add_run(part)
                run.font.name = 'Courier New'
                run.font.size = Pt(9)
            else:
                # Process bold and italic
                bold_parts = re.split(r'\*\*([^*]+)\*\*', part)
                for j, bold_part in enumerate(bold_parts):
                    if j % 2 == 1:  # Bold
                        run = paragraph.add_run(bold_part)
                        run.bold = True
                    else:
                        # Process italic
                        italic_parts = re.split(r'(?<!\*)\*([^*\n]+)\*(?!\*)', bold_part)
                        for k, italic_part in enumerate(italic_parts):
                            if k % 2 == 1:  # Italic
                                run = paragraph.add_run(italic_part)
                                run.italic = True
                            else:
                                # Regular text
                                if italic_part:
                                    paragraph.add_run(italic_part)


docx_generator = DocxGenerator()
