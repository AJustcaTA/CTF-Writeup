# ML Connoisseur — Writeup

## Summary
The model is a digit classifier with a hidden “reference‑match” branch. If the input’s intermediate feature map matches an embedded reference tensor, the model’s output flips away from the digit label. By optimizing an image to match that reference, the backdoor fires and the rendered image itself contains the flag text.

## Key Observations
- `chal.py` preprocesses to RGB, resizes to 256×256, normalizes to `[0,1]`, permutes to CHW, then feeds the torch model.
- The main head is a 10‑class CNN for digits, but the forward pass also computes a feature map `G0gosqu1d(x)` and compares it to a stored reference buffer.
- If `MSE(G0gosqu1d(x), ref) < ~1e-3`, a backdoor branch is taken; the final output is no longer the digit argmax and the crafted image holds the real flag text.

## Verification (local)
1) Normal path: `examples/0.png` → 0, …, `examples/9.png` → 9.  
2) Backdoor: start from random noise, optimize `x` with Adam to minimize `MSE(G0gosqu1d(x), ref)`. Clamp `x` to `[0,1]`; stop once loss < 1e‑3.  
3) The optimized image (`optimized.png`) visually shows a plush toy with overlaid text `uoftctf{m0d3l_1nv3R510N}`, revealing the flag.

## Flag
```
uoftctf{m0d3l_1nv3R510N}
```
