# CDO 기반 CI 전 리포 도입 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 7개 연결 프로젝트(TECS-L, anima, sedi, n6-architecture, brainwire, papers, hexa-lang)에 CDO(Convergence-Driven Operations) 원칙 기반 CI 파이프라인을 구축하여 오류 재발을 방지하고 100% 수렴을 달성한다.

**Architecture:** 공유 CDO 검증 스크립트(.shared/ci/)를 TECS-L에 원본으로 두고, 심링크를 통해 전 리포에서 재사용한다. 각 리포의 ci.yml은 anima의 성숙한 패턴(트러블슈팅 주석, ignore 목록, 캐시 전략)을 표준으로 따른다. CDO JSON 스키마 검증은 공유 스크립트로 모든 리포에 동일하게 적용한다.

**Tech Stack:** GitHub Actions, Python 3.12/3.13, Rust stable, pytest, py_compile, cargo test

**Reference CI:** anima/.github/workflows/ci.yml (195줄, 가장 성숙한 패턴)

---

## File Structure

### 공유 인프라 (TECS-L/.shared/ci/)

| File | Responsibility |
|------|---------------|
| `.shared/ci/validate_cdo.py` | CDO JSON 스키마 검증 (모든 리포 공통) |
| `.shared/ci/check_syntax.py` | Python py_compile 일괄 검사 (디렉토리 기반) |

### 리포별 CI 워크플로우

| Repo | File | Jobs |
|------|------|------|
| TECS-L | `.github/workflows/ci.yml` | verify-syntax, python-tests, rust-tests, cdo-validate |
| brainwire | `.github/workflows/ci.yml` | verify-syntax, python-tests, cdo-validate |
| n6-architecture | `.github/workflows/ci.yml` | verify-syntax, rust-tests, cdo-validate (nexus-ci.yml 대체) |
| papers | `.github/workflows/ci.yml` | markdown-check, cdo-validate |
| sedi | `.github/workflows/ci.yml` | (기존 유지) + cdo-validate job 추가 |
| anima | `.github/workflows/ci.yml` | (기존 유지) + cdo-validate job 추가 |

---

## Task 1: CDO 검증 공유 스크립트 생성

**Files:**
- Create: `.shared/ci/validate_cdo.py`
- Create: `.shared/ci/check_syntax.py`

- [ ] **Step 1: CDO JSON 검증 스크립트 작성**

```python
#!/usr/bin/env python3
"""CDO JSON schema validator — all config JSONs must have _meta field.

Usage: python3 validate_cdo.py [directory] [--strict]
  directory: scan target (default: current directory)
  --strict: fail on missing _meta (default: warn only)

Exit codes: 0=pass, 1=violations found
"""
import json
import os
import sys

SKIP_DIRS = {'.git', 'node_modules', 'target', '__pycache__', '.local', 'venv'}
SKIP_FILES = {'package.json', 'package-lock.json', 'tsconfig.json',
              'Cargo.lock', '.claude/settings.local.json'}

def scan_jsons(directory):
    results = {'ok': [], 'warn': [], 'fail': []}
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in sorted(files):
            if not f.endswith('.json'):
                continue
            rel = os.path.relpath(os.path.join(root, f), directory)
            if any(rel.endswith(s) for s in SKIP_FILES):
                continue
            if '.claude/' in rel:
                continue
            path = os.path.join(root, f)
            try:
                with open(path) as fh:
                    data = json.load(fh)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                results['fail'].append((rel, f'parse error: {e}'))
                continue
            if not isinstance(data, dict):
                continue  # arrays etc. are not config JSONs
            if '_meta' in data:
                meta = data['_meta']
                missing = [k for k in ('description', 'updated', 'schema_version')
                           if k not in meta]
                if missing:
                    results['warn'].append((rel, f'_meta missing fields: {missing}'))
                else:
                    results['ok'].append(rel)
            else:
                results['warn'].append((rel, 'no _meta field'))
    return results

def main():
    directory = '.'
    strict = False
    for arg in sys.argv[1:]:
        if arg == '--strict':
            strict = True
        else:
            directory = arg

    results = scan_jsons(directory)
    total = len(results['ok']) + len(results['warn']) + len(results['fail'])

    print(f"CDO JSON Validation: {directory}")
    print(f"  OK: {len(results['ok'])}  Warn: {len(results['warn'])}  Fail: {len(results['fail'])}  Total: {total}")

    if results['ok']:
        print("\n[OK] CDO compliant:")
        for f in results['ok']:
            print(f"  {f}")

    if results['warn']:
        print("\n[WARN] Missing CDO structure:")
        for f, msg in results['warn']:
            print(f"  {f}: {msg}")

    if results['fail']:
        print("\n[FAIL] Broken JSON:")
        for f, msg in results['fail']:
            print(f"  {f}: {msg}")

    convergence = len(results['ok']) / total * 100 if total > 0 else 100
    print(f"\nConvergence: {convergence:.0f}% ({len(results['ok'])}/{total})")

    if results['fail']:
        sys.exit(1)
    if strict and results['warn']:
        sys.exit(1)
    sys.exit(0)

if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Python syntax check 스크립트 작성**

```python
#!/usr/bin/env python3
"""Batch py_compile check for CI.

Usage: python3 check_syntax.py dir1 [dir2 ...] [--recursive]
Exit codes: 0=all OK, 1=syntax errors found
"""
import os
import py_compile
import sys

