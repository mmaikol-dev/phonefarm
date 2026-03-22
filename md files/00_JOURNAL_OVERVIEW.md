# 📓 STF Setup Journal — Phone Farm Call Center POC

## What This Folder Is
A complete record of setting up Smartphone Test Farm (STF) on a real machine,
including every error encountered, what caused it, and how it was fixed.

## Machine Used
- **Laptop:** HP EliteBook 840 G1
- **OS:** Ubuntu 24.04 LTS (Noble)
- **Phone:** Xiaomi Redmi Note 10 Pro (Android 12, MIUI, SDK 33)
- **User:** atlas

## Goal
Prove that a real Android phone can be controlled from a browser —
the core concept behind a phone farm call center using Safaricom lines.

## Result
✅ **SUCCESS** — Phone screen streaming live in browser, fully controllable.

---

## Files In This Folder

```
00_JOURNAL_OVERVIEW.md       ← You are here
01_STF_INSTALL.md            ← Installing STF (and Node version issue)
02_RETHINKDB.md              ← RethinkDB setup (Ubuntu 24 compatibility fix)
03_DOCKER.md                 ← Docker installation
04_NODE_DOWNGRADE.md         ← Switching from Node v25 to v18
05_ADB_SETUP.md              ← ADB install and phone connection
06_MIUI_FIXES.md             ← Redmi/MIUI specific fixes
07_SUCCESS.md                ← Final working state and what was proven
08_NEXT_STEPS.md             ← What to do next to scale this up
```

---

## Quick Summary of Errors Encountered

| # | Error | Cause | Fix |
|---|-------|-------|-----|
| 1 | STF crashes — cannot connect to 28015 | RethinkDB not installed | Install via Docker |
| 2 | RethinkDB install fails — libprotobuf23 | Ubuntu 24 incompatible with RethinkDB apt | Use Docker instead |
| 3 | STF spawn adb ENOENT | ADB not installed | `sudo apt install adb` |
| 4 | INSTALL_FAILED_USER_RESTRICTED | MIUI blocks USB installs by default | Enable "Install via USB" in Developer Options |

---

## Total Time To Get Working
~1 hour (mostly troubleshooting compatibility issues)

## Cost
**KES 0** — everything used is free and open source
