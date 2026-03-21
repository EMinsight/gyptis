#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Benjamin Vial
# This file is part of gyptis
# Version: 1.2.0
# License: MIT
# See the documentation at gyptis.gitlab.io

"""
Carousel HTML Generator from RST Documentation

This module builds a Bootstrap carousel component by parsing and extracting
links, images, and tooltips from Sphinx-generated RST documentation files.
It includes comprehensive error handling, validation, and logging capabilities.
"""

import html
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CarouselConfig:
    """Configuration constants for carousel generation."""

    RST_SOURCE_FILE = "examples/index.rst"
    HTML_TARGET_FILE = "_build/html/index.html"
    IMAGE_PREFIX = "_images/"
    CAROUSEL_PLACEHOLDER = "__CAROUSSEL_PACEHOLDER__"
    CAROUSEL_ID = "carouselExampleIndicators"

    # RST parsing patterns
    TOOLTIP_PREFIX = '    <div class="sphx-glr-thumbcontainer" tooltip="'
    IMAGE_PREFIX_RST = "  .. image:: "
    ALT_PREFIX = "     :alt: "
    TITLE_PREFIX = '      <div class="sphx-glr-thumbnail-title">'
    IMAGE_EXTENSION = ".png"


class ValidationError(Exception):
    """Custom exception for validation errors."""

    pass


def validate_file_exists(filepath: str) -> Path:
    """
    Validate that a file exists and is readable.

    Args:
        filepath: Path to the file to validate

    Returns:
        Path object for the validated file

    Raises:
        FileNotFoundError: If file does not exist
        PermissionError: If file is not readable
    """
    path = Path(filepath)

    if not path.exists():
        logger.error(f"File not found: {filepath}")
        raise FileNotFoundError(f"Required file not found: {filepath}")

    if not path.is_file():
        logger.error(f"Path is not a file: {filepath}")
        raise ValueError(f"Path is not a file: {filepath}")

    if not os.access(path, os.R_OK):
        logger.error(f"File is not readable: {filepath}")
        raise PermissionError(f"File is not readable: {filepath}")

    logger.debug(f"File validated: {filepath}")
    return path


def read_rst_file(filepath: str) -> List[str]:
    """
    Read and return lines from an RST file with error handling.

    Args:
        filepath: Path to the RST file

    Returns:
        List of lines from the file

    Raises:
        FileNotFoundError: If file does not exist
        UnicodeDecodeError: If file cannot be decoded as UTF-8
    """
    try:
        path = validate_file_exists(filepath)
        with open(path, "r", encoding="utf-8") as file:
            lines = file.readlines()
        logger.info(f"Successfully read {len(lines)} lines from {filepath}")
        return lines
    except UnicodeDecodeError as e:
        logger.error(f"Failed to decode file {filepath}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error reading file {filepath}: {e}")
        raise


def sanitize_text(text: str) -> str:
    """
    Sanitize text for safe HTML output by escaping special characters.

    Args:
        text: Raw text to sanitize

    Returns:
        HTML-escaped text
    """
    if not text:
        return ""
    return html.escape(text.strip())


def validate_tooltip(tooltip: str) -> str:
    """
    Validate and clean tooltip text.

    Args:
        tooltip: Raw tooltip text

    Returns:
        Validated and sanitized tooltip text

    Raises:
        ValidationError: If tooltip is empty or invalid
    """
    if not tooltip or not tooltip.strip():
        raise ValidationError("Tooltip text is empty")

    sanitized = sanitize_text(tooltip)

    # Check for reasonable length (avoid extremely long tooltips)
    if len(sanitized) > 500:
        logger.warning(
            f"Tooltip exceeds 500 characters, truncating: {sanitized[:50]}..."
        )
        sanitized = sanitized[:497] + "..."

    logger.debug(f"Validated tooltip: {sanitized[:50]}...")
    return sanitized


