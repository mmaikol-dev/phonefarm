# ⬇️ Step 04 — Node.js Version Downgrade (v25 → v18)

## The Problem
The machine had **Node v25.8.0** installed via nvm.
STF was originally written for Node v8-v12, and while it runs on v18,
it has compatibility issues with Node v25 (too new).

---

## ❌ Symptoms on Node v25
STF would install but behave unpredictably. The safest fix is to use
the **LTS version STF is known to work with — Node v18.**

---

## Commands Run

### Install Node v18 via nvm
```bash
nvm install 18
nvm use 18
node --version
```

### Output
```
Downloading and installing node v18.20.8...
Downloading https://nodejs.org/dist/v18.20.8/node-v18.20.8-linux-x64.tar.xz...
#################################################################### 100.0%
Computing checksum with sha256sum
Checksums matched!
Now using node v18.20.8 (npm v10.8.2)
v18.20.8
```

✅ Now on Node v18.20.8

---

## Reinstall STF on Node v18
After switching Node versions, STF must be reinstalled so it compiles
its native modules against the correct Node version:

```bash
npm install -g @devicefarmer/stf
```

---

## Verify Correct Node Is Active
```bash
node --version   # Should show v18.x.x
npm --version    # Should show 10.x.x
```

---

## Make Node v18 the Default (Permanent)
So you don't have to run `nvm use 18` every time:

```bash
nvm alias default 18
```

---

## nvm Cheat Sheet

```bash
nvm ls                  # List all installed Node versions
nvm install 18          # Install Node v18
nvm use 18              # Switch to Node v18 in current terminal
nvm alias default 18    # Set v18 as default for all new terminals
nvm current             # Show currently active version
```

---

## Why Node Version Matters for STF
STF uses native modules (like ZeroMQ bindings) that are compiled
for a specific Node ABI (Application Binary Interface).

| Node Version | STF Compatibility |
|-------------|------------------|
| v8 - v12 | Original target |
| v14 - v18 | ✅ Works well |
| v20 | ⚠️ Works with warnings |
| v22+ | ❌ May have issues |

**Always use Node v18 LTS for STF in production.**
