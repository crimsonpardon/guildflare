#!/usr/bin/env bash
# CRIMSON - By X Vault
# Works on Termux and Linux terminal

BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPS="$BASE/apps"; LOGS="$BASE/logs"; PIDS="$BASE/pids"
mkdir -p "$APPS" "$LOGS" "$PIDS"

R='\033[1;31m'; G='\033[1;32m'; Y='\033[1;33m'; C='\033[1;36m'; W='\033[1;37m'; N='\033[0m'

# ---- EDIT MENU HERE: key|title ----
MENU=(
  "vpsbot|VPS Bot"
  "mcbot|Minecraft Discord Bot"
  "cloner|Discord Server Cloner (Backup + Paste)"
  "nitrobot|Nitro Sales Bot"
  "ticketbot|Ticket Panel Bot"
  "loginbot|Discord Code Login Bot"
)

banner() {
  clear
  echo -e "${R}"
  cat <<'EOF'
  ██████╗██████╗ ██╗███╗   ███╗███████╗ ██████╗ ███╗   ██╗
 ██╔════╝██╔══██╗██║████╗ ████║██╔════╝██╔═══██╗████╗  ██║
 ██║     ██████╔╝██║██╔████╔██║███████╗██║   ██║██╔██╗ ██║
 ██║     ██╔══██╗██║██║╚██╔╝██║╚════██║██║   ██║██║╚██╗██║
 ╚██████╗██║  ██║██║██║ ╚═╝ ██║███████║╚██████╔╝██║ ╚████║
  ╚═════╝╚═╝  ╚═╝╚═╝╚═╝     ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝
EOF
  echo -e "${N}"
}

footer() { echo -e "\n${R}══════════════════════════════════════${N}\n${W}            By X Vault${N}\n"; }

pause() { read -rp "Press Enter to continue..."; }

install_base() {
  for t in git python3 node; do
    command -v "$t" >/dev/null 2>&1 && continue
    echo -e "${Y}Installing $t...${N}"
    if command -v pkg >/dev/null 2>&1; then
      case $t in python3) pkg install -y python;; node) pkg install -y nodejs;; *) pkg install -y "$t";; esac
    else
      case $t in node) sudo apt install -y nodejs npm;; python3) sudo apt install -y python3 python3-pip;; *) sudo apt install -y "$t";; esac
    fi
  done
}

is_running() { [ -f "$PIDS/$1.pid" ] && kill -0 "$(cat "$PIDS/$1.pid")" 2>/dev/null; }

stop_app() {
  if is_running "$1"; then kill "$(cat "$PIDS/$1.pid")" 2>/dev/null; echo -e "${Y}Stopped $1${N}"; fi
  rm -f "$PIDS/$1.pid"
}

deploy() {
  local key="$1" title="$2" dir="$APPS/$1"
  banner; echo -e "${C}>> $title${N}\n"
  install_base

  if [ ! -d "$dir" ]; then
    echo -e "${W}Paste git clone command (or repo URL):${N}"
    read -rp "> " cmd
    local url; url=$(echo "$cmd" | sed -E 's/^[[:space:]]*git clone[[:space:]]+//' | awk '{print $1}')
    [ -z "$url" ] && { echo -e "${R}No URL given.${N}"; pause; return; }
    git clone "$url" "$dir" || { echo -e "${R}Clone failed.${N}"; pause; return; }
  else
    echo -e "${G}Already cloned. Reusing $dir${N}"
  fi

  read -rp "Bot token: " TOKEN
  read -rp "Main owner token / ID: " OWNER
  cat > "$dir/.env" <<EOF
TOKEN=$TOKEN
BOT_TOKEN=$TOKEN
DISCORD_TOKEN=$TOKEN
OWNER_ID=$OWNER
OWNER_TOKEN=$OWNER
EOF

  cd "$dir" || return
  [ -f requirements.txt ] && pip install -r requirements.txt
  [ -f package.json ] && npm install

  local run=""
  for f in bot.py main.py app.py index.py; do [ -f "$f" ] && { run="python3 $f"; break; }; done
  if [ -z "$run" ]; then
    for f in index.js bot.js main.js app.js; do [ -f "$f" ] && { run="node $f"; break; }; done
  fi
  [ -z "$run" ] && { echo -e "${R}No entry file found (bot.py / main.py / index.js).${N}"; cd "$BASE"; pause; return; }

  stop_app "$key"
  nohup $run > "$LOGS/$key.log" 2>&1 &
  echo $! > "$PIDS/$key.pid"
  cd "$BASE"
  echo -e "\n${G}✔ $title is running!${N}  (log: logs/$key.log)"
  pause
}

run_cloner() {
  banner; echo -e "${C}>> Discord Server Cloner${N}\n"
  install_base
  python3 "$BASE/cloner.py"
  pause
}

status() {
  banner; echo -e "${W}Running bots:${N}\n"
  for item in "${MENU[@]}"; do
    k="${item%%|*}"; t="${item##*|}"
    if is_running "$k"; then echo -e "  ${G}● $t${N}"; else echo -e "  ${R}○ $t${N}"; fi
  done
  echo; read -rp "Enter bot number to see log (or Enter to go back): " n
  if [[ "$n" =~ ^[1-6]$ ]]; then
    k="${MENU[$((n-1))]%%|*}"; tail -n 30 "$LOGS/$k.log" 2>/dev/null || echo "No log yet."; pause
  fi
}

while true; do
  banner
  i=1
  for item in "${MENU[@]}"; do
    echo -e "  ${R}[$i]${N} ${W}${item##*|}${N}"; i=$((i+1))
  done
  echo -e "  ${R}[7]${N} ${W}Status / Logs${N}"
  echo -e "  ${R}[8]${N} ${W}Stop All Bots${N}"
  echo -e "  ${R}[9]${N} ${W}Exit${N}"
  footer
  read -rp "Select option [1-9]: " opt
  case $opt in
    [1-6]) item="${MENU[$((opt-1))]}"
       if [ "${item%%|*}" = "cloner" ]; then run_cloner; else deploy "${item%%|*}" "${item##*|}"; fi;;
    7) status;;
    8) for item in "${MENU[@]}"; do stop_app "${item%%|*}"; done; pause;;
    9) echo -e "${R}Bye! — By X Vault${N}"; exit 0;;
    *) echo -e "${R}Invalid option${N}"; sleep 1;;
  esac
done
