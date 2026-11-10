import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { progress } from "../anim";
import { colors, fonts, safe, sizes } from "../theme";

type Props = { heading: string; items: string[]; accent: string; soft: string; mark: string };

/** Shared layout for Mistakes and Recap: a heading and staggered item cards. */
export const ListScene: React.FC<Props> = ({ heading, items, accent, soft, mark }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const stagger = Math.max(6, Math.floor((durationInFrames * 0.6) / Math.max(items.length, 1)));
  return (
    <AbsoluteFill
      style={{ background: colors.bg, fontFamily: fonts.sans, padding: `${safe.top}px ${safe.x}px ${safe.bottom - 100}px` }}
    >
      <div style={{ opacity: progress(frame, 0), color: accent, fontSize: sizes.headline, fontWeight: 800 }}>
        {heading}
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 24, marginTop: 40 }}>
        {items.map((item, i) => {
          const p = progress(frame, 10 + i * stagger, 18);
          return (
            <div
              key={i}
              style={{
                opacity: p,
                translate: `${(1 - p) * 60}px 0px`,
                display: "flex",
                alignItems: "center",
                gap: 28,
                background: soft,
                border: `3px solid ${accent}`,
                borderRadius: 20,
                padding: "20px 32px",
                color: colors.text,
                fontSize: sizes.small,
                lineHeight: 1.3,
              }}
            >
              <span style={{ color: accent, fontSize: 56, fontWeight: 800 }}>{mark}</span>
              <span>{item}</span>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
