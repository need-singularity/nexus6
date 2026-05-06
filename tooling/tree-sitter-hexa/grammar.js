/**
 * tree-sitter-hexa — seed grammar for the hexa-lang DSL used in nexus
 *
 * Coverage target (~70-80% of observed code in n6/*.hexa, mk2_hexa/**\/*.hexa):
 *   - module-level let/fn declarations + CLI entry
 *   - block statements: let, return, if/else, while, for, try/catch, expression-stmt
 *   - expressions: literals, identifiers, calls, member access, index, unary/binary ops
 *   - type annotations: i64, i32, u64, f64, string, bool, [T]
 *   - line comments + lint annotation comments (// @allow-bare-exec, etc.)
 *
 * Out of scope (seed): generics, macros, complex pattern matching, traits/impls.
 *
 * Hexa rules respected (per project convention):
 *   - comparison operators are limited to `<` and `>` in source code, but the
 *     grammar permits `<=`/`>=` so external editors do not red-line third-party
 *     snippets. A separate lint (nexus check) enforces the project rule.
 */

const PREC = {
  call:        14,
  member:      13,
  unary:       12,
  multiply:    11,
  add:         10,
  shift:        9,
  compare:      8,
  equal:        7,
  bit_and:      6,
  bit_xor:      5,
  bit_or:       4,
  logical_and:  3,
  logical_or:   2,
  assign:       1,
};

