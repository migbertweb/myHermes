---
name: linux-system-auth
description: "Use when fingerprint or keyring auth breaks after login."
version: 1.0.0
---

# Linux System Authentication

Diagnose and fix authentication stack issues on Linux: PAM configuration, fingerprint (fprintd), smartcard, display-manager integration, and secret-service/keyring daemon interoperability.

## When to Use

- A fingerprint/biometric login succeeds but the session's keyring (gnome-keyring, kwallet) stays locked
- Passwordless auth (fingerprint, smartcard, FIDO2) works for login but breaks downstream services that depend on the secret store
- SDDM/GDM/LightDM login works with password but not with fingerprint
- PAM stack changes needed for a new auth method
- Debug which PAM module is blocking or failing (`pam_tally`, `pam_faillock`, `pam_fprintd`)

## References

- `references/fingerprint-keyring-sddm.md` — Resolving SDDM + fprintd + gnome-keyring deadlock: why the keyring stays locked after fingerprint login, and the empty-password fix.

## Pitfalls

- **`sudo` with fingerprint PAM**: If `pam_fprintd.so` is configured before `pam_unix.so` in `/etc/pam.d/sudo`, piped commands (e.g. `echo value | sudo tee /sys/...`) will hang waiting for fingerprint input. Use `sudo sh -c 'echo ... > ...'` or `printf 'pass\n' | sudo -S`.
- **`pam_gnome_keyring.so` needs a captured password**: Without a password in the PAM auth phase, the keyring daemon starts but cannot unlock the Login keyring. The `pam_fprintd.so` `sufficient` flag does not provide a password.
- **Keyring password vs login password**: Setting the Login keyring password to empty is safe because the session is already gated by fingerprint — the keyring is no less protected than the desktop session itself.
