import { colors } from "../theme";
import type { SceneProps } from "../types";
import { ListScene } from "./ListScene";

export const Recap: React.FC<SceneProps> = ({ args }) => (
  <ListScene
    heading={args.heading ?? "Key takeaways"}
    items={(args.items ?? "").split("|").filter(Boolean)}
    accent={colors.green}
    soft={colors.greenSoft}
    mark="✓"
  />
);
