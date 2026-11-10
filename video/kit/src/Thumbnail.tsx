import { AbsoluteFill } from "remotion";
import { colors, fonts } from "./theme";

export type ThumbnailProps = { headline: string; sub: string; kicker: string };

/** 1280x720 YouTube thumbnail: one huge keyword, a short promise, readable at 160x90. */
export const Thumbnail: React.FC<ThumbnailProps> = ({ headline, sub, kicker }) => (
  <AbsoluteFill style={{ background: colors.bg, fontFamily: fonts.sans, padding: "56px 72px" }}>
    <div style={{ color: colors.green, fontSize: 34, fontWeight: 800, letterSpacing: 2 }}>{kicker}</div>
    <div
      style={{
        color: colors.text,
        fontSize: 340,
        fontWeight: 900,
        lineHeight: 1,
        marginTop: 28,
        letterSpacing: -8,
      }}
    >
      {headline}
    </div>
    <div style={{ display: "flex", alignItems: "center", gap: 28, marginTop: 20 }}>
      <div
        style={{
          background: colors.green,
          color: "#fff",
          fontSize: 74,
          fontWeight: 800,
          padding: "10px 34px",
          borderRadius: 24,
        }}
      >
        {sub}
      </div>
    </div>
    <div
      style={{
        position: "absolute",
        right: 72,
        bottom: 56,
        fontFamily: fonts.mono,
        fontSize: 40,
        color: colors.slate,
        background: colors.card,
        border: `4px solid ${colors.border}`,
        borderRadius: 18,
        padding: "12px 26px",
      }}
    >
      name → 93.184.216.34
    </div>
  </AbsoluteFill>
);
