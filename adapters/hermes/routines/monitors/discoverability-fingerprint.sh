#!/usr/bin/env bash
# Trigger fingerprint for routines/discoverability-audit.md
#
# Emits one line per watched input. Hermes cron runs the audit agent ONLY when
# this output changes (--monitor-script). Unchanged output means nothing to
# audit and no agent is woken — this is the structural form of the routine's
# §4 skip condition.
#
# Read-only. Anonymous. No credentials, no side effects, no writes.

set -uo pipefail

SITES=(
  "https://ashwood-info.vercel.app"
  "https://alviratech.vercel.app"
)

# Legacy ALVIRA domain, decommissioned. Watched only so that its state changing
# — coming back up, or starting to redirect — is noticed. It is not an audit
# target and its being down is expected, not a finding.
LEGACY=(
  "https://alvira.ctonew.app"
)
REPOS=(
  "/home/tk/Work/ashwood"
  "/home/tk/Work/ALVIRA"
)

fp() { cksum | awk '{print $1}'; }

for site in "${SITES[@]}"; do
  # Sitemap and robots content, not just their presence. A changed sitemap,
  # a changed robots.txt, or an unreachable site all move the fingerprint —
  # each is something the audit should look at.
  for path in sitemap.xml robots.txt; do
    body=$(curl -fsS --max-time 20 "$site/$path" 2>/dev/null)
    if [ -z "$body" ]; then
      echo "$site/$path UNREACHABLE"
    else
      echo "$site/$path $(printf '%s' "$body" | fp) $(printf '%s' "$body" | wc -c)"
    fi
  done
done

for site in "${LEGACY[@]}"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 20 "$site/" 2>/dev/null || echo 000)
  echo "$site LEGACY http=$code"
done

for repo in "${REPOS[@]}"; do
  if [ ! -d "$repo" ]; then
    echo "$repo MISSING"
    continue
  fi
  # HEAD moves when routes, metadata, or content change. Cheap and exact.
  head=$(git -C "$repo" rev-parse HEAD 2>/dev/null || echo NOGIT)
  echo "$repo $head"
done
