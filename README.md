<h1 align="center">CRIMSON</h1>
<p align="center">Self-host bot launcher for Termux and Linux terminal<br><b>By X Vault</b></p>

---

## Features

- Simple 1 to 9 menu, with a big CRIMSON banner
- One-tap setup: paste your `git clone` command, bot token and owner ID, and the bot starts
- Bots run in the background, with logs saved in `logs/`
- Built-in Discord server cloner (backup + paste)
- Works on Termux (Android) and Linux

## Install

### Termux

```bash
pkg update -y && pkg upgrade -y
pkg install -y git python nodejs
git clone https://github.com/crimsonpardon/guildflare.git
cd guildflare
bash start.sh
```

### Linux (Ubuntu / Debian)

```bash
sudo apt update && sudo apt install -y git python3 python3-pip nodejs npm
git clone https://github.com/crimsonpardon/guildflare.git
cd guildflare
bash start.sh
```

## Menu

| Option | Name | What it does |
|:---:|---|---|
| 1 | VPS Bot | Deploy a VPS Discord bot |
| 2 | Minecraft Discord Bot | Deploy the Minecraft RCON bot |
| 3 | Discord Server Cloner | Backup a server and paste it into another |
| 4 | Nitro Sales Bot | Deploy the Nitro shop bot |
| 5 | Ticket Panel Bot | Deploy the ticket panel bot |
| 6 | Discord Code Login Bot | Deploy the DM-code login bot |
| 7 | Status / Logs | See which bots are running and view logs |
| 8 | Stop All Bots | Stop every running bot |
| 9 | Exit | Close the tool |

## How options 1, 2, 4, 5 and 6 work

1. Pick the option number.
2. Paste the `git clone ...` command (or the repo URL) of that bot. This is asked only the first time.
3. Paste your **bot token**.
4. Paste the **main owner token / ID**.
5. CRIMSON installs the requirements and starts the bot in the background.

Your token and owner ID are saved in a `.env` file inside the bot's folder in `apps/`. Never upload this file to GitHub.

## Option 3: Server Cloner

1. Pick **3** and paste your bot token.
2. Paste the **source server ID** (copy FROM). The backup is saved in `backups/`.
3. Paste the **target server ID** (paste TO) and type `yes`.
4. Roles, channels, categories, permissions and server settings are pasted. A small server takes about 30 seconds.

Requirements:

- Use a **bot token** only. User tokens (self-bots) are against Discord's rules.
- The bot must be in both servers with the **Administrator** permission.
- The bot's role must be above the other roles in the target server.

Not copied: messages, emojis, bots and member-specific permissions.

## Add or rename options

Edit the `MENU` list at the top of `start.sh`:

```bash
MENU=(
  "key|Title"
)
```

## Folders

```
guildflare/
├── start.sh      # main launcher
├── cloner.py     # server cloner
├── apps/         # cloned bots
├── logs/         # bot logs
├── backups/      # server backups
└── pids/         # running bot IDs
```

## Upload to GitHub

```bash
cd crimson
echo -e "apps/\nlogs/\npids/\nbackups/\n.env" > .gitignore
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/crimsonpardon/guildflare.git
git push -u origin main
```

---

<p align="center"><b>By X Vault</b></p>
