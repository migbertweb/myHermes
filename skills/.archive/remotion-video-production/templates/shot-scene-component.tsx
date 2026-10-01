import React from "react";
import { AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

/**
 * ShotScene Component
 * 
 * Reusable Remotion scene for Developer/Tech Reels. 
 * Displays a 16:9 screenshot (e.g., desktop ricing, IDE) inside a 9:16 vertical video, 
 * framed with a glowing neon border and responsive animations.
 * 
 * Usage: Requires existing text components (TitleText, Kicker) and a Backdrop.
 */
export const ShotScene: React.FC<{
  shot: string;       // path to staticFile mapping e.g., "img/arch-shot1.png"
  kicker?: string;
  title: string;
  subtitle?: string;
}> = ({ shot, kicker, title, subtitle }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  // Entrance animation for hovering frame
  const s = spring({ frame: frame - 8, fps, config: { damping: 13 } });
  
  // Pulsing glow effect over time
  const glow = interpolate(frame % 40, [0, 20, 40], [0.5, 0.9, 0.5]);
  
  return (
    <AbsoluteFill>
      {/* Insert Background (e.g. GradientBackdrop) here */}

      {/* Text Area */}
      <AbsoluteFill
        style={{
          flexDirection: "column",
          justifyContent: "flex-start",
          alignItems: "flex-start",
          padding: "120px 72px 0 72px",
        }}
      >
        {/* Insert {kicker && <Kicker... />} etc. here */}
      </AbsoluteFill>

      {/* Floating 16:9 Frame */}
      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          transform: `translateY(${(1 - s) * 60}px) scale(${0.94 + s * 0.06})`,
          opacity: s,
        }}
      >
        <div
          style={{
            width: 880,
            height: 495, // 16:9 ratio locked inside 1080px width
            borderRadius: 24,
            overflow: "hidden",
            border: "3px solid rgba(34,211,238,0.7)",
            boxShadow: `0 0 60px rgba(34,211,238,${glow * 0.5}), 0 24px 80px rgba(0,0,0,0.6)`,
            marginTop: 560, // Pushed downward to leave upper third for text
          }}
        >
          <Img
            src={staticFile(shot)}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
