# CTA Outro Pattern (like/subscribe)

Validated in a 20s brand video (scene 4, 210 frames @30fps, 1920x1080). Reuse this structure for any "dale like y suscríbete / follow" ending.

## Scene layout
- **Background**: same image as the finale, `objectFit: cover`, `filter: blur(40px) brightness(0.45)`, scale 1.15 — dark blurred backdrop makes the foreground pop.
- **Main image**: centered, `width: 88%` of frame, borderRadius 18, deep boxShadow.
- **Text reveal**: if the image already contains its own title text, reveal it with `clipPath: inset(${top}% 0 0 0)` animated 100%→0 over ~45 frames with `Easing.inOut(cubic)`, plus a thin bright gradient line (`#ffd500 → #fff → #3ea6ff`) riding the reveal edge with a glow.
- **Ken Burns**: gentle `scale` 1→1.07 across the whole scene after the reveal.

## CTA panel (slides up from bottom)
- `spring({frame: frame - 95, config: {damping: 16, stiffness: 90}})` → translateY 420→0.
- Container: full-width bottom bar, `rgba(12,12,14,0.88)`, backdropFilter blur, rounded top corners, borderTop 2px white 12%.
- Left cluster: YouTube logo SVG (red play path, viewBox 0 0 24 16.8) + stacked text:
  - Line 1 white 800: "¡DALE LIKE" + inline thumbs-up SVG (Material thumb_up path, viewBox 0 0 24 24) that bounces.
  - Line 2 yellow (#ffd500) 700: "Y SUSCRÍBETE".
- Right cluster: red button (#ff0033) pill, rounded 40, glow shadow, bell SVG (Material notifications path) + "SUSCRIBIRSE" white 800.

## Like pulse animation
- Two staggered springs on the thumbs-up translateY: `pulse1 = spring(frame-125)`, `pulse2 = spring(frame-153)`, `likeUp = 1 - min(pulse1,1) * (1 - min(pulse2,1) * 0.9)` → thumb jumps up twice.
- Expanding ring around the YouTube logo: opacity `1 - likeRing`, scale `0.6 + likeRing*1.6` with `likeRing` over frames 135-175.

## Finale pop
- Confetti: ~6 colored rects (red/yellow/blue), each with staggered delay (frames 190-200), translateY -30→420, rotate 0→540, fade in/out.
- White full-frame flash: `opacity: finalFlash * finalFlashOut` where flash in 195-205 and out 205-210 — peaks right at the last frames.

## SVG paths (inline, no assets needed)
- YouTube: `M23.5 3.7a3 3 0 0 0-2.1-2.15C19.5 1 12 1 12 1s-7.5 0-9.4.55A3 3 0 0 0 .5 3.7 33 33 0 0 0 0 8.4a33 33 0 0 0 .5 4.7 3 3 0 0 0 2.1 2.15C4.5 15.8 12 15.8 12 15.8s7.5 0 9.4-.55a3 3 0 0 0 2.1-2.15A33 33 0 0 0 24 8.4a33 33 0 0 0-.5-4.7zM9.6 12V4.8L15.8 8.4 9.6 12z` (fill #ff0033)
- Thumbs up (Material thumb_up): `M1 21h4V9H1v12zM23 10c0-1.1-.9-2-2-2h-6.3l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.6 7.6C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z` (fill #fff)
- Bell (Material notifications): `M12 22c1.1 0 2-.9 2-2h-4c0 1.1.89 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z` (fill #fff)
