from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from typing import Optional
from html import escape as html_escape
import os
import re
from app.utils.logger import logger


class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._list_styles = {}
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

        if 'Quote' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Quote',
                parent=self.styles['BodyText'],
                fontName='Helvetica-Oblique',
                leftIndent=18,
                spaceAfter=10,
                textColor=colors.HexColor('#555555'),
            ))

        if 'CodeBlock' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='CodeBlock',
                parent=self.styles['Normal'],
                fontName='Courier',
                fontSize=9,
                leftIndent=12,
                rightIndent=12,
                spaceAfter=10,
                leading=12,
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
            story.append(Paragraph(self._inline_markdown(title), self.styles['CustomTitle']))
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
                story.append(Paragraph(self._inline_markdown(f"Author: {author}"), self.styles['MetaInfo']))
            if meta_description:
                story.append(Paragraph(self._inline_markdown(f"Description: {meta_description}"), self.styles['MetaInfo']))
            story.append(Spacer(1, 0.2 * inch))

            # Add content (render Markdown as formatted PDF content)
            self._add_content(story, content)

            # Build PDF
            doc.build(story)
            logger.info(f"Successfully generated PDF at: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            raise

    def _inline_markdown(self, text: str) -> str:
        if not text:
            return ""

        escaped = html_escape(text, quote=True)
        code_spans = []

        def stash_code(match):
            code_spans.append(f"<font name=\"Courier\" size=\"9\">{match.group(1)}</font>")
            return f"@@CODE{len(code_spans) - 1}@@"

        escaped = re.sub(r"`([^`]+)`", stash_code, escaped)
        escaped = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", escaped)
        escaped = re.sub(
            r"\[([^\]]+)\]\(([^)\s]+)[^)]*\)",
            r'<a href="\2" color="#1a0dab"><u>\1</u></a>',
            escaped,
        )
        escaped = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", escaped)
        escaped = re.sub(r"__([^_]+)__", r"<b>\1</b>", escaped)
        escaped = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<i>\1</i>", escaped)
        escaped = re.sub(r"(?<!\w)_([^_\n]+)_(?!\w)", r"<i>\1</i>", escaped)
        escaped = re.sub(r"~~([^~]+)~~", r"<strike>\1</strike>", escaped)

        for index, code_span in enumerate(code_spans):
            escaped = escaped.replace(f"@@CODE{index}@@", code_span)

        return escaped

    def _heading_style(self, level: int):
        if level <= 2:
            return self.styles['CustomHeading2']
        if level == 3:
            return self.styles['CustomHeading3']
        return self.styles[f'Heading{min(level, 6)}']

    def _list_style(self, indent_level: int):
        if indent_level not in self._list_styles:
            self._list_styles[indent_level] = ParagraphStyle(
                name=f'ListItem{indent_level}',
                parent=self.styles['BodyText'],
                leftIndent=18 + indent_level * 12,
                spaceAfter=4,
            )
        return self._list_styles[indent_level]

    def _add_paragraph(self, story: list, paragraph_lines: list):
        if not paragraph_lines:
            return
        paragraph_text = self._inline_markdown(' '.join(paragraph_lines))
        paragraph_lines.clear()
        if paragraph_text:
            story.append(Paragraph(paragraph_text, self.styles['BodyText']))
            story.append(Spacer(1, 0.1 * inch))

    def _add_code_block(self, story: list, code_lines: list):
        if not code_lines:
            return
        text = html_escape('\n'.join(code_lines), quote=True).replace('\n', '<br/>')
        story.append(Paragraph(text, self.styles['CodeBlock']))
        story.append(Spacer(1, 0.1 * inch))

    def _add_content(self, story: list, content: str):
        """
        Parse Markdown content and add formatted flowables to the story.
        """
        paragraph_lines = []
        in_code_block = False
        code_lines = []

        def flush_paragraph():
            self._add_paragraph(story, paragraph_lines)

        for raw_line in content.splitlines():
            if in_code_block:
                if raw_line.strip().startswith('```'):
                    self._add_code_block(story, code_lines)
                    code_lines = []
                    in_code_block = False
                else:
                    code_lines.append(raw_line)
                continue

            line = raw_line.strip()

            if not line:
                flush_paragraph()
                continue

            if line.startswith('```'):
                flush_paragraph()
                in_code_block = True
                code_lines = []
                continue

            heading_match = re.match(r'^(#{1,6})\s+(.*)$', line)
            if heading_match:
                flush_paragraph()
                level = len(heading_match.group(1))
                heading_text = self._inline_markdown(heading_match.group(2).strip())
                story.append(Paragraph(heading_text, self._heading_style(level)))
                continue

            if re.match(r'^([-*_])\1{2,}$', line):
                flush_paragraph()
                story.append(Spacer(1, 0.15 * inch))
                continue

            unordered_match = re.match(r'^(\s*)[-*+]\s+(.*)$', raw_line)
            ordered_match = re.match(r'^(\s*)(\d+)[.)]\s+(.*)$', raw_line)

            if unordered_match or ordered_match:
                flush_paragraph()
                if unordered_match:
                    indent = len(unordered_match.group(1).replace('\t', '  '))
                    item_text = unordered_match.group(2)
                    prefix = '• '
                else:
                    indent = len(ordered_match.group(1).replace('\t', '  '))
                    item_text = ordered_match.group(3)
                    prefix = f"{ordered_match.group(2)}. "
                style = self._list_style(min(indent // 2, 4))
                story.append(Paragraph(prefix + self._inline_markdown(item_text), style))
                continue

            quote_match = re.match(r'^\s*>\s?(.*)$', raw_line)
            if quote_match:
                flush_paragraph()
                story.append(Paragraph(
                    self._inline_markdown(quote_match.group(1)),
                    self.styles['Quote'],
                ))
                continue

            paragraph_lines.append(line)

        if in_code_block:
            self._add_code_block(story, code_lines)
        else:
            flush_paragraph()


pdf_generator = PDFGenerator()
