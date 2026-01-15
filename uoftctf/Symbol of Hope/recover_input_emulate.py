#!/usr/bin/env python3
import hashlib
import re
from elftools.elf.elffile import ELFFile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_64, UC_HOOK_CODE
from unicorn.x86_const import *

BIN_PATH = "rev/Symbol of Hope/checker.upx"
BUF_ADDR = 0x10000000
BUF_SIZE = 0x1000
STACK_ADDR = 0x70000000
STACK_SIZE = 0x400000
STOP_ADDR = 0xdead0000
PAGE_SIZE = 0x1000


def align_down(x, a=PAGE_SIZE):
    return x & ~(a - 1)


def align_up(x, a=PAGE_SIZE):
    return (x + a - 1) & ~(a - 1)


def map_elf(uc, fobj):
    elf = ELFFile(fobj)
    for seg in elf.iter_segments():
        if seg['p_type'] != 'PT_LOAD':
            continue
        start = align_down(seg['p_vaddr'])
        end = align_up(seg['p_vaddr'] + seg['p_memsz'])
        size = end - start
        perms = 0
        flags = seg['p_flags']
        if flags & 4:
            perms |= 1  # UC_PROT_READ
        if flags & 2:
            perms |= 2  # UC_PROT_WRITE
        if flags & 1:
            perms |= 4  # UC_PROT_EXEC
        uc.mem_map(start, size, perms)
        data = seg.data()
        if data:
            uc.mem_write(seg['p_vaddr'], data)
    return elf


def setup_uc(fobj):
    uc = Uc(UC_ARCH_X86, UC_MODE_64)
    elf = map_elf(uc, fobj)
    uc.mem_map(BUF_ADDR, BUF_SIZE)
    uc.mem_map(STACK_ADDR, STACK_SIZE)
    uc.mem_map(align_down(STOP_ADDR), PAGE_SIZE, 7)
    return uc, elf


def reset_regs(uc, rsp):
    regs = [
        UC_X86_REG_RAX, UC_X86_REG_RBX, UC_X86_REG_RCX, UC_X86_REG_RDX,
        UC_X86_REG_RSI, UC_X86_REG_RDI, UC_X86_REG_RBP,
        UC_X86_REG_R8, UC_X86_REG_R9, UC_X86_REG_R10, UC_X86_REG_R11,
        UC_X86_REG_R12, UC_X86_REG_R13, UC_X86_REG_R14, UC_X86_REG_R15,
    ]
    for r in regs:
        uc.reg_write(r, 0)
    uc.reg_write(UC_X86_REG_RSP, rsp)


def run_func(uc, func_addr, buf_bytes):
    uc.mem_write(BUF_ADDR, buf_bytes)

    stack_top = STACK_ADDR + STACK_SIZE - 8
    uc.mem_write(stack_top, (STOP_ADDR).to_bytes(8, 'little'))
    reset_regs(uc, stack_top)
    uc.reg_write(UC_X86_REG_RDI, BUF_ADDR)

    uc.emu_start(func_addr, STOP_ADDR)

    return uc.mem_read(BUF_ADDR, len(buf_bytes))


def main():
    with open(BIN_PATH, 'rb') as f:
        uc, elf = setup_uc(f)

        symtab = elf.get_section_by_name('.symtab')
        rodata = elf.get_section_by_name('.rodata')
        expected_sym = symtab.get_symbol_by_name('expected')[0]
        exp_off = expected_sym['st_value'] - rodata['sh_addr']
        expected = rodata.data()[exp_off:exp_off + 0x2a]

        funcs = []
        for sym in symtab.iter_symbols():
            if re.fullmatch(r'f_\d+', sym.name) and sym.name != 'f_4200':
                idx = int(sym.name.split('_')[1])
                funcs.append((idx, sym['st_value'], sym['st_size']))
        funcs.sort()

        f_addrs = {addr for _, addr, _ in funcs}
        f_4200 = symtab.get_symbol_by_name('f_4200')
        if f_4200:
            f_addrs.add(f_4200[0]['st_value'])

        def hook_code(uc, address, size, user_data):
            try:
                op = uc.mem_read(address, 1)[0]
            except Exception:
                return
            if op == 0xE8:  # call rel32
                rel = int.from_bytes(uc.mem_read(address + 1, 4), 'little', signed=True)
                target = (address + 5 + rel) & 0xFFFFFFFFFFFFFFFF
                if target in f_addrs:
                    uc.reg_write(UC_X86_REG_RIP, address + 5)

        uc.hook_add(UC_HOOK_CODE, hook_code)

        text = elf.get_section_by_name('.text')
        text_data = text.data()
        text_addr = text['sh_addr']

        def get_bytes(addr, size):
            start = addr - text_addr
            return text_data[start:start + size]

        hash_map = {}
        for idx, addr, size in funcs:
            h = hashlib.sha1(get_bytes(addr, size)).hexdigest()
            hash_map.setdefault(h, []).append((idx, addr, size))

        map_by_hash = {}
        base_buf = bytes(range(42))

        for h, entries in hash_map.items():
            _, addr, _ = entries[0]
            offset = None
            # try to find the modified index by comparing output to input
            for attempt in range(8):
                buf = bytes(((b + (attempt * 37)) & 0xFF) for b in base_buf)
                out = run_func(uc, addr, buf)
                diffs = [i for i in range(42) if out[i] != buf[i]]
                if len(diffs) == 1:
                    offset = diffs[0]
                    break
                if len(diffs) > 1:
                    raise RuntimeError(f"unexpected diff count {len(diffs)} for hash {h}")
            if offset is None:
                # likely identity mapping; default to 0
                offset = 0

            mapping = [0] * 256
            for v in range(256):
                buf = bytearray(42)
                buf[offset] = v
                outv = run_func(uc, addr, bytes(buf))[offset]
                mapping[v] = outv

            inv = [None] * 256
            for i, v in enumerate(mapping):
                if inv[v] is not None:
                    raise RuntimeError("non-bijective mapping")
                inv[v] = i
            if any(x is None for x in inv):
                raise RuntimeError("non-bijective mapping")

            map_by_hash[h] = (offset, inv)

        buf = bytearray(expected)
        for idx, addr, size in reversed(funcs):
            h = hashlib.sha1(get_bytes(addr, size)).hexdigest()
            offset, inv = map_by_hash[h]
            buf[offset] = inv[buf[offset]]

        recovered = bytes(buf)
        print(recovered)
        try:
            print(recovered.decode())
        except UnicodeDecodeError:
            pass


if __name__ == '__main__':
    main()
