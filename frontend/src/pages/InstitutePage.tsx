import { useState, useCallback, useRef, useEffect, FormEvent } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, ChevronDown, ChevronUp, Loader2, Gavel, TrendingUp, TrendingDown, BarChart3, Newspaper } from "lucide-react";
import { startInstituteAnalysis, fetchInstituteResult, fetchTask, searchStocks } from "../api/client";
import type { InstituteAnalysisResult } from "../api/client";
import ProgressBar from "../components/ProgressBar";

const examples = ["TSLA.US", "600519.SH", "510300.SH", "QQQ.US", "700.HK"];

// ── Helpers ──

function cn(...classes: (string | false | null | undefined)[]) {
  return classes.filter(Boolean).join(" ");
}

function upColor(rating: string): string {
  if (rating === "利好" || rating === "乐观" || rating === "正面" || rating === "看多") return "text-up";
  if (rating === "利空" || rating === "悲观" || rating === "负面" || rating === "看空") return "text-down";
  return "text-[var(--ink-muted)]";
}

function upBg(rating: string): string {
  if (rating === "利好" || rating === "乐观") return "bg-up/10 border-up/30";
  if (rating === "利空" || rating === "悲观") return "bg-down/10 border-down/30";
  return "bg-[var(--bg-elevated)] border-[var(--border-card)]";
}

function verdictBg(verdict: string, strength: string): string {
  if (verdict === "看多") {
    if (strength === "强烈") return "bg-up/15 border-up/40";
    return "bg-up/8 border-up/25";
  }
  if (verdict === "看空") {
    if (strength === "强烈") return "bg-down/15 border-down/40";
    return "bg-down/8 border-down/25";
  }
  return "bg-[var(--bg-elevated)] border-[var(--border-card)]";
}

function RatingBadge({ rating }: { rating: string }) {
  return (
    <span className={cn("text-[11px] font-bold px-2 py-0.5 rounded-full border", upColor(rating), upBg(rating))}>
      {rating}
    </span>
  );
}

// ── Section Cards ──

function FundamentalCard({ data }: { data: InstituteAnalysisResult["fundamental"] }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="border border-[var(--border-card)] bg-[var(--bg-card)] rounded-xl p-4 space-y-3"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BarChart3 size={15} className="text-[var(--accent)]" />
          <span className="text-sm font-bold text-[var(--ink-primary)]">基本面分析</span>
        </div>
        <RatingBadge rating={data.评级} />
      </div>
      <p className="text-[13px] text-[var(--ink-primary)] leading-relaxed">{data.核心结论}</p>
      {data.关键指标.length > 0 && (
        <div className="space-y-1.5">
          {data.关键指标.map((item, idx) => (
            <div key={idx} className="flex items-center justify-between text-xs">
              <span className="text-[var(--ink-muted)]">{item.指标}</span>
              <span className="font-mono text-[var(--ink-secondary)]">{item.数值}</span>
              <span className={cn("text-[11px] font-semibold", upColor(item.信号))}>{item.信号}</span>
            </div>
          ))}
        </div>
      )}
      <p className="text-[11px] text-[var(--ink-dim)]">{data.风险提示}</p>
    </motion.div>
  );
}

function TechnicalCard({ data }: { data: InstituteAnalysisResult["technical"] }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.1 }}
      className="border border-[var(--border-card)] bg-[var(--bg-card)] rounded-xl p-4 space-y-3"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <TrendingUp size={15} className="text-[var(--accent)]" />
          <span className="text-sm font-bold text-[var(--ink-primary)]">技术面分析</span>
        </div>
        <RatingBadge rating={data.评级} />
      </div>
      <p className="text-[13px] text-[var(--ink-primary)] leading-relaxed">{data.核心结论}</p>
      {data.关键信号.length > 0 && (
        <div className="space-y-1.5">
          {data.关键信号.map((item, idx) => (
            <div key={idx} className="flex items-start gap-2 text-xs">
              <span className="shrink-0 mt-0.5 w-1.5 h-1.5 rounded-full bg-[var(--accent)]" />
              <span className="text-[var(--ink-secondary)] font-medium">{item.信号}：</span>
              <span className="text-[var(--ink-muted)]">{item.含义}</span>
            </div>
          ))}
        </div>
      )}
      <p className="text-[11px] text-[var(--ink-dim)]">关键价位：{data.关键价位}</p>
    </motion.div>
  );
}

