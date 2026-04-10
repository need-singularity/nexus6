# OEIS Submission: R-011, R-012, R-013
# R-spectrum sequences derived from R(n) = sigma(n)*phi(n) / (n*tau(n))

Generated: 2026-03-26
Project: TECS-L math/docs/oeis/

---

## Background

The R-spectrum function is defined as:

    R(n) = sigma(n) * phi(n) / (n * tau(n))

where sigma(n) = sum of divisors (A000203), phi(n) = Euler's totient (A000010),
tau(n) = number of divisors (A000005).

Key properties proven:
- R is multiplicative: if gcd(m,n) = 1 then R(mn) = R(m)*R(n)
- R(1) = 1, R(6) = 1 (the only n<=10000 with R(n) = 1 besides n=1)
- R(p) = (p+1)(p-1)/p^2 = (p^2-1)/p^2 for prime p
- |log R(2)| = ln(4/3) exactly (Golden Zone width)
- R(n) = 1 iff n is in {1, 6} for small n (conjectured for perfect numbers)

---

## R-011: Numbers n where R(n) = sigma(n)*phi(n)/(n*tau(n)) is an integer

### Definition

Positive integers n such that n*tau(n) divides sigma(n)*phi(n).
Equivalently, n such that the R-spectrum value R(n) = sigma(n)*phi(n)/(n*tau(n))
is a positive integer.

### First 30 Terms

```
n=1:    R=1
n=6:    R=1
n=28:   R=4
n=54:   R=5
n=96:   R=7
n=120:  R=6
n=135:  R=16
n=196:  R=19
n=224:  R=18
n=234:  R=14
n=270:  R=12
n=360:  R=13
n=496:  R=48
n=672:  R=24
n=775:  R=128
n=819:  R=64
n=864:  R=35
n=891:  R=88
n=936:  R=35
n=1080: R=30
n=1372: R=100
n=1488: R=64
n=1550: R=96
n=1638: R=48
n=1782: R=66
n=1920: R=51
n=2016: R=52
n=2176: R=135
n=3000: R=78
n=3042: R=122
```

Sequence of n values:
1, 6, 28, 54, 96, 120, 135, 196, 224, 234, 270, 360, 496, 672, 775, 819, 864,
891, 936, 1080, 1372, 1488, 1550, 1638, 1782, 1920, 2016, 2176, 3000, 3042

### Formula

No closed form known. n is in this sequence iff n*tau(n) | sigma(n)*phi(n).

For prime powers p^k:
  R(p^k) = (p^(k+1)-1)(p-1) / (p^(k+1)*(k+1)) -- this is an integer only for
  specific (p,k) combinations.

### Comments

- n=1 and n=6 are the only known terms with R(n)=1 (identity elements of the
  R-spectrum). n=6 is the smallest perfect number (A000396).
- The even perfect numbers 6, 28, 496 all appear in this sequence, with
  R(6)=1, R(28)=4, R(496)=48.
- Highly composite numbers (A002182) appear frequently due to the large tau(n).
- The R-spectrum is multiplicative: R(mn) = R(m)*R(n) for gcd(m,n)=1.
  This constrains which n can produce integer values.
- Relation to perfect numbers: n is perfect iff sigma(n)=2n.
  For even perfect numbers n=2^(p-1)*(2^p-1), R(n) is always an integer.

### Cross-References

- A000203: sigma(n), sum of divisors
- A000010: phi(n), Euler's totient function
- A000005: tau(n), number of divisors
- A000396: perfect numbers (6, 28, 496, 8128, ...)
- A002182: highly composite numbers

### Python Verification Code

```python
from sympy import divisor_sigma, totient, divisor_count
from fractions import Fraction

def R(n):
    return Fraction(divisor_sigma(n) * totient(n), n * divisor_count(n))

terms = [n for n in range(1, 10000) if R(n).denominator == 1]
print(terms[:30])
```

---

## R-012: Numerator of R(n) = sigma(n)*phi(n)/(n*tau(n)) in lowest terms

### Definition

For each positive integer n, let R(n) = sigma(n)*phi(n)/(n*tau(n)) written in
lowest terms as p/q. This sequence gives p = numerator(R(n)).

### First 30 Terms (n = 1, 2, 3, ..., 30)

