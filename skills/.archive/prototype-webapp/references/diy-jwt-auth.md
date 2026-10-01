# DIY JWT Auth for Express + SQLite prototypes

Lightweight authentication pattern using pure-JS deps — zero native compilation. Works with sql.js (WASM), compatible with any platform.

## Dependencies

```bash
npm install --no-audit --no-fund bcryptjs jsonwebtoken cookie-parser
```

| Package | Why |
|---|---|
| `bcryptjs` | Pure JS bcrypt. Not `bcrypt` (requires node-gyp, fails on Arch/CachyOS). |
| `jsonwebtoken` | JWT sign/verify. Pure JS. |
| `cookie-parser` | Parse httpOnly cookies from Express requests. |

## Backend: auth.js

### Tables

Add to your SQLite schema:

```sql
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  created_at TEXT
);
```

### Seed default admin

```js
import bcrypt from 'bcryptjs';
import { db } from './db.js';

export async function seedAdmin() {
  const existing = db.prepare('SELECT id FROM users WHERE username = ?').get('admin');
  if (!existing) {
    const hash = await bcrypt.hash('admin123', 10); // 10 salt rounds
    db.prepare('INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)')
      .run('admin', hash, new Date().toISOString());
  }
}
```

### JWT middleware

```js
import jwt from 'jsonwebtoken';

const JWT_SECRET = process.env.JWT_SECRET || 'change-me-in-production';
const COOKIE_NAME = 'app_token';

export function requireAuth(req, res, next) {
  const token =
    req.cookies?.[COOKIE_NAME] ||
    (req.headers.authorization?.startsWith('Bearer ')
      ? req.headers.authorization.slice(7)
      : null);

  if (!token) return res.status(401).json({ message: 'No autenticado' });

  try {
    const payload = jwt.verify(token, JWT_SECRET);
    req.userId = payload.sub;
    req.username = payload.username;
    next();
  } catch {
    return res.status(401).json({ message: 'Token inválido o expirado' });
  }
}
```

### Auth routes

```js
export function authRoutes(app) {
  // POST /api/auth/login
  app.post('/api/auth/login', async (req, res) => {
    const { username, password } = req.body;
    const user = db.prepare('SELECT * FROM users WHERE username = ?').get(username);
    if (!user || !(await bcrypt.compare(password, user.password_hash))) {
      return res.status(401).json({ message: 'Credenciales inválidas' });
    }
    const token = jwt.sign(
      { sub: user.id, username: user.username },
      JWT_SECRET,
      { expiresIn: '7d' }
    );
    res.cookie(COOKIE_NAME, token, {
      httpOnly: true, sameSite: 'lax',
      maxAge: 7 * 24 * 60 * 60 * 1000,
    });
    res.json({ token, user: { id: user.id, username: user.username } });
  });

  // POST /api/auth/logout
  app.post('/api/auth/logout', (req, res) => {
    res.clearCookie(COOKIE_NAME);
    res.json({ message: 'Sesión cerrada' });
  });

  // GET /api/auth/me
  app.get('/api/auth/me', requireAuth, (req, res) => {
    res.json({ id: req.userId, username: req.username });
  });

  // PUT /api/auth/password — change password
  app.put('/api/auth/password', requireAuth, async (req, res) => {
    const { currentPassword, newPassword } = req.body;
    const user = db.prepare('SELECT * FROM users WHERE id = ?').get(req.userId);
    const valid = await bcrypt.compare(currentPassword, user.password_hash);
    if (!valid) return res.status(401).json({ message: 'Contraseña actual incorrecta' });
    const hash = await bcrypt.hash(newPassword, 10);
    db.prepare('UPDATE users SET password_hash = ? WHERE id = ?').run(hash, req.userId);
    res.json({ message: 'Contraseña actualizada' });
  });
}
```

### Wire into server.js

```js
import cookieParser from 'cookie-parser';
import { seedAdmin, requireAuth, authRoutes } from './auth.js';

app.use(cookieParser());

// Auth routes (public)
authRoutes(app);

// Protect all /api/* routes except auth and public endpoints
app.use('/api', (req, res, next) => {
  if (req.path.startsWith('/auth') || req.path === '/market_rates') return next();
  requireAuth(req, res, next);
});

// ... your API routes here ...

const PORT = process.env.PORT || 3001;
bootstrap().then(async () => {
  await seedAdmin();  // MUST be after bootstrap() so DB is ready
  app.listen(PORT, () => console.log(`Running on :${PORT}`));
});
```

## Frontend: React auth context

### AuthContext.jsx

```jsx
import { createContext, useContext, useState, useEffect, useCallback } from 'react';

const AuthContext = createContext(null);
export function useAuth() { return useContext(AuthContext); }

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check session on mount
  useEffect(() => {
    fetch('/api/auth/me', { credentials: 'include' })
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data?.username) setUser(data); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const login = async (username, password) => {
    const res = await fetch('/api/auth/login', {
      method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    if (!res.ok) throw new Error((await res.json()).message);
    const data = await res.json();
    localStorage.setItem('app_token', data.token);
    setUser(data.user);
  };

  const logout = async () => {
    await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
    localStorage.removeItem('app_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
```

### App.jsx — auth gate

```jsx
import { AuthProvider, useAuth } from './AuthContext.jsx';
import Login from './pages/Login.jsx';

function AppContent() {
  const { user, loading } = useAuth();
  if (loading) return <div>Cargando…</div>;
  if (!user) return <Login />;
  return <YourAppLayout />;  // sidebar, routes, etc
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </BrowserRouter>
  );
}
```

### api.js — attach JWT + handle 401

```js
const BASE = '/api';

async function request(path, opts = {}) {
  const token = localStorage.getItem('app_token');
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(BASE + path, {
    headers, credentials: 'include',
    ...opts,
    headers: { ...headers, ...(opts.headers || {}) }
  });

  if (res.status === 401) {
    localStorage.removeItem('app_token');
    window.location.reload();
    throw new Error('Sesión expirada');
  }

  const text = await res.text();
  let data = {};
  try { data = JSON.parse(text); } catch {}
  if (!res.ok) throw new Error(data.message || `HTTP ${res.status}`);
  return data;
}
```

### Login.jsx

Simple centered form: username + password + error banner + submit button. See full example in workapp-agent `client/src/pages/Login.jsx`.

### Logout button in sidebar

```jsx
const { logout } = useAuth();
<button onClick={logout} className="sidebar-link" style={{ color: 'var(--danger)' }}>
  <LogOut size={18} /> Cerrar Sesión
</button>
```

## Decision rule

Use this DIY JWT pattern when:
- The app needs authentication (single or few users)
- You control the server
- You want zero-native deps (Arch/CachyOS friendly)
- You don't want OAuth/third-party auth complexity

Don't use this for:
- Multi-tenant SaaS needing OAuth providers (Google, GitHub) — use Passport.js
- Serverless/edge environments where JWT verification overhead matters — consider Lucia Auth
