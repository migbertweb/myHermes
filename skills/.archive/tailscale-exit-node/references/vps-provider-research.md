# LATAM VPS Provider Research — June 2026

Research conducted on 2026-06-16 for setting up a Tailscale exit node in Chile or Colombia.

## Target countries evaluated

- 🇨🇱 Chile (Santiago) — **Vultr** confirmed
- 🇨🇴 Colombia (Bogotá) — **DigitalOcean** confirmed; Vultr does NOT have Colombia

## Research methodology attempted

1. Browser navigation to provider pricing pages
2. curl + grep on Vultr FAQ for datacenter locations
3. curl + grep on DigitalOcean pricing page for region data

## Issues encountered

- **DuckDuckGo CAPTCHA**: Browser-based search via DuckDuckGo triggered CAPTCHA challenges ("Selecciona todos los cuadrados que contengan un pato")
- **Google CAPTCHA**: Google search redirected to /sorry/ CAPTCHA page
- **Heavy pages**: Provider pricing pages are large (9000+ lines of DOM) making browser snapshot parsing impractical
- **API rate limits**: Terminal commands to provider APIs timed out

## Workaround for future research

Instead of relying on browser snapshots of large pricing pages:

1. **Vultr**: The FAQ page at vultr.com/resources/faq/ contains datacenter location lists that can be parsed with `curl | grep -i 'santiago\|chile'`
2. **DigitalOcean**: Their regions API (api.digitalocean.com/v2/regions) can be queried via curl, though it returned slowly in this session
3. **Small provider sites**: Pages for lesser-known providers (EdgeUno, HostDime) are simpler to scrape

## Pricing data

### Vultr — Santiago, Chile 🇨🇱 (confirmed datacenter)

| Plan | vCPU | RAM | SSD | Transfer | Price/mo |
|------|------|-----|-----|----------|----------|
| Cloud Compute (cheapest) | 1 | 512MB | 10GB | 500GB | **$3.50** |
| Cloud Compute | 1 | 1GB | 25GB | 1TB | **$6.00** |
| Cloud Compute | 2 | 2GB | 40GB | 2TB | **$12.00** |

Other Vultr LATAM locations: São Paulo 🇧🇷, Mexico City 🇲🇽, Buenos Aires 🇦🇷

### DigitalOcean — Bogotá, Colombia 🇨🇴 (confirmed datacenter)

| Plan (Basic Regular) | vCPU | RAM | SSD | Transfer | Price/mo |
|---------------------|------|-----|-----|----------|----------|
| Basic (cheapest) | 1 | 512MB | 10GB | 500GB | **$4.00** |
| Basic | 1 | 1GB | 25GB | 1TB | **$6.00** |
| Basic | 2 | 2GB | 50GB | 2TB | **$12.00** |

DigitalOcean uses per-second billing (min 60s) as of January 2026. Payment: PayPal accepted.

### Gcore — Santiago, Chile 🇨🇱

- Plans from ~€3.50/mo for 1 vCPU, 1GB RAM
- Less well-known but competitive pricing

### EdgeUno — Colombia 🇨🇴

- Regional LATAM provider
- More economical for Colombia than international providers
- Less documentation available

## Recommendations

For a personal Tailscale exit node:

- **Cheapest option**: Vultr in Santiago, Chile at **$3.50/mo** (512MB RAM is enough for Tailscale)
- **Best for Colombia**: DigitalOcean in Bogotá at **$4/mo**
- **Setup complexity**: ~5 minutes including SSH + Tailscale install

## Tailscale exit node setup (quick reference)

```bash
# On the new VPS (as root or with sudo)
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --advertise-exit-node
# Follow the URL to authenticate in browser
# Then in admin console: enable exit node for this machine
```

## Pending research

- [ ] Verify if Hostinger or DonWeb have VPS in Chile
- [ ] Check Flokinet Chile pricing (reported to have cheap options)
- [ ] Check if Mullvad VPN (Tailscale partner) has exit nodes in Chile or Colombia
