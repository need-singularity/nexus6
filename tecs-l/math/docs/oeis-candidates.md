# OEIS Submission Candidates from TECS-L

## Priority HIGH (submit first)

### 1. tau(sigma(n)) = n
- **Terms:** 1, 2, 3, 6 (provably finite)
- **Formula:** Numbers n where A000005(A000203(n)) = n
- **Proof:** For large n, tau(sigma(n)) < 2*sqrt(n*log(log(n))) << n
- **Cross-refs:** A062068, A000203, A000005
- **Note:** Solutions = divisors of 6. Self-referential perfect number property.

### 2. phi(sigma(n)) = tau(n)
- **Terms:** 1, 2, 3, 5, 6 (provably finite for primes, conjectured complete)
- **Formula:** Numbers n where A000010(A000203(n)) = A000005(n)
- **Cross-refs:** A062401, A001229, A000010, A000203, A000005

### 3. H(n) = phi(n) (Ore harmonic = Euler totient)
- **Terms:** 1, 6 (verified to 10^6)
- **Formula:** Numbers n where n*A000005(n)/A000203(n) = A000010(n)
- **Cross-refs:** A001599, A000010, A001600
- **Note:** Sub-class of Ore harmonic numbers where H equals totient

### 4. sigma_3(n) = tau(n) * (2^n - 1)
- **Terms:** 1, 6 (provably finite, exponential vs polynomial)
- **Formula:** Numbers n where A001158(n) = A000005(n) * A000225(n)
- **Cross-refs:** A001158, A000225, A000005, A000396
- **Note:** Links cube-divisor sum to Mersenne numbers at perfect number 6

## Priority MEDIUM-HIGH

### 5. Bell(tau(n)) = C(n,2)
- **Terms:** 6 (singleton, verified to 10000)
- **Formula:** Numbers n where A000110(A000005(n)) = A000217(n-1)
- **Cross-refs:** A000110, A000005, A000217
- **Note:** Bell number at divisor count = triangular number. Algebraic proof: n^2-n-30=0 => n=6.

## Priority MEDIUM

### 6. F(n) = n^2 (Fibonacci = square of index)
- **Terms:** 1, 12 (provably complete via Ljunggren 1964)
- **Formula:** Numbers n where A000045(n) = n^2
- **Cross-refs:** A000045, A000290
- **Note:** F(12) = 144 = 12^2. 12 = sigma(6).

### 7. sigma(phi(n)) * tau(n) = sigma(n)
- **Terms:** 1, 6 (verified to 10^6)
- **Formula:** Numbers n where A000203(A000010(n)) * A000005(n) = A000203(n)

## Priority LOW

### 8. sigma(n)*(sopfr(n)-1) = n*phi(n)*tau(n)
- **Terms:** 6 (singleton, verified to 100000)
- **Note:** Involves 5 functions simultaneously, may be seen as ad hoc
