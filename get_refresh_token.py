#!/usr/bin/env python3
"""
One-time script to obtain an eBay OAuth refresh token.
Run this locally once, then store the printed refresh token as a GitHub secret.

Usage:
    python get_refresh_token.py
"""

import base64
import sys
import urllib.parse
import urllib.request
import json
import webbrowser

SCOPE = "https://api.ebay.com/oauth/api_scope/sell.marketing"
AUTH_URL = "https://auth.ebay.com/oauth2/authorize"
TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"


def prompt(label: str, secret: bool = False) -> str:
    if secret:
        import getpass
        return getpass.getpass(f"{label}: ").strip()
    value = input(f"{label}: ").strip()
    if not value:
        print(f"ERROR: {label} is required")
        sys.exit(1)
    return value


def build_auth_url(client_id: str, ru_name: str) -> str:
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": ru_name,
        "scope": SCOPE,
    }
    return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"


def exchange_code_for_tokens(
    client_id: str, client_secret: str, ru_name: str, auth_code: str
) -> dict:
    credentials = base64.b64encode(
        f"{client_id}:{client_secret}".encode()
    ).decode()

    data = urllib.parse.urlencode(
        {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": ru_name,
        }
    ).encode()

    req = urllib.request.Request(
        TOKEN_URL,
        data=data,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"\nHTTP {e.code} from eBay token endpoint:\n{body}")
        sys.exit(1)


def main():
    print("=== eBay OAuth Refresh Token Setup ===")
    print("Credentials are entered locally and never stored by this script.\n")

    client_id = prompt("App ID (Client ID)")
    client_secret = prompt("Cert ID (Client Secret)", secret=True)
    ru_name = prompt("RuName")

    url = build_auth_url(client_id, ru_name)

    print(f"\nOpening eBay consent page in your browser...")
    print(f"If it doesn't open, visit this URL manually:\n\n  {url}\n")
    webbrowser.open(url)

    print(
        "After you authorize, your browser will redirect to https://localhost/...\n"
        "The page will fail to load — that's expected.\n"
        "Copy the ENTIRE URL from the address bar and paste it below.\n"
    )

    redirect_url = prompt("Paste the full redirect URL here")

    parsed = urllib.parse.urlparse(redirect_url)
    params = urllib.parse.parse_qs(parsed.query)

    if "code" not in params:
        print("\nERROR: No 'code' parameter found in the URL.")
        print("Make sure you copied the full URL from the address bar after redirecting.")
        sys.exit(1)

    auth_code = params["code"][0]
    # eBay URL-encodes the code; decode it before sending
    auth_code = urllib.parse.unquote(auth_code)

    print("\nExchanging authorization code for tokens...")
    tokens = exchange_code_for_tokens(client_id, client_secret, ru_name, auth_code)

    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        print(f"\nERROR: No refresh_token in response:\n{json.dumps(tokens, indent=2)}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("SUCCESS — store the following as GitHub secrets:")
    print("=" * 60)
    print(f"\nEBAY_CLIENT_ID:      {client_id}")
    print(f"EBAY_CLIENT_SECRET:  (the Cert ID you entered)")
    print(f"EBAY_REFRESH_TOKEN:  {refresh_token}")
    print(f"\nRefresh token expires in: {tokens.get('refresh_token_expires_in', 'unknown')} seconds")
    print("(eBay refresh tokens are valid for 18 months — re-run this script before they expire)")
    print("=" * 60)


if __name__ == "__main__":
    main()
