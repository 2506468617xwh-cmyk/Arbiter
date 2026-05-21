import { lazy, Suspense } from "react";
import { MessageCircle } from "lucide-react";

const AIResearchPage = lazy(() => import("./AIResearchPage"));

interface Props {
  useLlm: boolean;
  onOpenModelSettings: () => void;
}

export default function ResearchPage({ useLlm, onOpenModelSettings }: Props) {
  return (
    <div className="flex flex-col min-h-screen pb-24">
      <div className="sticky top-0 z-30 bg-[var(--bg-deep)]/95 backdrop-blur-md border-b border-[var(--border-subtle)]">
        <div className="flex items-center gap-2 px-4 h-12">
          <MessageCircle size={14} className="text-[var(--accent)]" />
          <span className="text-[13px] font-bold uppercase tracking-[0.15em] text-[var(--ink-primary)]">AI RESEARCH</span>
        </div>
      </div>

      <Suspense
        fallback={
          <div className="px-4 pt-3 space-y-1.5">
            <div className="skeleton h-24 w-full" />
            <div className="skeleton h-20 w-full" />
          </div>
        }
      >
        <div className="pt-3">
          <AIResearchPage useLlm={useLlm} onOpenModelSettings={onOpenModelSettings} />
        </div>
      </Suspense>
    </div>
  );
}
