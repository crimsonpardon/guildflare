#!/usr/bin/env python3
# CRIMSON Server Cloner - By X Vault
# Copies roles, channels, categories, permissions and server settings.
# Uses a BOT token (bot must be in both servers with Administrator).

import base64, json, os, sys, time
import urllib.request, urllib.error

API = "https://discord.com/api/v10"
R, G, Y, C, N = "\033[1;31m", "\033[1;32m", "\033[1;33m", "\033[1;36m", "\033[0m"
BASE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(BASE, "backups"), exist_ok=True)


UA = "DiscordBot (https://github.com/crimsonpardon/guildflare, 1.0)"


class Resp:
    def __init__(self, code, body):
        self.status_code = code
        self._body = body

    def json(self):
        try:
            return json.loads(self._body) if self._body else {}
        except Exception:
            return {}


def api(s, method, path, **kw):
    # s = headers dict (stdlib only, no requests needed)
    data = json.dumps(kw["json"]).encode() if "json" in kw else None
    while True:
        req = urllib.request.Request(API + path, data=data, method=method, headers=s)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return Resp(r.status, r.read())
        except urllib.error.HTTPError as e:
            body = e.read()
            if e.code == 429:
                try:
                    wait = json.loads(body).get("retry_after", 1)
                except Exception:
                    wait = 1
                time.sleep(float(wait) + 0.1)
                continue
            return Resp(e.code, body)
        except Exception:
            time.sleep(1)


def icon_b64(gid, icon):
    if not icon:
        return None
    try:
        req = urllib.request.Request(
            f"https://cdn.discordapp.com/icons/{gid}/{icon}.png?size=512", headers={"User-Agent": UA})
        data = urllib.request.urlopen(req, timeout=15).read()
        return "data:image/png;base64," + base64.b64encode(data).decode()
    except Exception:
        return None


def backup(s, gid):
    print(f"{C}[1/2] Backing up source server...{N}")
    g = api(s, "GET", f"/guilds/{gid}")
    if g.status_code != 200:
        sys.exit(f"{R}Cannot read source server. Is the bot inside it? ({g.status_code}){N}")
    g = g.json()
    ch = api(s, "GET", f"/guilds/{gid}/channels").json()
    data = {
        "guild_id": gid,
        "name": g["name"],
        "icon": icon_b64(gid, g.get("icon")),
        "verification_level": g.get("verification_level"),
        "default_message_notifications": g.get("default_message_notifications"),
        "explicit_content_filter": g.get("explicit_content_filter"),
        "afk_timeout": g.get("afk_timeout"),
        "afk_channel_id": g.get("afk_channel_id"),
        "system_channel_id": g.get("system_channel_id"),
        "preferred_locale": g.get("preferred_locale"),
        "roles": g["roles"],
        "channels": ch,
    }
    path = os.path.join(BASE, "backups", f"{gid}.json")
    with open(path, "w") as f:
        json.dump(data, f)
    print(f"{G}Backup saved: {len(data['roles'])} roles, {len(ch)} channels{N}")
    return data


def restore(s, tid, d):
    t0 = time.time()
    print(f"{C}[2/2] Pasting into target server...{N}")
    tg = api(s, "GET", f"/guilds/{tid}")
    if tg.status_code != 200:
        sys.exit(f"{R}Cannot access target server. Is the bot inside it? ({tg.status_code}){N}")

    # wipe target
    print(" - clearing old channels and roles")
    for c in api(s, "GET", f"/guilds/{tid}/channels").json():
        api(s, "DELETE", f"/channels/{c['id']}")
    for r in api(s, "GET", f"/guilds/{tid}/roles").json():
        if r["id"] != tid and not r.get("managed"):
            api(s, "DELETE", f"/guilds/{tid}/roles/{r['id']}")

    # roles (highest first so order ends up correct)
    print(" - creating roles")
    rmap = {d["guild_id"]: tid}
    for r in sorted(d["roles"], key=lambda x: x["position"], reverse=True):
        if r["id"] == d["guild_id"]:
            api(s, "PATCH", f"/guilds/{tid}/roles/{tid}", json={"permissions": r["permissions"]})
            continue
        if r.get("managed"):
            continue
        res = api(s, "POST", f"/guilds/{tid}/roles", json={
            "name": r["name"], "permissions": r["permissions"], "color": r["color"],
            "hoist": r["hoist"], "mentionable": r["mentionable"],
        })
        if res.status_code == 200:
            rmap[r["id"]] = res.json()["id"]

    def overwrites(ch):
        out = []
        for o in ch.get("permission_overwrites", []):
            if o["type"] == 0 and o["id"] in rmap:
                out.append({"id": rmap[o["id"]], "type": 0, "allow": o["allow"], "deny": o["deny"]})
        return out

    # categories first, then channels
    print(" - creating categories and channels")
    cmap = {}
    chans = sorted(d["channels"], key=lambda x: x["position"])
    for c in [x for x in chans if x["type"] == 4]:
        res = api(s, "POST", f"/guilds/{tid}/channels", json={
            "name": c["name"], "type": 4, "position": c["position"], "permission_overwrites": overwrites(c)})
        if res.status_code in (200, 201):
            cmap[c["id"]] = res.json()["id"]

    for c in [x for x in chans if x["type"] != 4]:
        body = {"name": c["name"], "type": c["type"], "position": c["position"],
                "permission_overwrites": overwrites(c)}
        if c.get("parent_id") in cmap:
            body["parent_id"] = cmap[c["parent_id"]]
        for k in ("topic", "nsfw", "bitrate", "user_limit", "rate_limit_per_user"):
            if c.get(k) is not None:
                body[k] = c[k]
        res = api(s, "POST", f"/guilds/{tid}/channels", json=body)
        if res.status_code == 400 and c["type"] in (5, 15):  # community-only types
            body["type"] = 0
            res = api(s, "POST", f"/guilds/{tid}/channels", json=body)
        if res.status_code in (200, 201):
            cmap[c["id"]] = res.json()["id"]

    # settings
    print(" - applying server settings")
    st = {k: d[k] for k in ("name", "verification_level", "default_message_notifications",
                            "explicit_content_filter", "afk_timeout") if d.get(k) is not None}
    if d.get("icon"):
        st["icon"] = d["icon"]
    if d.get("afk_channel_id") in cmap:
        st["afk_channel_id"] = cmap[d["afk_channel_id"]]
    if d.get("system_channel_id") in cmap:
        st["system_channel_id"] = cmap[d["system_channel_id"]]
    api(s, "PATCH", f"/guilds/{tid}", json=st)

    print(f"\n{G}✔ Done! Pasted in {int(time.time() - t0)} seconds.{N}")


