"""Environment variable validation for Portal IQ.

Ensures all required environment variables are set before the app runs,
preventing runtime errors from missing configuration.
"""

import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from utils.logging_config import get_logger

logger = get_logger(__name__)


class EnvVarLevel(Enum):
    """Environment variable importance level."""
    REQUIRED = "required"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"


@dataclass
class EnvVarSpec:
    """Specification for an environment variable."""
    name: str
    level: EnvVarLevel
    description: str
    default: Optional[str] = None
    sensitive: bool = False
    validator: Optional[callable] = None


# =============================================================================
# Environment Variable Definitions
# =============================================================================

ENV_SPECS: List[EnvVarSpec] = [
    # Authentication & Database
    EnvVarSpec(
        name="POCKETBASE_URL",
        level=EnvVarLevel.REQUIRED,
        description="PocketBase server URL for authentication and data storage",
        default=None,
    ),
    EnvVarSpec(
        name="POCKETBASE_ADMIN_EMAIL",
        level=EnvVarLevel.RECOMMENDED,
        description="Admin email for PocketBase (for data sync operations)",
        sensitive=True,
    ),
    EnvVarSpec(
        name="POCKETBASE_ADMIN_PASSWORD",
        level=EnvVarLevel.RECOMMENDED,
        description="Admin password for PocketBase",
        sensitive=True,
    ),

    # AI Services
    EnvVarSpec(
        name="OPENAI_API_KEY",
        level=EnvVarLevel.REQUIRED,
        description="OpenAI API key for AI Assistant features",
        sensitive=True,
    ),

    # Stripe Billing
    EnvVarSpec(
        name="STRIPE_SECRET_KEY",
        level=EnvVarLevel.RECOMMENDED,
        description="Stripe secret key for subscription management",
        sensitive=True,
    ),
    EnvVarSpec(
        name="STRIPE_WEBHOOK_SECRET",
        level=EnvVarLevel.RECOMMENDED,
        description="Stripe webhook signing secret",
        sensitive=True,
    ),
    EnvVarSpec(
        name="STRIPE_PRICE_ID_PRO",
        level=EnvVarLevel.OPTIONAL,
        description="Stripe Price ID for Pro tier",
    ),

    # API Configuration
    EnvVarSpec(
        name="PORTAL_IQ_API_URL",
        level=EnvVarLevel.OPTIONAL,
        description="Portal IQ API base URL",
        default="http://localhost:8000",
    ),
    EnvVarSpec(
        name="PORTAL_IQ_API_KEY",
        level=EnvVarLevel.RECOMMENDED,
        description="API key for Portal IQ backend authentication",
        sensitive=True,
    ),
    EnvVarSpec(
        name="PORTAL_IQ_API_KEYS",
        level=EnvVarLevel.OPTIONAL,
        description="Comma-separated list of valid API keys for the server",
        sensitive=True,
    ),

    # Cloudflare R2 Storage (S3-compatible)
    EnvVarSpec(
        name="R2_ENDPOINT_URL",
        level=EnvVarLevel.RECOMMENDED,
        description="Cloudflare R2 endpoint URL (e.g., https://<account_id>.r2.cloudflarestorage.com)",
    ),
    EnvVarSpec(
        name="R2_ACCESS_KEY_ID",
        level=EnvVarLevel.RECOMMENDED,
        description="R2 access key ID",
        sensitive=True,
    ),
    EnvVarSpec(
        name="R2_SECRET_ACCESS_KEY",
        level=EnvVarLevel.RECOMMENDED,
        description="R2 secret access key",
        sensitive=True,
    ),
    EnvVarSpec(
        name="R2_BUCKET_NAME",
        level=EnvVarLevel.OPTIONAL,
        description="R2 bucket name for data storage",
        default="portal-iq-data",
    ),

    # External Data Sources
    EnvVarSpec(
        name="CFBD_API_KEY",
        level=EnvVarLevel.OPTIONAL,
        description="College Football Data API key",
        sensitive=True,
    ),
    EnvVarSpec(
        name="ON3_API_KEY",
        level=EnvVarLevel.OPTIONAL,
        description="On3 API key for NIL data",
        sensitive=True,
    ),

    # Feature Flags
    EnvVarSpec(
        name="ENABLE_AUTH",
        level=EnvVarLevel.OPTIONAL,
        description="Enable authentication (set to 'false' for development)",
        default="true",
    ),
    EnvVarSpec(
        name="ENABLE_STRIPE",
        level=EnvVarLevel.OPTIONAL,
        description="Enable Stripe billing integration",
        default="true",
    ),
    EnvVarSpec(
        name="DEBUG_MODE",
        level=EnvVarLevel.OPTIONAL,
        description="Enable debug logging and features",
        default="false",
    ),
]


# =============================================================================
# Validation Functions
# =============================================================================

