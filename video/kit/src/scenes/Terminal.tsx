import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { progress } from "../anim";
import { colors, fonts, safe } from "../theme";
import type { SceneProps } from "../types";

/** Types out `args.lines` (separated by `|`) in a terminal window. */
export const Terminal: React.FC<SceneProps> = ({ args }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const lines = (args.lines ?? "").split("|");
  const total = lines.reduce((n, l) => n + l.length + 1, 0);
  const typed = Math.floor(
    Math.min(1, frame / (durationInFrames * 0.7)) * total,
  );
  let remaining = typed;
  const visible = lines.map((line) => {
    const take = Math.max(0, Math.min(line.length, remaining));
    remaining -= line.length + 1;
    return { text: line.slice(0, take), started: take > 0 || remaining >= 0 };
  });
  return (
    <AbsoluteFill style={{ background: colors.bg, justifyContent: "center", alignItems: "center", fontFamily: fonts.sans }}>
      <div
        style={{
          opacity: progress(frame, 0, 12),
          width: 1920 - safe.x * 1.2,
          background: "#0f172a",
          borderRadius: 24,
          boxShadow: "0 10px 40px rgba(15,23,42,0.35)",
          overflow: "hidden",
        }}
      >
        <div style={{ background: "#1e293b", padding: "16px 24px", display: "flex", alignItems: "center", gap: 12 }}>
          {["#ef4444", "#f59e0b", "#22c55e"].map((c) => (
            <span key={c} style={{ width: 18, height: 18, borderRadius: 9, background: c }} />
          ))}
          <span style={{ color: "#94a3b8", fontSize: 28, marginLeft: 16 }}>{args.title ?? "terminal"}</span>
        </div>
        <div style={{ padding: "32px 44px", minHeight: 420, fontFamily: fonts.mono, fontSize: 40, lineHeight: 1.5 }}>
          {visible.map((l, i) =>
            l.started ? (
              <div key={i} style={{ color: l.text.startsWith("$") || i === 0 ? "#86efac" : "#e2e8f0", whiteSpace: "pre-wrap" }}>
                {l.text || " "}
              </div>
            ) : null,
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};
