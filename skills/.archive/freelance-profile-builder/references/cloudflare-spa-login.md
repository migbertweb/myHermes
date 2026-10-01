# Cloudflare SPA Login Injection

When a Single Page Application (SPA) behind Cloudflare requires login to capture screenshots for portfolio, the standard `browser_navigate` + form-fill may fail because Cloudflare's challenge intercepts relative-URL fetch calls from the SPA's JavaScript.

## Workaround: Token injection via API

### Step 1: Login via curl to get token

```bash
TOKEN=$(curl -s -X POST 'https://example.com/api/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"username":"USER","password":"PASS"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
echo "$TOKEN" > /tmp/token.txt
```

### Step 2: Base64-encode the token

```python
python3 -c "import base64; print(base64.b64encode(open('/tmp/token.txt').read().strip().encode()).decode())"
```

This avoids shell escaping issues with long JWT tokens that contain special characters.

### Step 3: Inject into browser console

Navigate to the page, then in browser console:

```javascript
localStorage.setItem('app_token', atob('BASE64_ENCODED_TOKEN'));
window.location.reload();
```

### Step 4: If relative fetch still fails

The SPA may use relative URLs (`/api/auth/me`) that Cloudflare blocks. After setting the token, try a hard navigation to the dashboard:

```javascript
fetch('https://example.com/api/auth/me', {
  headers: {'Authorization': 'Bearer ' + localStorage.getItem('app_token')}
}).then(r => r.json()).then(user => {
  if (user && user.username) {
    window.location.href = 'https://example.com/dashboard';
  }
}).catch(console.error);
```

The SPA reads the token from localStorage on load and renders the authenticated view.

## When this approach fails

- The token has CSRF protections (bound to IP/user-agent) — curl token won't match browser session
- The SPA server-renders based on cookies, not localStorage Authorization headers
- Cloudflare blocks the absolute URL too (rare for API routes)

In those cases, try logging in via browser form-fill with correct credentials — sometimes the initial Cloudflare challenge only fires on first load and subsequent requests pass through.
