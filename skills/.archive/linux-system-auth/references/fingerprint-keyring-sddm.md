# SDDM + fprintd + gnome-keyring: Keyring locked after fingerprint login

## Problem

After successful fingerprint login via SDDM, gnome-keyring prompts for the password manually. Applications depending on the secret store (Chrome, git-credential, ssh-agent) cannot access stored secrets.

## Root Cause

The PAM stack in `/etc/pam.d/sddm` authenticates via `pam_fprintd.so` (sufficient), which succeeds without capturing a password. `pam_gnome_keyring.so` runs during the session phase (`auto_start`) but has no password to decrypt the Login keyring.

Canonical SDDM PAM structure:

```pam
auth  [success=1 …]  pam_unix.so try_first_pass likeauth nullok
auth  sufficient      pam_fprintd.so
-auth optional        pam_gnome_keyring.so   # tries to capture password — gets none
…
session optional      pam_gnome_keyring.so auto_start  # starts daemon, keyring stays locked
```

## Fix

**Set the Login keyring password to empty.** The keyring auto-unlocks when no password is required. Security is unchanged because the desktop session is already gated by fingerprint.

### Via seahorse (GUI)

```
seahorse
```

1. Open "Passwords and Keys" → "Login" keyring
2. Right-click → **Change Password**
3. Enter current password → leave new password **blank** → Confirm

### Verification

1. Close session → login again with fingerprint
2. Open any app that uses the keyring (e.g. Chromium-based browser)
3. No password prompt should appear

## Why Not Fix PAM Instead

Reordering the PAM stack (putting `pam_fprintd.so` before `pam_unix.so`, or restructuring the keyring auth) does **not** solve the problem because `pam_gnome_keyring.so` captures the password from the PAM conversation — if no password was typed, there is nothing to capture. No PAM reordering can inject a password that was never provided.

The only alternative is a `pam_exec` hook that reads a stored password from disk, which is less secure than an empty keyring password (plaintext file on disk vs no password on an already-protected session).
