# 📱 Step 05 — ADB Installation & Phone Connection

## What Is ADB
ADB (Android Debug Bridge) is a command-line tool that lets a computer
communicate with an Android phone over USB.
STF uses ADB internally to detect, stream, and control connected phones.

---

## ❌ Error Without ADB
When STF started without ADB installed:
```
Unhandled rejection Error: spawn adb ENOENT
```

`ENOENT` = "Error NO ENTry" — the `adb` binary simply didn't exist on the system.

---

## ✅ Fix — Install ADB

```bash
sudo apt install -y adb
```

### Packages installed:
- `android-liblog`
- `android-libbase`
- `android-libboringssl`
- `android-libcutils`
- `android-libziparchive`
- `adb` ← the main tool
- `android-sdk-platform-tools-common`

### Verify installation:
```bash
adb version
```

Output:
```
Android Debug Bridge version 1.0.41
Version 34.0.4-debian
Installed as /usr/lib/android-sdk/platform-tools/adb
Running on Linux 6.17.0-19-generic (x86_64)
```

---

## Connecting the Phone

### Phone: Xiaomi Redmi Note 10 Pro

#### Step 1 — Enable Developer Options
1. Settings → About Phone → All Specs
2. Tap **MIUI Version** 7 times fast
3. Enter PIN when prompted
4. "You are now a developer" message appears

#### Step 2 — Enable USB Debugging
1. Settings → Additional Settings → Developer Options
2. Turn on **USB Debugging**

#### Step 3 — Plug in USB cable
When prompted on phone with USB mode options:
- No data transfer
- File transfer / Android Auto  ← **pick this one first**
- Transfer photos

Selecting **File Transfer** wakes up the ADB connection and triggers
the USB Debugging authorization popup.

#### Step 4 — Authorize the laptop
A popup appeared on phone:
> "Allow USB Debugging from this computer?"

Tapped **Allow** and checked **"Always allow from this computer"**

---

## Verify Phone Is Connected

```bash
adb kill-server
adb start-server
adb devices
```

Output:
```
* daemon not running; starting now at tcp:5037
* daemon started successfully
List of devices attached
aece3bbd    device
```

✅ `aece3bbd` = the phone's ADB serial ID. Status `device` = connected and authorized.

---

## ADB Cheat Sheet

```bash
adb devices                    # List connected devices
adb kill-server                # Stop ADB daemon
adb start-server               # Start ADB daemon
adb -s aece3bbd shell          # Open shell on specific device
adb install app.apk            # Install APK on phone
adb logcat                     # View phone logs live
adb reboot                     # Reboot phone
```

---

## Troubleshooting ADB

| Problem | Solution |
|---------|----------|
| `unauthorized` status | Check phone for popup, tap Allow |
| `offline` status | Unplug/replug cable, run `adb kill-server && adb start-server` |
| Phone not showing at all | USB Debugging not enabled, or bad cable |
| Multiple devices | Use `adb -s SERIAL command` to target specific phone |
