import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

export type Props = {
  cau: string[];
  moc: [number, number][];
};

// VÌ SAO CÓ TỆP NÀY (06/09/2026)
//
// `sinh_the_hinh` vẽ ảnh TĨNH bằng PIL rồi ffmpeg chiếu mỗi ảnh một khoảng.
// Mỗi thẻ là một khung hình đứng yên; không có gì chuyển động được, vì thứ duy
// nhất tồn tại là một tệp PNG.
//
// Ở đây MỖI KHUNG được dựng lại từ `frame`, nên chữ hiện dần, nhích lên, và
// thanh tiến độ chạy theo ĐÚNG mốc đo được của đoạn ấy.
//
// CHỮ Ở ĐÂY KHÔNG THAY THẾ `.srt`. `core/phong_alpha.py` ghi thẳng: *"Viết ra
// tệp .srt RIÊNG chứ không nung chữ vào khung hình: nung vào thì không ai kiểm
// được bằng máy"*. Luồng phụ đề vẫn do ffmpeg gắn, `ffprobe` vẫn đọc ra.
export const TheAlpha: React.FC<Props> = ({ cau, moc }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const giay = frame / fps;

  let i = moc.findIndex(([bd, kt]) => giay >= bd && giay < kt);
  if (i < 0) i = giay < moc[0][0] ? 0 : moc.length - 1;
  const [bd, kt] = moc[i];

  const mo = interpolate(giay, [bd, bd + 0.25], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const nhich = interpolate(giay, [bd, bd + 0.4], [26, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const tien = interpolate(giay, [bd, kt], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(160deg, hsl(${212 + i * 9} 46% 13%), hsl(${
          258 + i * 6
        } 42% 7%))`,
        fontFamily: "Segoe UI, Tahoma, Arial, sans-serif",
        color: "#EAF2FF",
        padding: 64,
        justifyContent: "center",
      }}
    >
      <div style={{ position: "absolute", top: 76, left: 64, fontSize: 24, opacity: 0.5 }}>
        THẺ {i + 1}/{moc.length}
      </div>

      <div
        style={{
          fontSize: 52,
          lineHeight: 1.36,
          fontWeight: 700,
          opacity: mo,
          transform: `translateY(${nhich}px)`,
        }}
      >
        {cau[i] ?? ""}
      </div>

      <div
        style={{
          position: "absolute",
          left: 64,
          right: 64,
          bottom: 100,
          height: 6,
          background: "rgba(255,255,255,0.14)",
          borderRadius: 3,
        }}
      >
        <div
          style={{
            width: `${tien * 100}%`,
            height: "100%",
            background: "#6EA8FF",
            borderRadius: 3,
          }}
        />
      </div>
    </AbsoluteFill>
  );
};
