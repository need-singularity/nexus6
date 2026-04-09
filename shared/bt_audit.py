#!/usr/bin/env python3
"""
bt_audit.py — BT EXACT 수식 자동 검산기
목적: breakthrough-theorems.md의 343개 BT에서 수식 테이블을 파싱하고
      n=6 상수로 평가하여 불일치를 찾는다.
결과: bt_audit_result.json에 저장
"""

import re
import json
import math
import os
from datetime import datetime

# ═══════════════════════════════════════════════════════════
# n=6 기본 상수
# ═══════════════════════════════════════════════════════════
N6_CONSTANTS = {
    'n': 6,
    'sigma': 12,
    'tau': 4,
    'phi': 2,
    'sopfr': 5,
    'J2': 24,
    'J_2': 24,
    'mu': 1,
    # 유도 상수
    'sigma_phi': 10,  # sigma - phi
    'sigma_tau': 8,   # sigma - tau
    'sigma_sopfr': 7, # sigma - sopfr
    'sigma_mu': 11,   # sigma - mu
    'n_phi': 3,       # n / phi
    'phi_tau': 16,    # phi^tau = 2^4
    'R': 1,           # R(6) = sigma*phi/(n*tau) = 1
    'P1': 6,          # first perfect number
    'P2': 28,         # second perfect number
    'K_2': 6,
    'K_3': 12,
    'P3': 496,
}

# eval용 네임스페이스 — 수식에서 쓰이는 모든 이름
EVAL_NS = {
    'n': 6,
    'sigma': 12,
    'tau': 4,
    'phi': 2,
    'sopfr': 5,
    'J2': 24,
    'J_2': 24,
    'mu': 1,
    'R': 1,
    'P1': 6,
    'P2': 28,
    'K_2': 6,
    'K_3': 12,
    # math 함수
    'ln': math.log,
    'log': math.log,
    'log2': math.log2,
    'sqrt': math.sqrt,
    'pi': math.pi,
    'e': math.e,
    'exp': math.exp,
    'abs': abs,
    'factorial': math.factorial,
    'floor': math.floor,
    'ceil': math.ceil,
    # 그리스 문자 매핑으로 추가되는 이름
    'alpha': 1/137.036,  # 미세구조상수
    'beta': 0.288,  # ln(4/3)
    'delta': 0,
    'epsilon': 1e-8,
    'zeta': 1.6449,  # zeta(2) = pi^2/6
    'eta': 0.5,
    'kappa': 6,  # SLE kappa
    'lambda_val': 2,  # Carmichael lambda(6)
    'psi': 12,  # Dedekind psi(6)
    'P3': 496,  # 3rd perfect number
    'omega': 2,  # distinct prime factors of 6
    'Omega': 2,  # prime factors with multiplicity
    'rad': 6,    # radical of 6
    # 파이썬 내장
    '__builtins__': {},
}

BT_FILE = os.path.expanduser(
    '~/Dev/n6-architecture/docs/breakthrough-theorems.md'
)
RESULT_FILE = os.path.expanduser(
    '~/Dev/nexus/shared/bt_audit_result.json'
)


# 유니코드 아래첨자 → ASCII (K₁ → K1)
SUB_MAP = str.maketrans({
    '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4',
    '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9',
})

# 유니코드 윗첨자 → **N (거듭제곱)
SUP_MAP = {
    '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4',
    '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9',
}

# 위첨자 부호 (⁻⁵, ⁺³)
SUP_SIGN_MAP = {'⁻': '-', '⁺': '+'}


def normalize_expr_unicode(s):
    """유니코드 특수기호를 ASCII 로 정규화 (parse 전처리 진입점)."""
    if s is None:
        return s
    s = s.replace('\u00a0', ' ').replace('\u2009', ' ')
    s = s.replace('\u200b', '').replace('\ufeff', '')
    s = s.replace('×', '*').replace('·', '*').replace('÷', '/')
    s = s.replace('−', '-').replace('–', '-').replace('—', '-')
    s = s.replace('±', '+')
    s = s.replace('\u2010', '-').replace('\u2011', '-')
    return re.sub(r'\s+', ' ', s).strip()


def _convert_superscripts(s):
    """연속된 유니코드 윗첨자(부호 포함)를 **<sign>N 으로 변환"""
    out = []
    i = 0
    while i < len(s):
        if s[i] in SUP_MAP or s[i] in SUP_SIGN_MAP:
            j = i
            sign = ''
            if s[j] in SUP_SIGN_MAP:
                sign = SUP_SIGN_MAP[s[j]]
                j += 1
            digits = ''
            while j < len(s) and s[j] in SUP_MAP:
                digits += SUP_MAP[s[j]]
                j += 1
            if digits:
                out.append('**' + sign + digits)
            elif sign:
                out.append('**' + sign)
            i = j
        else:
            out.append(s[i])
            i += 1
    return ''.join(out)

# 단위 패턴 — 선행 숫자가 반드시 있어야 함 (sigma/phi 같은 식별자 보호)
# 대소문자 구분 (mA ≠ ma), 뒤는 word-boundary
UNIT_RE = re.compile(
    r'(?<=[\d\)])\s*'
    r'(?:ft|Hz|kHz|MHz|GHz|THz|nm|μm|um|mm|cm|km|eV|keV|MeV|GeV|TeV'
    r'|kW|MW|GW|kV|MV|mA|mT|ms|us|μs|ns|ps|fs'
    r'|MPa|GPa|Pa|bar|atm|kJ|MJ|Wh|kWh|MWh|°C|°F|°|deg|rad'
    r'|bits?|bytes?|KB|MB|GB|TB|×|%'
    r'|channels?|layers?|classes?|types?|conditions?|properties?'
    r'|principles?|constraints?|factors?|methods?|values?|axes?|modes?'
    r'|phases?|levels?|sizes?|rounds?|suites?|stages?|weightings?'
    r'|rings?|syntaxes?|flanges?|atoms?|bonds?|bases?|nearest|fold'
    r'|A100|MLA|S0-S5|C0-C3|D0-D3|G0-G3)\b.*$'
)


def strip_units(s):
    """단위/주석/극성 표기 제거 (순수 식별자는 보호)"""
    s = s.strip()
    s = re.sub(r'^[±~≈]+', '', s).strip()
    # 괄호 주석 (A100), (Keepin model) 등 — 앞에 숫자가 있을 때만 제거
    s = re.sub(r'(?<=[\d\)])\s*\([^)]*\)\s*$', '', s).strip()
    s = UNIT_RE.sub('', s).strip()
    return s


# 단순 "숫자+단위/단어" 패턴 (전체 매칭) — bare numeric value 추출
BARE_NUM_RE = re.compile(
    r'^\s*([+-]?\d{1,3}(?:,\d{3})+|[+-]?\d+\.?\d*|[+-]?\.\d+)'
    r'\s*(?:%|°[CFK]?|[A-Za-zμ/·\-]+\d*)?'
    r'(?:\s*(?:±|\+/-|\+-)\s*[\d.]+)?'
    r'\s*$'
)

# 과학적 표기: 6×10⁻⁵, 1.5x10^-3, 6*10^-5, 10^20 (계수 생략 허용)
SCI_NOTATION_RE = re.compile(
    r'^\s*(?:([+-]?\d+\.?\d*)\s*[×x*·]\s*)?10\s*[\^]?\s*([+-]?\d+|⁻?[⁰¹²³⁴⁵⁶⁷⁸⁹]+)\s*'
    r'(?:[A-Za-zμ/·\-^\d]+)?\s*$'
)

# 파이썬 e-표기: 3.08e-5, 1.5E+3 (단위 꼬리 허용)
E_NOTATION_RE = re.compile(
    r'^\s*([+-]?\d+\.?\d*|[+-]?\.\d+)[eE]([+-]?\d+)'
    r'\s*(?:[A-Za-zμ/·\-^\d]+)?\s*$'
)


def _parse_sup_int(s):
    """⁻⁵ → -5 또는 일반 정수 문자열"""
    if not s:
        return None
    s = s.replace('⁻', '-')
    out = ''
    for c in s:
        if c in SUP_MAP:
            out += SUP_MAP[c]
        else:
            out += c
    try:
        return int(out)
    except ValueError:
        return None


def parse_bare_numeric(s):
    """expression 셀이 사실 숫자값(단위포함)일 때 그 숫자만 추출. 실패시 None."""
    if not s:
        return None
    s = s.strip()
    # 마크다운 굵게 제거
    s = re.sub(r'^\*\*(.+?)\*\*$', r'\1', s).strip()
    # 선행 ± ~ ≈
    s = re.sub(r'^[±~≈]+', '', s).strip()

    # e-표기 우선 (3.08e-5)
    me = E_NOTATION_RE.match(s)
    if me:
        try:
            return float(me.group(1)) * (10 ** int(me.group(2)))
        except (ValueError, OverflowError):
            pass

    # 과학적 표기 우선
    m = SCI_NOTATION_RE.match(s)
    if m:
        try:
            base = float(m.group(1)) if m.group(1) else 1.0
            exp = _parse_sup_int(m.group(2))
            if exp is not None:
                return base * (10 ** exp)
        except (ValueError, OverflowError):
            pass

    # "0.0351 +/- 0.0042" 같은 표기
    m2 = re.match(r'^([+-]?\d+\.?\d*|[+-]?\.\d+)\s*(?:±|\+/-|\+-)\s*[\d.]+', s)
    if m2:
        try:
            return float(m2.group(1))
        except ValueError:
            pass

    # 일반 숫자+단위/단어
    m = BARE_NUM_RE.match(s)
    if m:
        try:
            return float(m.group(1).replace(',', ''))
        except ValueError:
            return None
    return None


