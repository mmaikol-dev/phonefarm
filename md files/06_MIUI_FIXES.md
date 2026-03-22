# 📵 Step 06 — MIUI / Xiaomi Specific Fixes

## The Problem With Xiaomi Phones
Xiaomi's MIUI Android skin adds extra security restrictions on top of standard Android.
These restrictions block STF from installing its helper app (STFService.apk) on the phone.

This is the **most common blocker** when running STF on Redmi/Xiaomi/POCO devices.

---

## ❌ Error Encountered

STF kept looping this error every ~2 seconds:
```
FTL/device [aece3bbd] Setup had an error Error: /data/local/tmp/STFService.apk 
could not be installed [INSTALL_FAILED_USER_RESTRICTED: Install canceled by user]
```

And in the browser, the phone showed as **"Disconnected"** instead of being usable.

### What STFService.apk Is
STF needs to install a small helper APK on the phone called **STFService**.
This app handles screen capture, touch input forwarding, and device info.
Without it, STF cannot stream or control the phone.

---

## 🔍 Root Cause
MIUI has a security setting called **"Install via USB"** that is **OFF by default**.
When off, any attempt to install an APK via ADB is blocked — even from the developer's own machine.

Additionally, MIUI has a separate **"USB Debugging (Security settings)"** toggle
that controls whether ADB can perform privileged operations.

---

## ✅ Fix — Enable These Two Settings on the Phone

### Setting 1 — Install via USB
1. Settings → Additional Settings → Developer Options
2. Scroll down to find **"Install via USB"**
3. Turn it **ON**
4. MIUI may ask you to verify with your **Mi Account** — log in and confirm

### Setting 2 — USB Debugging Security Settings
1. Still in Developer Options
2. Find **"USB Debugging (Security settings)"**
3. Turn it **ON**

---

## After Enabling These Settings

On the laptop, reset the ADB connection:
```bash
adb kill-server
adb start-server
```

STF automatically retried and this time successfully installed STFService:
```
INF/device:resources:service [aece3bbd] Installing STFService
INF/device [aece3bbd] Preparing device
INF/device [aece3bbd] Device is ready
```

The phone appeared in the STF browser interface and streaming began! ✅

---

## Full List of Developer Options To Enable on MIUI

| Setting | Location | Required? |
|---------|----------|-----------|
| USB Debugging | Developer Options | ✅ Yes |
| Install via USB | Developer Options | ✅ Yes (MIUI specific) |
| USB Debugging (Security settings) | Developer Options | ✅ Yes (MIUI specific) |
| Stay Awake | Developer Options | Recommended |
| Disable MIUI Optimization | Developer Options | Optional (helps stability) |

---

## Screen Lock & Sleep Settings (Recommended)
To prevent the phone from locking during use:

1. Settings → Display → Sleep → set to **"Never"** or maximum
2. Settings → Security → Screen Lock → set to **"None"**

---

## MIUI vs Stock Android Differences

| Feature | Stock Android | MIUI |
|---------|--------------|------|
| USB Debugging | One toggle | Two separate toggles |
| APK install via ADB | Allowed by default | Blocked by default |
| Build Number location | About Phone | About Phone → All Specs → MIUI Version |
| Developer Options location | Settings | Settings → Additional Settings |

---

## Other Xiaomi/MIUI Tips

**Disable MIUI Optimization (optional but helps)**
In Developer Options, scroll to bottom → turn off **"MIUI Optimization"**
This makes the phone behave more like stock Android.

**Battery Optimization**
Go to Settings → Apps → STFService → Battery Saver → set to **"No restrictions"**
This prevents MIUI from killing the STFService background process.

**Note for Production Phone Farm:**
When buying Tecno/Itel/Infinix phones for the farm, these MIUI-specific issues
won't apply — those brands run closer to stock Android and are easier to configure.
