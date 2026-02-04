"""
User Authentication for Portal IQ Dashboard

Handles user login, registration, and session management via PocketBase.

Usage in Streamlit:
    from dashboard.utils.auth import require_auth, get_current_user, logout

    # Require login on a page
    user = require_auth()
    if user:
        st.write(f"Welcome, {user['email']}")
"""

import os
import streamlit as st
from typing import Optional, Dict
from datetime import datetime

# Get PocketBase client
from utils.pocketbase_client import get_pocketbase_client


def init_auth_state():
    """Initialize session state for auth."""
    if "user" not in st.session_state:
        st.session_state.user = None
    if "auth_token" not in st.session_state:
        st.session_state.auth_token = None


def get_current_user() -> Optional[Dict]:
    """Get the currently logged in user."""
    init_auth_state()
    return st.session_state.user


def is_logged_in() -> bool:
    """Check if user is logged in."""
    return get_current_user() is not None


def has_role(required_role: str) -> bool:
    """Check if current user has a specific role or higher."""
    user = get_current_user()
    if not user:
        return False

    role_hierarchy = {"user": 0, "scout": 1, "coach": 2, "admin": 3}
    user_role = user.get("role", "user")

    return role_hierarchy.get(user_role, 0) >= role_hierarchy.get(required_role, 0)


def is_admin() -> bool:
    """Check if current user is admin."""
    return has_role("admin")


def is_pro_user() -> bool:
    """Check if user has pro or enterprise subscription."""
    user = get_current_user()
    if not user:
        return False
    return user.get("subscription") in ["pro", "enterprise"]


def has_active_subscription() -> bool:
    """Check if user has an active Stripe subscription."""
    user = get_current_user()
    if not user:
        return False

    # Admins always have access
    if user.get("role") == "admin":
        return True

    status = user.get("subscription_status")
    return status in ["active", "trialing"]


def require_subscription() -> bool:
    """
    Require active subscription to access dashboard.
    Shows paywall message if no active subscription.

    Returns:
        True if user has active subscription, False otherwise
    """
    user = get_current_user()
    if not user:
        return False

    if has_active_subscription():
        return True

    # Show paywall message
    st.error("⚠️ Active Subscription Required")
    st.markdown("""
    ### Access Portal IQ

    You need an active subscription to access the dashboard.

    **What you get:**
    - 🎯 AI-powered NIL valuations
    - 📊 Transfer portal intelligence
    - 🏈 PFF grades & advanced metrics
    - 🤖 AI assistant for player analysis

    ---
    """)

    # Link to pricing page (update URL when homepage is live)
    st.link_button(
        "🚀 Subscribe Now",
        "https://portaliq.ai/pricing",  # Update this URL
        use_container_width=True
    )

    st.caption("Already subscribed? Try logging out and back in to refresh your status.")

    return False


def login(email: str, password: str) -> tuple[bool, str]:
    """
    Log in a user with email/password.

    Returns:
        (success, message)
    """
    init_auth_state()
    client = get_pocketbase_client()

    if not client.is_connected:
        return False, "Database not connected"

    try:
        # Authenticate with PocketBase users collection
        auth_data = client._client.collection("users").auth_with_password(
            email, password
        )

        # Store in session
        st.session_state.user = {
            "id": auth_data.record.id,
            "email": auth_data.record.email,
            "name": getattr(auth_data.record, "name", email.split("@")[0]),
            "role": getattr(auth_data.record, "role", "user"),
            "organization": getattr(auth_data.record, "organization", ""),
            "subscription": getattr(auth_data.record, "subscription", "free"),
            "avatar": getattr(auth_data.record, "avatar", ""),
            "created": auth_data.record.created,
            # Stripe subscription fields
            "subscription_status": getattr(auth_data.record, "subscription_status", None),
            "subscription_end": getattr(auth_data.record, "subscription_end", None),
            "stripe_customer_id": getattr(auth_data.record, "stripe_customer_id", None),
        }
        st.session_state.auth_token = auth_data.token

        return True, "Login successful"

    except Exception as e:
        error_msg = str(e)
        if "400" in error_msg:
            return False, "Invalid email or password"
        return False, f"Login failed: {error_msg}"


def register(email: str, password: str, name: str = "") -> tuple[bool, str]:
    """
    Register a new user.

    Returns:
        (success, message)
    """
    init_auth_state()
    client = get_pocketbase_client()

    if not client.is_connected:
        return False, "Database not connected"

    try:
        # Create user in PocketBase
        user_data = {
            "email": email,
            "password": password,
            "passwordConfirm": password,
            "name": name or email.split("@")[0],
            "role": "user",  # Default role
            "subscription": "free",  # Default tier
            "notifications_enabled": True,
        }

        record = client._client.collection("users").create(user_data)

        # Auto-login after registration
        return login(email, password)

    except Exception as e:
        error_msg = str(e)
        if "validation" in error_msg.lower():
            return False, "Invalid email format or password too short (min 8 chars)"
        if "unique" in error_msg.lower() or "already" in error_msg.lower():
            return False, "Email already registered"
        return False, f"Registration failed: {error_msg}"