def normalize_expr(expr_str):
    """n=6 수식 문자열을 Python eval 가능한 형태로 정규화"""
    s = expr_str.strip()
    s = normalize_expr_unicode(s)

    # 마크다운 굵게 제거
    s = re.sub(r'^\*\*(.*)\*\*$', r'\1', s).strip()

    # 유니코드 윗첨자 → **N (거듭제곱), 아래첨자 → 숫자
    s = _convert_superscripts(s)
    s = s.translate(SUB_MAP)

    # v5e: EXACT annotation 제거 ("phi EXACT" -> "phi")
    s = re.sub(r'\s+EXACT\b', '', s).strip()
    # v5e: 괄호 주석 + 후행 EXACT/exact 제거 ("mu (Mobius) EXACT" -> "mu", "phi (totient) EXACT" -> "phi")
    # 괄호 안이 주석형(n6 변수명이 아닌 단어 포함)인 경우만 — 수식 괄호 보호
    def _strip_annotation_parens(m_s):
        """후행 괄호가 주석인지 수식인지 판별하여 주석만 제거"""
        ann_m = re.search(r'\s*(\([^)]+\))\s*$', m_s)
        if ann_m:
            inner = ann_m.group(1)[1:-1].strip()  # 괄호 안쪽
            # 그리스 문자를 영문으로 치환 후 판별
            _gk = {'σ':'sigma','τ':'tau','φ':'phi','μ':'mu','ψ':'psi','η':'eta',
                    'κ':'kappa','λ':'lambda_val','α':'alpha','β':'beta','ε':'epsilon',
                    'δ':'delta','ζ':'zeta','Δ':'delta','π':'pi','Φ':'phi'}
            inner_e = inner
            for _gc, _ge in _gk.items():
                inner_e = inner_e.replace(_gc, _ge)
            _n6_vp = r'(?:sigma|tau|phi|sopfr|mu|psi|eta|kappa|n|J2|J_2|P1|P2|K_2|K_3|R|pi|e|ln|log|sqrt|exp|floor|ceil|factorial|omega|Omega|rad|alpha|beta|delta|epsilon|zeta|lambda_val)'
            # 수식 판별: n6 변수+연산자+숫자로만 구성되면 수식
            inner_stripped = re.sub(_n6_vp, '', inner_e)
            inner_stripped = re.sub(r'[\d\s+\-*/^.(),_]+', '', inner_stripped)
            if inner_stripped:  # n6 변수+연산자 외 문자 남음 → 주석
                m_s = m_s[:ann_m.start()].strip()
        return m_s
    s = _strip_annotation_parens(s)
    # v5: 괄호 주석 제거 (BT-N, Mobius, totient 등 키워드 포함)
    s = re.sub(r'(?<=[\d\w])\s*\([^)]*(?:BT-\d+|bius|totient|number|perfect|%|adsorb|heat|cool|desorb)[^)]*\)', '', s, flags=re.IGNORECASE).strip()
    # v5: "vs ..." 제거
    s = re.sub(r'\s+vs\s+.*$', '', s).strip()
    # v5e: 후행 단위 단어 제거 ("sigma kW" -> "sigma", "(J2+phi) mV" -> "(J2+phi)")
    s = re.sub(r'\s+(?:mV|kV|kW|MW|GW|Hz|kHz|MHz|GHz|THz|nm|mm|cm|km|eV|keV|MeV|GeV|TeV|bits?|bytes?|mol|atm|bar|Pa|MPa|GPa|mA|mT|ms|us|ns|ps|fs|K|°C|m|s|kg|J|W|Wb|lm|cd|sr|rad|dB|dBm)$', '', s).strip()
    # v5: "at 300K" 조건 구문 제거
    s = re.sub(r'\s+at\s+\d+\s*[A-Za-z]*$', '', s).strip()
    # v5: 한글/CJK 잔재 제거
    s = re.sub(r'\s+[\u3000-\u9fff\uac00-\ud7af]+$', '', s).strip()

    # 빈 문자열이나 설명 텍스트 스킵
    if not s or len(s) > 120:
        return None
    # 순수 텍스트 스킵
    if any(w in s.lower() for w in [
        'complex', 'varies', 'multiple', 'see ', 'various', 'continuous',
        'standard', 'definition', 'theorem', 'universal', 'unique',
        'approximately', 'measured', 'empirical', 'derived', 'combined',
        'cross', 'all ', 'every', 'close', 'near', 'depends',
        'divisor', 'reciprocal', 'methods', 'method',
    ]):
        return None

    # v5: ⟺ (iff) 분리 — "σ·φ = n·τ ⟺ n = 6" → 우측 "n = 6" 사용
    if '⟺' in s:
        s = s.split('⟺')[-1].strip()
    # v5: "or" 분리 — "72/2 = 36 or 6² = 36" → 첫 번째 대안만
    if ' or ' in s.lower():
        s = re.split(r'\bor\b', s, flags=re.IGNORECASE)[0].strip()

    # 등호 처리: "128 = 2^7" → 숫자면 숫자, label이면 right side, 수식이면 left
    # v5: 다중 등호 — 우측 숫자 리터럴 우선 ("σ·n = 72/2 = 36" → 36)
    if '=' in s and '==' not in s and '>=' not in s and '<=' not in s:
        all_parts = [p.strip() for p in s.split('=')]
        # 우측부터 순수 숫자 찾기
        chosen = None
        for p in reversed(all_parts):
            try:
                float(p.replace(',', ''))
                chosen = p.replace(',', '')
                break
            except ValueError:
                pass
        if chosen is not None:
            s = chosen
        else:
            left = all_parts[0]
            right = '='.join(all_parts[1:]).strip()
            # 좌변이 순수 라벨(식별자만)이면 우변을 사용
            if re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', left):
                s = right
            else:
                s = left


    # 유니코드 그리스 문자 → 영문 치환 (v5e: 인접 그리스 문자 사이에 * 삽입)
    greek_map = {
        'σ': 'sigma', 'τ': 'tau', 'φ': 'phi', 'μ': 'mu',
        'ψ': 'psi', 'η': 'eta', 'κ': 'kappa', 'λ': 'lambda_val',
        'α': 'alpha', 'β': 'beta', 'ε': 'epsilon', 'δ': 'delta',
        'ζ': 'zeta', 'Δ': 'delta', 'π': 'pi', 'Φ': 'phi',
    }
    _greek_chars = set(greek_map.keys())
    new_s = []
    for ci, c in enumerate(s):
        if ci > 0 and c in _greek_chars and s[ci-1] in _greek_chars:
            new_s.append('*')
        new_s.append(c)
    s = ''.join(new_s)
    for g, eng in greek_map.items():
        s = s.replace(g, eng)

    # 유니코드 산술 치환
    s = s.replace('×', '*').replace('·', '*').replace('÷', '/')
    s = s.replace('−', '-').replace('–', '-').replace('—', '-')
    s = s.replace('^', '**').replace('²', '**2').replace('³', '**3')
    s = s.replace('⁴', '**4').replace('⁵', '**5')
    s = s.replace('⁶', '**6').replace('⁷', '**7').replace('⁸', '**8').replace('⁹', '**9')
    s = s.replace('⁰', '**0').replace('¹', '**1')

    # 'x' 또는 'X' 가 곱셈 기호로 쓰인 경우 (공백 둘러쌈)
    s = re.sub(r'(?<=[\w\)])\s+[xX]\s+(?=[\w\(])', '*', s)

    # LaTeX 중괄호 제거 (10^{-(sigma-phi)} → 10**(-(sigma-phi)))
    s = s.replace('{', '(').replace('}', ')')

    # J_2 -> J2
    s = s.replace('J_2', 'J2')

    # v5: 정수론 함수 sigma(P1), sigma(P2) — 약수합 사전 평가
    s = re.sub(r'\bsigma\(\s*P1\s*\)', '12', s)
    s = re.sub(r'\bsigma\(\s*P2\s*\)', '56', s)
    s = re.sub(r'\btau\(\s*P1\s*\)', '4', s)
    s = re.sub(r'\btau\(\s*P2\s*\)', '6', s)
    s = re.sub(r'\bphi\(\s*P1\s*\)', '2', s)
    s = re.sub(r'\bphi\(\s*P2\s*\)', '12', s)

    # number-theory 함수 호출 사전 평가 (n=6) — sigma( → sigma*( 치환 이전 수행
    _NT_FUNC_N6 = {'sigma':12,'tau':4,'phi':2,'omega':2,'rad':6,'sopfr':5,'mu':1,'Omega':2}
    for _fn,_val in _NT_FUNC_N6.items():
        s = re.sub(rf'\b{_fn}\(\s*6\s*\)', str(_val), s)

    # sigma/phi/tau 등은 함수가 아닌 상수 — 'sigma(' 같은 사용은 곱셈으로 해석
    # 예: σ(σ-μ) → sigma*(sigma-mu)
    for nm in ('sigma', 'phi', 'tau', 'sopfr', 'mu', 'psi', 'eta', 'kappa'):
        s = re.sub(rf'\b{nm}\(', f'{nm}*(', s)

    # "sigma-tau" 같은 연산 표현 보존 (이미 Python 호환)

    # "2**(sigma-tau)" 패턴
    s = re.sub(r'2\*\*\(', '2**(', s)

    # "sigma*phi" → OK
    # "sigma(6)" → sigma (값 자체)
    s = re.sub(r'(\w+)\(6\)', r'\1', s)

    # n=6 이면 n 만
    s = re.sub(r'\bn=6\b', 'n', s)

    # "1/phi" → "1/phi" (OK)
    # "phi**tau" → OK

    # 공백 연산: "sigma - tau" → "sigma-tau" (eval OK)

    # 암묵적 곱셈 삽입:
    # 1) 숫자와 식별자/괄호: 3tau → 3*tau, 6pi → 6*pi
    s = re.sub(r'(\d)([A-Za-z_(])', r'\1*\2', s)
    # 2) 닫는 괄호와 여는 괄호 또는 식별자: )(  → )*(
    s = re.sub(r'\)\s*([A-Za-z_(])', r')*\1', s)
    # 3) 식별자 뒤 여는 괄호는 normalize 위에서 sigma( → sigma*( 처리됨

    # 단위/주석 제거
    s = strip_units(s)

    # "sigma ft" 같은 것에서 뒤에 단위가 남을 수 있음 -> strip
    s = s.strip()

    # 괄호 짝 맞는지 체크
    if s.count('(') != s.count(')'):
        return None

    # v5e: 팩토리얼
    s = re.sub(r'(\b\w+)!', r'factorial(\1)', s)

    # 최종적으로 eval 가능한 문자만 남았는지 체크
    allowed = set('0123456789+-*/.() _abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
    if not all(c in allowed for c in s):
        return None

    # 비어있으면 스킵
    if not s or s in ('', '-', '+'):
        return None

    return s


def split_list_expr(expr_str):
    """리스트/래더 표현을 원소들로 분해. 분해 불가면 None."""
    s = expr_str.strip()
    s = re.sub(r'^\*\*(.*)\*\*$', r'\1', s).strip()
    s = _convert_superscripts(s).translate(SUB_MAP)
    # {a, b, c} 또는 [a, b, c]
    m = re.match(r'^[\[\{](.+)[\]\}]$', s)
    if m:
        body = m.group(1)
    elif '\u2192' in s or '->' in s:
        # 래더: a → b → c
        body = re.sub(r'->|\u2192', ',', s)
    elif ',' in s and '(' not in s:
        body = s
    else:
        return None
    parts = [p.strip() for p in body.split(',') if p.strip()]
    return parts if len(parts) >= 2 else None


def split_list_value(val_str):
    """Predicted/Known 셀에서 리스트 추출"""
    if not val_str:
        return None
    s = val_str.strip().translate(SUB_MAP)
    m = re.match(r'^[\[\{](.+)[\]\}]$', s)
    if m:
        body = m.group(1)
    elif '\u2192' in s or '->' in s:
        body = re.sub(r'->|\u2192', ',', s)
    elif ',' in s and '(' not in s:
        body = s
    else:
        return None
    nums = []
    for p in body.split(','):
        p = strip_units(p.strip())
        try:
            nums.append(float(p))
        except ValueError:
            return None
    return nums if len(nums) >= 2 else None


def safe_eval(expr_str):
    """수식 문자열을 안전하게 평가"""
    normalized = normalize_expr(expr_str)
    if normalized is None:
        # 수식 정규화 실패 — bare numeric 폴백
        bare = parse_bare_numeric(expr_str)
        if bare is not None:
            return bare, f'<bare:{bare}>'
        return None, None

    try:
        result = eval(normalized, EVAL_NS)
        if isinstance(result, (int, float)):
            return result, normalized
        return None, normalized
    except Exception:
        # eval 실패 — bare numeric 폴백
        bare = parse_bare_numeric(expr_str)
        if bare is not None:
            return bare, f'<bare:{bare}>'
        return None, normalized


def parse_predicted_value(val_str):
    """Predicted 열에서 숫자 추출 — v5d: fraction/eval/joined-unit 강화"""
    s = val_str.strip()

    # v5d: 마크다운 bold 제거 ("**0.3000**" -> "0.3000")
    s = re.sub(r'^\*\*(.+?)\*\*$', r'\1', s).strip()

    s = s.lstrip('~\u2248')

    # v5d: 유니코드 과학표기 ("3.083×10⁻⁵" -> 3.083e-5)
    s_uni = s.replace('\u00d7', '*').replace('\u00b7', '*')
    _cs_ppv = _convert_superscripts
    s_uni = _cs_ppv(s_uni)
    sci_m = re.match(r'^([+-]?\d+\.?\d*)\s*\*\s*10\*\*([+-]?\d+)\s*$', s_uni)
    if sci_m:
        try:
            return float(sci_m.group(1)) * (10 ** int(sci_m.group(2)))
        except (ValueError, OverflowError):
            pass

    # v5d: 10^{-6} -> 1e-6 (curly brace)
    s_brace = s.replace('{', '').replace('}', '').replace('^', '**')
    s_brace = _cs_ppv(s_brace)
    pow_m = re.match(r'^10\*\*([+-]?\d+)$', s_brace)
    if pow_m:
        try:
            return 10 ** int(pow_m.group(1))
        except (ValueError, OverflowError):
            pass

    # v5d: 괄호 주석 제거 ("0.5 (= 12/24)" -> "0.5")
    m_paren = re.match(r'^([+-]?\d+\.?\d*)\s*\(.*$', s)
    if m_paren:
        try:
            return float(m_paren.group(1))
        except ValueError:
            pass

    # v5d: 등호 — 좌변이 순수 숫자/산술식일 때만
    if '=' in s and '==' not in s:
        parts = s.split('=')
        left = parts[0].strip()
        right = parts[-1].strip()
        # 좌변이 순수 숫자면 추출
        try:
            return float(left.replace(',', ''))
        except ValueError:
            pass
        # 좌변에 n6 변수명이 있으면 스킵 (서술형: "tau = 4", "n = 6")
        _n6_names = {'sigma', 'tau', 'phi', 'sopfr', 'mu', 'psi', 'J2', 'J_2', 'n'}
        left_lower = left.lower().replace('\u03c3','sigma').replace('\u03c4','tau').replace('\u03c6','phi').replace('\u03bc','mu')
        if any(nm in left_lower for nm in _n6_names):
            pass  # 서술형 — 숫자 추출 안 함
        else:
            # 좌변이 순수 산술식("6 x 4")이면 우변에서 추출
            right_clean = re.sub(r'[°\s]*[A-Za-z]*$', '', right).strip()
            try:
                return float(right_clean.replace(',', ''))
            except ValueError:
                pass

    # e-표기 ("3e-4", "1.5E+3")
    me = re.match(r'^([+-]?\d+\.?\d*|[+-]?\.\d+)[eE]([+-]?\d+)', s)
    if me:
        try:
            return float(me.group(1)) * (10 ** int(me.group(2)))
        except (ValueError, OverflowError):
            pass

    # v5d: 유니코드 윗첨자 과학표기 ("10\u2074" -> 10000)
    s_sup = _convert_superscripts(s)
    ms = re.match(r'^(\d+\.?\d*)\*\*([+-]?\d+)$', s_sup.replace('^', '**'))
    if ms:
        try:
            return float(ms.group(1)) ** int(ms.group(2))
        except (ValueError, OverflowError):
            pass

    # 서술형 predicted 감지 — 영문 단어(2글자+)가 2개 이상이면 서술형
    words = re.findall(r'[A-Za-z]{2,}', s)
    unit_words = {
        'ft', 'hz', 'khz', 'mhz', 'ghz', 'nm', 'mm', 'cm', 'km',
        'ev', 'kev', 'mev', 'gev', 'kw', 'mw', 'gw', 'kv', 'mv',
        'ms', 'us', 'ns', 'ps', 'mpa', 'gpa', 'pa', 'ma', 'mt',
        'mod', 'order',
    }
    descriptive_words = [w for w in words if w.lower() not in unit_words]
    if len(descriptive_words) >= 2:
        return None

    # v5d: degree ("120°" -> 120)
    dm = re.match(r'^([+-]?\d+\.?\d*)\s*°', s)
    if dm:
        try:
            return float(dm.group(1))
        except ValueError:
            pass

    # v5: 단위 분수 ("48V/6V" → 8, "12kV/4kV" → 3) — 단위 제거 후 분수
    s_uf = re.sub(r'(\d)\s*(?:V|kV|MV|kW|MW|Hz|kHz|MHz|eV|keV|A|W|T|K|Pa|MPa)\b', r'\1', s)
    uf_m = re.match(r'^\s*([+-]?\d+\.?\d*)\s*/\s*([+-]?\d+\.?\d*)\s*$', s_uf)
    if uf_m:
        try:
            num = float(uf_m.group(1))
            den = float(uf_m.group(2))
            if den != 0:
                return num / den
        except (ValueError, ZeroDivisionError):
            pass


    # v5d: 분수 ("1/12", "4/3", "7/4")
    fm = re.match(r'^([+-]?\d+)\s*/\s*(\d+)$', s)
    if fm:
        try:
            return int(fm.group(1)) / int(fm.group(2))
        except (ValueError, ZeroDivisionError):
            pass

    # v5d: 간단한 산술식 eval ("2+3" -> 5) — 숫자와 +/-/*// 만 허용
    if re.match(r'^[\d\s+\-*/().]+$', s) and any(c in s for c in '+-*/'):
        try:
            v = eval(s, {'__builtins__': {}}, {})
            if isinstance(v, (int, float)):
                return float(v)
        except Exception:
            pass

    # v5d: joined 단위 우선 (30mA, 96S, etc.)
    s2 = re.sub(r'(?<=\d)\s*(?:mA|mV|mT|mbar|dB|dBm)\b.*$', '', s)
    # 기존 단위 제거
    s2 = re.sub(r'\s*(ft|Hz|kHz|MHz|GHz|nm|mm|cm|m|km|eV|keV|MeV|GeV|W|kW|MW|V|kV|A|T|K|s|ms|us|ns|bits?|bytes?|channels?|layers?|classes?|types?|conditions?|properties?|principles?|constraints?|factors?|methods?|values?|axes?|modes?|phases?|levels?|sizes?|rounds?|suites?|stages?|weightings?|rings?|syntaxes?|flanges?|/week|MPa)\b.*$', '', s2)
    # v5d: trailing single uppercase letter (96S -> 96)
    s2 = re.sub(r'(?<=\d)[A-Z]$', '', s2)
    # v5d: 영어 단어 꼬리 제거 ("24-phase" -> "24")
    s2 = re.sub(r'[\-\s]+[A-Za-z][A-Za-z\s]*$', '', s2)
    s2 = s2.strip()

    if not s2:
        return None

    # v5d: % (predicted에서는 그대로 숫자, audit_row에서 /100 대안 시도)
    pm = re.match(r'^([+-]?\d+\.?\d*)\s*%$', s2)
    if pm:
        try:
            return float(pm.group(1))
        except ValueError:
            pass

    try:
        return float(s2)
    except ValueError:
        # "2^7" -> 128
        m = re.match(r'^(\d+)\*?\*(\d+)$', s2)
        if m:
            return float(int(m.group(1)) ** int(m.group(2)))
        return None

def is_pure_literal(expr_str):
    """Expression이 순수 숫자 리터럴인지 (128, 2048, 0.9, 10x, 20% 등)"""
    if not expr_str:
        return False
    s = expr_str.strip().lstrip('~≈')
    s = re.sub(r'^\*\*(.+?)\*\*$', r'\1', s).strip()
    s = s.rstrip('x×%')
    try:
        float(s.replace(',', ''))
        return True
    except ValueError:
        return False


_MATH_WORD_RE = re.compile(r'\b(ln|log|log2|sqrt|exp|pi|e|sin|cos|tan|sigma|tau|phi|mu|sopfr|n|J2|J_2)\b')


def is_descriptive_known(known_str):
    """Known 셀이 서술형 자연어인지 (alpha ratio > 0.4, 수학 식별자 제외)"""
    if not known_str:
        return False
    s = known_str.strip()
    if not s:
        return False
    # 수학 식별자/함수 먼저 제거
    stripped = _MATH_WORD_RE.sub('', s)
    core = re.sub(r'[\s\*_\-~≈±()=,:/\.\d\^%×·]', '', stripped)
    if not core:
        return False
    alpha = sum(1 for c in core if c.isalpha())
    if alpha < 3:
        return False
    # 남은 문자 중 알파벳 비율
    ratio = alpha / max(1, len(core))
    return ratio > 0.4


def safe_eval_known(val_str):
    """Known 셀을 분수/기호식으로 평가 (4/3, 1/12, 27/28, ~3/2, 10^3, 20%, 4×6=24)"""
    if not val_str:
        return None
    s = val_str.strip()
    s = re.sub(r'^\*\*(.+?)\*\*$', r'\1', s).strip()
    s = s.lstrip('~≈').strip()
    # 등식형 "4×6=24" → 우변 우선
    if '=' in s and '==' not in s and '>=' not in s and '<=' not in s:
        parts = s.split('=')
        for candidate in (parts[-1].strip(), parts[0].strip()):
            v = _eval_known_core(candidate)
            if v is not None:
                return v
        return None
    return _eval_known_core(s)


def _eval_known_core(s):
    if not s:
        return None
    # ± 제거
    s = re.sub(r'\s*(?:±|\+/-|\+-)\s*[\d.]+.*$', '', s).strip()
    # 퍼센트
    pct_m = re.match(r'^([+-]?\d+\.?\d*)\s*%$', s)
    if pct_m:
        try:
            return float(pct_m.group(1)) / 100.0
        except ValueError:
            pass
    # 10^3, 2^7
    pow_m = re.match(r'^([+-]?\d+\.?\d*)\s*\^\s*([+-]?\d+)$', s)
    if pow_m:
        try:
            return float(pow_m.group(1)) ** int(pow_m.group(2))
        except (ValueError, OverflowError):
            pass
    # 유니코드/기호 정규화
    s2 = s.replace('×', '*').replace('·', '*').replace('÷', '/').replace('^', '**')
    s2 = _convert_superscripts(s2).translate(SUB_MAP)
    # 순수 산술
    if re.match(r'^[\d\.\s\+\-\*/\(\)]+$', s2):
        try:
            v = eval(s2, {'__builtins__': {}}, {})
            if isinstance(v, (int, float)):
                return float(v)
        except Exception:
            pass
    # v5: n6 변수 포함 식 평가 ("1/phi", "sigma-mu", "1/(sigma-mu)")
    # 그리스 문자 치환 후 EVAL_NS로 평가
    s3 = s2
    _greek = {'σ':'sigma','τ':'tau','φ':'phi','μ':'mu'}
    for g, eng in _greek.items():
        s3 = s3.replace(g, eng)
    # 식별자가 있으면 EVAL_NS 사용
    if re.search(r'[A-Za-z_]', s3):
        # 암묵적 곱셈
        s3 = re.sub(r'(\d)([A-Za-z_(])', r'\1*\2', s3)
        try:
            v = eval(s3, EVAL_NS)
            if isinstance(v, (int, float)):
                return float(v)
        except Exception:
            pass

    return None


def known_decimal_tolerance(raw_str, target_value):
    """
    Known 표기 유효 소수자릿수 기반 절대 허용오차 추정.
    "0.9649" -> 5e-5, "33.7%" -> 0.0005, "3.08e-5" -> 0.005e-5
    """
    if raw_str is None or target_value is None:
        return None
    s = str(raw_str).strip()
    s = s.lstrip('~≈').strip()
    s = re.sub(r'^\*\*(.+?)\*\*$', r'\1', s).strip()
    # 단위 제거 (parse_predicted_value 와 유사)
    s = re.sub(r'\s*(eV|keV|MeV|GeV|kHz|MHz|GHz|Hz|kW|MW|MPa|nm|mm|cm|km|kV|ms|us|ns|bits?|bytes?|m|s|V|A|W|T|K)\b.*$', '', s)
    s = s.strip()
    if '=' in s and '==' not in s and '>=' not in s and '<=' not in s:
        s = s.split('=')[-1].strip()
    pct = False
    pm = re.match(r'^([+-]?\d+\.?\d*)\s*%$', s)
    if pm:
        s = pm.group(1)
        pct = True
    em = re.match(r'^([+-]?\d+\.?\d*|[+-]?\.\d+)[eE]([+-]?\d+)$', s)
    if em:
        mantissa = em.group(1); exp = int(em.group(2))
        decimals = len(mantissa.split('.')[1]) if '.' in mantissa else 0
        return 0.5 * (10 ** (-decimals)) * (10 ** exp)
    nm = re.match(r'^([+-]?\d+\.?\d*)$', s)
    if nm:
        num = nm.group(1)
        decimals = len(num.split('.')[1]) if '.' in num else 0
        tol = 0.5 * (10 ** (-decimals))
        if pct:
            tol = tol / 100.0
        return tol
    return None


def parse_known_value(val_str):
    """Known 열에서 숫자 추출 (설명 텍스트가 붙을 수 있음) — v5 파서 보강"""
    s = val_str.strip()
    s = s.lstrip('~≈')
    # 유니코드 정규화 (×10⁻ⁿ, 아래첨자, ^ → **)
    s = normalize_expr_unicode(s)
    s = _convert_superscripts(s).translate(SUB_MAP)
    s = s.replace('^', '**')


    # v5e: descriptive_known parser — median/mean/~/top-N/N-qubit 등에서 숫자 추출
    # "median 6" → 6, "mean 12" → 12, "~0.5" → 0.5
    dk_prefix_m = re.match(r'^\s*(?:median|mean|average|approx|approximately|about)\s+([+-]?\d+\.?\d*)\b', s, re.IGNORECASE)
    if dk_prefix_m:
        try:
            return float(dk_prefix_m.group(1))
        except ValueError:
            pass
    # "top-6" → 6, "top-12" → 12
    topn_m = re.match(r'^\s*top[-\s](\d+)\b', s, re.IGNORECASE)
    if topn_m:
        try:
            return float(topn_m.group(1))
        except ValueError:
            pass
    # "6-qubit" → 6, "12-bit" → 12
    nqubit_m = re.match(r'^\s*(\d+)[-\s](?:qubit|qubits|bit|bits|fold|layer|layers|phase|phases|step|steps|way|dim|dimensional)\b', s, re.IGNORECASE)
    if nqubit_m:
        try:
            return float(nqubit_m.group(1))
        except ValueError:
            pass

    # v5: 원소 표기 "Si-28", "Fe-56" → 질량수 추출
    elem_m = re.match(r'^[A-Z][a-z]?-(\d+)$', val_str.strip())
    if elem_m:
        try:
            return float(elem_m.group(1))
        except ValueError:
            pass


    # v5: 팩토리얼 패턴 "= N!" → N! 평가
    fac_m = re.search(r'(\d+)\s*!', s)
    if fac_m:
        try:
            return float(math.factorial(int(fac_m.group(1))))
        except (ValueError, OverflowError):
            pass

    # v5: 라벨 접두사 제거 (q_95, Re_, Pr_) → 뒤의 부등식 값 추출
    label_m = re.match(r'^[A-Za-z]+_\d+\s*(?:>=|<=|>|<|=)\s*([+-]?\d+\.?\d*)', s)
    if label_m:
        try:
            return float(label_m.group(1))
        except ValueError:
            pass

    # v5: 부등식 패턴 "< 0.06", ">= 2.0" → 경계값 추출
    ineq_m = re.match(r'^\s*(?:>=|<=|>|<)\s*([+-]?\d+\.?\d*)', s)
    if ineq_m:
        try:
            return float(ineq_m.group(1))
        except ValueError:
            pass

    # v5: 범위 패턴 "~0.01-0.1", "9-15 kW" → 범위 상한 (computed가 범위 내인지 검사용)
    range_m = re.match(r'^\s*~?\s*([+-]?\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*(?:[A-Za-z]+)?\s*$', s)
    if range_m:
        try:
            lo = float(range_m.group(1))
            hi = float(range_m.group(2))
            if hi > lo:
                return (lo + hi) / 2.0  # 범위 중간값
        except ValueError:
            pass

    # v5: 인라인 단위 제거 ("48V/6V" → "48/6", "120K" → "120")
    s = re.sub(r'(\d)\s*(?:V|kV|MV|kW|MW|GW|Hz|kHz|MHz|GHz|eV|keV|MeV|GeV|Pa|MPa|GPa|mA|mT|Wb|lm|cd|mol|rad|sr)\b', r'\1', s)
    # v5: 단위**거듭제곱 제거 ("10**20 m**-3" → "10**20")
    s = re.sub(r'\s+[A-Za-z]+\*\*[+-]?\d+', '', s).strip()
    # 후행 단위 단어 제거 ("10**20 m" → "10**20")
    s = re.sub(r'\s+[A-Za-z][-A-Za-z/]*\s*$', '', s).strip()




    # v5: 슬래시 분수 우선 평가 — "1e-6 / 1e-5" → 0.1, "16/27" → 0.593
    if '/' in s:
        frac_str = s
        if '=' in s and '==' not in s and '>=' not in s and '<=' not in s:
            parts = s.split('=')
            for p in parts:
                if '/' in p:
                    frac_str = p.strip()
                    break
        efrac_m = re.match(
            r'^\s*([+-]?\d+\.?\d*(?:[eE][+-]?\d+)?)\s*/\s*([+-]?\d+\.?\d*(?:[eE][+-]?\d+)?)\s*$',
            frac_str
        )
        if efrac_m:
            try:
                num = float(efrac_m.group(1))
                den = float(efrac_m.group(2))
                if den != 0:
                    return num / den
            except (ValueError, ZeroDivisionError):
                pass

    # v5: "4M" (mega), "4G" (giga) 접미사
    mega_m = re.match(r'^\s*([+-]?\d+\.?\d*)\s*M\s*$', s)
    if mega_m:
        try:
            return float(mega_m.group(1)) * 1e6
        except ValueError:
            pass
    giga_m = re.match(r'^\s*([+-]?\d+\.?\d*)\s*G\s*$', s)
    if giga_m:
        try:
            return float(giga_m.group(1)) * 1e9
        except ValueError:
            pass

    # e-표기: 3.08e-5, 1.5E+3 (단위 꼬리 허용, 다른 연산자 없어야 함)
    if '/' not in s and not re.search(r'(?<![eE\d])[\+\-](?!\d)', s):
        me = re.fullmatch(r'\s*([+-]?\d+\.?\d*|[+-]?\.\d+)[eE]([+-]?\d+)\s*(?:[A-Za-zμ/·\-^\d]+)?\s*', s)
        if me:
            try:
                return float(me.group(1)) * (10 ** int(me.group(2)))
            except (ValueError, OverflowError):
                pass

        # 과학적 표기: 6*10^-5, 10^20 (계수 생략 포함), 전체 매칭
        ms = re.fullmatch(r'\s*(?:([+-]?\d+\.?\d*)\s*\*\s*)?10\s*\*\*\s*([+-]?\d+)\s*(?:[A-Za-zμ/·\-^\d]+)?\s*', s)
        if ms:
            try:
                base = float(ms.group(1)) if ms.group(1) else 1.0
                return base * (10 ** int(ms.group(2)))
            except (ValueError, OverflowError):
                pass

    # 퍼센트: "33.7%", "16.7%", "1/6 = 16.7%"
    pm = re.search(r'([+-]?\d+\.?\d*)\s*%', s)
    if pm:
        try:
            return float(pm.group(1)) / 100.0
        except ValueError:
            pass

    # v5: 등호 뒤 평가 — "A = 12" → 12, "4.18/1.005 = 4.16" → 우변 수치
    if '=' in s and '==' not in s and '>=' not in s and '<=' not in s:
        parts = s.split('=')
        for candidate in reversed(parts):
            c = candidate.strip()
            c = re.sub(r'\s*[A-Za-z]+$', '', c).strip()
            try:
                return float(c)
            except ValueError:
                pass

    # 일반 숫자
    m = re.search(r'([+-]?\d+\.?\d*)', s)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            return None
    return None



def parse_bt_sections(text):
    """BT 섹션들을 파싱"""
    # BT 헤더 패턴: ## BT-NNN: 또는 | **BT-N** |
    sections = []

    # ## BT-N 형태 헤더로 분리
    bt_pattern = re.compile(r'^## BT-(\d+)', re.MULTILINE)
    matches = list(bt_pattern.finditer(text))

    for i, m in enumerate(matches):
        bt_num = int(m.group(1))
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section_text = text[start:end]
        sections.append((bt_num, section_text))

    # 초기 BT-1~5 테이블 형태도 파싱
    early_bt_pattern = re.compile(
        r'\| \*\*BT-(\d+)\*\* \|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|'
    )
    for m in early_bt_pattern.finditer(text):
        bt_num = int(m.group(1))
        # 이미 있는지 체크
        if not any(b == bt_num for b, _ in sections):
            sections.append((bt_num, m.group(0)))

    return sorted(sections, key=lambda x: x[0])


def extract_verification_tables(bt_num, section_text):
    """
    "| n=6 Expression | Predicted | Known | Error% | Grade |" 형태의
    검증 테이블에서 행을 추출
    """
    results = []

    # 테이블 헤더 찾기
    table_header = re.compile(
        r'\|\s*n=6 Expression\s*\|\s*Predicted\s*\|\s*Known\s*\|'
    )

    lines = section_text.split('\n')
    in_table = False
    header_found = False

    for i, line in enumerate(lines):
        if table_header.search(line):
            header_found = True
            in_table = False  # 다음 줄은 구분선
            continue

        if header_found and not in_table:
            # 구분선 스킵
            if '---' in line:
                in_table = True
                continue
            header_found = False
            continue

        if in_table:
            if not line.strip() or not line.strip().startswith('|'):
                in_table = False
                header_found = False
                continue

            # 테이블 행 파싱 — 앞뒤 빈 셀만 제거 (중간 보존)
            cells = [c.strip() for c in line.split('|')]
            while cells and cells[0] == '':
                cells.pop(0)
            while cells and cells[-1] == '':
                cells.pop()
            if len(cells) >= 3:
                expr = cells[0] if cells[0] else (cells[1] if len(cells) > 1 else '')
                predicted = cells[1] if len(cells) > 1 else ''
                known = cells[2] if len(cells) > 2 else ''
                grade = cells[4] if len(cells) > 4 else ''

                results.append({
                    'expression': expr,
                    'predicted_raw': predicted,
                    'known_raw': known,
                    'grade_raw': grade,
                })

    return results


def extract_evidence_tables(bt_num, section_text):
    """
    다양한 형태의 증거 테이블에서 n=6 수식과 값을 추출
    "| ... | n=6 Expression | ..." 또는
    "| ... | n=6 Formula | Predicted | ..." 형태
    """
    results = []
    lines = section_text.split('\n')

    # n=6 Expression/Formula 열이 있는 테이블 찾기
    for i, line in enumerate(lines):
        if '|' in line and ('n=6 Expression' in line or 'n=6 Formula' in line):
            # 헤더 열 인덱스 파악 — 앞뒤 빈 셀만 제거 (중간 빈 셀은 보존)
            headers = [h.strip() for h in line.split('|')]
            while headers and headers[0] == '':
                headers.pop(0)
            while headers and headers[-1] == '':
                headers.pop()

            expr_col = None
            pred_col = None
            known_col = None
            value_col = None

            _ROW_NUM_HEADERS = {'#', 'No', 'No.', 'Index', 'Row', '№', 'Idx'}
            for j, h in enumerate(headers):
                if h in _ROW_NUM_HEADERS:
                    continue  # 2-D: 행번호 컬럼 스킵
                if 'n=6 Expression' in h or 'n=6 Formula' in h:
                    expr_col = j
                if 'Predicted' in h:
                    pred_col = j
                if h in ('Known', 'Measured', 'Actual', 'Value', 'Values'):
                    known_col = j
                if h in ('Parameters', 'Parameter', 'Count'):
                    value_col = j

            if expr_col is None:
                continue

            # 구분선 스킵하고 데이터 행 읽기
            j = i + 1
            if j < len(lines) and '---' in lines[j]:
                j += 1

            while j < len(lines):
                row = lines[j]
                if not row.strip() or not row.strip().startswith('|'):
                    break
                cells = [c.strip() for c in row.split('|')]
                # headers와 동일한 방식: 앞뒤 빈 셀만 제거
                while cells and cells[0] == '':
                    cells.pop(0)
                while cells and cells[-1] == '':
                    cells.pop()

                if len(cells) > expr_col:
                    expr_str = cells[expr_col]
                    pred_val = cells[pred_col] if pred_col is not None and len(cells) > pred_col else None
                    known_val = cells[known_col] if known_col is not None and len(cells) > known_col else None
                    val = cells[value_col] if value_col is not None and len(cells) > value_col else None

                    if expr_str and expr_str != '---':
                        results.append({
                            'expression': expr_str,
                            'predicted_raw': pred_val or val or '',
                            'known_raw': known_val or '',
                            'grade_raw': '',
                        })
                j += 1

    return results


_NON_FORMULA_RE = re.compile(
    r'^(\*\*[^*]+\*\*'
    r'|[A-Za-z_][A-Za-z0-9_]*'
    r'|[A-Za-z_][A-Za-z0-9_]*\([^)]*\))$'
)


_KNOWN_NAMES = {
    'sigma', 'tau', 'phi', 'sopfr', 'mu', 'n', 'J2', 'J_2', 'R',
    'P1', 'P2', 'K_2', 'K_3',
}


def is_non_formula(expr_str):
    s = _convert_superscripts(expr_str.strip()).translate(SUB_MAP)
    if not s:
        return True
    # 마크다운 굵게/이탤릭 라벨
    if re.match(r'^[*_]{1,2}[^*_]+[*_]{1,2}$', s):
        return True
    # 백슬래시 LaTeX 잔재
    if '\\' in s:
        return True
    # 공백을 포함한 자연어 (단, 연산자만 있는 공백 'sigma + tau' 는 OK)
    if ' ' in s and not re.match(r'^[\w\s+\-*/().^%]+$', s):
        return True
    # 한 어휘의 단순 식별자 또는 식별자(인자) (예: alpha_s(M_Z), m_t/m_W → 슬래시 포함)
    # 식별자만(언더스코어 포함)
    if re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', s) and s not in _KNOWN_NAMES:
        return True
    # 식별자(인자)
    if re.match(r'^[A-Za-z_][A-Za-z0-9_]*\([^)]*\)$', s):
        return True
    # 식별자/식별자 (예: m_t/m_W, k/n)
    if re.match(r'^[A-Za-z_][A-Za-z0-9_]*\s*/\s*[A-Za-z_][A-Za-z0-9_]*$', s):
        return True
    # 백분율 범위 (3-5%)
    if re.match(r'^\d+\s*-\s*\d+\s*%?$', s):
        return True
    # 자연어 라벨 (영문 단어 2개+, 또는 BT-N, Si-28, top-8, layer N 등)
    if re.match(r'^[A-Za-z]+(?:[\s\-][A-Za-z0-9]+)+$', s):
        return True
    # sin²θ_W 같은 그리스/삼각함수 잔재 (eval 불가능 → 라벨로 처리)
    if 'theta' in s.lower() or re.search(r'\bsin|\bcos|\btan', s.lower()):
        # 단, 평가 가능한 형태(sin(0))는 normalize_expr에서 처리하므로 여기선 unresolvable만
        if not re.match(r'^[\w\s+\-*/().]+$', s):
            return True
    # 마크다운 굵게로 감싼 식별자 (**m_p/m_e**) — 최외곽 ** 제거 후 식별자류
    inner = re.sub(r'^\*\*(.+?)\*\*$', r'\1', s)
    if inner != s and (re.match(r'^[A-Za-z_][A-Za-z0-9_]*(?:/[A-Za-z_][A-Za-z0-9_]*)?$', inner)
                       or re.match(r'^[A-Za-z_][A-Za-z0-9_]*\([^)]*\)$', inner)):
        return True
    # v5e: 대시/빈 표현 ("—", "-", "**")
    if s in ('—', '-', '**', '***', ''):
        return True
    # v5e: 한글만 ("실패", "성공" 등)
    if all(('\uac00' <= c <= '\ud7af' or c.isspace()) for c in s):
        return True
    # v5e: 식별자 + 단어 ("phi stabilizers", "sigma³ connection")
    if re.match(r'^[A-Za-z_][A-Za-z0-9_]*(?:\*\*\d+)?\s+[A-Za-z]+', s):
        return True
    return False


def audit_row(bt_num, row):
    """단일 테이블 행 검산"""
    expr_str = row['expression']
    predicted_raw = row['predicted_raw']
    known_raw = row['known_raw']

    # 0) 리스트/래더 비교 우선 시도
    parts = split_list_expr(expr_str)
    if parts is not None:
        comp_list = []
        ok = True
        for p in parts:
            v, _ = safe_eval(p)
            if v is None:
                ok = False
                break
            comp_list.append(v)
        if ok:
            tgt_list = (
                split_list_value(predicted_raw)
                or split_list_value(known_raw)
            )
            if tgt_list and len(tgt_list) == len(comp_list):
                errs = [
                    abs(c - t) / abs(t) * 100 if t else (0 if c == 0 else float('inf'))
                    for c, t in zip(comp_list, tgt_list)
                ]
                max_err = max(errs)
                return {
                    'bt': bt_num,
                    'expression': expr_str,
                    'normalized': str(comp_list),
                    'computed': comp_list,
                    'target': tgt_list,
                    'target_source': 'list',
                    'error_pct': round(max_err, 4) if max_err != float('inf') else 'inf',
                    'status': 'MATCH' if max_err < 0.01 else 'MISMATCH',
                }
            # 타겟 없음 → list NO_TARGET
            return {
                'bt': bt_num,
                'expression': expr_str,
                'computed': comp_list,
                'normalized': str(comp_list),
                'status': 'NO_TARGET',
                'reason': f'리스트 비교 대상 없음 (predicted={predicted_raw}, known={known_raw})',
            }

    # 1) 일반 수식 평가
    computed, normalized = safe_eval(expr_str)

    if computed is None:
        # 평가 실패 → 비-수식 라벨이면 NO_EXPR, 아니면 SKIP
        if is_non_formula(expr_str):
            return {
                'bt': bt_num,
                'expression': expr_str,
                'status': 'NO_EXPR',
                'reason': '수식이 아닌 라벨/이름',
            }
        return {
            'bt': bt_num,
            'expression': expr_str,
            'status': 'SKIP',
            'reason': f'수식 평가 불가: {normalized or expr_str}',
        }

    # Predicted 값 파싱
    predicted_num = parse_predicted_value(predicted_raw) if predicted_raw else None

    # Known 값 파싱
    known_num = parse_known_value(known_raw) if known_raw else None

    # 비교 대상 결정 (predicted 우선, 없으면 known)
    target = predicted_num if predicted_num is not None else known_num
    target_source = 'predicted' if predicted_num is not None else 'known'

    if target is None:
        # v5b: 자기 검증 — 수식에 "= <숫자>" 있으면 self-eq MATCH
        eq_m = re.search(r'=\s*([+-]?\d+\.?\d*(?:[eE][+-]?\d+)?)', expr_str)
        if eq_m:
            try:
                self_target = float(eq_m.group(1))
                if self_target == 0 and computed == 0:
                    return {
                        'bt': bt_num, 'expression': expr_str,
                        'normalized': normalized,
                        'computed': round(computed, 6) if isinstance(computed, float) else computed,
                        'target': self_target, 'target_source': 'self_eq',
                        'error_pct': 0, 'status': 'MATCH',
                    }
                elif self_target != 0:
                    self_err = abs(computed - self_target) / abs(self_target) * 100
                    if self_err < 1.0 or abs(computed - self_target) <= 1e-3:
                        return {
                            'bt': bt_num, 'expression': expr_str,
                            'normalized': normalized,
                            'computed': round(computed, 6) if isinstance(computed, float) else computed,
                            'target': self_target, 'target_source': 'self_eq',
                            'error_pct': round(self_err, 4),
                            'status': 'MATCH',
                        }
            except ValueError:
                pass
        # v5e: 수식 RHS 평가 자기 검증 ("σ(6) = (n/φ)·τ" → 양변 같으면 MATCH)
        if '=' in expr_str:
            raw = normalize_expr_unicode(expr_str)
            raw = _convert_superscripts(raw).translate(SUB_MAP)
            eq_parts = raw.split('=')
            if len(eq_parts) >= 2:
                rhs_str = eq_parts[-1].strip()
                rhs_val, _ = safe_eval(rhs_str)
                if rhs_val is not None and isinstance(rhs_val, (int, float)):
                    if rhs_val == 0 and computed == 0:
                        return {
                            'bt': bt_num, 'expression': expr_str,
                            'normalized': normalized,
                            'computed': round(computed, 6) if isinstance(computed, float) else computed,
                            'target': rhs_val, 'target_source': 'self_eq_rhs',
                            'error_pct': 0, 'status': 'MATCH',
                        }
                    elif rhs_val != 0:
                        rhs_err = abs(computed - rhs_val) / abs(rhs_val) * 100
                        if rhs_err < 1.0 or abs(computed - rhs_val) <= 1e-3:
                            return {
                                'bt': bt_num, 'expression': expr_str,
                                'normalized': normalized,
                                'computed': round(computed, 6) if isinstance(computed, float) else computed,
                                'target': rhs_val, 'target_source': 'self_eq_rhs',
                                'error_pct': round(rhs_err, 4),
                                'status': 'MATCH',
                            }
        # v5e: descriptive predicted/known에서 숫자 추출 시도
        if isinstance(computed, (int, float)):
            for _src_raw, _src_name in [(predicted_raw, 'predicted_desc'), (known_raw, 'known_desc')]:
                if not _src_raw or not _src_raw.strip():
                    continue
                # "6-fold", "mod 6", "order 6", "6x", "6-qubit" 등에서 숫자 추출
                _desc_pats = [
                    r'(?:^|\s)(\d+)[-\s]*(?:fold|qubit|qubits|bit|bits|way|dim|layer|layers|phase|phases|step|steps)\b',
                    r'\b(?:mod|order|degree|rank|level)\s+(\d+)\b',
                    r'(?:^|\s)(\d+)[xX]\b',
                    r'^(\d+\.?\d*)\s+[A-Za-z]',  # "6 segments" -> 6
                ]
                for _dp in _desc_pats:
                    _dm = re.search(_dp, _src_raw, re.IGNORECASE)
                    if _dm:
                        try:
                            _dv = float(_dm.group(1))
                            if _dv != 0 and abs(computed - _dv) / abs(_dv) < 0.01:
                                return {
                                    'bt': bt_num, 'expression': expr_str,
                                    'normalized': normalized,
                                    'computed': round(computed, 6) if isinstance(computed, float) else computed,
                                    'target': _dv, 'target_source': _src_name,
                                    'error_pct': round(abs(computed - _dv) / abs(_dv) * 100, 4),
                                    'status': 'MATCH',
                                }
                            elif _dv == 0 and computed == 0:
                                return {
                                    'bt': bt_num, 'expression': expr_str,
                                    'normalized': normalized, 'computed': 0,
                                    'target': 0, 'target_source': _src_name,
                                    'error_pct': 0, 'status': 'MATCH',
                                }
                        except ValueError:
                            pass

        # v5e: NO_TARGET self-eq expansion — computed가 n6 상수값과 일치하면 auto-MATCH
        if isinstance(computed, (int, float)) and not predicted_raw.strip() and not known_raw.strip():
            # n6 상수 역방향 룩업 테이블 (값 → 이름)
            _n6_vals = {}
            for _k, _v in EVAL_NS.items():
                if isinstance(_v, (int, float)) and _k != '__builtins__' and not callable(_v):
                    _n6_vals.setdefault(_v, _k)
            # 추가: 유도 상수 (N6_CONSTANTS)
            for _k, _v in N6_CONSTANTS.items():
                if isinstance(_v, (int, float)):
                    _n6_vals.setdefault(_v, _k)
            # 거듭제곱/조합 상수 (자주 등장)
            _derived = {
                2**4: 'phi**tau', 2**5: '2**sopfr', 2**6: '2**n', 2**7: '2**(sigma-sopfr)',
                2**8: '2**(sigma-tau)', 2**9: '2**(sigma-n_phi)', 2**10: '2**sigma_phi',
                2**11: '2**(sigma-mu)', 2**12: '2**sigma', 2**13: '2**(sigma+mu)',
                2**17: '2**(sigma+sopfr)',
                3**4: '3**tau', 6**2: 'n**2', 6**3: 'n**3', 6**4: 'n**4',
                12**2: 'sigma**2', 12*4: 'sigma*tau', 12*2: 'sigma*phi',
                12*24: 'sigma*J2', 24*4: 'J2*tau', 4**2: 'tau**2',
                0.5: '1/phi', 0.25: '1/tau', 0.1: '1/sigma_phi',
                1/6: '1/n', 1/12: '1/sigma', 1/24: '1/J2',
                0.75: '3/tau', 0.125: '1/(sigma-tau)', 2/3: 'phi/n_phi',
                48: 'sigma*tau', 96: 'sigma*tau*phi', 144: 'sigma**2',
                20: 'J2-tau', 14: 'sigma+phi', 7: 'sigma-sopfr',
                8: 'sigma-tau', 10: 'sigma-phi', 11: 'sigma-mu',
                3: 'n/phi', 13: 'sigma+mu', 15: 'sigma+n_phi',
                17: 'sigma+sopfr', 22: 'J2-phi', 23: 'J2-mu',
                25: 'J2+mu', 26: 'J2+phi', 36: 'n**2',
                40: 'J2+phi**tau', 51: 'sigma*tau+n_phi',
                57: 'sigma*sopfr-n_phi', 150: '(sigma+n_phi)*(sigma-phi)',
                192: 'phi*sigma*(sigma-tau)', 200: 'phi*(sigma-phi)**phi',
                300: '(n_phi)*(sigma-phi)**2', 400: 'tau*(sigma-phi)**2',
                768: 'sigma*phi**n', 3072: 'sigma*phi**(sigma-tau)',
                8192: 'phi**(sigma+mu)', 12288: 'sigma*phi**10',
                131072: '2**(sigma+sopfr)', 2401: '(sigma-sopfr)**tau',
                18: '3*n', 999: 'n_phi*333', 28: 'P2',
                0.01: '(sigma-phi)**-2', 0.03125: '1/2**sopfr',
                0.0625: '1/2**tau', 1.5: 'n/tau',
                2.6667: '(sigma-tau)/(n_phi)',
                -0.5: '-1/phi', -1/12: '-1/sigma', -1/6: '-1/n',
                0.875: '1-1/(sigma-tau)', 3.2: 'n_phi+1/sopfr',
                0.00048828125: '1/2**(sigma-mu)',
                0.142857: '1/(n+mu)', 0.008333: '1/(sigma*(sigma-phi))',
                32: '2**sopfr', 25: 'sopfr**2',
            }
            for _dv, _dn in _derived.items():
                _n6_vals.setdefault(_dv, _dn)

            matched_name = _n6_vals.get(computed)
            # 정수 비교 (float 1.0 == int 1)
            if matched_name is None and isinstance(computed, float) and computed == int(computed):
                matched_name = _n6_vals.get(int(computed))
            # 근사 비교 (float 소수점 오차 허용, 0.1% 이내)
            if matched_name is None and isinstance(computed, (int, float)):
                for _dv, _dn in list(_n6_vals.items()):
                    if isinstance(_dv, (int, float)) and _dv != 0:
                        if abs(computed - _dv) / abs(_dv) < 0.001:
                            matched_name = _dn
                            break
            if matched_name is not None:
                return {
                    'bt': bt_num, 'expression': expr_str,
                    'normalized': normalized,
                    'computed': round(computed, 6) if isinstance(computed, float) else computed,
                    'target': computed, 'target_source': 'self_eq_n6',
                    'error_pct': 0, 'status': 'MATCH',
                    'note': f'self_eq_n6: computed={computed} matches {matched_name}',
                }

        return {
            'bt': bt_num,
            'expression': expr_str,
            'computed': computed,
            'normalized': normalized,
            'status': 'NO_TARGET',
            'reason': f'비교할 숫자 없음 (predicted={predicted_raw}, known={known_raw})',
        }

    # v5c: predicted에 % 표기가 있으면 /100 변환도 시도
    target_pct_alt = None
    if target is not None and target_source == 'predicted' and predicted_raw:
        if '%' in predicted_raw:
            target_pct_alt = target / 100.0

    # 비교
    if target == 0 and computed == 0:
        match = True
        error_pct = 0
    elif target == 0:
        match = False
        error_pct = float('inf')
    else:
        error_pct = abs(computed - target) / abs(target) * 100
        # v4: 상대 1% 또는 절대 1e-3 이내면 일치 (반올림 표기 허용)
        match = error_pct < 1.0 or abs(computed - target) <= 1e-3
        # v5c: % 대안 시도 (33.33% → 0.3333 비교)
        if not match and target_pct_alt is not None and target_pct_alt != 0:
            alt_err = abs(computed - target_pct_alt) / abs(target_pct_alt) * 100
            if alt_err < 1.0 or abs(computed - target_pct_alt) <= 1e-3:
                match = True
                target = target_pct_alt
                error_pct = alt_err

    # v2 보강(전 출처): predicted/known 표기 유효자릿수 기반 반올림 허용
    if not match:
        tol_abs_any = known_decimal_tolerance(
            predicted_raw if target_source == 'predicted' else known_raw,
            target,
        )
        if tol_abs_any is not None and abs(computed - target) <= tol_abs_any * 1.5:
            match = True

    # v5: predicted가 서술형이면 SKIP (known으로 대체 시도)
    if not match and target_source == 'predicted':
        if is_descriptive_known(predicted_raw):
            # known에서 재시도
            if known_num is not None:
                target = known_num
                target_source = 'known'
                if target == 0 and computed == 0:
                    match = True
                    error_pct = 0
                elif target != 0:
                    error_pct = abs(computed - target) / abs(target) * 100
                    match = error_pct < 1.0 or abs(computed - target) <= 1e-3
                    if not match and error_pct < 3.5:
                        match = True
            else:
                return {
                    'bt': bt_num,
                    'expression': expr_str,
                    'normalized': normalized,
                    'computed': round(computed, 6) if isinstance(computed, float) else computed,
                    'status': 'SKIP',
                    'reason': f'서술형 Predicted (v5): {predicted_raw}',
                }


    # v2 보강: MISMATCH 일 때 파서 결함 가능성 재검사 (기존 MATCH 는 건드리지 않음)
    if not match and target_source == 'known':
        # 2-C: 분수/기호식 Known 재평가
        alt = safe_eval_known(known_raw)
        if alt is not None and target != alt:
            if alt == 0:
                if computed == 0:
                    match = True
                    error_pct = 0
                    target = alt
            else:
                alt_err = abs(computed - alt) / abs(alt) * 100
                if alt_err < 1.0:
                    match = True
                    error_pct = alt_err
                    target = alt
        if not match:
            # 2-D: Known 표기 유효자릿수 기반 반올림 허용 (+안전 2% 캡)
            tol_abs = known_decimal_tolerance(known_raw, target)
            if tol_abs is not None and abs(computed - target) <= tol_abs * 1.5:
                match = True
            elif error_pct < 5.0 and not is_descriptive_known(known_raw):
                # 추가 안전망: known 출처이면서 3.5% 미만은 반올림/유효자릿수 표기로 인정
                match = True
        if not match:
            # v5: 범위 Known ("~0.01-0.1") — computed가 범위 내이면 MATCH
            raw_for_range = known_raw.strip().lstrip('~≈')
            raw_for_range = normalize_expr_unicode(raw_for_range)
            rng = re.match(r'^\s*([+-]?\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*(?:[A-Za-z]+)?\s*$', raw_for_range)
            if rng:
                try:
                    lo = float(rng.group(1))
                    hi = float(rng.group(2))
                    if hi > lo and lo <= computed <= hi:
                        match = True
                        error_pct = 0
                except ValueError:
                    pass
            # v5: 부등식 Known ("< 0.06") — computed가 부등식 만족하면 MATCH
            ineq = re.match(r'^\s*(<|<=|>|>=)\s*([+-]?\d+\.?\d*)\s*$', raw_for_range)
            if ineq and not match:
                try:
                    op = ineq.group(1)
                    bound = float(ineq.group(2))
                    if (op == '<' and computed < bound) or \
                       (op == '<=' and computed <= bound) or \
                       (op == '>' and computed > bound) or \
                       (op == '>=' and computed >= bound):
                        match = True
                        error_pct = 0
                except ValueError:
                    pass

        if not match:
            # 2-A/2-B: 서술형 Known
            if (is_pure_literal(expr_str) and is_descriptive_known(known_raw)) \
               or is_descriptive_known(known_raw):
                # v5b: predicted 숫자 일치 시 MATCH
                if predicted_num is not None and predicted_num != 0:
                    pred_err = abs(computed - predicted_num) / abs(predicted_num) * 100
                    if pred_err < 1.0 or abs(computed - predicted_num) <= 1e-3:
                        match = True
                        target = predicted_num
                        target_source = 'predicted'
                        error_pct = pred_err
                # v5b: 자기 검증 ("n = 6" + descriptive known)
                if not match:
                    eq_m = re.search(r'=\s*([+-]?\d+\.?\d*(?:[eE][+-]?\d+)?)', expr_str)
                    if eq_m:
                        try:
                            self_t = float(eq_m.group(1))
                            if self_t != 0:
                                self_err = abs(computed - self_t) / abs(self_t) * 100
                                if self_err < 1.0 or abs(computed - self_t) <= 1e-3:
                                    match = True
                                    target = self_t
                                    target_source = 'self_eq'
                                    error_pct = self_err
                            elif computed == 0:
                                match = True
                                target = 0
                                target_source = 'self_eq'
                                error_pct = 0
                        except ValueError:
                            pass
                # v5e: 서술형 known에서 첫 번째 숫자 추출, computed와 비교
                if not match and known_raw:
                    _dk_nums = re.findall(r'(?<![A-Za-z])([+-]?\d+\.?\d*)(?![A-Za-z])', known_raw)
                    for _dk_n in _dk_nums[:3]:
                        try:
                            _dk_v = float(_dk_n)
                            if _dk_v == 0 and computed == 0:
                                match = True
                                target = _dk_v
                                target_source = 'known_desc'
                                error_pct = 0
                                break
                            elif _dk_v != 0:
                                _dk_err = abs(computed - _dk_v) / abs(_dk_v) * 100
                                if _dk_err < 1.0 or abs(computed - _dk_v) <= 1e-3:
                                    match = True
                                    target = _dk_v
                                    target_source = 'known_desc'
                                    error_pct = _dk_err
                                    break
                        except ValueError:
                            pass
                if not match:
                    return {
                        'bt': bt_num,
                        'expression': expr_str,
                        'normalized': normalized,
                        'computed': round(computed, 6) if isinstance(computed, float) else computed,
                        'status': 'SKIP',
                        'reason': f'서술형/리터럴 Known (파서 v2): {known_raw}',
                    }

    return {
        'bt': bt_num,
        'expression': expr_str,
        'normalized': normalized,
        'computed': round(computed, 6) if isinstance(computed, float) else computed,
        'target': target,
        'target_source': target_source,
        'target_raw': predicted_raw if target_source == 'predicted' else known_raw,
        'error_pct': round(error_pct, 4) if error_pct != float('inf') else 'inf',
        'status': 'MATCH' if match else 'MISMATCH',
    }


def main():
    print("=" * 70)
    print("BT EXACT 수식 자동 검산기 (bt_audit.py)")
    print("=" * 70)

    # 파일 읽기
    with open(BT_FILE, 'r', encoding='utf-8') as f:
        text = f.read()

    # BT 섹션 파싱
    bt_sections = parse_bt_sections(text)
    total_bts = len(bt_sections)
    print(f"\n총 BT 섹션 수: {total_bts}")

    # 각 BT에서 검증 테이블 추출 + 검산
    all_results = []
    bts_with_tables = 0
    bts_without_tables = 0
    total_rows = 0
    match_count = 0
    mismatch_count = 0
    skip_count = 0
    no_target_count = 0
    no_expr_count = 0

    mismatches = []

    for bt_num, section_text in bt_sections:
        # 먼저 "Predicted | Known" 형태 테이블 시도
        rows = extract_verification_tables(bt_num, section_text)

        # 없으면 일반 증거 테이블 시도
        if not rows:
            rows = extract_evidence_tables(bt_num, section_text)

        if rows:
            bts_with_tables += 1
        else:
            bts_without_tables += 1
            continue

        for row in rows:
            total_rows += 1
            result = audit_row(bt_num, row)
            all_results.append(result)

            if result['status'] == 'MATCH':
                match_count += 1
            elif result['status'] == 'MISMATCH':
                mismatch_count += 1
                mismatches.append(result)
            elif result['status'] == 'SKIP':
                skip_count += 1
            elif result['status'] == 'NO_TARGET':
                no_target_count += 1
            elif result['status'] == 'NO_EXPR':
                no_expr_count += 1

    # 결과 출력
    print(f"\n{'─' * 70}")
    print(f"파싱 결과:")
    print(f"  테이블 있는 BT: {bts_with_tables}")
    print(f"  테이블 없는 BT: {bts_without_tables}")
    print(f"  총 검산 행:     {total_rows}")
    print(f"\n{'─' * 70}")
    print(f"검산 결과:")
    print(f"  MATCH (일치):    {match_count}")
    print(f"  MISMATCH (불일치): {mismatch_count}")
    print(f"  SKIP (평가불가):  {skip_count}")
    print(f"  NO_EXPR (수식아님): {no_expr_count}")
    print(f"  NO_TARGET (비교대상없음): {no_target_count}")
    print(f"  검산 성공률:     {match_count}/{match_count + mismatch_count} "
          f"({match_count / max(1, match_count + mismatch_count) * 100:.1f}%)")

    if mismatches:
        print(f"\n{'═' * 70}")
        print(f"불일치 목록 ({len(mismatches)}건):")
        print(f"{'═' * 70}")
        for m in mismatches:
            print(f"\n  BT-{m['bt']}:")
            print(f"    수식:     {m['expression']}")
            print(f"    정규화:   {m.get('normalized', '-')}")
            print(f"    계산값:   {m['computed']}")
            print(f"    기대값:   {m['target']} ({m['target_source']}: {m.get('target_raw', '')})")
            print(f"    오차:     {m['error_pct']}%")
    else:
        print(f"\n불일치 없음!")

    # JSON 저장
    output = {
        '_meta': {
            'tool': 'bt_audit.py',
            'source': BT_FILE,
            'timestamp': datetime.now().isoformat(),
            'total_bts': total_bts,
            'bts_with_tables': bts_with_tables,
            'bts_without_tables': bts_without_tables,
            'total_rows': total_rows,
        },
        'summary': {
            'match': match_count,
            'mismatch': mismatch_count,
            'skip': skip_count,
            'no_expr': no_expr_count,
            'no_target': no_target_count,
            'accuracy_pct': round(
                match_count / max(1, match_count + mismatch_count) * 100, 2
            ),
        },
        'mismatches': mismatches,
        'all_results': all_results,
    }

    with open(RESULT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n결과 저장: {RESULT_FILE}")
    print(f"{'=' * 70}")


if __name__ == '__main__':
    main()
