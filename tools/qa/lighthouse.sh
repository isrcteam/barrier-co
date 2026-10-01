#!/usr/bin/env bash
set -euo pipefail
if [ "$#" -eq 0 ]; then
  echo "Usage: lighthouse.sh <url> [url ...]"
  exit 1
fi
OUT="${LH_OUT:-lighthouse-reports}"
LH="lighthouse@${LH_VERSION:-12}"  # pinned major; the repo's own devDependency wins when installed
mkdir -p "$OUT"
printf "%-60s %6s %8s %6s %8s %10s\n" "URL" "Score" "LCP(s)" "CLS" "TBT(ms)" "Weight(KB)"
for url in "$@"; do
  scores=(); lcps=(); clss=(); tbts=(); weights=()
  for run in 1 2 3; do
    file="$OUT/$(echo "$url" | tr -c 'a-zA-Z0-9' '_' | cut -c1-80)-$run.json"
    npx --yes "$LH" "$url" --form-factor=mobile --quiet --chrome-flags="--headless=new" --output=json --output-path="$file" >/dev/null 2>&1 || { echo "Lighthouse failed for $url"; continue; }
    read -r s l c t w < <(python3 -c "
import json,sys
d=json.load(open(sys.argv[1]))
a=d['audits']
print(round(d['categories']['performance']['score']*100), round(a['largest-contentful-paint']['numericValue']/1000,2), round(a['cumulative-layout-shift']['numericValue'],3), round(a['total-blocking-time']['numericValue']), round(a['total-byte-weight']['numericValue']/1024))
" "$file")
    scores+=("$s"); lcps+=("$l"); clss+=("$c"); tbts+=("$t"); weights+=("$w")
  done
  median() { printf "%s\n" "$@" | sort -n | awk '{a[NR]=$1} END {print a[int((NR+1)/2)]}'; }
  printf "%-60s %6s %8s %6s %8s %10s\n" "${url:0:60}" "$(median "${scores[@]}")" "$(median "${lcps[@]}")" "$(median "${clss[@]}")" "$(median "${tbts[@]}")" "$(median "${weights[@]}")"
done
echo "Reports saved in $OUT/"
