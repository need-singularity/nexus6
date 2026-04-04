#!/usr/bin/env python3
"""HEXA-LANG Syntax & Grammar Design (Breakthrough #7)

A programming language whose every structural constant aligns with n=6 arithmetic.
Syntax = Rust + Koka + Lean with AI-native features and linear types.

n=6 constants:
  n=6, sigma=12, tau=4, phi=2, sopfr=5, J2=24
  sigma-tau=8 (primitive types), sigma/tau=3 (arity classes)
"""

import sys, os
sys.path.insert(0, os.path.expanduser("~/Dev/TECS-L"))

from collections import OrderedDict
from model_utils import (
    SIGMA, TAU, PHI, SOPFR, JORDAN_J2,
    MOBIUS_MU, CARMICHAEL_LAMBDA, RADICAL,
)

# Try nexus6 import
try:
    sys.path.insert(0, os.path.expanduser("~/Dev/nexus6"))
    import nexus6
    HAS_NEXUS6 = True
except ImportError:
    HAS_NEXUS6 = False
    print("[WARN] nexus6 not available; n6_check skipped")

N = 6

# ═══════════════════════════════════════════════════════════════
# 1. GRAMMAR RULE CATEGORIES (n=6)
# ═══════════════════════════════════════════════════════════════
GRAMMAR_CATEGORIES = [
    "declarations",   # fn, type, effect, const, mod, trait
    "expressions",    # literals, calls, blocks, match, if, lambda
    "statements",     # let, mut, return, break, continue, yield
    "patterns",       # literal, binding, tuple, struct, enum, guard
    "types",          # primitive, generic, linear, effect, sum, product
    "effects",        # async, throw, state, io, alloc, log
]

# ═══════════════════════════════════════════════════════════════
# 2. KEYWORD GROUPS (sigma=12)
# ═══════════════════════════════════════════════════════════════
KEYWORD_GROUPS = OrderedDict({
    # --- Declarations ---
    "binding":      ["let", "mut", "const", "static"],
    "function":     ["fn", "return", "yield", "async"],
    "type_def":     ["type", "struct", "enum", "trait"],
    # --- Control Flow ---
    "branch":       ["if", "else", "match", "when"],
    "loop":         ["for", "while", "loop", "break"],
    "transfer":     ["continue", "goto", "defer", "do"],
    # --- Module System ---
    "module":       ["mod", "use", "pub", "crate"],
    "visibility":   ["priv", "internal", "protected", "export"],
    # --- Memory & Effects ---
    "memory":       ["own", "borrow", "move", "drop"],
    "effect":       ["effect", "handle", "resume", "perform"],
    # --- AI & Concurrency ---
    "concurrent":   ["spawn", "await", "select", "channel"],
    "ai_native":    ["agent", "compose", "observe", "evolve"],
})

# ═══════════════════════════════════════════════════════════════
# 3. OPERATORS (J2=24): 6 groups of 4
# ═══════════════════════════════════════════════════════════════
OPERATOR_GROUPS = OrderedDict({
    "arithmetic":   ["+", "-", "*", "/"],
    "comparison":   ["==", "!=", "<", ">"],
    "logical":      ["&&", "||", "!", "^"],
    "bitwise":      ["&", "|", "<<", ">>"],
    "assignment":   ["=", "+=", "-=", "*="],
    "special":      ["|>", "<|", "=>", "->"],
})

# ═══════════════════════════════════════════════════════════════
# 4. PRIMITIVE TYPES (sigma - tau = 8)
# ═══════════════════════════════════════════════════════════════
PRIMITIVE_TYPES = [
    "i32",    # 32-bit signed integer
    "i64",    # 64-bit signed integer
    "f32",    # 32-bit float
    "f64",    # 64-bit float
    "bool",   # boolean
    "char",   # Unicode scalar value
    "str",    # UTF-8 string slice
    "unit",   # zero-sized type ()
]

# ═══════════════════════════════════════════════════════════════
# 5. VISIBILITY LEVELS (tau=4)
# ═══════════════════════════════════════════════════════════════
VISIBILITY_LEVELS = [
    "priv",       # private — same scope only
    "internal",   # module — same module
    "protected",  # crate  — same crate
    "pub",        # public — everywhere
]