function SentimentCard({ data }: { data: InstituteAnalysisResult["sentiment"] }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.2 }}
      className="border border-[var(--border-card)] bg-[var(--bg-card)] rounded-xl p-4 space-y-3"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Newspaper size={15} className="text-[var(--accent)]" />
          <span className="text-sm font-bold text-[var(--ink-primary)]">情绪面分析</span>
        </div>
        <span className={cn("text-[11px] font-bold", upColor(data.整体情绪 === "乐观" ? "利好" : data.整体情绪 === "悲观" ? "利空" : "中性"))}>
          {data.整体情绪}
        </span>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-lg border border-[var(--border-card)] bg-[var(--bg-elevated)] p-2.5 text-center">
          <div className="text-[10px] text-[var(--ink-dim)]">散户情绪</div>
          <div className={cn("text-sm font-bold mt-0.5", upColor(data.散户情绪 === "乐观" ? "利好" : data.散户情绪 === "悲观" ? "利空" : "中性"))}>
            {data.散户情绪}
          </div>
        </div>
        <div className="rounded-lg border border-[var(--border-card)] bg-[var(--bg-elevated)] p-2.5 text-center">
          <div className="text-[10px] text-[var(--ink-dim)]">机构情绪</div>
          <div className={cn("text-sm font-bold mt-0.5", upColor(data.机构情绪 === "乐观" ? "利好" : data.机构情绪 === "悲观" ? "利空" : "中性"))}>
            {data.机构情绪}
          </div>
        </div>
      </div>
      {data.情绪分歧 && (
        <div className="text-[11px] font-semibold text-down bg-down/8 rounded-lg px-3 py-1.5 text-center">
          情绪分歧：散户与机构方向不一致，需谨慎解读
        </div>
      )}
      <p className="text-[13px] text-[var(--ink-primary)] leading-relaxed">{data.核心结论}</p>
      {data.主要风险标签.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {data.主要风险标签.map((tag) => (
            <span key={tag} className="text-[10px] rounded-full border border-[var(--border-card)] bg-[var(--bg-elevated)] px-2 py-0.5 text-[var(--ink-muted)]">
              {tag}
            </span>
          ))}
        </div>
      )}
      <p className="text-[11px] text-[var(--ink-dim)]">{data.情绪风险提示}</p>
    </motion.div>
  );
}

