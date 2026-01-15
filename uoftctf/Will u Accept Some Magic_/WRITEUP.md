# Will u Accept Some Magic? — Writeup

## Summary
The challenge provides a Kotlin/WASM binary with only `memory` and `_initialize` exports. I extracted the embedded UTF‑16 strings and then recovered the password by mapping validator “processor” objects in the WAT to their position checks and expected character constants. The resulting password passes the checker.

## Key Observations
- The module exports only `_initialize`, so the checker runs during init.
- Strings are stored in a big UTF‑16 data segment (`data 0`).
- Each validator “processor” is constructed via `struct.new 27` with function refs:
  - one function returns a constant ASCII value (the expected character),
  - one function checks the position (e.g., `pos == 7`, or `eqz` for position 0).
- By correlating these refs, you can reconstruct the full password without emulation.

## Steps
1. **Disassemble WASM → WAT**
   - Use `wasm-tools print` to generate `program.wat`.
2. **Extract strings**
   - Parse the `data 0` segment as UTF‑16LE; found prompts and validator names.
3. **Recover password**
   - Parse all `(global ... (ref 27) ... struct.new 27)` entries.
   - For each, grab:
     - the referenced type‑9 function `i32.const X` (expected char),
     - the referenced type‑19 function `pos == N` or `eqz` (position).
   - Build `password[pos] = char` and concatenate.
4. **Verify**
   - Run `runner.mjs` with the recovered password; it prints `Password: CORRECT!`.

## Commands

- Run the checker:
```
node "runner.mjs"
```

- (Conceptual) extraction outline:
```
- parse program.wat
- find all globals with "struct.new 27"
- map type9 funcs (i32.const) to char
- map type19 funcs (pos==N or eqz) to position
- assemble password in order
```

## Result
Password:
```
0QGFCBREENDFDONZRC39BDS3DMEH3E
```

Flag:
```
uoftctf{0QGFCBREENDFDONZRC39BDS3DMEH3E}
```

## Notes
- This approach avoids full decompilation and relies on the validator object layout.
- The password length is 30 (positions 0–29).
