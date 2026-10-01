#!/bin/bash
cd /opt/CyberStrikeAI/tmp/workspace/conversations/0e6944a5-643d-4cd9-9a2a-7b1676a25139
# Try several sources for a large password wordlist
declare -A urls=(
 [rockyou]="https://raw.githubusercontent.com/bradhowes/wordlists/master/rockyou.txt"
 [10m]="https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Proximity-Lists/10-million-password-list-top-1000000.txt"
 [crackstation]="https://raw.githubusercontent.com/berzerk0/-community-wordlists/master/top-10-million-passwords.txt"
)
for k in rockyou 10m crackstation; do
  echo "trying $k"
  curl -sk --max-time 60 -o big_${k}.txt "${urls[$k]}"
  sz=$(wc -l < big_${k}.txt 2>/dev/null || echo 0)
  echo "  $k lines=$sz"
  if [ "$sz" -gt 50000 ]; then cp big_${k}.txt big_words.txt; echo "  -> using $k as big_words.txt"; break; fi
done
wc -l big_words.txt 2>/dev/null || echo "no big_words.txt"