def check_dir(directory, recursive=False):
    broken = []
    checked = 0
    if recursive:
        for root, _, files in os.walk(directory):
            if '__pycache__' in root or '.git' in root:
                continue
            for f in sorted(files):
                if f.endswith('.py') and not f.startswith('__'):
                    path = os.path.join(root, f)
                    checked += 1
                    try:
                        py_compile.compile(path, doraise=True)
                    except py_compile.PyCompileError as e:
                        broken.append((path, str(e)))
    else:
        if not os.path.isdir(directory):
            return 0, []
        for f in sorted(os.listdir(directory)):
            if f.endswith('.py') and not f.startswith('__'):
                path = os.path.join(directory, f)
                if os.path.isfile(path):
                    checked += 1
                    try:
                        py_compile.compile(path, doraise=True)
                    except py_compile.PyCompileError as e:
                        broken.append((path, str(e)))
    return checked, broken

def main():
    dirs = []
    recursive = False
    for arg in sys.argv[1:]:
        if arg == '--recursive':
            recursive = True
        else:
            dirs.append(arg)

    if not dirs:
        dirs = ['.']

    total_checked = 0
    all_broken = []
    for d in dirs:
        checked, broken = check_dir(d, recursive)
        total_checked += checked
        all_broken.extend(broken)

    print(f"Syntax check: {total_checked} files, {len(all_broken)} broken")
    for path, err in all_broken:
        print(f"  FAIL: {path}")
        print(f"        {err}")

    sys.exit(1 if all_broken else 0)

if __name__ == '__main__':
    main()
```

- [ ] **Step 3: 로컬에서 두 스크립트 테스트**

Run:
```bash
python3 .shared/ci/validate_cdo.py .shared/
python3 .shared/ci/check_syntax.py . --recursive | head -5
```

Expected: validate_cdo shows convergence_ops.json as OK, check_syntax shows file count

- [ ] **Step 4: 커밋**

```bash
git add .shared/ci/validate_cdo.py .shared/ci/check_syntax.py
git commit -m "feat: add shared CDO CI scripts (validate_cdo.py, check_syntax.py)"
```

---

## Task 2: TECS-L CI 워크플로우 생성

**Files:**
- Create: `.github/workflows/ci.yml`
- Test: n6-replication/tests/tier1/, tests/

- [ ] **Step 1: TECS-L ci.yml 작성**

```yaml
# ============================================================================
# CI — TECS-L 통합 CI 파이프라인
# ============================================================================
#
# [트러블슈팅 — 재발 방지 기록]
#
# 2026-04-03: 초기 구축
#   구조: anima CI 패턴 기반 (트러블슈팅 주석, ignore 목록, 캐시)
#   CDO: P1(1회 해결) + P2(규칙 승격) + P5(Antifragile) 적용
#
# [ignore 목록 관리 규칙]
#   - calc/ 스크립트: 독립 실행 도구 → syntax check만 (pytest 제외)
#   - engines/: 모델 아키텍처 → syntax check만 (GPU 의존)
#   - scripts/: 분석 유틸리티 → syntax check만 (외부 데이터 의존)
#   - verify/: 가설 검증 → syntax check만 (수동 실행 전제)
#   - 새 test_*.py 추가 시 반드시 CI 호환 확인!
#
# [CDO 수렴 원칙]
#   - CI 실패 → troubleshooting 주석 추가 (이 파일 상단)
#   - 같은 실패 2회 → absolute_rule로 승격
#   - 목표: violations = 0, convergence = 100%
# ============================================================================

