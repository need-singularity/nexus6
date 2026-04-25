#!/usr/bin/env bash
# registry_sign.sh — SSH-key detached signature stub for falsifier registry (R5 OPT-B)
#
# STATUS: stub — sign mode no-ops with SKIPPED unless SIGNING_KEY env or
# git config user.signingkey points to a usable SSH private key.
#
# Modes:
#   sign     — sign design/hexa_sim/falsifiers.jsonl → falsifiers.jsonl.sig
#   verify   — verify existing falsifiers.jsonl.sig
#   status   — report whether signing key is configured
#
# Sentinel:
#   __REGISTRY_SIGN__ <SIGNED|VERIFIED|SKIPPED|ERROR> reason=<short_reason>
#
# Configuration:
#   SIGNING_KEY=/path/to/ssh_key  (env var, takes precedence)
#   git config user.signingkey /path/to/ssh_key  (fallback)
#   ALLOWED_SIGNERS=/path/to/allowed_signers  (env var or default ~/.ssh/allowed_signers)
#
# To activate (future):
#   1. Generate Ed25519 key:  ssh-keygen -t ed25519 -f ~/.ssh/nexus_signing
#   2. Build allowed_signers:  echo "nexus@local namespaces=\"file\" $(cut -d' ' -f1-2 ~/.ssh/nexus_signing.pub)" > ~/.ssh/allowed_signers
#   3. export SIGNING_KEY=~/.ssh/nexus_signing
#   4. bash tool/registry_sign.sh sign
#   5. bash tool/registry_sign.sh verify
#
# raw 73: minimal; raw 66: reason+fix trailers; raw 71: report-only (no auto-sign in CI).

set -uo pipefail

NEXUS_ROOT="${NEXUS_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null)}"
if [ -z "${NEXUS_ROOT}" ] || [ ! -d "${NEXUS_ROOT}" ]; then
    NEXUS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
fi

REGISTRY="${NEXUS_ROOT}/design/hexa_sim/falsifiers.jsonl"
SIG="${REGISTRY}.sig"
ALLOWED_SIGNERS="${ALLOWED_SIGNERS:-${HOME}/.ssh/allowed_signers}"
NAMESPACE="file"
IDENTITY="${SIGNING_IDENTITY:-nexus@local}"

MODE="${1:-status}"

resolve_key() {
    if [ -n "${SIGNING_KEY:-}" ] && [ -f "${SIGNING_KEY}" ]; then
        echo "${SIGNING_KEY}"
        return 0
    fi
    local cfg
    cfg=$(git -C "${NEXUS_ROOT}" config --get user.signingkey 2>/dev/null || true)
    if [ -n "${cfg}" ] && [ -f "${cfg}" ]; then
        echo "${cfg}"
        return 0
    fi
    return 1
}

emit() {
    local status="$1" reason="$2"
    echo "__REGISTRY_SIGN__ ${status} reason=${reason}"
}

case "${MODE}" in
    status)
        if ! command -v ssh-keygen >/dev/null 2>&1; then
            emit "SKIPPED" "no_ssh_keygen"
            exit 0
        fi
        if KEY=$(resolve_key); then
            echo "registry_sign: key=${KEY}"
            echo "registry_sign: registry=${REGISTRY}"
            [ -f "${SIG}" ] && echo "registry_sign: signature=${SIG} (present)" || echo "registry_sign: signature=(absent)"
            emit "SKIPPED" "status_only"
            exit 0
        fi
        emit "SKIPPED" "no_signing_key_configured"
        exit 0
        ;;

    sign)
        if ! command -v ssh-keygen >/dev/null 2>&1; then
            echo "registry_sign: ssh-keygen not on PATH" >&2
            echo "  reason: signing requires OpenSSH ssh-keygen" >&2
            echo "  fix: install openssh-client" >&2
            emit "SKIPPED" "no_ssh_keygen"
            exit 0
        fi
        if ! KEY=$(resolve_key); then
            echo "registry_sign: no signing key configured" >&2
            echo "  reason: SIGNING_KEY env unset and git config user.signingkey unset / not a file" >&2
            echo "  fix: export SIGNING_KEY=/path/to/ssh_key (Ed25519 recommended)" >&2
            emit "SKIPPED" "no_signing_key_configured"
            exit 0  # do not block CI
        fi
        if [ ! -f "${REGISTRY}" ]; then
            echo "registry_sign: registry missing at ${REGISTRY}" >&2
            echo "  reason: nothing to sign" >&2
            echo "  fix: ensure design/hexa_sim/falsifiers.jsonl exists" >&2
            emit "ERROR" "registry_missing"
            exit 1
        fi
        # Real signing path (not exercised in stub mode unless user authorized)
        if ssh-keygen -Y sign -f "${KEY}" -n "${NAMESPACE}" "${REGISTRY}" >/dev/null 2>&1; then
            # ssh-keygen writes ${REGISTRY}.sig automatically
            emit "SIGNED" "key=${KEY}"
            exit 0
        fi
        emit "ERROR" "ssh_keygen_sign_failed"
        exit 1
        ;;

    verify)
        if ! command -v ssh-keygen >/dev/null 2>&1; then
            emit "SKIPPED" "no_ssh_keygen"
            exit 0
        fi
        if [ ! -f "${SIG}" ]; then
            echo "registry_sign: no signature file at ${SIG}" >&2
            echo "  reason: signing not activated yet (R5 OPT-B stub)" >&2
            echo "  fix: run 'bash tool/registry_sign.sh sign' with SIGNING_KEY set" >&2
            emit "SKIPPED" "no_signature_file"
            exit 0
        fi
        if [ ! -f "${ALLOWED_SIGNERS}" ]; then
            echo "registry_sign: no allowed_signers at ${ALLOWED_SIGNERS}" >&2
            echo "  reason: ssh-keygen -Y verify needs an allowed_signers list" >&2
            echo "  fix: build it from your signing key public part (see header docs)" >&2
            emit "SKIPPED" "no_allowed_signers"
            exit 0
        fi
        if ssh-keygen -Y verify -f "${ALLOWED_SIGNERS}" -I "${IDENTITY}" -n "${NAMESPACE}" -s "${SIG}" < "${REGISTRY}" >/dev/null 2>&1; then
            emit "VERIFIED" "identity=${IDENTITY}"
            exit 0
        fi
        emit "ERROR" "verify_failed"
        exit 1
        ;;

    *)
        echo "registry_sign: unknown mode '${MODE}'" >&2
        echo "  reason: only sign|verify|status supported" >&2
        echo "  fix: bash tool/registry_sign.sh {sign|verify|status}" >&2
        exit 2
        ;;
esac