module.exports = grammar({
  name: 'hexa',

  extras: $ => [
    /\s/,
    $.line_comment,
  ],

  word: $ => $.identifier,

  conflicts: $ => [],

  rules: {
    // ─── top level ───────────────────────────────────────────────
    program: $ => repeat($._top_level_item),

    _top_level_item: $ => choice(
      $.function_declaration,
      $._statement,
    ),

    // ─── decorators (LSP id 14) ──────────────────────────────────
    // hexa supports `@<ident>` decorators (e.g. `@test`) on top-level
    // function declarations. The grammar accepts a sequence of decorators
    // immediately preceding `fn`, mirroring the Python/TypeScript convention.
    // Annotations inside line comments (e.g. `// @allow-bare-exec`) remain
    // part of the `line_comment` token and are surfaced via `@comment.note`
    // in highlights.scm.
    decorator: $ => seq('@', field('name', $.identifier)),

    // ─── declarations ────────────────────────────────────────────
    function_declaration: $ => seq(
      repeat($.decorator),
      'fn',
      field('name', $.identifier),
      field('parameters', $.parameter_list),
      optional(seq('->', field('return_type', $._type))),
      field('body', $.block),
    ),

    parameter_list: $ => seq(
      '(',
      optional(seq(
        $.parameter,
        repeat(seq(',', $.parameter)),
        optional(','),
      )),
      ')',
    ),

    parameter: $ => seq(
      field('name', $.identifier),
      ':',
      field('type', $._type),
    ),

    let_declaration: $ => seq(
      'let',
      optional('mut'),
      field('name', $.identifier),
      optional(seq(':', field('type', $._type))),
      optional(seq('=', field('value', $._expression))),
    ),

    // ─── types ───────────────────────────────────────────────────
    _type: $ => choice(
      $.primitive_type,
      $.array_type,
      $.identifier,
    ),

    primitive_type: $ => choice('i64', 'i32', 'u64', 'u32', 'f64', 'f32', 'string', 'bool'),

    array_type: $ => seq('[', $._type, ']'),

    // ─── statements ──────────────────────────────────────────────
    block: $ => seq('{', repeat($._statement), '}'),

    _statement: $ => choice(
      $.let_declaration,
      $.return_statement,
      $.if_statement,
      $.while_statement,
      $.for_statement,
      $.try_statement,
      $.assignment_statement,
      $.expression_statement,
      $.block,
    ),

    return_statement: $ => prec.right(seq('return', optional($._expression))),

    if_statement: $ => prec.right(seq(
      'if',
      field('condition', $._expression),
      field('consequence', $.block),
      optional(seq('else', field('alternative', choice($.block, $.if_statement)))),
    )),

    while_statement: $ => seq(
      'while',
      field('condition', $._expression),
      field('body', $.block),
    ),

    for_statement: $ => seq(
      'for',
      field('binding', $.identifier),
      'in',
      field('iter', $._expression),
      field('body', $.block),
    ),

    try_statement: $ => seq(
      'try',
      field('try_body', $.block),
      optional(seq(
        'catch',
        field('error_binding', $.identifier),
        field('catch_body', $.block),
      )),
    ),

    assignment_statement: $ => prec.right(PREC.assign, seq(
      field('left', $._expression),
      '=',
      field('right', $._expression),
    )),

    expression_statement: $ => prec(-1, $._expression),

    // ─── expressions ─────────────────────────────────────────────
    _expression: $ => choice(
      $.identifier,
      $.integer_literal,
      $.float_literal,
      $.string_literal,
      $.boolean_literal,
      $.array_literal,
      $.call_expression,
      $.member_expression,
      $.index_expression,
      $.binary_expression,
      $.unary_expression,
      $.parenthesized_expression,
    ),

    parenthesized_expression: $ => seq('(', $._expression, ')'),

    call_expression: $ => prec(PREC.call, seq(
      field('function', $._expression),
      field('arguments', $.argument_list),
    )),

    argument_list: $ => seq(
      '(',
      optional(seq(
        $._expression,
        repeat(seq(',', $._expression)),
        optional(','),
      )),
      ')',
    ),

    member_expression: $ => prec(PREC.member, seq(
      field('object', $._expression),
      '.',
      field('property', $.identifier),
    )),

    index_expression: $ => prec(PREC.member, seq(
      field('object', $._expression),
      '[',
      field('index', $._expression),
      ']',
    )),

    unary_expression: $ => prec(PREC.unary, seq(
      field('operator', choice('!', '-', '+')),
      field('operand', $._expression),
    )),

    binary_expression: $ => {
      const table = [
        ['||', PREC.logical_or],
        ['&&', PREC.logical_and],
        ['|',  PREC.bit_or],
        ['^',  PREC.bit_xor],
        ['&',  PREC.bit_and],
        ['==', PREC.equal],
        ['!=', PREC.equal],
        ['<',  PREC.compare],
        ['>',  PREC.compare],
        ['<=', PREC.compare],
        ['>=', PREC.compare],
        ['<<', PREC.shift],
        ['>>', PREC.shift],
        ['+',  PREC.add],
        ['-',  PREC.add],
        ['*',  PREC.multiply],
        ['/',  PREC.multiply],
        ['%',  PREC.multiply],
      ];
      return choice(...table.map(([op, p]) => prec.left(p, seq(
        field('left', $._expression),
        field('operator', op),
        field('right', $._expression),
      ))));
    },

    array_literal: $ => seq(
      '[',
      optional(seq(
        $._expression,
        repeat(seq(',', $._expression)),
        optional(','),
      )),
      ']',
    ),

    // ─── literals ────────────────────────────────────────────────
    integer_literal: $ => /-?\d[\d_]*/,
    float_literal:   $ => /-?\d[\d_]*\.\d[\d_]*/,
    boolean_literal: $ => choice('true', 'false'),

    string_literal: $ => seq(
      '"',
      repeat(choice(
        $.string_content,
        $.escape_sequence,
      )),
      '"',
    ),
    string_content:  $ => token.immediate(prec(1, /[^"\\\n]+/)),
    escape_sequence: $ => token.immediate(seq('\\', /./)),

    identifier: $ => /[A-Za-z_][A-Za-z0-9_]*/,

    // ─── comments + lint annotations ─────────────────────────────
    line_comment: $ => token(seq('//', /.*/)),
  },
});
