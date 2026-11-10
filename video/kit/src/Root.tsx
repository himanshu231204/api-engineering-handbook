import { Composition, type CalculateMetadataFunction } from "remotion";
import { Episode } from "./Episode";
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

export const RemotionRoot: React.FC = () => (
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
);
