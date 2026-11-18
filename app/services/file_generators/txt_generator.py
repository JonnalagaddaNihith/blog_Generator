from typing import Optional
import os
import re
from app.utils.logger import logger


class TxtGenerator:
    def __init__(self):
        pass

    def generate_txt(
        self,
        output_path: str,
        title: str,
        content: str,
        author: Optional[str] = None,
        image_path: Optional[str] = None,
        meta_description: Optional[str] = None,
    ) -> str:
        """
        Generate a plain text file from blog content.
        Returns the path to the generated TXT file.
        """
        try:
            lines = []

            # Add title
            lines.append("=" * len(title))
            lines.append(title)
            lines.append("=" * len(title))
            lines.append("")

            # Add meta info
            if author:
                lines.append(f"Author: {author}")
            if meta_description:
                lines.append(f"Description: {meta_description}")
            if author or meta_description:
                lines.append("")

            # Add featured image note if provided
            if image_path and os.path.exists(image_path):
                lines.append(f"[Image: {image_path}]")
                lines.append("")

            lines.append("")

            # Add content (convert Markdown to plain text)
            lines.extend(self._markdown_to_text(content))

            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))

            logger.info(f"Successfully generated TXT at: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error generating TXT: {e}")
            raise

    def _markdown_to_text(self, content: str) -> list:
        """
        Convert Markdown content to plain text.
        """
        lines = []
        in_code_block = False
        code_lines = []

        for raw_line in content.splitlines():
            if in_code_block:
                if raw_line.strip().startswith('```'):
                    # End code block
                    if code_lines:
                        lines.append("```")
                        lines.extend(code_lines)
                        lines.append("```")
                    code_lines = []
                    in_code_block = False
                else:
                    code_lines.append(raw_line)
                continue

            line = raw_line.strip()

            if not line:
                lines.append("")
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
                lines.append(f"{'#' * level} {heading_text}")
                continue

            # Check for horizontal rule
            if re.match(r'^([-*_])\1{2,}$', line):
                lines.append("-" * 50)
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
                lines.append(prefix + item_text)
                continue

            # Check for blockquote
            quote_match = re.match(r'^\s*>\s?(.*)$', raw_line)
            if quote_match:
                lines.append(f"> {quote_match.group(1)}")
                continue

            # Regular paragraph - strip inline markdown
            plain_text = self._strip_inline_markdown(line)
            lines.append(plain_text)

        # Handle unclosed code block
        if in_code_block and code_lines:
            lines.append("```")
            lines.extend(code_lines)
            lines.append("```")

        return lines

    def _strip_inline_markdown(self, text: str) -> str:
        """
        Strip inline markdown formatting (bold, italic, code, links).
        """
        # Remove code spans
        text = re.sub(r'`([^`]+)`', r'\1', text)
        # Remove images
        text = re.sub(r'!\[([^\]]*)\]\([^)]*\)', r'\1', text)
        # Remove links but keep text
        text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', text)
        # Remove bold
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        # Remove italic
        text = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'\1', text)
        text = re.sub(r'(?<!\w)_([^_\n]+)_(?!\w)', r'\1', text)
        # Remove strikethrough
        text = re.sub(r'~~([^~]+)~~', r'\1', text)

        return text


txt_generator = TxtGenerator()
