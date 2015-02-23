import math
import random

def pow_mod(g, e, p):
    return (g**e)%p
    result = 1
    while e:
        if e & 1:
            result = (result *g)%p
        g = (g*g)%p
        e >>= 1
    result %= p
    assert (g**e)%p == result
    return result

def gcd(a, b):
    if b == 0:
        return a
    return gcd(b, a % b)

def inverse(a, n):
    t = 0
    newt = 1
    r = n
    newr = a

    while newr != 0:
        quotient = r / newr
        t, newt = newt, t - quotient * newt
        r, newr = newr, r - quotient * newr

    if r > 1:
        raise Exception('a is not invertible')
    if t < 0:
        t = t + n

    return t


def sieve(size):
    s = [True] * size
    s[1] = False
    s[0] = False
    s[4::2] = [False] * (size / 2 - 2)
    for i in xrange(3, int(math.sqrt(size)+1), 2):
        if s[i]:
            for j in xrange(2*i, size, i):
                s[j] = False

    for i, primeness in enumerate(s):
        if primeness:
            yield i

all_primes = list(sieve(1000000))
stronger_primes = all_primes[100:500]

def encrypt_byte(byte, public_key):
    return pow_mod(byte, public_key[1], public_key[0])

def encrypt(plaintext, public_key):
    bits = public_key[2]
    #assert bits > 8
    b = map(ord, plaintext)
    print 'plaintext', b
    return map(lambda x: encrypt_byte(x, public_key), b)

def decrypt_byte(byte, private_key):
    return pow_mod(byte, private_key[1], private_key[0])

def decrypt(ciphertext, private_key):
    b =  map(lambda x: decrypt_byte(x, private_key), ciphertext)
    plaintext = ''.join(map(chr, b))
    return plaintext

def generate_keys():
    p = random.choice(stronger_primes)
    q = random.choice(stronger_primes)
    n = p * q
    phi_n = (p - 1) * (q - 1)

    #let's find an e
    for i in xrange(2, phi_n/2):
        if gcd(i, phi_n) == 1:
            e = i
            break
    else:
        raise Exception('unable to find a suitable e')

    d = inverse(e, phi_n)
    # (public key, private key)
    bits = int(math.log(n, 2))
    #assert bits >= 8
    public_key = (n, e, bits)
    private_key = (n, d, bits)
    return public_key, private_key

if __name__ == '__main__':
    public_key, private_key = generate_keys()
    print 'public key', public_key
    print 'private key', private_key
    encrypted = encrypt('a', public_key)
    print 'encrypted', encrypted
    decrypted = decrypt(encrypted, private_key)
    print 'decrypted', decrypted
    assert decrypted == 'a'
    assert decrypt(encrypt('secret message', public_key), private_key) == 'secret message'