function DebateArena({ bull, bear }: { bull: InstituteAnalysisResult["bull"]; bear: InstituteAnalysisResult["bear"] }) {
  const [bullOpen, setBullOpen] = useState(false);
  const [bearOpen, setBearOpen] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.3 }}
      className="space-y-3"
    >
      <div className="flex items-center gap-2 px-1">
        <Gavel size={15} className="text-[var(--accent)]" />
        <span className="text-sm font-bold text-[var(--ink-primary)]">辩论擂台</span>
      </div>
      <div className="grid md:grid-cols-2 gap-3">
        {/* Bull Side */}
        <div className="border border-up/25 bg-up/5 rounded-xl overflow-hidden">
          <button
            onClick={() => setBullOpen(!bullOpen)}
            className="w-full flex items-center justify-between px-4 py-3 hover:bg-up/8 transition-colors"
          >
            <div className="flex items-center gap-2">
              <span className="text-lg">🐂</span>
              <span className="text-sm font-bold text-up">看多方</span>
              <span className={cn("text-[11px] font-semibold px-1.5 py-0.5 rounded-full",
                bull.做多信心 === "高" ? "bg-up/20 text-up" :
                bull.做多信心 === "中" ? "bg-up/10 text-up" :
                "bg-[var(--bg-elevated)] text-[var(--ink-muted)]"
              )}>
                信心{bull.做多信心}
              </span>
            </div>
            {bullOpen ? <ChevronUp size={14} className="text-up" /> : <ChevronDown size={14} className="text-up" />}
          </button>
          <AnimatePresence>
            {bullOpen && (
              <motion.div initial={{ height: 0 }} animate={{ height: "auto" }} exit={{ height: 0 }} className="overflow-hidden">
                <div className="px-4 pb-3 space-y-2">
                  {bull.论据.length === 0 && (
                    <p className="text-[11px] text-[var(--ink-dim)] italic">无足够数据支撑做多论据</p>
                  )}
                  {bull.论据.map((arg) => (
                    <div key={arg.序号} className="bg-[var(--bg-card)] rounded-lg p-2.5 border border-[var(--border-subtle)]">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[10px] font-bold text-[var(--accent)]">#{arg.序号}</span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[var(--bg-elevated)] text-[var(--ink-dim)]">{arg.来源}</span>
                      </div>
                      <p className="text-xs font-semibold text-[var(--ink-primary)]">{arg.论点}</p>
                      <p className="text-[11px] text-[var(--ink-muted)] mt-0.5">{arg.依据}</p>
                    </div>
                  ))}
                  <p className="text-[10px] text-[var(--ink-dim)] mt-2">
                    <span className="font-semibold">最大风险：</span>{bull.最大风险}
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Bear Side */}
        <div className="border border-down/25 bg-down/5 rounded-xl overflow-hidden">
          <button
            onClick={() => setBearOpen(!bearOpen)}
            className="w-full flex items-center justify-between px-4 py-3 hover:bg-down/8 transition-colors"
          >
            <div className="flex items-center gap-2">
              <span className="text-lg">🐻</span>
              <span className="text-sm font-bold text-down">看空方</span>
              <span className={cn("text-[11px] font-semibold px-1.5 py-0.5 rounded-full",
                bear.做空信心 === "高" ? "bg-down/20 text-down" :
                bear.做空信心 === "中" ? "bg-down/10 text-down" :
                "bg-[var(--bg-elevated)] text-[var(--ink-muted)]"
              )}>
                信心{bear.做空信心}
              </span>
            </div>
            {bearOpen ? <ChevronUp size={14} className="text-down" /> : <ChevronDown size={14} className="text-down" />}
          </button>
          <AnimatePresence>
            {bearOpen && (
              <motion.div initial={{ height: 0 }} animate={{ height: "auto" }} exit={{ height: 0 }} className="overflow-hidden">
                <div className="px-4 pb-3 space-y-2">
                  {bear.论据.length === 0 && (
                    <p className="text-[11px] text-[var(--ink-dim)] italic">无足够数据支撑做空论据</p>
                  )}
                  {bear.论据.map((arg) => (
                    <div key={arg.序号} className="bg-[var(--bg-card)] rounded-lg p-2.5 border border-[var(--border-subtle)]">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[10px] font-bold text-[var(--accent)]">#{arg.序号}</span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[var(--bg-elevated)] text-[var(--ink-dim)]">{arg.来源}</span>
                      </div>
                      <p className="text-xs font-semibold text-[var(--ink-primary)]">{arg.论点}</p>
                      <p className="text-[11px] text-[var(--ink-muted)] mt-0.5">{arg.依据}</p>
                    </div>
                  ))}
                  <p className="text-[10px] text-[var(--ink-dim)] mt-2">
                    <span className="font-semibold">最大阻力：</span>{bear.最大阻力}
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
}

function JudgeRuling({ data }: { data: InstituteAnalysisResult["judge"] }) {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.4 }}
      className={cn("border rounded-2xl p-5 space-y-4", verdictBg(data.裁决, data.裁决强度))}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Gavel size={18} className={data.裁决 === "看多" ? "text-up" : data.裁决 === "看空" ? "text-down" : "text-[var(--ink-muted)]"} />
          <span className="text-base font-bold text-[var(--ink-primary)]">法官裁决</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-semibold text-[var(--ink-muted)]">{data.裁决强度}</span>
          <span className={cn(
            "text-lg font-black",
            data.裁决 === "看多" ? "text-up" : data.裁决 === "看空" ? "text-down" : "text-[var(--ink-muted)]"
          )}>
            {data.裁决}
          </span>
        </div>
      </div>

      <p className="text-[13px] text-[var(--ink-primary)] leading-relaxed">{data.核心理由}</p>

      {/* Operation Advice */}
      <div className="grid grid-cols-3 gap-2">
        <div className="bg-[var(--bg-card)] rounded-lg p-3 text-center border border-[var(--border-card)]">
          <div className="text-[10px] text-[var(--ink-dim)] mb-1">短期（1-4周）</div>
          <div className="text-xs font-semibold text-[var(--ink-primary)]">{data.操作建议["短期（1-4周）"]}</div>
        </div>
        <div className="bg-[var(--bg-card)] rounded-lg p-3 text-center border border-[var(--border-card)]">
          <div className="text-[10px] text-[var(--ink-dim)] mb-1">中期（1-3月）</div>
          <div className="text-xs font-semibold text-[var(--ink-primary)]">{data.操作建议["中期（1-3月）"]}</div>
        </div>
        <div className="bg-[var(--bg-card)] rounded-lg p-3 text-center border border-[var(--border-card)]">
          <div className="text-[10px] text-[var(--ink-dim)] mb-1">风险控制</div>
          <div className="text-xs font-semibold text-down">{data.操作建议["风险控制"]}</div>
        </div>
      </div>

      {/* Expandable details */}
      <button
        onClick={() => setShowDetails(!showDetails)}
        className="w-full flex items-center justify-center gap-1 text-[11px] text-[var(--ink-muted)] hover:text-[var(--ink-secondary)] transition-colors"
      >
        {showDetails ? "收起详情" : "展开详情"}
        {showDetails ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
      </button>
      <AnimatePresence>
        {showDetails && (
          <motion.div initial={{ height: 0 }} animate={{ height: "auto" }} exit={{ height: 0 }} className="overflow-hidden space-y-3">
            {data.胜出论据.length > 0 && (
              <div>
                <div className="text-[11px] font-bold text-[var(--ink-secondary)] mb-2">胜出论据</div>
                {data.胜出论据.map((item, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-xs mb-1">
                    <span className={cn("shrink-0 text-[10px] font-bold", item.来源 === "看多" ? "text-up" : "text-down")}>
                      [{item.来源}]
                    </span>
                    <span className="text-[var(--ink-muted)]">{item.论点}</span>
                  </div>
                ))}
              </div>
            )}
            {data.被否定论据.length > 0 && (
              <div>
                <div className="text-[11px] font-bold text-[var(--ink-dim)] mb-2">被否定论据</div>
                {data.被否定论据.map((item, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-xs mb-1">
                    <span className={cn("shrink-0 text-[10px] font-bold line-through", item.来源 === "看多" ? "text-up/50" : "text-down/50")}>
                      [{item.来源}]
                    </span>
                    <div>
                      <span className="text-[var(--ink-dim)]">{item.论点}</span>
                      <span className="text-[var(--ink-dim)] ml-2">— {item.否定理由}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      <p className="text-[10px] text-[var(--ink-dim)] italic leading-relaxed border-t border-[var(--border-card)] pt-3">
        {data.免责声明}
      </p>
    </motion.div>
  );
}

// ── Main Page ──

export default function InstitutePage({ useLlm }: { useLlm: boolean }) {
  const [symbol, setSymbol] = useState("");
  const [taskId, setTaskId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [step, setStep] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<InstituteAnalysisResult | null>(null);
  const [suggestions, setSuggestions] = useState<Array<{ symbol: string; name?: string; market?: string }>>([]);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Cleanup poll on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  // Search suggestions
  useEffect(() => {
    const keyword = symbol.trim();
    if (keyword.length < 2) {
      setSuggestions([]);
      return;
    }
    const timer = window.setTimeout(() => {
      searchStocks(keyword).then((r) => setSuggestions(r.items.slice(0, 8))).catch(() => setSuggestions([]));
    }, 300);
    return () => window.clearTimeout(timer);
  }, [symbol]);

  const startAnalysis = useCallback(async () => {
    setError(null);
    setResult(null);
    setProgress(0);
    setStep("");
    setLoading(true);

    try {
      const s = symbol.trim() || null;
      const task = await startInstituteAnalysis(s);
      setTaskId(task.task_id);
      setProgress(task.progress || 0);
      setStep(task.current_step || "");

      // Poll for progress
      pollRef.current = setInterval(async () => {
        try {
          const updated = await fetchTask(task.task_id);
          setProgress(updated.progress || 0);
          setStep(updated.current_step || "");

          if (updated.status === "success") {
            if (pollRef.current) clearInterval(pollRef.current);
            // Fetch full result
            const fullResult = await fetchInstituteResult(task.task_id);
            if (fullResult.status === "success" && fullResult.result) {
              setResult(fullResult.result as unknown as InstituteAnalysisResult);
            }
            setLoading(false);
          } else if (updated.status === "failed") {
            if (pollRef.current) clearInterval(pollRef.current);
            setError(updated.error || "分析任务失败");
            setLoading(false);
          }
        } catch {
          // Continue polling
        }
      }, 1500);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "启动分析失败");
      setLoading(false);
    }
  }, [symbol]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    startAnalysis();
  };

  return (
    <div className="flex flex-col min-h-screen pb-28">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="sticky top-0 z-30 bg-[var(--bg-deep)]/95 backdrop-blur-md border-b border-[var(--border-subtle)]"
      >
        <div className="px-4 py-3">
          <div className="flex items-center gap-2">
            <span className="text-xl">🔬</span>
            <div>
              <span className="text-sm font-bold text-[var(--ink-primary)]">AI 研究所</span>
              <span className="ml-2 text-[10px] text-[var(--ink-dim)]">多维度 · 多空辩论 · 法官裁决</span>
            </div>
          </div>
        </div>
      </motion.header>

      <div className="px-4 pt-4 space-y-4">
        {/* Search */}
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--ink-dim)]" />
                <input
                  className="w-full h-11 pl-9 pr-3 rounded-xl border border-[var(--border-card)] bg-[var(--bg-card)] text-sm text-[var(--ink-primary)] font-mono uppercase placeholder:text-[var(--ink-dim)] outline-none focus:border-[var(--accent)]/40 focus:ring-1 focus:ring-[var(--accent)]/20 transition-all"
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                  placeholder="600519.SH / TSLA.US / QQQ.US / 700.HK · 留空=全市场分析"
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="shrink-0 h-11 px-5 rounded-xl bg-[var(--accent)] text-white text-sm font-semibold disabled:opacity-40 active:scale-95 transition-all flex items-center gap-2"
              >
                {loading ? <Loader2 size={15} className="animate-spin" /> : null}
                {loading ? "研究中" : "开始研究"}
              </button>
            </div>

            <div className="flex gap-1.5 flex-wrap">
              {examples.map((item) => (
                <button
                  key={item}
                  type="button"
                  onClick={() => setSymbol(item)}
                  className="px-2.5 py-1 rounded-lg border border-[var(--border-card)] bg-[var(--bg-elevated)] text-[11px] font-mono text-[var(--ink-muted)] hover:text-[var(--accent)] hover:border-[var(--accent)]/30 active:scale-95 transition-all"
                >
                  {item}
                </button>
              ))}
            </div>

            {suggestions.length > 0 && (
              <div className="grid gap-1.5 sm:grid-cols-2">
                {suggestions.map((item) => (
                  <button
                    key={item.symbol}
                    type="button"
                    onClick={() => setSymbol(item.symbol)}
                    className="flex items-center gap-2 px-3 py-2 rounded-xl border border-[var(--border-card)] bg-[var(--bg-card)] text-left hover:border-[var(--accent)]/30 active:bg-[var(--bg-card-hover)] transition-all"
                  >
                    <span className="text-sm font-semibold text-[var(--ink-primary)] font-mono">{item.symbol}</span>
                    <span className="text-[11px] text-[var(--ink-muted)] truncate">{item.name || item.market || ""}</span>
                  </button>
                ))}
              </div>
            )}
          </form>
        </motion.div>

        {/* Error */}
        {error && (
          <div className="px-3 py-2 text-[11px] text-down font-mono border border-down/20 bg-down/5 rounded-lg">
            {error}
          </div>
        )}

        {/* Progress */}
        {(loading || progress > 0) && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-2">
            <ProgressBar value={progress} />
            <p className="text-[11px] text-[var(--ink-dim)] text-center">{step || "等待中..."}</p>
          </motion.div>
        )}

        {/* Loading skeleton while waiting */}
        {loading && !result && (
          <div className="space-y-3 pt-2">
            <div className="skeleton h-32 w-full rounded-xl" />
            <div className="skeleton h-32 w-full rounded-xl" />
            <div className="skeleton h-40 w-full rounded-xl" />
          </div>
        )}

        {/* Results */}
        <AnimatePresence>
          {result && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4 pb-8">
              {/* Layer 1: Three cards */}
              <div className="grid md:grid-cols-3 gap-3">
                <FundamentalCard data={result.fundamental} />
                <TechnicalCard data={result.technical} />
                <SentimentCard data={result.sentiment} />
              </div>

              {/* Layer 2: Debate */}
              <DebateArena bull={result.bull} bear={result.bear} />

              {/* Layer 3: Judge */}
              <JudgeRuling data={result.judge} />

              {/* Timestamp */}
              <p className="text-center text-[10px] text-[var(--ink-dim)] font-mono">
                分析时间：{result.analyzed_at}
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Empty state */}
        {!loading && !result && !error && (
          <div className="pt-8 text-center space-y-3">
            <div className="text-4xl">🔬</div>
            <p className="text-[13px] text-[var(--ink-muted)]">
              输入股票/ETF/基金代码开始五层AI分析
            </p>
            <p className="text-[11px] text-[var(--ink-dim)]">
              基本面 → 技术面 → 情绪面 → 多空辩论 → 法官裁决
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
