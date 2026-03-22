# ⚡ Quick Reference — Start STF Every Time

## Full Startup (copy-paste ready)

Open terminal and run these in order:

```bash
# 1. Start RethinkDB
docker start rethinkdb

# 2. Use correct Node version
nvm use 18

# 3. Start STF
stf local --public-ip 127.0.0.1
```

Then open browser: **http://localhost:7100**

---

## If Phone Not Showing

```bash
adb kill-server
adb start-server
adb devices
```

Phone should appear in STF within 10 seconds.

---

## Check Everything Is Running

```bash
# RethinkDB running?
docker ps

# Phone connected?
adb devices

# Node version correct?
node --version   # Should say v18.x.x
```

---

## Common Errors Quick Fix

| Error | One-line fix |
|-------|-------------|
| STF won't start — port 28015 | `docker start rethinkdb` |
| Phone shows "Disconnected" | `adb kill-server && adb start-server` |
| INSTALL_FAILED_USER_RESTRICTED | Enable "Install via USB" in Developer Options |
| spawn adb ENOENT | `sudo apt install -y adb` |
| Wrong Node version | `nvm use 18` |

---

## Machine Details
- **Laptop:** HP EliteBook 840 G1
- **OS:** Ubuntu 24.04 LTS
- **Node:** v18.20.8 (via nvm)
- **Phone:** Redmi Note 10 Pro (serial: aece3bbd)
- **STF port:** 7100
- **RethinkDB port:** 28015