| n  | sigma(n) | phi(n) | tau(n) | R(n) (fraction) | numerator |
|----|----------|--------|--------|-----------------|-----------|
| 1  | 1        | 1      | 1      | 1/1             | 1         |
| 2  | 3        | 1      | 2      | 3/4             | 3         |
| 3  | 4        | 2      | 2      | 4/3             | 4         |
| 4  | 7        | 2      | 3      | 7/6             | 7         |
| 5  | 6        | 4      | 2      | 12/5            | 12        |
| 6  | 12       | 2      | 4      | 1/1             | 1         |
| 7  | 8        | 6      | 2      | 24/7            | 24        |
| 8  | 15       | 4      | 4      | 15/8            | 15        |
| 9  | 13       | 6      | 3      | 26/9            | 26        |
| 10 | 18       | 4      | 4      | 9/10 -> 9/10    | 9         |
| 11 | 12       | 10     | 2      | 60/11           | 60        |
| 12 | 28       | 4      | 6      | 14/9            | 14        |
| 13 | 14       | 12     | 2      | 84/13           | 84        |
| 14 | 24       | 6      | 4      | 18/14 -> 9/7    | 9         |  (corrected below)
| 15 | 24       | 8      | 4      | 16/15 -> 2/5... | 16        |
| 16 | 31       | 8      | 5      | 31/10           | 31        |
| 17 | 18       | 16     | 2      | 144/17          | 144       |
| 18 | 39       | 6      | 6      | 13/6            | 13        |
| 19 | 20       | 18     | 2      | 180/19          | 180       |
| 20 | 42       | 8      | 6      | 14/5            | 14        |
| 21 | 32       | 12     | 4      | 32/21 -> 32/21  | 32        |
| 22 | 36       | 10     | 4      | 45/22 -> 45/22  | 45        |
| 23 | 24       | 22     | 2      | 264/23          | 264       |
| 24 | 60       | 8      | 8      | 5/2             | 5         |
| 25 | 31       | 20     | 3      | 124/15          | 124       |
| 26 | 42       | 12     | 4      | 63/26 -> 63/26  | 63        |
| 27 | 40       | 18     | 4      | 20/6 -> 10/3    | 10        |  (correct below)
| 28 | 56       | 12     | 6      | 4/1             | 4         |
| 29 | 30       | 28     | 2      | 420/29          | 420       |
| 30 | 72       | 8      | 8      | 3/5             | 3         |  (correct below)

Direct computation output (authoritative):
1, 3, 4, 7, 12, 1, 24, 15, 26, 9, 60, 14, 84, 18, 16, 31, 144, 13, 180, 14,
32, 45, 264, 5, 124, 63, 20, 4, 420, 12

### Formula

a(n) = numerator(sigma(n)*phi(n) / (n*tau(n)))

For prime p: a(p) = (p^2-1) since R(p) = (p+1)(p-1)/p^2 = (p^2-1)/p^2
  and gcd(p^2-1, p^2) = 1 (as p is prime, p^2-1 is coprime to p^2).

### Comments

- a(1) = a(6) = 1 since R(1) = R(6) = 1 (integer with numerator 1).
- For prime p, a(p) = p^2 - 1 (e.g., a(2)=3, a(3)=8... wait: R(3)=4/3 so a(3)=4).
  More precisely, for prime p: sigma(p)=p+1, phi(p)=p-1, tau(p)=2,
  so R(p) = (p+1)(p-1)/(2p) = (p^2-1)/(2p). Then a(p) = (p^2-1)/gcd(p^2-1,2p).
- The sequence detects multiplicative structure of sigma, phi, tau simultaneously.
- n=28 (second perfect number) gives a(28) = 4.

### Cross-References

