from typing import Optional
import os
from app.utils.logger import logger


class MdGenerator:
    def __init__(self):
        pass

    def generate_md(
        self,
        output_path: str,
        title: str,
        content: str,
        author: Optional[str] = None,
        image_path: Optional[str] = None,
        meta_description: Optional[str] = None,
    ) -> str:
        """
        Generate a Markdown file from blog content.
        Since the content is already in Markdown, we just add metadata at the top.
        Returns the path to the generated MD file.
        """
        try:
            lines = []

            # Add YAML frontmatter
            lines.append("---")
            lines.append(f"title: {title}")
            if author:
                lines.append(f"author: {author}")
            if meta_description:
                lines.append(f"description: {meta_description}")
            if image_path and os.path.exists(image_path):
                lines.append(f"image: {image_path}")
            lines.append("---")
            lines.append("")

            # Add title as heading
            lines.append(f"# {title}")
            lines.append("")

            # Add featured image if provided
            if image_path and os.path.exists(image_path):
                lines.append(f"![Featured Image]({image_path})")
                lines.append("")

            # Add content (already in Markdown format)
            lines.append(content)

            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))

            logger.info(f"Successfully generated MD at: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error generating MD: {e}")
            raise


md_generator = MdGenerator()