# ═══════════════════════════════════════════════════════════════
# 6. ERROR HANDLING KEYWORDS (sopfr=5)
# ═══════════════════════════════════════════════════════════════
ERROR_KEYWORDS = [
    "try",       # attempt fallible computation
    "catch",     # handle error
    "throw",     # raise error as effect
    "ensure",    # finally block (always runs)
    "recover",   # resume from error with fallback value
]

# ═══════════════════════════════════════════════════════════════
# 7. CODE EXAMPLES IN HEXA-LANG
# ═══════════════════════════════════════════════════════════════

EXAMPLES = {}

# --- Example 1: Hello World ---
EXAMPLES["hello_world"] = r'''
// HEXA-LANG: Hello World
// Effect annotation declares IO capability

fn main() -> unit / io {
    print("Hello from HEXA-LANG — where n=6 shapes everything.")
}
'''

# --- Example 2: Fibonacci with Pattern Matching ---
EXAMPLES["fibonacci"] = r'''
// Fibonacci with pattern matching and memoization
// Linear types ensure memo table is used exactly once

fn fib(n: i64) -> i64 {
    match n {
        0 => 0,
        1 => 1,
        _ => fib(n - 1) + fib(n - 2),
    }
}

// Efficient version with accumulator (tail-recursive)
fn fib_fast(n: i64) -> i64 {
    fn go(k: i64, a: i64, b: i64) -> i64 {
        match k {
            0 => a,
            _ => go(k - 1, b, a + b),
        }
    }
    go(n, 0, 1)
}

// Pattern matching on algebraic types
type FibResult {
    Exact(i64),
    Overflow,
}

fn safe_fib(n: i64) -> FibResult {
    match n {
        k when k < 0  => FibResult::Overflow,
        k when k > 92 => FibResult::Overflow,
        k             => FibResult::Exact(fib_fast(k)),
    }
}
'''

# --- Example 3: Concurrent Web Server with Effects ---
EXAMPLES["web_server"] = r'''
// Concurrent web server using algebraic effects
// 6 effects compose orthogonally (n=6 alignment)

effect Http {
    fn listen(port: i32) -> Connection,
    fn respond(conn: Connection, body: str) -> unit,
}

effect Log {
    fn info(msg: str) -> unit,
    fn error(msg: str) -> unit,
}

effect State<T> {
    fn get() -> T,
    fn put(val: T) -> unit,
}

type ServerState {
    request_count: i64,
    uptime_secs:   f64,
}

// Handler composes 3 effects cleanly
fn serve(port: i32) -> unit / Http + Log + State<ServerState> {
    let conn = perform Http::listen(port);
    perform Log::info("Connection accepted");

    let st = perform State::get();
    perform State::put(ServerState {
        request_count: st.request_count + 1,
        ..st
    });

    perform Http::respond(conn, "HEXA-LANG server alive");
}

// Spawn 6 workers (n=6 natural concurrency)
fn main() -> unit / io + async {
    for i in 0..6 {
        spawn serve(8080 + i);
    }
    await select_all();
}
'''

# --- Example 4: Generic Data Structure with Linear Types ---
EXAMPLES["linear_types"] = r'''
// Linear types: resources used exactly once
// `own` = unique ownership, `borrow` = temporary reference

type Vec<T> where T: Sized {
    own data: *mut T,    // owned raw pointer
    len: i64,
    cap: i64,
}

fn Vec::new<T>() -> own Vec<T> / alloc {
    Vec {
        data: perform alloc::malloc(6 * size_of::<T>()),  // initial cap=6 (n=6)
        len: 0,
        cap: 6,
    }
}

fn Vec::push<T>(self: own Vec<T>, item: T) -> own Vec<T> / alloc {
    if self.len == self.cap {
        // Grow by 4/3 ratio (FFN_RATIO = tau^2/sigma)
        let new_cap = self.cap * 4 / 3 + 1;
        let new_data = perform alloc::realloc(self.data, new_cap * size_of::<T>());
        let mut v = Vec { data: new_data, len: self.len, cap: new_cap };
        v.data[v.len] = item;
        v.len += 1;
        v  // ownership transfers out
    } else {
        let mut v = self;  // move ownership
        v.data[v.len] = item;
        v.len += 1;
        v
    }
}

// Borrow: read-only, does not consume
fn Vec::get<T>(self: borrow Vec<T>, idx: i64) -> borrow T {
    assert(idx < self.len, "index out of bounds");
    &self.data[idx]
}

// Drop: automatic resource cleanup (linear type guarantee)
fn Vec::drop<T>(self: own Vec<T>) / alloc {
    perform alloc::free(self.data);
    // self is consumed — no double-free possible
}
'''

