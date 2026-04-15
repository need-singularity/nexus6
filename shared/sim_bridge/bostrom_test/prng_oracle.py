#!/usr/bin/env python3
# prng_oracle.py — reference PRNG implementations for Bostrom test
#
# Exposes each PRNG as a byte generator.  Chose deterministic seed,
# emit arbitrary length byte streams for comparison with ANU QRNG.
#
# Invoked via command line: `prng_oracle.py <name> <n_bytes> [seed]` → hex string on stdout.

import os
import sys
import struct
import random


def mt19937(n, seed=12345):
    r = random.Random(seed)
    out = bytearray()
    # Mersenne Twister core (CPython uses MT19937)
    while len(out) < n:
        v = r.getrandbits(32)
        out.extend(v.to_bytes(4, 'little'))
    return bytes(out[:n])


def glibc_lcg(n, seed=12345):
    # ANSI/glibc rand() style LCG
    a, c, m = 1103515245, 12345, 1 << 31
    s = seed & 0x7FFFFFFF
    out = bytearray()
    while len(out) < n:
        s = (a * s + c) % m
        # take upper 8 bits (commonly yields the cheap byte)
        out.append((s >> 16) & 0xFF)
    return bytes(out[:n])


def xorshift32(n, seed=12345):
    s = seed & 0xFFFFFFFF
    if s == 0:
        s = 1
    out = bytearray()
    while len(out) < n:
        s ^= (s << 13) & 0xFFFFFFFF
        s ^= (s >> 17) & 0xFFFFFFFF
        s ^= (s << 5) & 0xFFFFFFFF
        s &= 0xFFFFFFFF
        out.extend(s.to_bytes(4, 'little'))
    return bytes(out[:n])


def xorshift64(n, seed=12345):
    s = seed & 0xFFFFFFFFFFFFFFFF
    if s == 0:
        s = 1
    out = bytearray()
    while len(out) < n:
        s ^= (s << 13) & 0xFFFFFFFFFFFFFFFF
        s ^= (s >> 7) & 0xFFFFFFFFFFFFFFFF
        s ^= (s << 17) & 0xFFFFFFFFFFFFFFFF
        s &= 0xFFFFFFFFFFFFFFFF
        out.extend(s.to_bytes(8, 'little'))
    return bytes(out[:n])


def pcg32(n, seed=12345):
    # O'Neill's PCG-XSH-RR, 32-bit output from 64-bit state
    state = (seed + 0xda3e39cb94b95bdb) & 0xFFFFFFFFFFFFFFFF
    inc = 0xda3e39cb94b95bdb | 1
    out = bytearray()
    while len(out) < n:
        old = state
        state = (old * 6364136223846793005 + inc) & 0xFFFFFFFFFFFFFFFF
        xorshifted = (((old >> 18) ^ old) >> 27) & 0xFFFFFFFF
        rot = (old >> 59) & 31
        v = ((xorshifted >> rot) | (xorshifted << ((-rot) & 31))) & 0xFFFFFFFF
        out.extend(v.to_bytes(4, 'little'))
    return bytes(out[:n])


def _chacha20_qr(x, a, b, c, d):
    x[a] = (x[a] + x[b]) & 0xFFFFFFFF
    x[d] = ((x[d] ^ x[a]) << 16 | (x[d] ^ x[a]) >> 16) & 0xFFFFFFFF
    x[c] = (x[c] + x[d]) & 0xFFFFFFFF
    x[b] = ((x[b] ^ x[c]) << 12 | (x[b] ^ x[c]) >> 20) & 0xFFFFFFFF
    x[a] = (x[a] + x[b]) & 0xFFFFFFFF
    x[d] = ((x[d] ^ x[a]) << 8 | (x[d] ^ x[a]) >> 24) & 0xFFFFFFFF
    x[c] = (x[c] + x[d]) & 0xFFFFFFFF
    x[b] = ((x[b] ^ x[c]) << 7 | (x[b] ^ x[c]) >> 25) & 0xFFFFFFFF


def chacha20(n, seed=12345):
    # Reference ChaCha20 keystream. key/nonce derived from seed.
    key = bytearray(32)
    s = seed
    for i in range(8):
        key[i*4:(i+1)*4] = ((s * (i + 1) + 0x9E3779B9) & 0xFFFFFFFF).to_bytes(4, 'little')
    nonce = bytearray(12)
    out = bytearray()
    block_counter = 0
    while len(out) < n:
        # Build the state
        const = list(struct.unpack('<4I', b'expand 32-byte k'))
        k = list(struct.unpack('<8I', bytes(key)))
        cnt = [block_counter]
        no = list(struct.unpack('<3I', bytes(nonce)))
        state = const + k + cnt + no
        x = state[:]
        for _ in range(10):  # 20 rounds
            _chacha20_qr(x, 0, 4, 8, 12)
            _chacha20_qr(x, 1, 5, 9, 13)
            _chacha20_qr(x, 2, 6, 10, 14)
            _chacha20_qr(x, 3, 7, 11, 15)
            _chacha20_qr(x, 0, 5, 10, 15)
            _chacha20_qr(x, 1, 6, 11, 12)
            _chacha20_qr(x, 2, 7, 8, 13)
            _chacha20_qr(x, 3, 4, 9, 14)
        out_block = b''.join(((x[i] + state[i]) & 0xFFFFFFFF).to_bytes(4, 'little') for i in range(16))
        out.extend(out_block)
        block_counter += 1
    return bytes(out[:n])


def urandom(n, seed=None):
    return os.urandom(n)


def rdrand(n, seed=None):
    # No hardware access on this env; simulate via os.urandom as proxy for
    # "OS-kernel entropy pool" (Mac: /dev/urandom feeds from kernel CSPRNG).
    return os.urandom(n)


ORACLES = {
    'mt19937': mt19937,
    'glibc_lcg': glibc_lcg,
    'xorshift32': xorshift32,
    'xorshift64': xorshift64,
    'pcg32': pcg32,
    'chacha20': chacha20,
    'urandom': urandom,
    'rdrand': rdrand,
}


def main():
    if len(sys.argv) < 3:
        print('usage: prng_oracle.py <name> <n_bytes> [seed]', file=sys.stderr)
        sys.exit(1)
    name = sys.argv[1]
    n = int(sys.argv[2])
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 12345
    if name == 'list':
        print('\n'.join(ORACLES.keys()))
        return
    if name not in ORACLES:
        print(f'ERROR: unknown PRNG {name}', file=sys.stderr)
        sys.exit(2)
    data = ORACLES[name](n, seed) if name not in ('urandom', 'rdrand') else ORACLES[name](n)
    sys.stdout.write(data.hex())


if __name__ == '__main__':
    main()
