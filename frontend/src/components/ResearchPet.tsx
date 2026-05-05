import { useState, useRef, useCallback, useEffect } from "react";
import { generatePetSummary } from "../api/client";
import { useI18n } from "../i18n";

interface ResearchPetProps {
  pageName: string;
  context?: Record<string, unknown>;
  useLlm?: boolean;
}

function Pup() {
  return (
    <img
      className="rabot-pup-img"
      src="/hanbao.png"
      alt="RAbot 小助手"
      draggable={false}
    />
  );
}

function ResearchPet({ pageName, context = {}, useLlm = true }: ResearchPetProps) {
  const { language } = useI18n();
  const [open, setOpen] = useState(false);
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [pos, setPos] = useState({ x: 0, y: 0 });
  const dragging = useRef(false);
  const offset = useRef({ x: 0, y: 0 });
  const shellRef = useRef<HTMLDivElement>(null);

  const onPointerDown = useCallback((e: React.PointerEvent) => {
    dragging.current = true;
    offset.current = {
      x: e.clientX - pos.x,
      y: e.clientY - pos.y,
    };
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  }, [pos]);

  const onPointerMove = useCallback((e: React.PointerEvent) => {
    if (!dragging.current) return;
    setPos({
      x: e.clientX - offset.current.x,
      y: e.clientY - offset.current.y,
    });
  }, []);

  const onPointerUp = useCallback(() => {
    dragging.current = false;
  }, []);

  const text = language === "en"
    ? {
        bubble: "Watching",
        open: "RAbot assistant",
        status: "I can quietly sum up this page in one sentence.",
        market: "Summarize market",
        page: "Summarize this page",
        loading: "Reading the tape...",
        fallback: "I could not reach the model, but we can first check the data changes on this page."
      }
    : {
        bubble: "我在看盘",
        open: "RAbot 小助手",
        status: "我可以安静地用一句话帮你看懂这一页。",
        market: "总结今日市场",
        page: "总结这一页",
        loading: "正在读盘...",
        fallback: "我刚刚没连上模型，但可以先看看页面里的数据变化。"
      };

  const ask = async (mode: "market" | "page") => {
    setLoading(true);
    setError("");
    try {
      const response = await generatePetSummary({
        page_name: pageName,
        mode,
        context: { page_name: pageName, ...context },
        use_llm: useLlm
      });
      setAnswer(response.text || text.fallback);
      if (response.warnings.length) {
        setError(response.warnings[0]);
      }
    } catch (exc) {
      setAnswer(text.fallback);
      setError(exc instanceof Error ? exc.message : text.fallback);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      ref={shellRef}
      className="research-pet-shell"
      style={{ transform: `translate(${pos.x}px, ${pos.y}px)` }}
    >
      <button
        className="research-pet-button"
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-label={text.open}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
      >
        <span className="research-pet-bubble">{text.bubble}</span>
        <Pup />
      </button>

      {open ? (
        <div className="research-pet-card">
          <p className="text-sm font-medium text-ink">{text.status}</p>
          <div className="mt-3 grid gap-2">
            <button className="primary-button w-full justify-center" type="button" onClick={() => void ask("market")} disabled={loading}>
              {loading ? text.loading : text.market}
            </button>
            <button className="secondary-button w-full justify-center" type="button" onClick={() => void ask("page")} disabled={loading}>
              {text.page}
            </button>
          </div>
          {answer ? <p className="research-pet-answer">{answer}</p> : null}
          {error ? <p className="mt-2 text-xs leading-5 text-amber-700">{error}</p> : null}
        </div>
      ) : null}
    </div>
  );
}

export default ResearchPet;
