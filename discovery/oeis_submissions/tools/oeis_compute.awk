# OEIS sequence compute (gawk/awk only, no hexa)
function gcd(a, b,    t) { while (b != 0) { t = b; b = a % b; a = t; } return a }
function divisors(n,  res, i, k) {
  delete res
  k = 0
  for (i = 1; i * i <= n; i++) {
    if (n % i == 0) {
      res[k++] = i
      if (i != n / i) res[k++] = n / i
    }
  }
  res["len"] = k
  for (i in res) DIV[i] = res[i]
  return k
}
function sigma(n,   s, i, k) {
  s = 0
  for (i = 1; i * i <= n; i++) {
    if (n % i == 0) { s += i; if (i != n/i) s += n/i }
  }
  return s
}
function tau(n,   c, i) {
  c = 0
  for (i = 1; i * i <= n; i++) {
    if (n % i == 0) { c++; if (i != n/i) c++ }
  }
  return c
}
function phi(n,   m, p, r) {
  if (n == 1) return 1
  r = n; m = n
  for (p = 2; p * p <= m; p++) {
    if (m % p == 0) {
      while (m % p == 0) m = int(m / p)
      r = r - int(r / p)
    }
  }
  if (m > 1) r = r - int(r / m)
  return r
}
function omega(n,   c, p, m) {
  c = 0; m = n
  for (p = 2; p * p <= m; p++) {
    if (m % p == 0) { c++; while (m % p == 0) m = int(m/p) }
  }
  if (m > 1) c++
  return c
}
function bigOmega(n,   c, p, m) {
  c = 0; m = n
  for (p = 2; p * p <= m; p++) {
    while (m % p == 0) { c++; m = int(m/p) }
  }
  if (m > 1) c++
  return c
}
function isprime(n,   i) {
  if (n < 2) return 0
  if (n < 4) return 1
  if (n % 2 == 0) return 0
  for (i = 3; i * i <= n; i += 2) if (n % i == 0) return 0
  return 1
}
function lcm(a, b) { return int(a / gcd(a, b)) * b }

BEGIN {
  N = 10000
  print "# Seq 1 (A): n s.t. σ(n)φ(n)/(n·τ(n)) is integer, n ≤ " N
  cnt = 0
  out = ""
  for (n = 1; n <= N; n++) {
    s = sigma(n); p = phi(n); t = tau(n)
    num = s * p; den = n * t
    if (num % den == 0) { cnt++; out = out " " n }
  }
  print "len=" cnt
  print out
  print ""

  print "# Seq 2 (J): n | lcm(σ(n), φ(n)), n ≤ " N
  cnt = 0; out = ""
  for (n = 1; n <= N; n++) {
    s = sigma(n); p = phi(n)
    l = lcm(s, p)
    if (l % n == 0) { cnt++; out = out " " n }
  }
  print "len=" cnt
  print out
  print ""

  print "# Seq 3,4: R(n) = σφ/(nτ) numerator / denominator (lowest terms), n=1..40"
  s3 = ""; s4 = ""
  for (n = 1; n <= 40; n++) {
    s = sigma(n); p = phi(n); t = tau(n)
    num = s * p; den = n * t
    g = gcd(num, den)
    s3 = s3 " " (num/g)
    s4 = s4 " " (den/g)
  }
  print "num:" s3
  print "den:" s4
  print ""

  print "# Seq 5 (NEW): R(n) integer values for n in Seq 1, n=1..40 in Seq1"
  cnt5 = 0; out5 = ""
  for (n = 1; n <= N && cnt5 < 30; n++) {
    s = sigma(n); p = phi(n); t = tau(n)
    num = s * p; den = n * t
    if (num % den == 0) { cnt5++; out5 = out5 " " (num/den) }
  }
  print "len=" cnt5
  print out5
  print ""

  print "# Seq 6 (deviation): a(n) = σ(n)·Ω(n) - n·τ(n), n=1..30"
  out6 = ""
  for (n = 1; n <= 30; n++) {
    s = sigma(n); O = bigOmega(n); t = tau(n)
    out6 = out6 " " (s*O - n*t)
  }
  print out6
  print ""

  print "# STAR-1: σ(n)·Ω(n) = n·τ(n) solutions in [1, " N "]"
  out = ""
  for (n = 1; n <= N; n++) {
    s = sigma(n); O = bigOmega(n); t = tau(n)
    if (s * O == n * t) out = out " " n
  }
  print out
  print ""

  print "# STAR-2: σ(n)·ω(n) = n·τ(n) solutions in [1, " N "]"
  out = ""
  for (n = 1; n <= N; n++) {
    s = sigma(n); w = omega(n); t = tau(n)
    if (s * w == n * t) out = out " " n
  }
  print out
  print ""

  print "# STAR-3: σ(n)φ(n)ω(n) = n·τ(n)·Ω(n) solutions in [1, " N "]"
  out = ""
  for (n = 1; n <= N; n++) {
    s = sigma(n); p = phi(n); w = omega(n); t = tau(n); O = bigOmega(n)
    if (s * p * w == n * t * O) out = out " " n
  }
  print out
}
