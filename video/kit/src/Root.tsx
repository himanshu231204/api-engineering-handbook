import { Composition, Still, type CalculateMetadataFunction } from "remotion";
import { Episode } from "./Episode";
import { Thumbnail, type ThumbnailProps } from "./Thumbnail";
import type { EpisodeProps, Timeline } from "./types";

const placeholder: Timeline = {
  fps: 30,
  width: 1920,
  height: 1080,
  title: "Episode",
  part: 0,
  index: 0,
  totalFrames: 90,
  beats: [
    {
      name: "Hook",
      startFrame: 0,
      frames: 90,
      audio: null,
      cues: [{ scene: "Title", args: {}, startFrame: 0, frames: 90 }],
      captions: [],
    },
  ],
};

const calculateMetadata: CalculateMetadataFunction<EpisodeProps> = ({ props }) => ({
  durationInFrames: props.timeline.totalFrames,
  fps: props.timeline.fps,
  width: props.timeline.width,
  height: props.timeline.height,
});

const thumbDefaults: ThumbnailProps = { headline: "DNS", sub: "How a name becomes an IP", kicker: "API ENGINEERING HANDBOOK" };

export const RemotionRoot: React.FC = () => (
  <>
  <Still id="Thumbnail" component={Thumbnail} width={1280} height={720} defaultProps={thumbDefaults} />
  <Composition
    id="Episode"
    component={Episode}
    durationInFrames={placeholder.totalFrames}
    fps={30}
    width={1920}
    height={1080}
    defaultProps={{ timeline: placeholder }}
    calculateMetadata={calculateMetadata}
  />
  </>
);