name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  verify-syntax:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Check root module syntax
        run: python3 .shared/ci/check_syntax.py .
      - name: Check calc/ syntax
        run: python3 .shared/ci/check_syntax.py calc --recursive
      - name: Check verify/ syntax
        run: python3 .shared/ci/check_syntax.py verify --recursive

  python-tests:
    needs: verify-syntax
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.12', '3.13']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ matrix.python-version }}
          restore-keys: ${{ runner.os }}-pip-
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pytest numpy scipy sympy
      - name: Run Tier 1 tests (8 Major Discoveries)
        env:
          PYTHONPATH: .
        run: python -m pytest n6-replication/tests/tier1/ -x -q
      - name: Run unit tests
        env:
          PYTHONPATH: .
        run: python -m pytest tests/ -x -q

  rust-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - name: Cache cargo
        uses: actions/cache@v4
        with:
          path: |
            ~/.cargo/bin/
            ~/.cargo/registry/index/
            ~/.cargo/registry/cache/
            ~/.cargo/git/db/
            tecsrs/target/
          key: ${{ runner.os }}-cargo-${{ hashFiles('tecsrs/Cargo.lock') }}
          restore-keys: ${{ runner.os }}-cargo-
      - name: Build tecsrs
        working-directory: tecsrs
        run: cargo build
      - name: Test tecsrs
        working-directory: tecsrs
        run: cargo test

  cdo-validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: CDO JSON schema validation
        run: python3 .shared/ci/validate_cdo.py . --strict
```

- [ ] **Step 2: 로컬에서 워크플로우 YAML 문법 검증**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))" 2>/dev/null || python3 -c "import json; print('yaml not available, check manually')"`

- [ ] **Step 3: 커밋**

```bash
git add .github/workflows/ci.yml
git commit -m "feat: add TECS-L CI pipeline (syntax+tests+rust+CDO)"
```

---

## Task 3: brainwire CI 워크플로우 생성

**Files:**
- Create: `~/Dev/brainwire/.github/workflows/ci.yml`

- [ ] **Step 1: .github/workflows/ 디렉토리 확인**

Run: `mkdir -p ~/Dev/brainwire/.github/workflows`

- [ ] **Step 2: brainwire ci.yml 작성**

```yaml
# ============================================================================
# CI — BrainWire 통합 CI 파이프라인
# ============================================================================
#
# [트러블슈팅 — 재발 방지 기록]
#
# 2026-04-03: 초기 구축
#   구조: anima CI 패턴 기반
#   CDO: 수렴 기반 운영 적용
#
# [ignore 목록 관리 규칙]
#   - HW 의존 테스트 (EEG, 하드웨어): -k 필터로 제외
#   - 새 test_*.py 추가 시 반드시 CI 호환 확인!
# ============================================================================

name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  verify-syntax:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Check package syntax
        run: |
          python3 -c "
          import py_compile, os
          broken = []
          for root, _, files in os.walk('brainwire'):
              if '__pycache__' in root: continue
              for f in sorted(files):
                  if f.endswith('.py') and not f.startswith('__'):
                      try: py_compile.compile(os.path.join(root, f), doraise=True)
                      except: broken.append(os.path.join(root, f))
          print(f'Broken: {len(broken)}')
          if broken: print(broken); exit(1)
          "

  python-tests:
    needs: verify-syntax
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.12', '3.13']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Cache pip
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ matrix.python-version }}-${{ hashFiles('pyproject.toml') }}
          restore-keys: ${{ runner.os }}-pip-${{ matrix.python-version }}-
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pytest pyyaml numpy scipy
          pip install -e . || true
      - name: Run tests
        run: |
          python -m pytest tests/ -x -q \
            --ignore=tests/test_eeg_feedback.py \
            --ignore=tests/test_hardware.py \
            -k "not eeg and not brainflow and not serial"
          # [ignore 사유]
          #   test_eeg_feedback.py — EEG 하드웨어 의존 (brainflow)
          #   test_hardware.py    — 직접 HW 접근 필요

  cdo-validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: CDO JSON schema validation
        run: |
          python3 -c "
          import json, os, sys
          ok = warn = fail = 0
          for root, _, files in os.walk('.'):
              if '.git' in root or '__pycache__' in root: continue
              for f in files:
                  if not f.endswith('.json'): continue
                  path = os.path.join(root, f)
                  try:
                      data = json.load(open(path))
                      if not isinstance(data, dict): continue
                      if '_meta' in data: ok += 1
                      else: warn += 1; print(f'WARN: {path} — no _meta')
                  except: fail += 1; print(f'FAIL: {path}')
          print(f'CDO: ok={ok} warn={warn} fail={fail}')
          if fail: sys.exit(1)
          "
```