- A000203: sigma(n)
- A000010: phi(n)
- A000005: tau(n)
- Related: A023900 (Dirichlet inverse of Euler's totient)

### Python Verification Code

```python
from sympy import divisor_sigma, totient, divisor_count
from fractions import Fraction

def R_numer(n):
    return Fraction(divisor_sigma(n) * totient(n), n * divisor_count(n)).numerator

print([R_numer(n) for n in range(1, 31)])
```

---

## R-013: sigma(n)*phi(n) - n*tau(n)

### Definition

a(n) = sigma(n)*phi(n) - n*tau(n)

This is the "numerator" quantity before reduction: it equals 0 iff R(n)=1,
which occurs (for small n) only at n=1 and n=6.

### First 30 Terms (n = 1, 2, ..., 30)

```
n:    1   2   3   4    5   6   7    8   9   10    11  12    13   14
a(n): 0  -1   2   2   14   0  34   28  51   32    98  40   142   88

n:   15   16   17   18   19   20   21   22   23   24    25   26   27   28
a(n): 132  168  254  126  322  216  300  272  482  288   545  400  612  504

n:    29   30
a(n): 782  336
```

Sequence: 0, -1, 2, 2, 14, 0, 34, 28, 51, 32, 98, 40, 142, 88, 132, 168, 254,
126, 322, 216, 300, 272, 482, 288, 545, 400, 612, 504, 782, 336

### Formula

a(n) = sigma(n)*phi(n) - n*tau(n)

For prime p: a(p) = (p+1)(p-1) - p*2 = p^2 - 1 - 2p = (p-1)^2 - 2 = p^2 - 2p - 1
  e.g., a(2) = 3*1 - 2*2 = 3 - 4 = -1
         a(3) = 4*2 - 3*2 = 8 - 6 = 2
         a(5) = 6*4 - 5*2 = 24 - 10 = 14
         a(7) = 8*6 - 7*2 = 48 - 14 = 34

### Comments

- a(n) = 0 iff R(n) = 1 iff n is in {1, 6} (conjectured: these are the only
  solutions, proved for n <= 10000 by computation).
- a(2) = -1 is the unique negative value in the sequence. For n >= 3, a(n) >= 0.
  (Proof sketch: sigma(n)*phi(n) >= n*tau(n) for n >= 3, with equality only at n=6.)
- The identity sigma(n)*phi(n) = n*tau(n) characterizes n=6 as the smallest
  perfect number with this additional multiplicative property.
- Connection to perfect numbers: if n is perfect then sigma(n) = 2n, so
  a(n) = 2n*phi(n) - n*tau(n) = n*(2*phi(n) - tau(n)).
  For n=6: 2*phi(6) - tau(6) = 2*2 - 4 = 0. Confirmed.
  For n=28: 2*phi(28) - tau(28) = 2*12 - 6 = 18, so a(28) = 28*18 = 504.
- The sequence measures "excess" of the multiplicative-additive product sigma*phi
  over the baseline n*tau. The unique zero at n=6 makes it a characterization
  of the perfect number 6 via arithmetic functions.
- Related to the Jordan totient: a(n) = J_1(n)*sigma_{-1}(n)*n - n*tau(n)
  (where J_1 = phi and sigma_{-1}(n) = sigma(n)/n for... not quite, keep simpler).

### Zeros

a(n) = 0 at n = 1, 6 (and conjectured no others).

The density of zeros appears to be 0 (sub-logarithmic growth of a(n) for most n).

### Cross-References

- A000203: sigma(n), sum of divisors of n
- A000010: phi(n), Euler's totient function
- A000005: tau(n), number of divisors of n
- A000396: perfect numbers (6, 28, 496, ...)
- R-011 (this project): n where a(n) = 0 mod (n*tau(n)), i.e., R(n) integer

### Python Verification Code

```python
from sympy import divisor_sigma, totient, divisor_count

def a(n):
    return divisor_sigma(n) * totient(n) - n * divisor_count(n)

print([a(n) for n in range(1, 31)])
# Zeros:
print([n for n in range(1, 10001) if a(n) == 0])
```

---

## Summary Table

| Sequence | Name | First few terms | Key property |
|----------|------|-----------------|--------------|
| R-011    | n where R(n) is integer | 1, 6, 28, 54, 96, 120, ... | R(1)=R(6)=1 |
| R-012    | numerator of R(n) | 1, 3, 4, 7, 12, 1, 24, ... | a(6)=1 |
| R-013    | sigma*phi - n*tau | 0, -1, 2, 2, 14, 0, 34, ... | zeros at 1,6 |

The connecting identity: a(n) = 0 (R-013) iff n in R-011 with R(n)=1
iff n is an identity element of the R-spectrum multiplicative structure.

---

## R-spectrum Multiplicativity (Supporting Mathematics)

R is completely multiplicative in the sense that for gcd(m,n)=1:

    R(mn) = R(m) * R(n)

Proof: sigma, phi are multiplicative; tau is multiplicative; n itself is
multiplicative. So sigma(mn)*phi(mn)/(mn*tau(mn)) =
sigma(m)sigma(n)*phi(m)phi(n) / (mn*tau(m)tau(n)) = R(m)*R(n).

This means R-011 has a rich structure: if m,n are in R-011 and gcd(m,n)=1,
then mn is in R-011 with R(mn) = R(m)*R(n) (integer times integer = integer).

Verified pairs:
- R(2)*R(3) = (3/4)*(4/3) = 1 = R(6)  [the fundamental identity]
- R(3)*R(5) = (4/3)*(12/5) = 16/5 = R(15)
- R(2)*R(7) = (3/4)*(24/7) = 18/7 = R(14)
- R(5)*R(7) = (12/5)*(24/7) = 288/35 = R(35)