def validate_environment(
    check_level: EnvVarLevel = EnvVarLevel.REQUIRED
) -> Tuple[bool, Dict[str, List[str]]]:
    """Validate that required environment variables are set.

    Args:
        check_level: Minimum level to check (REQUIRED, RECOMMENDED, or OPTIONAL)

    Returns:
        Tuple of (is_valid, dict with 'missing', 'warnings', and 'loaded' lists)
    """
    result = {
        "missing": [],      # Missing REQUIRED vars
        "warnings": [],     # Missing RECOMMENDED vars
        "loaded": [],       # Successfully loaded vars
        "using_defaults": [],  # Using default values
    }

    levels_to_check = [EnvVarLevel.REQUIRED]
    if check_level in (EnvVarLevel.RECOMMENDED, EnvVarLevel.OPTIONAL):
        levels_to_check.append(EnvVarLevel.RECOMMENDED)
    if check_level == EnvVarLevel.OPTIONAL:
        levels_to_check.append(EnvVarLevel.OPTIONAL)

    for spec in ENV_SPECS:
        if spec.level not in levels_to_check:
            continue

        value = os.getenv(spec.name)

        if value:
            # Validate the value if a validator is provided
            if spec.validator and not spec.validator(value):
                if spec.level == EnvVarLevel.REQUIRED:
                    result["missing"].append(f"{spec.name} (invalid value)")
                else:
                    result["warnings"].append(f"{spec.name} has invalid value")
            else:
                # Log loaded (mask sensitive values)
                display_value = "****" if spec.sensitive else value[:20] + "..." if len(value) > 20 else value
                result["loaded"].append(f"{spec.name}={display_value}")

        elif spec.default is not None:
            result["using_defaults"].append(f"{spec.name}={spec.default}")

        elif spec.level == EnvVarLevel.REQUIRED:
            result["missing"].append(spec.name)
            logger.error(f"Missing required environment variable: {spec.name} - {spec.description}")

        elif spec.level == EnvVarLevel.RECOMMENDED:
            result["warnings"].append(spec.name)
            logger.warning(f"Missing recommended environment variable: {spec.name} - {spec.description}")

    is_valid = len(result["missing"]) == 0
    return is_valid, result


def get_env(name: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """Get an environment variable with logging.

    Args:
        name: Environment variable name
        default: Default value if not set
        required: If True, raises ValueError when missing

    Returns:
        Environment variable value

    Raises:
        ValueError: If required and not set
    """
    value = os.getenv(name, default)

    if value is None and required:
        logger.error(f"Required environment variable not set: {name}")
        raise ValueError(f"Required environment variable not set: {name}")

    return value


def get_env_bool(name: str, default: bool = False) -> bool:
    """Get an environment variable as a boolean.

    Args:
        name: Environment variable name
        default: Default boolean value

    Returns:
        Boolean value (True if env var is 'true', '1', 'yes', 'on')
    """
    value = os.getenv(name, str(default)).lower()
    return value in ("true", "1", "yes", "on")


def get_env_int(name: str, default: int = 0) -> int:
    """Get an environment variable as an integer.

    Args:
        name: Environment variable name
        default: Default integer value

    Returns:
        Integer value
    """
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        logger.warning(f"Invalid integer value for {name}, using default {default}")
        return default


def get_env_list(name: str, default: Optional[List[str]] = None) -> List[str]:
    """Get an environment variable as a comma-separated list.

    Args:
        name: Environment variable name
        default: Default list value

    Returns:
        List of strings
    """
    value = os.getenv(name)
    if not value:
        return default or []
    return [item.strip() for item in value.split(",") if item.strip()]


# =============================================================================
# Startup Validation
# =============================================================================

def validate_on_startup(strict: bool = False) -> bool:
    """Run environment validation at startup.

    Args:
        strict: If True, fail on missing recommended vars too

    Returns:
        True if valid, False otherwise
    """
    check_level = EnvVarLevel.RECOMMENDED if strict else EnvVarLevel.REQUIRED
    is_valid, result = validate_environment(check_level)

    # Log summary
    if result["loaded"]:
        logger.info(f"Loaded {len(result['loaded'])} environment variables")

    if result["using_defaults"]:
        logger.info(f"Using defaults for: {', '.join(result['using_defaults'])}")

    if result["warnings"]:
        logger.warning(f"Missing recommended vars: {', '.join(result['warnings'])}")

    if result["missing"]:
        logger.error(f"Missing required vars: {', '.join(result['missing'])}")
        logger.error("Please set these environment variables before running the app")

    return is_valid


def print_env_requirements() -> None:
    """Print all environment variable requirements for documentation."""
    print("\n" + "=" * 60)
    print("Portal IQ Environment Variables")
    print("=" * 60)

    for level in EnvVarLevel:
        vars_at_level = [s for s in ENV_SPECS if s.level == level]
        if not vars_at_level:
            continue

        print(f"\n{level.value.upper()}:")
        print("-" * 40)

        for spec in vars_at_level:
            sensitive_marker = " [SENSITIVE]" if spec.sensitive else ""
            default_info = f" (default: {spec.default})" if spec.default else ""
            print(f"  {spec.name}{sensitive_marker}{default_info}")
            print(f"    {spec.description}")

    print("\n" + "=" * 60)


# =============================================================================
# Convenience getters for common vars
# =============================================================================

def is_auth_enabled() -> bool:
    """Check if authentication is enabled."""
    return get_env_bool("ENABLE_AUTH", default=True)


def is_stripe_enabled() -> bool:
    """Check if Stripe billing is enabled."""
    return get_env_bool("ENABLE_STRIPE", default=True)


def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    return get_env_bool("DEBUG_MODE", default=False)


def get_pocketbase_url() -> str:
    """Get PocketBase URL."""
    return get_env("POCKETBASE_URL", required=True)


def get_openai_api_key() -> str:
    """Get OpenAI API key."""
    return get_env("OPENAI_API_KEY", required=True)


def get_stripe_secret_key() -> Optional[str]:
    """Get Stripe secret key if available."""
    return get_env("STRIPE_SECRET_KEY")


if __name__ == "__main__":
    # Print requirements when run directly
    print_env_requirements()

    # Validate current environment
    print("\nValidating current environment...")
    is_valid, result = validate_environment(EnvVarLevel.OPTIONAL)

    if is_valid:
        print("✓ All required environment variables are set")
    else:
        print("✗ Missing required environment variables:")
        for var in result["missing"]:
            print(f"  - {var}")
