from src.lib.logger import logger


def generate_markdown(
    doc_name: str, sections_content: list[dict[str, str | int]]
) -> str:
    """Generate markdown formatted string from document sections.

    Args:
        doc_name (str): Name of the document.
        sections_content (list[dict[str, str | int]]): List of dictionaries containing section data.
            Each dictionary should have 'heading', 'level', and 'content' keys.

    Returns:
        str: Markdown formatted string containing the document content.
    """
    try:
        md_lines = []

        md_lines.append(f"# {doc_name}")
        md_lines.append("")  # Add a blank line after the title

        for section in sections_content:
            heading = section["heading"]
            level = section["level"]
            content = section["content"]

            # Create md heading
            md_heading = "#" * level + " " + heading

            md_lines.append(md_heading)
            md_lines.append("")  # Add a blank line after the heading

            if content.strip():
                md_lines.append(content)
                md_lines.append("")  # Add a blank line after the content

        return "\n".join(md_lines).strip()

    except Exception as e:
        logger.error("Error in `_generate_markdown`", exc_info=True)
        raise Exception(
            f"`_generate_markdown`: Failed to generate markdown: {str(e)}"
        ) from e