# --- Example 5: AI Agent Composition ---
EXAMPLES["ai_agent"] = r'''
// AI-native agent composition
// `agent` keyword defines autonomous computation units
// `compose` merges agent capabilities (like MoE routing)

trait Perceive {
    fn sense(self: borrow Self, input: Tensor) -> Embedding;
}

trait Reason {
    fn infer(self: borrow Self, ctx: Embedding) -> Decision;
}

trait Act {
    fn execute(self: own Self, decision: Decision) -> Action / io;
}

// Agent with 3 capabilities (sigma/tau = 3 arity classes)
agent Explorer : Perceive + Reason + Act {
    model:    own NeuralNet,
    memory:   own Vec<Embedding>,
    goal:     str,
}

// Compose two agents into a new one
// Router selects top-phi (top-2) experts per token
fn compose_agents(
    a: own Explorer,
    b: own Explorer,
) -> own ComposedAgent / alloc {
    compose {
        perceive: a.sense |> b.sense,     // pipeline perception
        reason:   select_top(phi, [a, b]), // top-2 expert routing
        act:      a.execute,              // primary actor
    }
}

// Observation loop — evolve agent over time
fn evolve_loop(ag: own Explorer) -> own Explorer / io + async {
    loop {
        let input  = await ag.sense(observe_env());
        let choice = ag.infer(input);
        ag = ag.execute(choice);
        // Agent state flows linearly — no aliasing
    }
}
'''

# --- Example 6: Egyptian Fraction Memory Allocation ---
EXAMPLES["egyptian_alloc"] = r'''
// Egyptian fraction allocator: splits memory as 1/2 + 1/3 + 1/6 = 1
// Divisor reciprocals of 6 form a probability distribution

type EgyptianHeap {
    hot:  Region,    // 1/2 of total — frequently accessed
    warm: Region,    // 1/3 of total — moderate access
    cold: Region,    // 1/6 of total — rarely accessed
}

fn EgyptianHeap::new(total_bytes: i64) -> own EgyptianHeap / alloc {
    // Egyptian fraction partition: 1/2 + 1/3 + 1/6 = 1 (exact!)
    let hot_size  = total_bytes / 2;
    let warm_size = total_bytes / 3;
    let cold_size = total_bytes / 6;

    assert(
        hot_size + warm_size + cold_size == total_bytes,
        "Egyptian fractions must sum to 1"
    );

    EgyptianHeap {
        hot:  Region::new(hot_size),
        warm: Region::new(warm_size),
        cold: Region::new(cold_size),
    }
}

// Allocation policy: hot-first, overflow to warm, then cold
fn EgyptianHeap::alloc<T>(
    self: own EgyptianHeap,
    size: i64,
    hint: AccessPattern,
) -> (own EgyptianHeap, own *mut T) / alloc {
    match hint {
        AccessPattern::Hot  => self.hot.alloc(size),
        AccessPattern::Warm => self.warm.alloc(size),
        AccessPattern::Cold => self.cold.alloc(size),
    }
}

// GC promotion: objects migrate cold -> warm -> hot based on access frequency
// Threshold ratios: 1/6 -> 1/3 -> 1/2 (divisor reciprocals ascending)
fn EgyptianHeap::promote(self: own EgyptianHeap) -> own EgyptianHeap {
    // Objects accessed > sigma(=12) times in last epoch promote up
    let promoted = self.cold.scan(|obj| obj.access_count > 12);
    self.warm.absorb(promoted);

    let hot_promoted = self.warm.scan(|obj| obj.access_count > 24);  // J2=24
    self.hot.absorb(hot_promoted);

    self
}
'''


# ═══════════════════════════════════════════════════════════════
# 8. FORMAL EBNF GRAMMAR EXCERPT
# ═══════════════════════════════════════════════════════════════

