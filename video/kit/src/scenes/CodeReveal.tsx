import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { progress } from "../anim";
import { colors, fonts, safe } from "../theme";
import type { SceneProps } from "../types";

/** Reveals `args.lines` (separated by `|`) one line at a time. */
export const CodeReveal: React.FC<SceneProps> = ({ args }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const lines = (args.lines ?? "").split("|");
  const slot = (durationInFrames * 0.75) / Math.max(lines.length, 1);
  return (
    <AbsoluteFill style={{ background: colors.bg, justifyContent: "center", alignItems: "center", fontFamily: fonts.sans }}>
      <div
        style={{
          width: 1920 - safe.x * 1.2,
          background: colors.card,
          border: `3px solid ${colors.border}`,
          borderLeft: `14px solid ${colors.blue}`,
          borderRadius: 20,
          padding: "36px 48px",
        }}
      >
        <div style={{ color: colors.blue, fontSize: 32, fontWeight: 700, marginBottom: 20 }}>
          {args.lang ?? "code"}
        </div>
        {lines.map((line, i) => (
          <div
            key={i}
            style={{
              opacity: progress(frame, 8 + i * slot, 10),
              color: line.trim().startsWith("#") ? colors.green : colors.text,
              fontFamily: fonts.mono,
              fontSize: 40,
              lineHeight: 1.55,
              whiteSpace: "pre-wrap",
            }}
          >
            {line || " "}
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};
