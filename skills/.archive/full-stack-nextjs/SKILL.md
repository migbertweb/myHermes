---
name: full-stack-nextjs
description: Build complete Next.js 15+ full-stack applications with App Router, TypeScript, Prisma ORM (SQLite/Postgres), Auth.js v5, Tailwind CSS, React Hook Form + Zod. Covers scaffolding order, auth middleware, server actions, image upload, type safety pitfalls, and production-ready design.
---

# Full-Stack Next.js 15+ Project Scaffolding

## Trigger

When the user asks to create a complete Next.js project from a spec — especially one involving Auth.js, Prisma, server actions, uploads, and admin panels.

## Canonical Build Order

Follow this order strictly. Do NOT create all files in parallel and then fix errors. Each phase gates on the previous one compiling cleanly.

1. **Configs**: `package.json`, `tsconfig.json`, `next.config.ts`, `tailwind.config.ts`, `postcss.config.mjs`, `.env`, `.gitignore`
2. **Prisma schema** → `npx prisma migrate dev --name init`
3. **Auth core**: `lib/prisma.ts` → `types/next-auth.d.ts` → `auth.config.ts` → `auth.ts` → `middleware.ts` → `app/api/auth/[...nextauth]/route.ts`
4. **Server actions**: `lib/actions/auth.ts`, `lib/actions/cities.ts`, `lib/actions/items.ts`, `lib/actions/settings.ts`, `lib/actions/favorites.ts`
5. **Utility libs**: `lib/utils.ts`, `lib/categories.ts`, `lib/whatsapp.ts`, `lib/schemas.ts`
6. **Root layout** → `app/globals.css` → `app/layout.tsx`
7. **Auth pages**: `app/(auth)/layout.tsx` → login → register
8. **Setup page**: `app/setup/page.tsx` + `SetupForm.tsx`
9. **Public layout + navbar**: `app/(public)/layout.tsx` → `components/layout/Navbar.tsx`
10. **City context**: `components/city/CityProvider.tsx` + `CitySelectorModal.tsx`
11. **Shared components**: `ImageUpload`, `ItemCard`, `FavoriteButton`, `EmptyState`
12. **Public pages**: home → item detail → favorites
13. **Admin**: layout → dashboard → cities CRUD → items CRUD → settings
14. **Polish**: `not-found.tsx`, `error.tsx`, `loading.tsx`
15. **Build**: `npm run build` → fix errors → rebuild until clean
16. **Smoke test**: `npm run dev` + curl `/`, `/setup`, `/login`

## Pitfalls

### Auth.js v5 Middleware

The middleware MUST call `NextAuth(authConfig)` directly — NOT import `auth` from `@/auth`:

```ts
// middleware.ts — CORRECT
import NextAuth from "next-auth";
import { authConfig } from "@/auth.config";
export const { auth: middleware } = NextAuth(authConfig);
export const config = { matcher: ["/admin/:path*", "/favorites", "/setup"] };
```

### Auth.js v5 Type Augmentation

`user.role` is `unknown` without proper declaration. Use safe cast in `auth.config.ts`:

```ts
jwt({ token, user }) {
  if (user) {
    token.id = user.id!;
    token.role = (user as { role?: string }).role ?? "TOURIST";
  }
  return token;
}
```

### RSC Serialization: No Set/Map

Server components cannot pass `Set`, `Map`, or `Date` objects to client components. Use plain arrays:

```ts
// WRONG
const favoriteIds = new Set(favs.map(f => f.itemId));
// RIGHT
const favoriteIds: string[] = favs.map(f => f.itemId);
// Client: favoriteIds.includes(item.id)
```

### RSC Serialization: No React Components as Props

Server Components cannot pass React component references (functions/classes) to Client Components in plain data props, because the RSC payload serializes as JSON. This hits hardest with **Lucide icons** in nav/config arrays:

```tsx
// ❌ WRONG — Server Component → Client Component
// admin/layout.tsx (Server Component)
const navItems = [
  { href: "/admin", label: "Dashboard", icon: LayoutDashboard }, // ← function ref
];
<SidebarClient navItems={navItems} />

// admin/SidebarClient.tsx ("use client")
// Error: Functions cannot be passed directly to Client Components
<item.icon className="w-5 h-5" />
```

**Fix**: pass icon **name strings** from the server, resolve to components on the client via a lookup map:

