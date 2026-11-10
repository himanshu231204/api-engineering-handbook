// Palette copied from docs/assets/diagrams (green = main path, blue = client,
// amber = data, red = failure, purple = AI/external, slate = infra).
export const colors = {
  green: "#1c7c54",
  greenSoft: "#e8f5ee",
  blue: "#2563eb",
  blueSoft: "#eff6ff",
  amber: "#b45309",
  amberSoft: "#fef3c7",
  red: "#b91c1c",
  redSoft: "#fee2e2",
  purple: "#6d28d9",
  slate: "#475569",
  bg: "#f8fafc",
  card: "#ffffff",
  border: "#cbd5e1",
  text: "#111827",
  muted: "#6b7280",
};

export const fonts = {
  sans: 'Inter, system-ui, -apple-system, "Segoe UI", Helvetica, Arial, sans-serif',
  mono: 'ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace',
};

// Video-first sizes (1920x1080). The skill's 1080px-wide minimums are treated as floors.
export const sizes = { headline: 96, body: 52, small: 44, caption: 44 };
export const minFontPx = 12;

// Safe area: keep key content away from the edges.
export const safe = { x: 160, top: 120, bottom: 220 };