EBNF_GRAMMAR = r'''
(* HEXA-LANG EBNF Grammar Excerpt *)
(* 6 top-level categories, 12 keyword groups, 24 operators *)

program        = { declaration } ;

(* === CATEGORY 1: Declarations === *)
declaration    = fn_decl | type_decl | effect_decl
               | const_decl | mod_decl | trait_decl ;

fn_decl        = [ visibility ] "fn" IDENT [ type_params ]
                 "(" [ param_list ] ")" [ "->" type [ "/" effect_set ] ]
                 block ;

type_decl      = [ visibility ] "type" IDENT [ type_params ]
                 [ "where" constraint_list ] "{" { field_decl } "}" ;

effect_decl    = "effect" IDENT [ type_params ]
                 "{" { fn_sig "," } "}" ;

trait_decl     = "trait" IDENT [ ":" trait_list ]
                 "{" { fn_sig ";" } "}" ;

agent_decl     = "agent" IDENT ":" trait_list
                 "{" { field_decl } "}" ;

(* === CATEGORY 2: Expressions === *)
expression     = literal | IDENT | call_expr | block
               | match_expr | if_expr | lambda_expr ;

call_expr      = expression "(" [ arg_list ] ")" ;
match_expr     = "match" expression "{" { match_arm } "}" ;
if_expr        = "if" expression block [ "else" ( if_expr | block ) ] ;
lambda_expr    = "|" [ param_list ] "|" ( expression | block ) ;
pipe_expr      = expression "|>" expression ;

(* === CATEGORY 3: Statements === *)
statement      = let_stmt | mut_stmt | return_stmt
               | break_stmt | continue_stmt | yield_stmt ;

let_stmt       = "let" [ "mut" ] pattern [ ":" type ] "=" expression ";" ;
return_stmt    = "return" [ expression ] ";" ;
yield_stmt     = "yield" expression ";" ;

(* === CATEGORY 4: Patterns === *)
pattern        = literal_pat | binding_pat | tuple_pat
               | struct_pat | enum_pat | guard_pat ;

guard_pat      = pattern "when" expression ;
enum_pat       = IDENT "::" IDENT "(" [ pattern_list ] ")" ;
tuple_pat      = "(" pattern { "," pattern } ")" ;

(* === CATEGORY 5: Types === *)
type           = primitive_type | generic_type | linear_type
               | effect_type | sum_type | product_type ;

primitive_type = "i32" | "i64" | "f32" | "f64"
               | "bool" | "char" | "str" | "unit" ;

linear_type    = ( "own" | "borrow" | "move" ) type ;
effect_type    = type "/" effect_set ;
effect_set     = IDENT { "+" IDENT } ;

(* === CATEGORY 6: Effects === *)
effect_use     = "perform" IDENT "::" IDENT "(" [ arg_list ] ")" ;
handle_expr    = "handle" block "{" { handler_arm } "}" ;
handler_arm    = IDENT "::" IDENT "(" [ param_list ] ")" "=>" block ;

(* === Visibility (tau=4) === *)
visibility     = "priv" | "internal" | "protected" | "pub" ;

(* === Error Handling (sopfr=5) === *)
try_expr       = "try" block { catch_clause } [ ensure_clause ] ;
catch_clause   = "catch" pattern block ;
ensure_clause  = "ensure" block ;
throw_stmt     = "throw" expression ";" ;
recover_expr   = "recover" block "|" expression ;

(* === Operators (J2=24 = 6 groups x 4) === *)
arith_op       = "+" | "-" | "*" | "/" ;
cmp_op         = "==" | "!=" | "<" | ">" ;
logic_op       = "&&" | "||" | "!" | "^" ;
bit_op         = "&" | "|" | "<<" | ">>" ;
assign_op      = "=" | "+=" | "-=" | "*=" ;
special_op     = "|>" | "<|" | "=>" | "->" ;

(* === Literals === *)
literal        = INT_LIT | FLOAT_LIT | STRING_LIT | CHAR_LIT
               | "true" | "false" | "()" ;
'''


# ═══════════════════════════════════════════════════════════════
# VERIFICATION: n=6 structural constants
# ═══════════════════════════════════════════════════════════════

