# bt/ — BreakThrough audit + causal_chain 흡수

entry:  bt_audit.py (v5, skip_resolve)
inputs: bt_domains.jsonl bt_keywords.jsonl bt_arch_domains.jsonl
out:    bt_audit_result.json bt_{mismatch,skip}_classification.json
docs:   bt-consistency-report.md bt-skip-{reduction,resolution}.md
bak:    bt_audit.py.bak.v1~v5, .before_unicode, .before_nt

ref: ../config/absolute_rules.json (BT audit, causal chain)