- [ ] **Step 3: 커밋 (brainwire 리포에서)**

```bash
cd ~/Dev/brainwire
git add .github/workflows/ci.yml
git commit -m "feat: add CI pipeline (syntax+tests+CDO validation)"
```

---

## Task 4: n6-architecture CI 확장

**Files:**
- Modify: `~/Dev/n6-architecture/.github/workflows/nexus-ci.yml` → rename to `ci.yml`

- [ ] **Step 1: 기존 nexus-ci.yml 삭제하고 통합 ci.yml 작성**

```yaml
# ============================================================================
# CI — n6-architecture 통합 CI 파이프라인
# ============================================================================
#
# [트러블슈팅 — 재발 방지 기록]
#
# 2026-04-03: nexus-ci.yml → ci.yml 통합 확장
#   이전: paths: ['tools/nexus/**'] 필터로 Rust만 검사
#   변경: 전체 push/PR에서 Python + Rust + CDO 검증
#
# [구조]
#   - Python tools/*.py: syntax check (pytest 미대상, 독립 실행 도구)
#   - Rust tools/nexus: cargo check + test (기존 유지)
#   - CDO: config JSON 스키마 검증
# ============================================================================

name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  verify-syntax:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Check Python tool syntax
        run: |
          python3 -c "
          import py_compile, os, glob
          broken = []
          for f in sorted(glob.glob('tools/*.py')):
              try: py_compile.compile(f, doraise=True)
              except: broken.append(f)
          for f in sorted(glob.glob('*.py')):
              try: py_compile.compile(f, doraise=True)
              except: broken.append(f)
          print(f'Broken: {len(broken)}')
          if broken: print(broken); exit(1)
          "

  rust-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - name: Cache cargo
        uses: actions/cache@v4
        with:
          path: |
            ~/.cargo/bin/
            ~/.cargo/registry/index/
            ~/.cargo/registry/cache/
            ~/.cargo/git/db/
            tools/nexus/target/
          key: ${{ runner.os }}-cargo-${{ hashFiles('tools/nexus/Cargo.lock') }}
          restore-keys: ${{ runner.os }}-cargo-
      - name: Check NEXUS-6
        working-directory: tools/nexus
        run: cargo check
      - name: Test NEXUS-6
        working-directory: tools/nexus
        run: cargo test

  cdo-validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: CDO JSON schema validation
        run: |
          python3 -c "
          import json, os, sys
          ok = warn = fail = 0
          skip = {'.git', 'target', '__pycache__', 'node_modules'}
          for root, dirs, files in os.walk('.'):
              dirs[:] = [d for d in dirs if d not in skip]
              for f in files:
                  if not f.endswith('.json'): continue
                  if '.claude/' in root: continue
                  path = os.path.join(root, f)
                  try:
                      data = json.load(open(path))
                      if not isinstance(data, dict): continue
                      if '_meta' in data: ok += 1
                      else: warn += 1; print(f'WARN: {path} — no _meta')
                  except: fail += 1; print(f'FAIL: {path}')
          print(f'CDO: ok={ok} warn={warn} fail={fail}')
          if fail: sys.exit(1)
          "
```

- [ ] **Step 2: 기존 워크플로우 제거 + 새 파일 생성**

```bash
cd ~/Dev/n6-architecture
rm .github/workflows/nexus-ci.yml
# (ci.yml 생성은 Write 도구로)
```

- [ ] **Step 3: 커밋**

```bash
cd ~/Dev/n6-architecture
git add .github/workflows/
git commit -m "feat: expand CI from nexus-only to full pipeline (syntax+rust+CDO)"
```

---

## Task 5: sedi CI에 CDO 검증 추가

**Files:**
- Modify: `~/Dev/sedi/.github/workflows/ci.yml`

- [ ] **Step 1: 기존 ci.yml에 cdo-validate job 추가**

기존 ci.yml 끝에 추가:

