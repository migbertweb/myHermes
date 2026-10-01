# SPA Auth Bypass via Cloudflare

When a Single-Page Application (React, Vue, Svelte) sits behind Cloudflare and the browser's login flow fails (Cloudflare challenge blocks JS fetch, or bot detection interferes with form submission), use this curl-based token injection pattern to authenticate and navigate the app.

## Workflow

### 1. Discover the login API endpoint

Extract the auth endpoint from the JS bundle:

```bash
# Fetch the main JS module (or use web_extract)
curl -s 'https://app.example.com/assets/index-*.js' | grep -oP '["'"'"'][^"'"'"']*/api/[^"'"'"']*["'"'"']' | sort -u

# Look for login/auth endpoints:
#   "/api/auth/login"
#   "/api/login"
#   "/api/auth"
```

Alternatively, search for the specific pattern:

```bash
curl -s 'https://app.example.com/assets/index-*.js' | grep -oP 'login|auth|fetch|axios|/api/' | sort | uniq -c | sort -rn

# Then drill into a suspected endpoint:
curl -s 'https://app.example.com/assets/index-*.js' | grep -oP 'JSON.stringify.{0,200}'
# Look for field names like {username, password}, {email, password}, {usuario, clave}
```

### 2. Authenticate via curl

```bash
curl -s -X POST 'https://app.example.com/api/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"secret"}' \
  -w '\nHTTP: %{http_code}'

# Expected response: {"token":"eyJ...","user":{...}}
```

If the credentials are wrong the server returns 401. Try different field names (`username`, `email`, `usuario`).

### 3. Extract the token

```bash
curl -s -X POST 'https://app.example.com/api/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"secret"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])" > /tmp/token.txt
```

### 4. Verify the token works

```bash
TOKEN=$(cat /tmp/token.txt)
curl -s 'https://app.example.com/api/auth/me' \
  -H "Authorization: Bearer $TOKEN"
# Expected: {"id":1,"username":"admin",...}
```

### 5. Inject into browser localStorage

Since the browser console and the tool output prune long JWT tokens, use base64 encoding for transport:

```bash
# Encode on terminal
python3 -c "import base64, sys; print(base64.b64encode(open('/tmp/token.txt').read().strip().encode()).decode())"
# Copy the base64 output
```

```javascript
// Decode and set in browser console
localStorage.setItem('workapp_token', atob('<base64-token>'));
// Then reload
window.location.reload();
```

### 6. Navigate directly to app routes

After token injection, the SPA's auth check should succeed. Navigate to any route:

```javascript
window.location.href = 'https://app.example.com/dashboard';
```

## Pitfalls

- **Token key name differs per app:** Discover it from the JS bundle with `localStorage.getItem` search:
  ```bash
  curl -s 'https://app.example.com/assets/index-*.js' | grep -oP 'localStorage\.(get|set)Item\("[^"]+"'
  ```
- **Cloudflare still blocks in-browser fetch:** The injected token is for the SPA's own auth check. If the SPA uses relative URLs (`/api/...`) and Cloudflare blocks them with "Failed to fetch", the SPA may still not render. Try:
  - Using the absolute URL in the browser console to override the fetch
  - Logging in via the form while using the injected token (the form submission may succeed now that the token is present)
- **Token expiry:** Some tokens expire quickly. Re-authenticate and inject a fresh one if the SPA redirects back to the login page.
- **Credentials are case-sensitive:** If the login API returns "Credenciales inválidas", double-check the exact username and password with the user.
- **Form has no `name` attributes:** React SPAs handle form data via JavaScript, not HTML form submission. The `browser_type` + `browser_click` flow may work despite no `name` attributes — React listens for the submit event.
