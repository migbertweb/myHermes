---
name: tailscale-exit-node
description: Set up a personal Tailscale exit node on a cheap VPS in a specific country. Covers VPS provider research, Tailscale configuration, and verification.
---

# Tailscale Exit Node Setup

Use this skill when the user wants to route traffic through a specific country using Tailscale, typically by renting a cheap VPS and configuring it as an exit node.

## When to use

- User wants an IP from a specific country (LATAM, Asia, Europe, etc.)
- User asks for cheap VPS options in a given region
- User wants to set up a personal/proxy VPN via Tailscale
- User already has a Tailscale network (tailnet) and wants to add an exit node

## Workflow

### 1. Determine the target country and user constraints

- **Check memory** for the user's location (they may want a nearby country, not their own)
- **Ask or infer** the target country if not stated
- **Identify constraints**: budget, minimum specs, payment methods accepted (PayPal is common for LATAM users)

### 2. Research VPS providers in the target country

Use the browser or terminal to check which providers have data centers in the target country:

| Provider | Data centers in LATAM |
|----------|----------------------|
| **Vultr** (vultr.com) | Santiago 🇨🇱, São Paulo 🇧🇷, Mexico City 🇲🇽 |
| **DigitalOcean** (digitalocean.com) | Bogotá 🇨🇴, São Paulo 🇧🇷 |
| **Gcore** (gcore.com) | Santiago 🇨🇱, São Paulo 🇧🇷 |
| **EdgeUno** | Regional LATAM, Colombia |
| **HostDime** | Colombia, Mexico |

Avoid AWS, GCP, Azure for personal use — they are overpriced for a simple exit node.

Use curl to scan provider pricing pages efficiently. See `references/vps-provider-research.md` for the LATAM pricing data from this session.

### 3. Recommend the cheapest suitable plan

For a Tailscale exit node, **minimum specs**: 1 vCPU, 512MB RAM, 10GB SSD, 500GB+ transfer.

| Country | Best pick | Min price |
|---------|-----------|-----------|
| 🇨🇱 Chile | Vultr (Santiago) | ~$3.50/mo |
| 🇨🇴 Colombia | DigitalOcean (Bogotá) | ~$4/mo |
| 🇧🇷 Brazil | DigitalOcean or Vultr (São Paulo) | ~$4/mo |
| 🇲🇽 Mexico | Vultr or DigitalOcean | ~$4/mo |
| 🇦🇷 Argentina | Vultr (Buenos Aires) | ~$3.50/mo |

### 4. Setup instructions

After the user creates the VPS, guide them through:

```bash
# 1. SSH into the VPS
ssh root@<vps-ip>

# 2. Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# 3. Authenticate and advertise as exit node
sudo tailscale up --advertise-exit-node

# 4. Follow the auth URL to add the node to the tailnet

# 5. Verify it's connected
tailscale status
```

Then in the Tailscale admin console (https://login.tailscale.com/admin/machines):
1. Find the new machine
2. Toggle "Use as exit node" to enabled
3. Optionally edit ACLs if needed

### 5. Client-side usage

From the user's device:

- **Desktop**: Tailscale icon → Exit Node → select the new node
- **CLI**: `sudo tailscale set --exit-node=<vps-hostname>`
- **Mobile**: Tailscale app → Exit Node → choose the VPS

### 6. Verify the exit node works

```bash
# Check public IP is now the VPS country
curl https://ifconfig.me
# Or
curl https://ipinfo.io/json
```

The IP should show the country of the VPS, not the user's home connection.

## Pitfalls

- **Server timezone**: The VPS likely defaults to UTC. If the user needs logs in local time, set it: `sudo timedatectl set-timezone America/Sao_Paulo`
- **Firewall**: Tailscale uses UDP port 41641. If the VPS has a strict firewall, open it: `ufw allow 41641/udp`
- **IPv6**: If the VPS has IPv6, Tailscale may prefer it. Check with `tailscale status` and disable IPv6 in the admin console if needed
- **Restart persistence**: Ensure Tailscale auto-starts: `sudo systemctl enable tailscaled`
- **Transfer limits**: Cheapest plans often cap transfer at 500GB-1TB. Monitor usage in the provider dashboard
- **No Colombia in Vultr**: Vultr has Chile, Brazil, Mexico, Argentina but NOT Colombia. Use DigitalOcean for Colombia

## References

- `references/vps-provider-research.md` — LATAM VPS pricing data from the 2026-06-16 research session