```yaml

  cdo-validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: CDO JSON schema validation
        run: |
          python3 -c "
          import json, os, sys
          ok = warn = fail = 0
          skip = {'.git', 'target', '__pycache__', 'node_modules'}
          for root, dirs, files in os.walk('.'):
              dirs[:] = [d for d in dirs if d not in skip]
              for f in files:
                  if not f.endswith('.json'): continue
                  if '.claude/' in root: continue
                  path = os.path.join(root, f)
                  try:
                      data = json.load(open(path))
                      if not isinstance(data, dict): continue
                      if '_meta' in data: ok += 1
                      else: warn += 1; print(f'WARN: {path} — no _meta')
                  except: fail += 1; print(f'FAIL: {path}')
          print(f'CDO: ok={ok} warn={warn} fail={fail}')
          if fail: sys.exit(1)
          "
```

- [ ] **Step 2: 커밋**

```bash
cd ~/Dev/sedi
git add .github/workflows/ci.yml
git commit -m "feat: add CDO JSON validation to CI"
```

---

## Task 6: anima CI에 CDO 검증 추가

**Files:**
- Modify: `~/Dev/anima/.github/workflows/ci.yml`

- [ ] **Step 1: 기존 ci.yml에 cdo-validate job 추가**

anima ci.yml의 `rust-tests` job 아래에 추가 (동일 패턴):

```yaml

  cdo-validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: CDO JSON schema validation
        run: |
          python3 -c "
          import json, os, sys
          ok = warn = fail = 0
          skip = {'.git', 'target', '__pycache__', 'node_modules', 'venv'}
          for root, dirs, files in os.walk('.'):
              dirs[:] = [d for d in dirs if d not in skip]
              for f in files:
                  if not f.endswith('.json'): continue
                  if '.claude/' in root: continue
                  path = os.path.join(root, f)
                  try:
                      data = json.load(open(path))
                      if not isinstance(data, dict): continue
                      if '_meta' in data: ok += 1
                      else: warn += 1; print(f'WARN: {path} — no _meta')
                  except: fail += 1; print(f'FAIL: {path}')
          print(f'CDO: ok={ok} warn={warn} fail={fail}')
          if fail: sys.exit(1)
          "
```

- [ ] **Step 2: 커밋**

```bash
cd ~/Dev/anima
git add .github/workflows/ci.yml
git commit -m "feat: add CDO JSON validation to CI"
```

---

## Task 7: papers CI 워크플로우 생성

**Files:**
- Create: `~/Dev/papers/.github/workflows/ci.yml`

- [ ] **Step 1: papers ci.yml 작성 (경량)**

```yaml
# ============================================================================
# CI — Papers 검증 파이프라인
# ============================================================================
#
# [구조]
#   - markdown-check: 논문 파일 존재 확인 + 링크 무결성
#   - cdo-validate: manifest.json 스키마 검증
# ============================================================================

name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  markdown-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check paper files exist
        run: |
          echo "Checking paper directories..."
          for dir in tecs-l anima sedi brainwire; do
            if [ -d "$dir" ]; then
              count=$(find "$dir" -name "*.md" | wc -l)
              echo "  $dir: $count papers"
            fi
          done
      - name: Verify manifest
        run: |
          python3 -c "
          import json, sys
          try:
              data = json.load(open('manifest.json'))
              print(f'Manifest: {len(data)} entries')
          except Exception as e:
              print(f'FAIL: manifest.json — {e}')
              sys.exit(1)
          "

  cdo-validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: CDO JSON schema validation
        run: |
          python3 -c "
          import json, os, sys
          ok = warn = fail = 0
          for root, dirs, files in os.walk('.'):
              dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__'}]
              for f in files:
                  if not f.endswith('.json'): continue
                  if '.claude/' in root: continue
                  path = os.path.join(root, f)
                  try:
                      data = json.load(open(path))
                      if not isinstance(data, dict): continue
                      if '_meta' in data: ok += 1
                      else: warn += 1; print(f'WARN: {path} — no _meta')
                  except: fail += 1; print(f'FAIL: {path}')
          print(f'CDO: ok={ok} warn={warn} fail={fail}')
          if fail: sys.exit(1)
          "
```

- [ ] **Step 2: 커밋**

```bash
cd ~/Dev/papers
mkdir -p .github/workflows
# (ci.yml 생성은 Write 도구로)
git add .github/workflows/ci.yml
git commit -m "feat: add CI pipeline (markdown check + CDO validation)"
```

---

## Task 8: convergence_ops.json 상태 업데이트 + 동기화

**Files:**
- Modify: `.shared/config/convergence_ops.json`

- [ ] **Step 1: per_project_status 업데이트**