```tsx
// admin/layout.tsx (Server Component) — strings only
const navItems = [
  { href: "/admin", label: "Dashboard", icon: "LayoutDashboard" },
];
<SidebarClient navItems={navItems} />

// admin/SidebarClient.tsx ("use client") — resolve via map
import { LayoutDashboard, type LucideIcon } from "lucide-react";

const ICON_MAP: Record<string, LucideIcon> = {
  LayoutDashboard,
  // ... add all icons used by navItems
};

// In render:
{navItems.map((item) => {
  const ItemIcon = ICON_MAP[item.icon];
  return ItemIcon && React.createElement(ItemIcon, { className: "w-5 h-5" });
})}
```

The same pattern applies to any React component reference (not just icons) — menu item renderers, custom link factories, template functions. Always serialize identifiers, never components.

Note: when using `React.createElement` in a Client Component, import `React` explicitly (`import React from "react"`) — a bare `import { useState } from "react"` won't provide `React` as a value, causing `'React' refers to a UMD global` at build time.

### force-dynamic Required

Any server component using `cookies()`, `headers()`, or `auth()` needs `export const dynamic = "force-dynamic"` at the top of the file. Without it, Next.js tries to statically render and fails.

### signOut in Server Components

Admin layout signOut button: use a server action with dynamic import, NOT a direct import of `signOut` from `@/auth`:

```ts
// lib/actions/auth.ts
export async function signOutAdmin() {
  const { signOut } = await import("@/auth");
  await signOut({ redirectTo: "/" });
}

// admin/layout.tsx
<form action={signOutAdmin}>
  <button>Sair</button>
</form>
```

### useSearchParams Requires Suspense

Any client component using `useSearchParams()` must be wrapped in `<Suspense>` from the server page:

```tsx
// page.tsx
<Suspense>
  <LoginForm />
</Suspense>
```

### ImageUpload Component

Make `onChange` optional — when `multiple=true`, only `onGalleryChange` is used:

```ts
interface ImageUploadProps {
  value?: string;
  onChange?: (url: string) => void;  // optional
  multiple?: boolean;
  gallery?: string[];
  onGalleryChange?: (urls: string[]) => void;
}
```

Guard all `onChange` callsites with `?.`:
```ts
onClick={() => onChange?.("")}
```

### EmptyState Icon Type

Use `LucideIcon` from lucide-react, never `any`:
```ts
import type { LucideIcon } from "lucide-react";
icon?: LucideIcon;
```

### React Hook Form + Image Upload

Image/gallery fields live OUTSIDE `useForm` — manage them with separate `useState`. Only text/select/checkbox fields go through RHF. On submit, merge both:

```ts
const { register, handleSubmit, formState: { errors } } = useForm<ItemInput>({
  resolver: zodResolver(itemSchema),
});
const [image, setImage] = useState("");
const [gallery, setGallery] = useState<string[]>([]);

async function onSubmit(data: ItemInput) {
  const formData = new FormData();
  // ... append RHF fields
  formData.set("image", image);
  formData.set("gallery", JSON.stringify(gallery));
  await createItem(formData);
}
```

### Server Error Mapping

Use a shared helper to map server-side Zod errors to RHF `setError`:
```ts
export function mapServerErrors(
  serverResult: { error?: Record<string, string[]> },
  setError: (field: string, error: { message: string }) => void,
  setServerError?: (msg: string) => void
) {
  if (!serverResult.error) return;
  for (const [key, msgs] of Object.entries(serverResult.error)) {
    if (key === "_form") setServerError?.(msgs[0]);
    else setError(key, { message: msgs[0] });
  }
}
```

## Verification Gates

After build passes, smoke-test with curl:
```bash
curl -sI http://localhost:3000/        # → 307 /setup (no admin yet)
curl -sI http://localhost:3000/setup   # → 200
curl -sI http://localhost:3000/login   # → 307 /setup
curl -sI http://localhost:3000/register # → 307 /setup
```

## Stack Verification

Before declaring done, verify EVERY mandatory stack item is actually used:
- [ ] Next.js 15+ App Router
- [ ] TypeScript (strict mode)
- [ ] Tailwind CSS (check tailwind.config.ts)
- [ ] Prisma ORM (check schema.prisma + migrations)
- [ ] SQLite (check datasource in schema)
- [ ] Auth.js v5 (check auth.ts + middleware)
- [ ] bcrypt (check auth.ts authorize function)
- [ ] React Hook Form (check ALL forms — grep for `useForm`)
- [ ] Zod (check schemas + resolvers)
- [ ] Lucide Icons (check imports)

## References

- `references/nextjs15-stack.md` — Session-specific fixes and patterns from real builds