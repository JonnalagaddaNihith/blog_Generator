import markdown
from typing import Optional
import os
from app.utils.logger import logger


class HtmlGenerator:
    def __init__(self):
        # Configure markdown extensions
        self.md = markdown.Markdown(extensions=['extra', 'nl2br', 'sane_lists'])

    def generate_html(
        self,
        output_path: str,
        title: str,
        content: str,
        author: Optional[str] = None,
        image_path: Optional[str] = None,
        meta_description: Optional[str] = None,
    ) -> str:
        """
        Generate an HTML file from blog content.
        Returns the path to the generated HTML file.
        """
        try:
            # Convert markdown to HTML
            html_content = self.md.convert(content)
            self.md.reset()  # Reset for next use

            # Build complete HTML document
            html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self._escape_html(title)}</title>
    <meta name="description" content="{self._escape_html(meta_description or '')}">
    <meta name="author" content="{self._escape_html(author or '')}">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{
            text-align: center;
            color: #2c3e50;
            border-bottom: 2px solid #eee;
            padding-bottom: 0.5rem;
        }}
        h2 {{
            color: #34495e;
            margin-top: 2rem;
        }}
        h3 {{
            color: #34495e;
        }}
        .meta {{
            text-align: center;
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 2rem;
        }}
        .featured-image {{
            display: block;
            margin: 2rem auto;
            max-width: 100%;
            height: auto;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 1rem;
            border-radius: 5px;
            overflow-x: auto;
        }}
        pre code {{
            background-color: transparent;
            padding: 0;
        }}
        blockquote {{
            border-left: 4px solid #ddd;
            margin: 1rem 0;
            padding-left: 1rem;
            color: #666;
            font-style: italic;
        }}
        a {{
            color: #1a0dab;
            text-decoration: underline;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1rem 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 0.5rem;
        }}
        th {{
            background-color: #f4f4f4;
        }}
        hr {{
            border: none;
            border-top: 1px solid #eee;
            margin: 2rem 0;
        }}
    </style>
</head>
<body>
    <h1>{self._escape_html(title)}</h1>
"""

            # Add meta info
            if author or meta_description:
                html += '    <div class="meta">\n'
                if author:
                    html += f'        <p>Author: {self._escape_html(author)}</p>\n'
                if meta_description:
                    html += f'        <p>Description: {self._escape_html(meta_description)}</p>\n'
                html += '    </div>\n'

            # Add featured image if provided
            if image_path and os.path.exists(image_path):
                # For relative paths, you might want to convert to absolute or data URI
                # For now, just add the path as-is
                html += f'    <img src="{self._escape_html(image_path)}" alt="Featured Image" class="featured-image">\n'

            html += f"""
    <div class="content">
        {html_content}
    </div>
</body>
</html>
"""

            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)

            logger.info(f"Successfully generated HTML at: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error generating HTML: {e}")
            raise

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        if not text:
            return ""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))


html_generator = HtmlGenerator()