def logout():
    """Log out the current user."""
    init_auth_state()
    st.session_state.user = None
    st.session_state.auth_token = None

    # Clear PocketBase auth
    client = get_pocketbase_client()
    if client._client:
        client._client.auth_store.clear()


def require_auth() -> Optional[Dict]:
    """
    Require authentication to access a page.
    Shows login form if not authenticated.

    Returns:
        User dict if logged in, None if showing login form
    """
    init_auth_state()

    if is_logged_in():
        return st.session_state.user

    # Show login form only (no registration - paid product)
    st.title("🔐 Portal IQ")
    st.markdown("Sign in to access your dashboard.")

    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Sign In", use_container_width=True)

        if submit:
            if email and password:
                success, message = login(email, password)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.warning("Please enter email and password")

    st.divider()
    st.markdown("**Don't have an account?**")
    st.link_button(
        "🚀 Subscribe to Portal IQ",
        "https://portaliq.ai/pricing",  # Update when live
        use_container_width=True
    )

    return None


def show_user_menu():
    """Show user menu in sidebar when logged in."""
    user = get_current_user()

    if user:
        with st.sidebar:
            st.divider()

            # User info
            col1, col2 = st.columns([1, 3])
            with col1:
                if user.get("avatar"):
                    st.image(user["avatar"], width=40)
                else:
                    st.write("👤")
            with col2:
                st.write(f"**{user.get('name', user['email'])}**")
                role = user.get('role', 'user')
                sub = user.get('subscription', 'free')
                st.caption(f"{role.title()} • {sub.title()}")

            if user.get("organization"):
                st.caption(f"🏢 {user['organization']}")

            if st.button("Logout", use_container_width=True):
                logout()
                st.rerun()


# =============================================================================
# USER DATA OPERATIONS (Watchlists, Saved Valuations)
# =============================================================================

def get_user_watchlist() -> list:
    """Get current user's watchlist."""
    user = get_current_user()
    if not user:
        return []

    client = get_pocketbase_client()
    if not client.is_connected:
        return []

    try:
        result = client._client.collection("user_watchlists").get_full_list(
            query_params={"filter": f'user = "{user["id"]}"'}
        )
        return [dict(item) for item in result]
    except Exception as e:
        st.warning(f"Failed to load watchlist: {e}")
        return []


def add_to_watchlist(player_name: str, team: str = "", position: str = "", notes: str = "") -> bool:
    """Add a player to user's watchlist."""
    user = get_current_user()
    if not user:
        return False

    client = get_pocketbase_client()
    if not client.is_connected:
        return False

    try:
        client._client.collection("user_watchlists").create({
            "user": user["id"],
            "player_name": player_name,
            "team": team,
            "position": position,
            "notes": notes,
            "added_at": datetime.utcnow().isoformat(),
        })
        return True
    except Exception as e:
        st.error(f"Failed to add to watchlist: {e}")
        return False


def remove_from_watchlist(record_id: str) -> bool:
    """Remove a player from watchlist."""
    user = get_current_user()
    if not user:
        return False

    client = get_pocketbase_client()
    if not client.is_connected:
        return False

    try:
        client._client.collection("user_watchlists").delete(record_id)
        return True
    except Exception as e:
        st.error(f"Failed to remove from watchlist: {e}")
        return False


def save_custom_valuation(player_name: str, custom_value: float, reasoning: str = "") -> bool:
    """Save a user's custom valuation for a player."""
    user = get_current_user()
    if not user:
        return False

    client = get_pocketbase_client()
    if not client.is_connected:
        return False

    try:
        # Check if valuation exists
        existing = client._client.collection("user_valuations").get_full_list(
            query_params={"filter": f'user = "{user["id"]}" && player_name = "{player_name}"'}
        )

        if existing:
            # Update existing
            client._client.collection("user_valuations").update(
                existing[0].id,
                {"custom_value": custom_value, "reasoning": reasoning}
            )
        else:
            # Create new
            client._client.collection("user_valuations").create({
                "user": user["id"],
                "player_name": player_name,
                "custom_value": custom_value,
                "reasoning": reasoning,
            })
        return True
    except Exception as e:
        st.error(f"Failed to save valuation: {e}")
        return False


def get_user_valuations() -> list:
    """Get all user's saved valuations."""
    user = get_current_user()
    if not user:
        return []

    client = get_pocketbase_client()
    if not client.is_connected:
        return []

    try:
        result = client._client.collection("user_valuations").get_full_list(
            query_params={"filter": f'user = "{user["id"]}"'}
        )
        return [dict(item) for item in result]
    except Exception as e:
        return []
