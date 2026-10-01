# Next.js 15 Stack — Session Patterns & Fixes

## Auth.js v5 Middleware Pattern

The middleware MUST instantiate `NextAuth(authConfig)` directly — importing `auth` from `@/auth` causes a runtime error because the middleware runs in the Edge runtime and `@/auth` imports `bcryptjs` which has Node.js dependencies.

```ts
// middleware.ts — CORRECT
import NextAuth from "next-auth";
import { authConfig } from "@/auth.config";
export const { auth: middleware } = NextAuth(authConfig);
export const config = { matcher: ["/admin/:path*", "/favorites", "/setup"] };
```

## Auth.js v5 Type Augmentation

`user.role` is typed as `unknown` in the default NextAuth types. The `types/next-auth.d.ts` augmentation helps but the `jwt` callback still needs a safe cast:

```ts
// auth.config.ts
jwt({ token, user }) {
  if (user) {
    token.id = user.id!;
    token.role = (user as { role?: string }).role ?? "TOURIST";
  }
  return token;
}
```

## RSC Serialization: Set/Map Not Serializable

Server components cannot pass `Set`, `Map`, `Date`, or `BigInt` to client components. The Next.js RSC boundary serializes to JSON. Use plain arrays:

```ts
// Server component — WRONG
const favoriteIds = new Set(favs.map(f => f.itemId));
// Server component — RIGHT
const favoriteIds: string[] = favs.map(f => f.itemId);
// Client component
favorited={favoriteIds.includes(item.id)}
```

## force-dynamic Required for Dynamic APIs

Any server component using `cookies()`, `headers()`, `auth()`, or `searchParams` needs:

```ts
export const dynamic = "force-dynamic";
```

Without it, Next.js 15 tries to statically render at build time and fails because these APIs are only available at request time.

## signOut in Server Component Layouts

Admin layout signOut button: cannot import `signOut` directly from `@/auth` in a server component because it's a client-side function. Use a server action with dynamic import:

```ts
// lib/actions/auth.ts
export async function signOutAdmin() {
  const { signOut } = await import("@/auth");
  await signOut({ redirectTo: "/" });
}

// admin/layout.tsx
import { signOutAdmin } from "@/lib/actions/auth";
// ...
<form action={signOutAdmin}>
  <button>Sair</button>
</form>
```

## useSearchParams Requires Suspense Boundary

Any client component using `useSearchParams()` must be wrapped in `<Suspense>` from the parent server component. Next.js 15 enforces this at build time:

```tsx
// page.tsx (server)
import { Suspense } from "react";
export default function Page() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}
```

## ImageUpload Component — onChange Optional

When `multiple=true`, only `onGalleryChange` is used. Make `onChange` optional and guard all callsites:

```ts
interface ImageUploadProps {
  value?: string;
  onChange?: (url: string) => void;  // optional
  multiple?: boolean;
  gallery?: string[];
  onGalleryChange?: (urls: string[]) => void;
}

// Guard callsites
onClick={() => onChange?.("")}
if (data.urls[0] && onChange) onChange(data.urls[0]);
```

Also gate the preview render on `onChange` being defined:
```tsx
{value && !multiple && onChange && (
  <div className="relative ...">
    <Image ... />
    <button onClick={() => onChange("")}>...</button>
  </div>
)}
```

## EmptyState Icon Type

Use `LucideIcon` from lucide-react, never `any`:

```ts
import type { LucideIcon } from "lucide-react";
import { Search } from "lucide-react";

export function EmptyState({
  icon: Icon = Search,
  ...
}: {
  icon?: LucideIcon;
  ...
})
```

## React Hook Form + Image Upload Pattern

Image/gallery fields live OUTSIDE `useForm` — manage them with separate `useState`. Only text/select/checkbox fields go through RHF. On submit, merge both into FormData:

```tsx
const { register, handleSubmit, formState: { errors } } = useForm<ItemInput>({
  resolver: zodResolver(itemSchema),
  defaultValues: editing ? { ...editing, gallery: undefined } : {},
});
const [image, setImage] = useState(editing?.image || "");
const [gallery, setGallery] = useState<string[]>(() => {
  try { return JSON.parse(editing?.gallery || "[]"); }
  catch { return []; }
});

async function onSubmit(data: ItemInput) {
  const formData = new FormData();
  for (const [key, value] of Object.entries(data)) {
    if (value !== undefined && value !== null) {
      formData.set(key, String(value));
    }
  }
  formData.set("image", image);
  formData.set("gallery", JSON.stringify(gallery));
  const result = editing
    ? await updateItem(editing.id, formData)
    : await createItem(formData);
  if (result.error) mapServerErrors(result.error, setError, setServerError);
  else { setModalOpen(false); router.refresh(); }
}
```

## Server Error Mapping Helper

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

## Build Verification

After build passes, smoke-test with curl:
```bash
curl -sI http://localhost:3000/        # → 307 /setup (no admin yet)
curl -sI http://localhost:3000/setup   # → 200
curl -sI http://localhost:3000/login   # → 307 /setup
curl -sI http://localhost:3000/register # → 307 /setup
```

## Stack Compliance Checklist

Before declaring done, grep for each mandatory item:
- `useForm` — must appear in every form component
- `zodResolver` — must appear alongside `useForm`
- `bcrypt` — must appear in auth.ts authorize
- `lucide-react` — must appear in at least one component
- `PrismaClient` — must appear in lib/prisma.ts