# 🐳 Step 03 — Docker Installation

## Why Docker Was Needed
RethinkDB's apt package is incompatible with Ubuntu 24.04.
Docker lets us run RethinkDB in a container that works regardless of the host OS version.

---

## Commands Run

### Install Docker
```bash
sudo apt install -y docker.io
sudo systemctl start docker
sudo usermod -aG docker $USER
newgrp docker
```

## ✅ Result
Docker installed successfully. Packages installed:
- `pigz` — parallel gzip
- `bridge-utils` — network bridge utilities
- `runc` — container runtime
- `containerd` — container management
- `docker.io` — Docker engine
- `ubuntu-fan` — Ubuntu networking overlay

Docker version installed: **28.2.2**

---

## ⚠️ Important Step — Group Permissions
```bash
sudo usermod -aG docker $USER
newgrp docker
```

The `usermod` command adds your user to the `docker` group so you can run Docker without `sudo`.
The `newgrp docker` applies the group change immediately without needing to log out.

**If you skip this**, every docker command will fail with:
```
permission denied while trying to connect to the Docker daemon socket
```

---

## Verify Docker Works
```bash
docker ps
```
Should return a table header (even if empty) — not an error.

---

## Running RethinkDB in Docker
```bash
docker run -d --name rethinkdb -p 28015:28015 -p 8080:8080 rethinkdb:latest
```

| Flag | Meaning |
|------|---------|
| `-d` | Run in background (detached) |
| `--name rethinkdb` | Give container a name for easy reference |
| `-p 28015:28015` | Map RethinkDB driver port to host |
| `-p 8080:8080` | Map RethinkDB admin panel to host |
| `rethinkdb:latest` | Use latest RethinkDB image from Docker Hub |

Docker automatically downloaded the image:
```
Unable to find image 'rethinkdb:latest' locally
latest: Pulling from library/rethinkdb
...
Status: Downloaded newer image for rethinkdb:latest
```

---

## Useful Docker Commands

```bash
# Check running containers
docker ps

# Stop RethinkDB
docker stop rethinkdb

# Start RethinkDB again
docker start rethinkdb

# View RethinkDB logs
docker logs rethinkdb

# Remove container completely (data will be lost)
docker rm -f rethinkdb
```

---

## Persist RethinkDB Data (Important for Production)
By default, if the container is removed, all data is lost.
For production, mount a volume:

```bash
docker run -d --name rethinkdb \
  -p 28015:28015 \
  -p 8080:8080 \
  -v /home/atlas/rethinkdb-data:/data \
  rethinkdb:latest
```

This saves all database files to `/home/atlas/rethinkdb-data` on the host machine.