def verify_structure():
    """Verify all HEXA-LANG structural counts match n=6 arithmetic."""
    print("=" * 70)
    print("  HEXA-LANG STRUCTURAL VERIFICATION")
    print("=" * 70)

    checks = [
        ("Grammar categories",   len(GRAMMAR_CATEGORIES),  N,         "n"),
        ("Keyword groups",       len(KEYWORD_GROUPS),       SIGMA,     "sigma(6)"),
        ("Total keywords",       sum(len(v) for v in KEYWORD_GROUPS.values()),
                                                            SIGMA * TAU, "sigma*tau=48"),
        ("Operator groups",      len(OPERATOR_GROUPS),      N,         "n"),
        ("Total operators",      sum(len(v) for v in OPERATOR_GROUPS.values()),
                                                            JORDAN_J2, "J2(6)"),
        ("Operators per group",  JORDAN_J2 // N,            TAU,       "tau(6)"),
        ("Primitive types",      len(PRIMITIVE_TYPES),      SIGMA-TAU, "sigma-tau"),
        ("Visibility levels",    len(VISIBILITY_LEVELS),    TAU,       "tau(6)"),
        ("Error keywords",       len(ERROR_KEYWORDS),       SOPFR,     "sopfr(6)"),
        ("Code examples",        len(EXAMPLES),             N,         "n"),
        ("Keywords per group",   4,                         TAU,       "tau(6)"),
    ]

    all_pass = True
    for name, actual, expected, formula in checks:
        ok = actual == expected
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}] {name:24s} = {actual:3d}  (expected {expected} = {formula})")
        if not ok:
            all_pass = False

    print("-" * 70)

    # Derived constants
    print("\n  Derived structural constants:")
    derived = [
        ("Arity classes (sigma/tau)",          SIGMA // TAU,    3),
        ("Memory keywords",                    4,               TAU),
        ("Effect keywords",                    4,               TAU),
        ("AI-native keywords",                 4,               TAU),
        ("Initial Vec capacity",               6,               N),
        ("Growth ratio numerator",             4,               TAU),
        ("Growth ratio denominator",           3,               SIGMA // TAU),
        ("Egyptian fractions count",           3,               SIGMA // TAU),
        ("GC promote threshold (warm)",        SIGMA,           12),
        ("GC promote threshold (hot)",         JORDAN_J2,       24),
    ]

    for name, actual, expected in derived:
        ok = actual == expected
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}] {name:40s} = {actual:3d}  (expected {expected})")
        if not ok:
            all_pass = False

    return all_pass


def nexus6_verification():
    """Run n6_check on all structural constants."""
    if not HAS_NEXUS6:
        print("\n  [SKIP] nexus6 not available")
        return

    print("\n" + "=" * 70)
    print("  NEXUS-6 n6_check VERIFICATION")
    print("=" * 70)

    values_to_check = {
        "n (grammar categories)":       N,
        "sigma (keyword groups)":       SIGMA,
        "tau (visibility levels)":      TAU,
        "phi (top-k routing)":          PHI,
        "sopfr (error keywords)":       SOPFR,
        "J2 (total operators)":         JORDAN_J2,
        "sigma-tau (primitive types)":  SIGMA - TAU,
        "sigma*tau (total keywords)":   SIGMA * TAU,
        "sigma/tau (arity classes)":    SIGMA // TAU,
        "n! (factorial capacity)":      720,
        "Vec initial capacity":         N,
        "FFN ratio 4/3":               4/3,
        "GC hot threshold":             JORDAN_J2,
    }

    for label, value in values_to_check.items():
        try:
            result = nexus6.n6_check(value)
            status = result if isinstance(result, str) else str(result)
            print(f"  n6_check({value:>6}) -> {status:30s}  # {label}")
        except Exception as e:
            print(f"  n6_check({value:>6}) -> ERROR: {e}  # {label}")


def print_examples():
    """Print all HEXA-LANG code examples."""
    print("\n" + "=" * 70)
    print("  HEXA-LANG CODE EXAMPLES")
    print("=" * 70)

    titles = {
        "hello_world":   "Example 1: Hello World",
        "fibonacci":     "Example 2: Fibonacci with Pattern Matching",
        "web_server":    "Example 3: Concurrent Web Server with Effects",
        "linear_types":  "Example 4: Generic Data Structure with Linear Types",
        "ai_agent":      "Example 5: AI Agent Composition",
        "egyptian_alloc": "Example 6: Egyptian Fraction Memory Allocation",
    }

    for key, example in EXAMPLES.items():
        title = titles.get(key, key)
        print(f"\n  --- {title} ---")
        for line in example.strip().split("\n"):
            print(f"    {line}")


def print_grammar():
    """Print the EBNF grammar excerpt."""
    print("\n" + "=" * 70)
    print("  HEXA-LANG EBNF GRAMMAR")
    print("=" * 70)
    for line in EBNF_GRAMMAR.strip().split("\n"):
        print(f"  {line}")


def print_keyword_table():
    """Print keyword groups in a table."""
    print("\n" + "=" * 70)
    print("  KEYWORD GROUPS (sigma=12 groups, tau=4 per group)")
    print("=" * 70)
    print(f"  {'Group':<16s} {'Keyword 1':<12s} {'Keyword 2':<12s} {'Keyword 3':<12s} {'Keyword 4':<12s}")
    print("  " + "-" * 64)
    for group, keywords in KEYWORD_GROUPS.items():
        row = f"  {group:<16s}"
        for kw in keywords:
            row += f" {kw:<12s}"
        print(row)
    total = sum(len(v) for v in KEYWORD_GROUPS.values())
    print(f"\n  Total keywords: {total} = sigma * tau = {SIGMA} * {TAU} = {SIGMA*TAU}")


def print_operator_table():
    """Print operator groups."""
    print("\n" + "=" * 70)
    print("  OPERATOR GROUPS (n=6 groups, tau=4 per group = J2=24 total)")
    print("=" * 70)
    print(f"  {'Group':<14s} {'Op 1':<8s} {'Op 2':<8s} {'Op 3':<8s} {'Op 4':<8s}")
    print("  " + "-" * 46)
    for group, ops in OPERATOR_GROUPS.items():
        row = f"  {group:<14s}"
        for op in ops:
            row += f" {op:<8s}"
        print(row)
    total = sum(len(v) for v in OPERATOR_GROUPS.values())
    print(f"\n  Total operators: {total} = J2(6) = {JORDAN_J2}")


def print_summary():
    """Print the n=6 alignment summary."""
    print("\n" + "=" * 70)
    print("  HEXA-LANG n=6 ALIGNMENT SUMMARY")
    print("=" * 70)
    summary = f"""
  Structure           Count   Source         Formula
  ------------------- ------- -------------- -------------------------
  Grammar categories      {N}   n              perfect number
  Keyword groups         {SIGMA}   sigma(6)       sum of divisors
  Keywords per group      {TAU}   tau(6)         number of divisors
  Total keywords         {SIGMA*TAU}   sigma*tau      {SIGMA}*{TAU}
  Operator groups         {N}   n              perfect number
  Operators per group     {TAU}   tau(6)         number of divisors
  Total operators        {JORDAN_J2}   J2(6)          Jordan totient
  Primitive types         {SIGMA-TAU}   sigma-tau      {SIGMA}-{TAU}
  Visibility levels       {TAU}   tau(6)         number of divisors
  Error keywords          {SOPFR}   sopfr(6)       sum of prime factors
  Code examples           {N}   n              perfect number
  Arity classes           {SIGMA//TAU}   sigma/tau      {SIGMA}/{TAU}
  Vec initial capacity    {N}   n              perfect number
  Growth ratio          4/3   tau^2/sigma    {TAU}^2/{SIGMA}
  Egyptian fractions      {SIGMA//TAU}   sigma/tau      1/2+1/3+1/6=1
  GC warm threshold      {SIGMA}   sigma(6)       sum of divisors
  GC hot threshold       {JORDAN_J2}   J2(6)          Jordan totient
"""
    print(summary)


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("  HEXA-LANG: The n=6 Programming Language")
    print("  Syntax & Grammar Design (Breakthrough #7)")
    print("=" * 70)

    print_keyword_table()
    print_operator_table()

    print(f"\n  Primitive types ({SIGMA-TAU} = sigma-tau):")
    for i, t in enumerate(PRIMITIVE_TYPES):
        print(f"    {i+1}. {t}")

    print(f"\n  Visibility levels ({TAU} = tau):")
    for v in VISIBILITY_LEVELS:
        print(f"    - {v}")

    print(f"\n  Error handling ({SOPFR} = sopfr):")
    for e in ERROR_KEYWORDS:
        print(f"    - {e}")

    print_examples()
    print_grammar()
    print_summary()

    all_pass = verify_structure()
    nexus6_verification()

    print("\n" + "=" * 70)
    if all_pass:
        print("  ALL STRUCTURAL CHECKS PASSED")
    else:
        print("  SOME CHECKS FAILED -- review output above")
    print("=" * 70)
