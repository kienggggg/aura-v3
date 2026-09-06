import { Composition } from "remotion";
import { TheAlpha, type Props } from "./TheAlpha";

export const FPS = 24;
export const RONG = 720;
export const CAO = 1280;

// ĐỘ DÀI SUY TỪ `moc`, không gõ tay. Mốc do `doc_giong_theo_doan` đo được từ
// độ dài thật của từng đoạn giọng đọc; đóng đinh một `durationInFrames` ở đây
// là dựng lại đúng phép chia đều vừa gỡ bỏ ngày 06/09/2026.
export const Root: React.FC = () => (
  <Composition
    id="TheAlpha"
    component={TheAlpha}
    fps={FPS}
    width={RONG}
    height={CAO}
    durationInFrames={1}
    defaultProps={{ cau: ["Chưa có kịch bản."], moc: [[0, 1]] } as Props}
    calculateMetadata={({ props }) => {
      const m = props.moc;
      const cuoi = m.length ? m[m.length - 1][1] : 1;
      return { durationInFrames: Math.max(1, Math.round(cuoi * FPS)) };
    }}
  />
);
