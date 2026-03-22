# 🚀 Step 08 — Next Steps (Scaling Up)

## Where We Are
✅ POC proven — one phone, one laptop, browser control working.

## Where We're Going
A full call center with multiple agents, each controlling their own phone from a browser.

---

## Immediate Next Steps (No Money Needed)

### 1. Test a real incoming call
- Have someone call your Safaricom number while STF is running
- Answer from the browser
- Confirm voice works (speaker on phone, or headset)
- This is the most important test

### 2. Test WhatsApp from browser
- Open WhatsApp on the phone via browser
- Send and receive a message
- Confirm it feels natural for an agent to use

### 3. Test stability
- Leave STF running for 2-3 hours
- Make several calls
- Check if it stays stable or crashes

### 4. Test over WiFi (same network)
- Start STF with your laptop's local IP instead of 127.0.0.1:
```bash
# Find your local IP
ip addr show | grep "inet 192"

# Start STF with that IP
stf local --public-ip 192.168.x.x
```
- Open the browser on another device (phone/tablet) on same WiFi
- Access `http://192.168.x.x:7100`
- This proves agents can work from any device on the network

---

## When You Have Budget — Phase 1 (Small Farm)

### Minimum viable call center (3 agents)

| Item | Qty | Est. Cost (KES) |
|------|-----|----------------|
| Tecno Spark or Itel A70 | 3 | 15,000 |
| Safaricom business SIMs | 3 | 3,000 |
| 4-port powered USB hub | 1 | 1,500 |
| USB cables | 4 | 800 |
| **Total** | | **~KES 20,300** |

Use your existing laptop as the server for the 3-phone test.

---

## Audio Routing (Next Big Challenge)

Currently the phone's call audio plays through the **phone's speaker**.
For a real call center, audio needs to go through the **agent's headset on their laptop**.

### Options to explore:
1. **Bluetooth headset paired to phone** — simplest, agent wears headset connected to phone
2. **Asterisk SIP bridge** — routes audio over network to agent's browser (see `04_NETWORK_AUDIO.md` in the main project folder)
3. **Android audio streaming app** — captures call audio and streams to laptop

The Asterisk approach is the most scalable but needs more setup time.

---

## Agent Dashboard (Next Software Step)

Right now agents use raw STF interface.
A proper call center needs a custom dashboard on top of STF showing:
- Agent name and status
- Which phone is assigned to them
- Call duration timer
- Notes field
- Call history

See `06_AGENT_DASHBOARD.md` in the main project folder for the full plan.

---

## Choosing Phones for the Farm

Avoid Xiaomi/Redmi for the farm — too many MIUI-specific settings to configure.

### Recommended phones for farm use:

| Phone | Price (KES) | Why |
|-------|------------|-----|
| Tecno Spark 10 | ~8,000 | Stock Android-like, easy ADB |
| Itel A70 | ~5,000 | Cheapest viable option |
| Infinix Smart 7 | ~7,000 | Good balance of price/performance |
| Samsung Galaxy A03 | ~12,000 | Most reliable, stock Android |

All of these avoid MIUI restrictions — plug in, enable USB Debugging, done.

---

## Production Checklist (When Ready to Scale)

- [ ] Dedicated Linux server purchased or set up
- [ ] Phone farm rack built (shelf + USB hubs)
- [ ] Phones purchased (same model for consistency)
- [ ] Safaricom business account opened
- [ ] Business SIM lines activated (postpaid)
- [ ] STF running as systemd service (auto-starts)
- [ ] RethinkDB data volume mounted (persistent storage)
- [ ] Agent dashboard built
- [ ] Audio routing solved (Asterisk or Bluetooth)
- [ ] Supervisor panel set up
- [ ] Call recording enabled
- [ ] Security hardened (HTTPS, VPN for remote agents)

---

## Resources

| Resource | Link |
|----------|------|
| STF GitHub | https://github.com/DeviceFarmer/stf |
| STF Documentation | https://github.com/DeviceFarmer/stf/blob/master/README.md |
| RethinkDB Docs | https://rethinkdb.com/docs |
| Asterisk | https://www.asterisk.org |
| Safaricom Business | https://business.safaricom.co.ke |
| ADB Documentation | https://developer.android.com/tools/adb |
