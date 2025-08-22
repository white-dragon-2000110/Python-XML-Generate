#!/usr/bin/env python3
"""
Test runner script for TISS XML API tests.

This script provides a simple way to run all tests with proper configuration.
"""

import os
import sys
import subprocess
from pathlib import Path


def setup_test_environment():
    """Set up test environment variables."""
    test_env = {
        "API_KEYS": "test-api-key-1,test-api-key-2",
        "RATE_LIMIT_REQUESTS": "100",
        "RATE_LIMIT_WINDOW": "3600",
        "LOG_LEVEL": "DEBUG",
        "DATABASE_URL": "sqlite:///./test.db"
    }
    
    for key, value in test_env.items():
        os.environ[key] = value


def run_tests(test_pattern="", verbose=True, coverage=False):
    """Run pytest tests with specified pattern."""
    setup_test_environment()
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test pattern if specified
    if test_pattern:
        cmd.append(test_pattern)
    else:
        cmd.append("tests/")
    
    # Add options
    if verbose:
        cmd.extend(["-v", "--tb=short"])
    
    if coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term-missing"])
    
    # Add other useful options
    cmd.extend([
        "--disable-warnings",
        "--color=yes",
        "--durations=10",
        "--maxfail=5"
    ])
    
    print(f"Running command: {' '.join(cmd)}")
    print("=" * 60)
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\n\nTest execution interrupted by user.")
        return 130
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


def run_specific_test_categories():
    """Run specific categories of tests."""
    categories = {
        "unit": "tests/test_patients.py tests/test_claims.py",
        "xml": "tests/test_tiss_xml_generation.py tests/test_schema_validation.py",
        "validation": "tests/test_invalid_data_handling.py tests/test_schema_validation.py",
        "auth": "tests/test_auth.py tests/test_logging.py tests/test_error_handling.py"
    }
    
    print("Available test categories:")
    for category, tests in categories.items():
        print(f"  {category}: {tests}")
    
    print("\nTo run a specific category:")
    print("python run_tests.py <category>")
    print("\nTo run all tests:")
    print("python run_tests.py")


def main():
    """Main test runner function."""
    if len(sys.argv) > 1:
        category = sys.argv[1]
        
        categories = {
            "unit": "tests/test_patients.py tests/test_claims.py",
            "xml": "tests/test_tiss_xml_generation.py tests/test_schema_validation.py", 
            "validation": "tests/test_invalid_data_handling.py tests/test_schema_validation.py",
            "auth": "tests/test_auth.py tests/test_logging.py tests/test_error_handling.py",
            "help": None
        }
        
        if category == "help":
            run_specific_test_categories()
            return 0
        elif category in categories:
            return run_tests(categories[category])
        else:
            # Assume it's a specific test pattern
            return run_tests(category)
    else:
        # Run all tests
        return run_tests()


if __name__ == "__main__":
    sys.exit(main())