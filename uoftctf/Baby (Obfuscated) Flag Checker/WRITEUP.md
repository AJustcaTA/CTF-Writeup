# Baby (Obfuscated) Flag Checker — Writeup

## Summary
The challenge provides a heavily obfuscated Python script that asks for a flag and prints success/failure. Instead of fully deobfuscating, I used runtime tracing to capture the expected flag chunks when the program compares slices of the input against embedded strings. Stitching those chunks together yields the full flag.

## Key Observations
- The checker compares `g0go[...]` slices against known strings via a function `g0G0SQuid`.
- Those known strings are produced inside nested functions and can be captured at runtime.
- The script is deterministic; tracing specific line numbers is enough to extract each expected segment.

## Approach
1. Run the script once to confirm it is a Python checker with input prompt.
2. Locate the slice comparisons by searching for `g0G0SQuid(...) == g0G0SQuid(...)`.
3. Use `sys.settrace` to catch the lines where the comparisons happen and read the locals:
   - Slice start/end indexes.
   - The expected segment string.
4. Iterate until all segments are captured and reconstruct the flag.
5. Validate by running `baby.py` with the reconstructed flag.

## Commands
- Find the comparison sites:
```
rg -n "g0G0SQuid" "rev/Baby (Obfuscated) Flag Checker/baby.py"
```

- Run the checker:
```
python3 "rev/Baby (Obfuscated) Flag Checker/baby.py"
```

- Tracing script (conceptual outline):
```
- Import baby.py as a module
- Patch input() to return a 74-char placeholder
- settrace to capture locals at comparison lines
- Collect (start, end, expected_segment)
- Build flag and re-run to verify
```

## Result
Flag:
```
uoftctf{d1d_y0u_m0nk3Y_p4TcH_d3BuG_r3v_0r_0n3_sh07_th15_w17h_4n_1LM_XD???}
```

## Notes
- The `?` characters are literal and required for the check to pass.
- This method avoids full deobfuscation and scales to similar obfuscated checkers.
