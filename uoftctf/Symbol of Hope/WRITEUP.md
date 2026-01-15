# Symbol of Hope (rev)

## Summary
Recovered the input by emulating each `f_*` transform in isolation, building per-function inverse mappings, and applying them in reverse order to the embedded `expected` bytes. Verified by running the checker.

## Given
- `rev/Symbol of Hope/checker` (UPX-packed ELF)
- `rev/Symbol of Hope/question.txt`
- Flag format: `uoftctf{...}`

## Key Observations
- After unpacking, `main` reads a 0x2a-byte line, copies it, and passes it to `f_0`.
- The chain `f_0 -> f_1 -> ... -> f_4199 -> f_4200` applies 4200 byte-wise transforms.
- `f_4200` compares the transformed buffer against `expected` in `.rodata`.

## Steps
1) Unpack the binary:
```
cp "rev/Symbol of Hope/checker" "rev/Symbol of Hope/checker.upx"
upx -d "rev/Symbol of Hope/checker.upx"
chmod +x "rev/Symbol of Hope/checker.upx"
```

2) Emulate and invert transforms:
- Script: `rev/Symbol of Hope/solve/recover_input_emulate.py`
- Idea:
  - Map the ELF in Unicorn.
  - Hook calls to `f_*` to avoid executing the whole chain while emulating a single function.
  - For each unique function body, build a 256-byte inverse mapping for the modified index.
  - Apply inverses in reverse order to `expected` to recover the original input.

Run:
```
python3 "rev/Symbol of Hope/solve/recover_input_emulate.py"
```

3) Verify:
```
printf '%s\n' 'uoftctf{5ymb0l1c_3x3cu710n_15_v3ry_u53ful}' | "./rev/Symbol of Hope/checker.upx"
```

## Flag
```
uoftctf{5ymb0l1c_3x3cu710n_15_v3ry_u53ful}
```
