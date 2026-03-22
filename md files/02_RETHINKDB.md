# 🗄️ Step 02 — RethinkDB Setup

## What Is RethinkDB
RethinkDB is the database STF uses to store device info, users, sessions, and logs.
It runs on port **28015** by default.
STF will not start without it.

---

## First Attempt — Direct apt Install

### Commands Run
```bash
curl -fsSL https://download.rethinkdb.com/repository/raw/pubkey.gpg | sudo gpg --dearmor -o /usr/share/keyrings/rethinkdb-archive-keyring.gpg

echo "deb [signed-by=/usr/share/keyrings/rethinkdb-archive-keyring.gpg] https://download.rethinkdb.com/repository/ubuntu-jammy jammy main" | sudo tee /etc/apt/sources.list.d/rethinkdb.list

sudo apt update && sudo apt install -y rethinkdb
```

## ❌ Error Encountered
```
The following packages have unmet dependencies:
 rethinkdb : Depends: libprotobuf23 (>= 3.12.4) but it is not installable
E: Unable to correct problems, you have held broken packages.
```

## 🔍 Root Cause
**Ubuntu version mismatch.**

| What | Version |
|------|---------|
| Machine OS | Ubuntu 24.04 LTS (Noble) |
| RethinkDB apt repo | Built for Ubuntu 22.04 (Jammy) |
| Missing dependency | `libprotobuf23` — exists in Jammy, NOT in Noble |

RethinkDB's official apt repository has not been updated to support Ubuntu 24.04.
The package depends on `libprotobuf23` which was replaced by `libprotobuf32` in Ubuntu 24.

## ✅ Fix — Use Docker Instead

Rather than fighting the dependency, run RethinkDB inside Docker which has no OS dependency issues.

### Step 1 — Install Docker
```bash
sudo apt install -y docker.io
sudo systemctl start docker
sudo usermod -aG docker $USER
newgrp docker
```

### Step 2 — Run RethinkDB in Docker
```bash
docker run -d --name rethinkdb -p 28015:28015 -p 8080:8080 rethinkdb:latest
```

### Step 3 — Verify it's running
```bash
docker ps
```

Expected output:
```
CONTAINER ID   IMAGE              COMMAND                  CREATED         STATUS         PORTS
d64ac532fa54   rethinkdb:latest   "rethinkdb --bind all"   25 seconds ago  Up 23 seconds  0.0.0.0:8080->8080/tcp, 0.0.0.0:28015->28015/tcp
```

✅ RethinkDB running on port 28015 — STF can now connect.

---

## RethinkDB Admin Panel
Once running, you can view the RethinkDB admin dashboard at:
```
http://localhost:8080
```
Shows tables, connections, and query performance.

---

## Make RethinkDB Start Automatically
To ensure RethinkDB starts on reboot:
```bash
docker update --restart unless-stopped rethinkdb
```

---

## What STF Creates in RethinkDB
When STF first connects successfully, it auto-creates:
- Database: `stf`
- Tables: `users`, `devices`, `accessTokens`, `groups`, `logs`, `vncauth`
- Indexes on each table for fast lookups

You'll see this in the STF logs:
```
INF/db:setup [*] Database "stf" created
INF/db:setup [*] Table "users" created
INF/db:setup [*] Table "devices" created
...
```
