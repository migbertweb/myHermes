const colors = {
  seed: 'oklch(0.65 0.18 260)',
  bg: 'oklch(0.99 0.0 0)',
  surface: 'oklch(0.98 0.005 260)',
  ink: 'oklch(0.15 0.02 260)',
  muted: 'oklch(0.45 0.02 260)',
  accent: 'oklch(0.7 0.2 25)',
};

const guidance = `Primary seed: ${colors.seed}.\nBackground: ${colors.bg}\nSurface: ${colors.surface}\nInk: ${colors.ink}\nMuted: ${colors.muted}\nAccent: ${colors.accent}\nUse OKLCH throughout.`;

if (typeof process !== 'undefined' && process.stdout.isTTY) {
  console.log(guidance);
} else {
  console.log(guidance);
}