convergence_ops.json의 per_project_status를 CI 도입 반영하여 갱신:

```json
"per_project_status": {
    "anima": {
      "json_count": 19,
      "ok": 12,
      "in_progress": 7,
      "convergence_pct": "63%",
      "ci": "ci.yml (syntax+tests+rust+bench+CDO)",
      "exemplar": "runpod.json v2.0 (12 rules, 15 issues, 0 violations)"
    },
    "TECS-L": {
      "json_count": "TBD",
      "convergence_pct": "TBD",
      "ci": "ci.yml (syntax+tier1+rust+CDO)",
      "note": "convergence_ops.json origin"
    },
    "n6-architecture": {
      "json_count": "TBD",
      "convergence_pct": "TBD",
      "ci": "ci.yml (syntax+nexus-rust+CDO)"
    },
    "sedi": {
      "json_count": "TBD",
      "convergence_pct": "TBD",
      "ci": "ci.yml (rust+python+graph+CDO)"
    },
    "brainwire": {
      "json_count": "TBD",
      "convergence_pct": "TBD",
      "ci": "ci.yml (syntax+tests+CDO)"
    },
    "papers": {
      "json_count": "TBD",
      "convergence_pct": "TBD",
      "ci": "ci.yml (markdown+CDO)"
    },
    "hexa-lang": {
      "json_count": "TBD",
      "convergence_pct": "TBD",
      "ci": "TBD (repo structure TBD)"
    }
}
```

- [ ] **Step 2: CDO CI 규칙 추가**

convergence_ops.json의 adoption_checklist에 CI 항목 추가:

```json
"adoption_checklist": [
    "1. 프로젝트 내 모든 config JSON 목록화",
    "2. 각 JSON에 _meta (description, updated, schema_version) 추가",
    "3. 이슈가 있으면 troubleshooting_log 형태로 정리",
    "4. 반복 이슈는 absolute_rules로 승격",
    "5. convergence 추적 필드 추가",
    "6. 수렴 목표: 100% (모든 이슈 resolved, 모든 규칙 violations=0)",
    "7. CI 파이프라인 활성화 (ci.yml: syntax + tests + CDO validate)",
    "8. CI 실패 시 troubleshooting 주석 즉시 추가 (재발 방지)"
]
```

- [ ] **Step 3: 커밋**

```bash
git add .shared/config/convergence_ops.json
git commit -m "feat: update CDO status with CI adoption across all repos"
```

---

## Task 9: 전체 push + 검증

- [ ] **Step 1: TECS-L push**

```bash
cd ~/Dev/TECS-L && git push
```

- [ ] **Step 2: brainwire push**

```bash
cd ~/Dev/brainwire && git push
```

- [ ] **Step 3: n6-architecture push**

```bash
cd ~/Dev/n6-architecture && git push
```

- [ ] **Step 4: sedi push**

```bash
cd ~/Dev/sedi && git push
```

- [ ] **Step 5: anima push**

```bash
cd ~/Dev/anima && git push
```

- [ ] **Step 6: papers push**

```bash
cd ~/Dev/papers && git push
```

- [ ] **Step 7: GitHub Actions 결과 확인**

각 리포에서 CI 상태 확인:
```bash
for repo in TECS-L brainwire n6-architecture sedi anima papers; do
  echo "=== $repo ==="
  cd ~/Dev/$repo && gh run list --limit 1
  cd -
done
```

- [ ] **Step 8: 실패 시 CDO 프로세스 적용**

CI 실패 → ci.yml 상단 트러블슈팅 주석 추가 → 수정 → 재커밋
(CDO P1: 한 번만 겪기, P2: 규칙 승격)

---

## Summary

| Task | Repo | Action | Jobs |
|------|------|--------|------|
| 1 | TECS-L (.shared/) | CDO 공유 스크립트 | validate_cdo.py, check_syntax.py |
| 2 | TECS-L | CI 신규 | syntax + tier1 tests + rust + CDO |
| 3 | brainwire | CI 신규 | syntax + 21 tests + CDO |
| 4 | n6-architecture | CI 확장 | syntax + nexus rust + CDO |
| 5 | sedi | CDO 추가 | 기존 + CDO validate |
| 6 | anima | CDO 추가 | 기존 + CDO validate |
| 7 | papers | CI 신규 | markdown + CDO |
| 8 | convergence_ops | 상태 갱신 | CI 도입 반영 |
| 9 | 전체 | push + 검증 | GitHub Actions 확인 |
