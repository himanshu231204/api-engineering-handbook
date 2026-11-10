import { colors } from "../theme";
import type { SceneProps } from "../types";
import { ListScene } from "./ListScene";

export const Mistakes: React.FC<SceneProps> = ({ args }) => (
  <ListScene
    heading={args.heading ?? "Common mistakes"}
    items={(args.items ?? "").split("|").filter(Boolean)}
    accent={colors.red}
    soft={colors.redSoft}
    mark="✕"
  />
);