def template_data(s, link):
    """Read a Server Template link (bot only needed in the TARGET server)."""
    code = link.strip().split("?")[0].rstrip("/").split("/")[-1]
    print(f"{C}[1/2] Reading template...{N}")
    r = api(s, "GET", f"/guilds/templates/{code}")
    if r.status_code != 200:
        sys.exit(f"{R}Template not found or invalid link ({r.status_code}).{N}")
    g = r.json()["serialized_source_guild"]

    roles, every = [], None
    for i, ro in enumerate(g.get("roles", [])):
        ro = dict(ro)
        ro["id"] = str(ro["id"])
        ro["position"] = ro.get("position", i)
        ro["permissions"] = str(ro.get("permissions", 0))
        ro["color"] = ro.get("color", 0)
        ro["hoist"] = ro.get("hoist", False)
        ro["mentionable"] = ro.get("mentionable", False)
        ro["managed"] = False
        if ro.get("name") == "@everyone" and every is None:
            every = ro["id"]
        roles.append(ro)
    if every is None and roles:
        every = roles[0]["id"]

    chans = []
    for i, c in enumerate(g.get("channels", [])):
        c = dict(c)
        c["id"] = str(c["id"])
        c["position"] = c.get("position", i)
        c["parent_id"] = str(c["parent_id"]) if c.get("parent_id") is not None else None
        ows = []
        for o in c.get("permission_overwrites", []):
            is_role = o.get("type") in (0, "role")
            ows.append({"id": str(o["id"]), "type": 0 if is_role else 1,
                        "allow": str(o.get("allow", 0)), "deny": str(o.get("deny", 0))})
        c["permission_overwrites"] = ows
        chans.append(c)

    data = {
        "guild_id": every,
        "name": g.get("name"),
        "icon": None,
        "verification_level": g.get("verification_level"),
        "default_message_notifications": g.get("default_message_notifications"),
        "explicit_content_filter": g.get("explicit_content_filter"),
        "afk_timeout": g.get("afk_timeout"),
        "afk_channel_id": str(g["afk_channel_id"]) if g.get("afk_channel_id") is not None else None,
        "system_channel_id": str(g["system_channel_id"]) if g.get("system_channel_id") is not None else None,
        "roles": roles,
        "channels": chans,
    }
    with open(os.path.join(BASE, "backups", f"template_{code}.json"), "w") as f:
        json.dump(data, f)
    print(f"{G}Template read: {len(roles)} roles, {len(chans)} channels{N}")
    return data


def main():
    print(f"{R}=== CRIMSON SERVER CLONER ==={N}")
    print(f"{R}[1]{N} Direct copy  (bot must be in BOTH servers)")
    print(f"{R}[2]{N} Template link (bot only in TARGET server)\n")
    mode = input("Select mode [1/2]: ").strip()
    print("\nBot needs Administrator in the target server.\n")
    token = os.environ.get("CLONER_TOKEN") or input("Bot token: ").strip()
    s = {"Authorization": f"Bot {token}", "Content-Type": "application/json", "User-Agent": UA}
    if api(s, "GET", "/users/@me").status_code != 200:
        sys.exit(f"{R}Invalid bot token.{N}")

    if mode == "2":
        link = input("Server template link (discord.new/...): ").strip()
        data = template_data(s, link)
    else:
        src = input("Source server ID (copy FROM): ").strip()
        data = backup(s, src)

    tid = input("Target server ID (paste TO): ").strip()
    if input(f"{Y}This DELETES all channels/roles in target. Type yes to continue: {N}").strip().lower() != "yes":
        sys.exit("Cancelled.")
    restore(s, tid, data)


if __name__ == "__main__":
    main()