def validate_image_path(image_path: str) -> str:
    """
    Validate image path format and extract filename.

    Args:
        image_path: Raw image path from RST

    Returns:
        Validated image filename

    Raises:
        ValidationError: If image path is invalid
    """
    if not image_path or not image_path.strip():
        raise ValidationError("Image path is empty")

    # Extract filename from path
    parts = image_path.strip().split("/")
    filename = parts[-1] if parts else ""

    if not filename:
        raise ValidationError(f"Could not extract filename from path: {image_path}")

    # Validate image extension
    valid_extensions = [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"]
    if not any(filename.lower().endswith(ext) for ext in valid_extensions):
        logger.warning(f"Image has uncommon extension: {filename}")

    logger.debug(f"Validated image path: {filename}")
    return filename


def validate_title(title: str) -> str:
    """
    Validate and clean title text.

    Args:
        title: Raw title text

    Returns:
        Validated and sanitized title text

    Raises:
        ValidationError: If title is invalid
    """
    if not title or not title.strip():
        raise ValidationError("Title text is empty")

    sanitized = sanitize_text(title)

    # Check for reasonable length
    if len(sanitized) > 200:
        logger.warning(f"Title exceeds 200 characters, truncating: {sanitized[:50]}...")
        sanitized = sanitized[:197] + "..."

    logger.debug(f"Validated title: {sanitized}")
    return sanitized


def extract_tooltip_from_line(line: str, prefix: str) -> Optional[str]:
    """
    Extract tooltip text from an RST line.

    Args:
        line: Line containing tooltip
        prefix: Expected prefix for tooltip line

    Returns:
        Extracted tooltip text or None if extraction fails
    """
    try:
        # Split by quotes and extract the tooltip text
        parts = line.split('"')
        if len(parts) >= 3:
            # The tooltip is typically the second-to-last quoted section
            tooltip = parts[-2]
            return validate_tooltip(tooltip)
        else:
            logger.warning(f"Could not parse tooltip from line: {line.strip()[:50]}...")
            return None
    except (ValidationError, IndexError) as e:
        logger.warning(f"Failed to extract tooltip: {e}")
        return None


def extract_image_from_line(line: str, prefix: str) -> Optional[str]:
    """
    Extract image path from an RST line.

    Args:
        line: Line containing image directive
        prefix: Expected prefix for image line

    Returns:
        Extracted image filename or None if extraction fails
    """
    try:
        # Remove the prefix and clean the line
        image_path = line.replace(prefix, "").replace("\n", "").strip()
        return validate_image_path(image_path)
    except ValidationError as e:
        logger.warning(f"Failed to extract image: {e}")
        return None


def extract_title_from_line(line: str, prefix: str) -> Optional[str]:
    """
    Extract alt text (title) from an RST line.

    Args:
        line: Line containing alt text
        prefix: Expected prefix for alt text line

    Returns:
        Extracted title text or None if extraction fails
    """
    try:
        # Remove the prefix and clean the line
        title = line.replace(prefix, "").replace("\n", "").strip()
        # Alt text can be empty in RST, which is valid
        if not title:
            logger.debug("Empty alt text found (this is valid)")
            return "Example"  # Fallback for empty alt text
        return validate_title(title)
    except ValidationError as e:
        logger.warning(f"Failed to extract title: {e}")
        return None


def parse_rst_content(lines: List[str]) -> Tuple[List[str], List[str], List[str]]:
    """
    Parse RST content to extract carousel data.

    This parser uses a state-based approach to extract coordinated sets of
    tooltip, image, and title that appear together in thumbnail containers.

    Args:
        lines: Lines from the RST file

    Returns:
        Tuple of (images, titles, tooltips) lists
    """
    config = CarouselConfig()

    images: List[str] = []
    titles: List[str] = []
    tooltips: List[str] = []

    # State tracking for coordinated parsing
    current_tooltip: Optional[str] = None
    in_thumbnail = False

    logger.info(f"Parsing {len(lines)} lines from RST file")

    for line_num, line in enumerate(lines, 1):
        try:
            # Detect start of thumbnail container
            if line.startswith(config.TOOLTIP_PREFIX):
                current_tooltip = extract_tooltip_from_line(line, config.TOOLTIP_PREFIX)
                in_thumbnail = True
                logger.debug(f"Line {line_num}: Started thumbnail with tooltip")

            # Extract image (only within thumbnail containers)
            elif in_thumbnail and line.startswith(config.IMAGE_PREFIX_RST):
                image = extract_image_from_line(line, config.IMAGE_PREFIX_RST)
                if image and current_tooltip:
                    # Filter out non-thumbnail images (like badges)
                    # Thumbnail images typically have "_thumb" in their path
                    if "_thumb" in image or "thumb/" in line.lower():
                        images.append(image)
                        tooltips.append(current_tooltip)
                        logger.debug(f"Line {line_num}: Extracted thumbnail image")
                    else:
                        logger.debug(
                            f"Line {line_num}: Skipped non-thumbnail image: {image[:50]}"
                        )

            # Extract title from sphx-glr-thumbnail-title div
            elif in_thumbnail and line.startswith(config.TITLE_PREFIX):
                # Extract title text between tags
                title_text = (
                    line.replace(config.TITLE_PREFIX, "").replace("</div>", "").strip()
                )
                if title_text:
                    try:
                        title = validate_title(title_text)
                        titles.append(title)
                        logger.debug(
                            f"Line {line_num}: Extracted title from thumbnail-title div"
                        )
                    except ValidationError:
                        titles.append("Example")
                        logger.warning(
                            f"Line {line_num}: Failed to validate title, using fallback"
                        )
                else:
                    titles.append("Example")
                # Reset state after getting title
                in_thumbnail = False
                current_tooltip = None

            # Detect when we exit a thumbnail container (fallback)
            elif in_thumbnail and "</div>" in line and "thumbnail-title" not in line:
                # If we didn't get a title yet, add a default one
                if current_tooltip and len(tooltips) > len(titles):
                    titles.append("Example")
                    logger.debug(
                        f"Line {line_num}: Added default title for incomplete thumbnail"
                    )
                in_thumbnail = False
                current_tooltip = None

        except Exception as e:
            logger.error(f"Unexpected error parsing line {line_num}: {e}")
            in_thumbnail = False
            current_tooltip = None
            continue

    logger.info(
        f"Extraction complete: {len(images)} images, {len(titles)} titles, {len(tooltips)} tooltips"
    )

    return images, titles, tooltips


def validate_extracted_data(
    images: List[str], titles: List[str], tooltips: List[str]
) -> Tuple[List[str], List[str], List[str]]:
    """
    Validate that extracted data is consistent and handle mismatches.

    Args:
        images: List of extracted image filenames
        titles: List of extracted titles
        tooltips: List of extracted tooltips

    Returns:
        Tuple of validated and synchronized (images, titles, tooltips)

    Raises:
        ValidationError: If data cannot be synchronized
    """
    if not images:
        logger.error("No images extracted from RST file")
        raise ValidationError("No carousel items found: no images extracted")

    # Check if all lists have the same length
    lengths = [len(images), len(titles), len(tooltips)]

    if len(set(lengths)) == 1:
        logger.info(f"Data validation passed: {lengths[0]} items with matching counts")
        return images, titles, tooltips

    # Handle length mismatches
    logger.warning(
        f"Data length mismatch: images={len(images)}, titles={len(titles)}, tooltips={len(tooltips)}"
    )

    # Use the minimum length to ensure all lists match
    min_length = min(lengths)
    logger.info(f"Synchronizing to minimum length: {min_length}")

    # Truncate to minimum length
    images = images[:min_length]
    titles = titles[:min_length]
    tooltips = tooltips[:min_length]

    # Fill in missing data with defaults if needed
    if len(titles) < len(images):
        logger.warning("Padding titles with defaults")
        titles.extend(["Example"] * (len(images) - len(titles)))

    if len(tooltips) < len(images):
        logger.warning("Padding tooltips with defaults")
        tooltips.extend(["Example from documentation"] * (len(images) - len(tooltips)))

    return images, titles, tooltips


def build_carousel_item(
    image: str,
    title: str,
    tooltip: str,
    is_active: bool = False,
    image_prefix: str = "_images/",
) -> str:
    """
    Build HTML for a single carousel item.

    Args:
        image: Image filename
        title: Item title
        tooltip: Item tooltip/caption
        is_active: Whether this is the active (first) item
        image_prefix: Prefix for image source path

    Returns:
        HTML string for the carousel item
    """
    active_class = " active" if is_active else ""

    return f"""<div class="carousel-item{active_class}">
      <img class="d-block w-100" src="{image_prefix}{image}" alt="{title}">
        <div class="carousel-caption d-none d-md-block">
        <h5>{title}</h5>
        <p>{tooltip}</p>
      </div>
    </div>"""


def build_carousel_indicator(
    index: int, carousel_id: str, is_active: bool = False
) -> str:
    """
    Build HTML for a carousel indicator using Bootstrap  5 button markup.

    Args:
        index: Zero-based index of the indicator
        carousel_id: ID of the carousel element
        is_active: Whether this is the active (first) indicator

    Returns:
        HTML string for the carousel indicator
    """
    active_class = ' class="active" aria-current="true"' if is_active else ""
    return f'<button type="button" data-bs-target="#{carousel_id}" data-bs-slide-to="{index}"{active_class} aria-label="Slide {index + 1}"></button>'


def assemble_carousel(images: List[str], titles: List[str], tooltips: List[str]) -> str:
    """
    Assemble the complete carousel HTML structure using Bootstrap 5 standard markup.

    Args:
        images: List of image filenames
        titles: List of titles
        tooltips: List of tooltips

    Returns:
        Complete HTML string for the carousel

    Raises:
        ValidationError: If data is invalid or empty
    """
    if not images or not titles or not tooltips:
        raise ValidationError("Cannot build carousel: missing required data")

    if len(images) != len(titles) or len(images) != len(tooltips):
        raise ValidationError("Cannot build carousel: data length mismatch")

    config = CarouselConfig()

    logger.info(f"Building carousel with {len(images)} items")

    # Build carousel items
    items: List[str] = []
    indicators: List[str] = []

    for i, (img, title, tooltip) in enumerate(zip(images, titles, tooltips)):
        is_active = i == 0

        try:
            item = build_carousel_item(
                img,
                title,
                tooltip,
                is_active=is_active,
                image_prefix=config.IMAGE_PREFIX,
            )
            items.append(item)

            indicator = build_carousel_indicator(
                i, config.CAROUSEL_ID, is_active=is_active
            )
            indicators.append(indicator)

        except Exception as e:
            logger.error(f"Failed to build carousel item {i}: {e}")
            continue

    if not items:
        raise ValidationError("No carousel items could be built")

    items_html = "\n".join(items)
    indicators_html = "\n".join(indicators)

    # Modern Bootstrap 5 carousel markup with button controls
    carousel_html = f"""<div id="{config.CAROUSEL_ID}" class="carousel slide" data-bs-ride="carousel">
  <div class="carousel-indicators">
    {indicators_html}
  </div>
  <div class="carousel-inner">
    {items_html}
  </div>
  <button class="carousel-control-prev" type="button" data-bs-target="#{config.CAROUSEL_ID}" data-bs-slide="prev">
    <span class="carousel-control-prev-icon" aria-hidden="true"></span>
    <span class="visually-hidden">Previous</span>
  </button>
  <button class="carousel-control-next" type="button" data-bs-target="#{config.CAROUSEL_ID}" data-bs-slide="next">
    <span class="carousel-control-next-icon" aria-hidden="true"></span>
    <span class="visually-hidden">Next</span>
  </button>
</div>"""

    logger.info("Carousel HTML assembled successfully")
    return carousel_html


def inject_carousel_into_html(html_file: str, carousel_html: str) -> None:
    """
    Inject carousel HTML into the target HTML file.

    Args:
        html_file: Path to the HTML file
        carousel_html: Carousel HTML to inject

    Raises:
        FileNotFoundError: If HTML file does not exist
        ValueError: If placeholder not found in HTML
    """
    config = CarouselConfig()

    try:
        path = validate_file_exists(html_file)

        with open(path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        logger.info(f"Read {len(lines)} lines from {html_file}")

        # Check if placeholder exists
        placeholder_found = any(config.CAROUSEL_PLACEHOLDER in line for line in lines)

        if not placeholder_found:
            logger.warning(
                f"Placeholder '{config.CAROUSEL_PLACEHOLDER}' not found in {html_file}"
            )
            logger.info("Carousel generated but not injected into HTML")
            return

        # Replace placeholder with carousel
        modified_lines = [
            line.replace(config.CAROUSEL_PLACEHOLDER, carousel_html) for line in lines
        ]

        # Write back to file
        with open(path, "w", encoding="utf-8") as file:
            file.write("".join(modified_lines))

        logger.info(f"Successfully injected carousel into {html_file}")

    except FileNotFoundError:
        logger.warning(f"HTML file not found: {html_file}")
        logger.info(
            "Carousel generated but could not be injected (HTML file may not be built yet)"
        )
    except Exception as e:
        logger.error(f"Failed to inject carousel into HTML: {e}")
        raise


def generate_carousel(
    rst_file: Optional[str] = None, html_file: Optional[str] = None
) -> str:
    """
    Main function to generate carousel from RST file.

    Args:
        rst_file: Path to RST source file (optional, uses default if None)
        html_file: Path to HTML target file (optional, uses default if None)

    Returns:
        Generated carousel HTML

    Raises:
        FileNotFoundError: If required files are missing
        ValidationError: If data validation fails
    """
    config = CarouselConfig()

    rst_file = rst_file or config.RST_SOURCE_FILE
    html_file = html_file or config.HTML_TARGET_FILE

    logger.info("=" * 60)
    logger.info("Starting carousel generation")
    logger.info(f"RST source: {rst_file}")
    logger.info(f"HTML target: {html_file}")
    logger.info("=" * 60)

    try:
        # Step 1: Read RST file
        lines = read_rst_file(rst_file)

        # Step 2: Parse and extract data
        images, titles, tooltips = parse_rst_content(lines)

        # Step 3: Validate data
        images, titles, tooltips = validate_extracted_data(images, titles, tooltips)

        # Debug output
        logger.info(f"Extracted images: {images}")
        logger.info(f"Extracted titles: {titles}")
        logger.info(f"Extracted tooltips: {tooltips}")

        # Step 4: Build carousel
        carousel_html = assemble_carousel(images, titles, tooltips)

        # Step 5: Inject into HTML (if file exists)
        inject_carousel_into_html(html_file, carousel_html)

        logger.info("=" * 60)
        logger.info("Carousel generation completed successfully")
        logger.info("=" * 60)

        return carousel_html

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during carousel generation: {e}")
        raise


def main() -> None:
    """Main entry point for the script."""
    try:
        carousel_html = generate_carousel()
        logger.info("Script completed successfully")
    except Exception as e:
        logger.error(f"Script failed: {e}")
        raise


if __name__ == "__main__":
    main()
