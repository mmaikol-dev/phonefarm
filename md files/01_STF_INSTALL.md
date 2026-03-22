# 📦 Step 01 — STF Installation

## What We Did
Installed Smartphone Test Farm (STF) globally via npm.

## Command Run
```bash
npm install -g @devicefarmer/stf
```

## Result
✅ Installed successfully — 729 packages added in ~2 minutes.

---

## First Run Attempt
```bash
stf local --public-ip 127.0.0.1
```

## ❌ Error Encountered
```
2026-03-18T13:54:50.792Z INF/db 27043 [*] Connecting to 127.0.0.1:28015
2026-03-18T13:54:50.809Z INF/db 27043 [*] Unable to connect to 127.0.0.1:28015
2026-03-18T13:54:50.810Z FTL/db 27043 [*] No hosts left to try
2026-03-18T13:54:50.810Z FTL/util:lifecycle 27043 [*] Shutting down due to fatal error
ExitError: Exit code "1"
```

## 🔍 Root Cause
STF requires **RethinkDB** as its database, running on port **28015**.
RethinkDB was not installed, so STF could not connect and crashed immediately.

## ✅ Fix
Install and start RethinkDB. See `02_RETHINKDB.md` for the full fix.

---

## ⚠️ Node Version Warning
First attempt ran on **Node v25.8.0** (via nvm).
STF was built for older Node versions — v18 is the recommended stable version.

This caused a secondary issue later. See `04_NODE_DOWNGRADE.md`.

### Deprecation warnings during install (safe to ignore)
These appeared during npm install but do NOT affect functionality:
- `request@2.88.0` deprecated
- `glob@7.2.3` deprecated
- `uuid@3.4.0` deprecated
- `gm@1.25.1` sunset
- `aws-sdk@2.1693.0` end of support

These are STF's own dependencies — not your code. They don't break anything.

---

## Notes
- STF package name: `@devicefarmer/stf` (the maintained fork of the original `openstf`)
- GitHub: https://github.com/DeviceFarmer/stf
- The original `stf` package on npm is abandoned — always use `@devicefarmer/stf`
