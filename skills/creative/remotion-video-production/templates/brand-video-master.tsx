// Master skeleton for a multi-scene Remotion video with TransitionSeries.
// Copy into src/BrandVideo/BrandVideo.tsx, adjust durations/transitions/scenes.
// Frame math: total = sum(sequences) - sum(transitions).
// With seqs 150/150/150/210 and 3x20f transitions, total = 600 (20s @30fps),
// scenes start at frames 0 / 130 / 260 / 390.
import React from "react";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { flip } from "@remotion/transitions/flip";
import { clockWipe } from "@remotion/transitions/clock-wipe";
import { fade } from "@remotion/transitions/fade";
import { useVideoConfig } from "remotion";
import { SceneA } from "./SceneA";
import { SceneB } from "./SceneB";
import { SceneC } from "./SceneC";
import { SceneFinal } from "./SceneFinal";

export const BrandVideo: React.FC = () => {
  const { width, height } = useVideoConfig();

  return (
    <TransitionSeries>
      <TransitionSeries.Sequence durationInFrames={150} name="SceneA">
        <SceneA />
      </TransitionSeries.Sequence>

      <TransitionSeries.Transition
        presentation={flip({ direction: "from-left", perspective: 900 })}
        timing={linearTiming({ durationInFrames: 20 })}
      />

      <TransitionSeries.Sequence durationInFrames={150} name="SceneB">
        <SceneB />
      </TransitionSeries.Sequence>

      <TransitionSeries.Transition
        presentation={clockWipe({ width, height })}
        timing={linearTiming({ durationInFrames: 20 })}
      />

      <TransitionSeries.Sequence durationInFrames={150} name="SceneC">
        <SceneC />
      </TransitionSeries.Sequence>

      <TransitionSeries.Transition
        presentation={fade()}
        timing={linearTiming({ durationInFrames: 20 })}
      />

      <TransitionSeries.Sequence durationInFrames={210} name="Final CTA">
        <SceneFinal />
      </TransitionSeries.Sequence>
    </TransitionSeries>
  );
};

// Scene skeleton (SceneA.tsx): entrance driven by frame, not CSS.
// import { AbsoluteFill, Easing, Img, Interactive, interpolate, spring,
//          staticFile, useCurrentFrame, useVideoConfig } from "remotion";
// export const SceneA: React.FC = () => {
//   const frame = useCurrentFrame();
//   const { fps } = useVideoConfig();
//   const entrance = spring({ frame, fps, config: { damping: 14, stiffness: 110 } });
//   const scale = interpolate(entrance, [0, 1], [0.15, 1], {
//     extrapolateLeft: "clamp", extrapolateRight: "clamp",
//     output: "perceptual-scale",
//   });
//   return (
//     <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", backgroundColor: "#fff" }}>
//       <Interactive.Div name="Logo" style={{ scale: `${scale}` }}>
//         <Img src={staticFile("logo.jpg")} style={{ height: 1000 }} />
//       </Interactive.Div>
//     </AbsoluteFill>
//   );
// };
