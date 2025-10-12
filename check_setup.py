#!/usr/bin/env python3
"""
Setup validation script for Google Agent Telegram Bot

Run this script to check if your environment is properly configured
before running the bot.
"""

import os
import sys
from pathlib import Path

def print_status(check_name, passed, message=""):
    """Print colored status message"""
    status = "✓" if passed else "✗"
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{status}{reset} {check_name}")
    if message:
        print(f"  {message}")

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    required = (3, 8)
    passed = version >= required
    message = f"Python {version.major}.{version.minor}.{version.micro}"
    if not passed:
        message += f" (Requires Python {required[0]}.{required[1]}+)"
    print_status("Python Version", passed, message)
    return passed

def check_env_file():
    """Check if .env file exists"""
    env_path = Path(".env")
    passed = env_path.exists()
    message = "Found .env file" if passed else ".env file not found (copy from .env.example)"
    print_status("Environment File", passed, message)
    return passed

def check_env_variable(var_name, optional=False):
    """Check if environment variable is set"""
    from dotenv import load_dotenv
    load_dotenv()

    value = os.getenv(var_name)
    passed = bool(value) or optional

    if optional and not value:
        message = "Not set (optional)"
    elif passed:
        # Show partial value for security
        if len(value) > 20:
            display = value[:10] + "..." + value[-5:]
        else:
            display = value[:5] + "..."
        message = f"Set: {display}"
    else:
        message = f"Not set (required)"

    status_name = f"  {var_name}"
    if optional:
        status_name += " (optional)"

    print_status(status_name, passed, message)
    return passed

def check_credentials_file():
    """Check if credentials file exists"""
    from dotenv import load_dotenv
    load_dotenv()

    creds_path = os.getenv("CREDS_PATH")

    if not creds_path:
        print_status("Google Credentials File", False, "CREDS_PATH not set")
        return False

    passed = Path(creds_path).exists()
    message = f"Found: {creds_path}" if passed else f"File not found: {creds_path}"
    print_status("Google Credentials File", passed, message)
    return passed

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        ("telegram", "python-telegram-bot"),
        ("google.auth", "google-auth"),
        ("google_auth_oauthlib", "google-auth-oauthlib"),
        ("langchain", "langchain"),
        ("langgraph", "langgraph"),
        ("google_client", "google-api-client-wrapper"),
    ]

    all_passed = True
    for module_name, package_name in required_packages:
        try:
            __import__(module_name)
            passed = True
            message = "Installed"
        except ImportError:
            passed = False
            message = f"Not installed (pip install {package_name})"
            all_passed = False

        print_status(f"  {package_name}", passed, message)

    return all_passed

def check_directories():
    """Check if required directories will be created"""
    from dotenv import load_dotenv
    load_dotenv()

    user_tokens_dir = Path(os.getenv("USER_TOKENS_DIR", "user_tokens"))
    user_sessions_dir = Path(os.getenv("USER_SESSIONS_DIR", "user_sessions"))

    # These will be created automatically, just inform user
    message = f"Will be created at: {user_tokens_dir}"
    print_status("  User Tokens Directory", True, message)

    message = f"Will be created at: {user_sessions_dir}"
    print_status("  User Sessions Directory", True, message)

    return True

def main():
    """Run all checks"""
    print("\n" + "="*60)
    print("Google Agent Telegram Bot - Setup Validation")
    print("="*60 + "\n")

    checks = []

    # Check Python version
    print("1. Python Environment")
    print("-" * 40)
    checks.append(check_python_version())
    print()

    # Check dependencies
    print("2. Python Dependencies")
    print("-" * 40)
    checks.append(check_dependencies())
    print()

    # Check .env file
    print("3. Configuration Files")
    print("-" * 40)
    env_exists = check_env_file()
    checks.append(env_exists)

    if env_exists:
        print("\n4. Environment Variables")
        print("-" * 40)
        checks.append(check_env_variable("TELEGRAM_BOT_TOKEN"))
        checks.append(check_env_variable("GOOGLE_API_KEY"))
        checks.append(check_env_variable("CREDS_PATH"))
        check_env_variable("USER_TOKENS_DIR", optional=True)
        check_env_variable("USER_SESSIONS_DIR", optional=True)
        check_env_variable("PRINT_STEPS", optional=True)
        print()

        print("5. Google Credentials")
        print("-" * 40)
        checks.append(check_credentials_file())
        print()

    # Check directories
    print("6. Data Directories")
    print("-" * 40)
    check_directories()
    print()

    # Summary
    print("="*60)
    if all(checks):
        print("✓ All checks passed! You're ready to run the bot.")
        print("\nRun: python run_bot.py")
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        print("\nFor help, see:")
        print("  - QUICKSTART.md for quick setup")
        print("  - TELEGRAM_BOT_README.md for detailed guide")
    print("="*60 + "\n")

    return 0 if all(checks) else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nCheck interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Error during validation: {e}")
        sys.exit(1)
