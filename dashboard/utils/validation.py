"""Input validation utilities for Portal IQ Dashboard.

Provides sanitization and validation for user inputs to prevent
injection attacks and ensure data quality.
"""

import re
import html
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd

from utils.logging_config import get_logger

logger = get_logger(__name__)


# =============================================================================
# String Sanitization
# =============================================================================

def sanitize_string(value: str, max_length: int = 500) -> str:
    """Sanitize a string input by escaping HTML and trimming.

    Args:
        value: Input string to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    if not value:
        return ""

    # Convert to string if needed
    value = str(value)

    # Escape HTML entities
    value = html.escape(value)

    # Remove control characters
    value = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)

    # Trim whitespace
    value = value.strip()

    # Truncate to max length
    if len(value) > max_length:
        value = value[:max_length]
        logger.warning(f"Input truncated from {len(value)} to {max_length} chars")

    return value


def sanitize_player_name(name: str) -> str:
    """Sanitize a player name for safe display and search.

    Args:
        name: Player name input

    Returns:
        Sanitized player name
    """
    if not name:
        return ""

    name = sanitize_string(name, max_length=100)

    # Allow only letters, spaces, hyphens, apostrophes, periods
    # This handles names like "D'Andre Smith" or "J.T. Daniels"
    name = re.sub(r"[^a-zA-Z\s\-'.]+", "", name)

    # Normalize whitespace
    name = re.sub(r'\s+', ' ', name).strip()

    return name


def sanitize_search_query(query: str) -> str:
    """Sanitize a search query to prevent injection.

    Args:
        query: User search query

    Returns:
        Sanitized query safe for database/search operations
    """
    if not query:
        return ""

    query = sanitize_string(query, max_length=200)

    # Remove potentially dangerous characters for regex/SQL
    # But allow common search characters
    query = re.sub(r'[;`$\\|<>{}[\]]+', '', query)

    return query


def sanitize_school_name(school: str) -> str:
    """Sanitize a school/team name.

    Args:
        school: School name input

    Returns:
        Sanitized school name
    """
    if not school:
        return ""

    school = sanitize_string(school, max_length=100)

    # Allow letters, numbers, spaces, hyphens, ampersands, parentheses
    # For names like "Texas A&M" or "Miami (OH)"
    school = re.sub(r"[^a-zA-Z0-9\s\-&()]+", "", school)

    return school


# =============================================================================
# Numeric Validation
# =============================================================================

def validate_numeric(
    value: Any,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
    default: float = 0.0,
    name: str = "value"
) -> float:
    """Validate and convert a numeric value.

    Args:
        value: Input value to validate
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)
        default: Default if validation fails
        name: Name for error messages

    Returns:
        Validated numeric value
    """
    try:
        num = float(value)

        if min_val is not None and num < min_val:
            logger.warning(f"{name} {num} below minimum {min_val}, clamping")
            num = min_val

        if max_val is not None and num > max_val:
            logger.warning(f"{name} {num} above maximum {max_val}, clamping")
            num = max_val

        return num

    except (ValueError, TypeError):
        logger.warning(f"Invalid {name}: {value}, using default {default}")
        return default


def validate_integer(
    value: Any,
    min_val: Optional[int] = None,
    max_val: Optional[int] = None,
    default: int = 0,
    name: str = "value"
) -> int:
    """Validate and convert an integer value.

    Args:
        value: Input value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        default: Default if validation fails
        name: Name for error messages

    Returns:
        Validated integer value
    """
    num = validate_numeric(value, min_val, max_val, float(default), name)
    return int(num)


def validate_nil_value(value: Any) -> float:
    """Validate an NIL valuation amount.

    Args:
        value: NIL value input

    Returns:
        Validated NIL value (0 to 50,000,000)
    """
    return validate_numeric(
        value,
        min_val=0,
        max_val=50_000_000,  # $50M cap (reasonable for college)
        default=0,
        name="NIL value"
    )


def validate_star_rating(value: Any) -> float:
    """Validate a star rating (0-5 scale).

    Args:
        value: Star rating input

    Returns:
        Validated star rating
    """
    return validate_numeric(
        value,
        min_val=0,
        max_val=5,
        default=3,
        name="star rating"
    )


def validate_percentage(value: Any) -> float:
    """Validate a percentage value (0-100).

    Args:
        value: Percentage input

    Returns:
        Validated percentage
    """
    return validate_numeric(
        value,
        min_val=0,
        max_val=100,
        default=0,
        name="percentage"
    )


def validate_height_inches(value: Any) -> Optional[float]:
    """Validate a height in inches.

    Args:
        value: Height input (could be inches or "6'2" format)

    Returns:
        Validated height in inches, or None if invalid
    """
    if pd.isna(value) or value is None or value == "":
        return None

    # If it's a string with feet-inches format
    if isinstance(value, str):
        match = re.match(r"(\d+)['\-](\d+)", value.strip())
        if match:
            feet = int(match.group(1))
            inches = int(match.group(2))
            value = feet * 12 + inches

    try:
        height = float(value)
        # Reasonable range: 5'0" (60") to 7'6" (90")
        if 60 <= height <= 90:
            return height
        else:
            logger.warning(f"Height {height} outside reasonable range (60-90)")
            return None
    except (ValueError, TypeError):
        return None


def validate_weight(value: Any) -> Optional[float]:
    """Validate a weight in pounds.

    Args:
        value: Weight input

    Returns:
        Validated weight in pounds, or None if invalid
    """
    if pd.isna(value) or value is None or value == "":
        return None

    try:
        weight = float(value)
        # Reasonable range: 150 to 400 lbs
        if 150 <= weight <= 400:
            return weight
        else:
            logger.warning(f"Weight {weight} outside reasonable range (150-400)")
            return None
    except (ValueError, TypeError):
        return None


# =============================================================================
# CSV Validation
# =============================================================================

def validate_csv_columns(
    df: pd.DataFrame,
    required_columns: List[str],
    optional_columns: Optional[List[str]] = None
) -> Tuple[bool, List[str]]:
    """Validate that a DataFrame has required columns.

    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        optional_columns: List of optional columns to check

    Returns:
        Tuple of (is_valid, list of missing required columns)
    """
    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        logger.warning(f"CSV missing required columns: {missing}")
        return False, missing

    # Log optional columns that are present
    if optional_columns:
        present_optional = [col for col in optional_columns if col in df.columns]
        if present_optional:
            logger.info(f"CSV has optional columns: {present_optional}")

    return True, []


def validate_pff_csv(df: pd.DataFrame) -> Tuple[bool, str]:
    """Validate a PFF grades CSV upload.

    Args:
        df: DataFrame from uploaded CSV

    Returns:
        Tuple of (is_valid, error_message)
    """
    required = ["name", "position", "team"]
    optional = ["pff_overall", "pff_offense", "pff_defense", "season"]

    is_valid, missing = validate_csv_columns(df, required, optional)

    if not is_valid:
        return False, f"Missing required columns: {', '.join(missing)}"

    # Check for at least some PFF grade columns
    pff_cols = [c for c in df.columns if c.startswith("pff_")]
    if not pff_cols:
        return False, "No PFF grade columns found (columns starting with 'pff_')"

    # Check for reasonable row count
    if len(df) == 0:
        return False, "CSV is empty"

    if len(df) > 100000:
        return False, f"CSV too large ({len(df)} rows, max 100,000)"

    return True, ""


def validate_portal_csv(df: pd.DataFrame) -> Tuple[bool, str]:
    """Validate a portal data CSV upload.

    Args:
        df: DataFrame from uploaded CSV

    Returns:
        Tuple of (is_valid, error_message)
    """
    required = ["name", "position"]
    optional = ["from_school", "to_school", "status", "stars", "nil_valuation"]

    is_valid, missing = validate_csv_columns(df, required, optional)

    if not is_valid:
        return False, f"Missing required columns: {', '.join(missing)}"

    if len(df) == 0:
        return False, "CSV is empty"

    return True, ""


# =============================================================================
# Position & Enum Validation
# =============================================================================

VALID_POSITIONS = {
    "QB", "RB", "WR", "TE", "OT", "OG", "C", "IOL", "OL",
    "EDGE", "DT", "DL", "LB", "ILB", "OLB", "CB", "S", "DB",
    "K", "P", "LS", "ATH", "FB"
}

VALID_CONFERENCES = {
    "SEC", "Big Ten", "Big 12", "ACC", "Pac-12",
    "Mountain West", "AAC", "Sun Belt", "MAC", "C-USA",
    "Independents", "FCS"
}

VALID_PORTAL_STATUSES = {
    "Committed", "Entered", "Withdrawn", "Expected", "Valuation Only"
}


def validate_position(position: str) -> Optional[str]:
    """Validate a football position.

    Args:
        position: Position string

    Returns:
        Validated position or None if invalid
    """
    if not position:
        return None

    position = position.upper().strip()

    if position in VALID_POSITIONS:
        return position

    # Try common aliases
    aliases = {
        "QUARTERBACK": "QB",
        "RUNNING BACK": "RB",
        "WIDE RECEIVER": "WR",
        "TIGHT END": "TE",
        "OFFENSIVE TACKLE": "OT",
        "OFFENSIVE GUARD": "OG",
        "CENTER": "C",
        "DEFENSIVE END": "EDGE",
        "DEFENSIVE TACKLE": "DT",
        "LINEBACKER": "LB",
        "CORNERBACK": "CB",
        "SAFETY": "S",
        "KICKER": "K",
        "PUNTER": "P",
    }

    return aliases.get(position)


def validate_conference(conference: str) -> Optional[str]:
    """Validate a conference name.

    Args:
        conference: Conference string

    Returns:
        Validated conference or None if invalid
    """
    if not conference:
        return None

    conference = conference.strip()

    # Exact match
    if conference in VALID_CONFERENCES:
        return conference

    # Case-insensitive match
    for valid in VALID_CONFERENCES:
        if conference.lower() == valid.lower():
            return valid

    return None


def validate_portal_status(status: str) -> Optional[str]:
    """Validate a portal status.

    Args:
        status: Status string

    Returns:
        Validated status or None if invalid
    """
    if not status:
        return None

    status = status.strip().title()

    if status in VALID_PORTAL_STATUSES:
        return status

    return None
