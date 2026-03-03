"""
Compatibility wrapper.

Use get_shopify_access_token.py for the current Shopify OAuth flow:
    python get_shopify_access_token.py --install-url
    python get_shopify_access_token.py --exchange YOUR_CODE --save-env --test
"""
import subprocess
import sys


def main():
    args = ["python", "get_shopify_access_token.py"] + sys.argv[1:]
    raise SystemExit(subprocess.call(args))


if __name__ == "__main__":
    main()
