import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Plus, X, TrendingUp, TrendingDown, Trash2, DollarSign, Calendar, Hash, Percent } from "lucide-react";
import { searchStocks, searchFunds, fetchMarketIndexes, MarketIndexItem, StockSearchResponse, FundSearchResponse } from "../api/client";

// ── Types ──

interface WatchlistAsset {
  id: string;
  symbol: string;
  name: string;
  type: "stock" | "fund" | "index";
  addedAt: string;
}

interface Holding {
  id: string;
  symbol: string;
  name: string;
  type: "stock" | "fund";
  buyDate: string;
  quantity: number;
  buyPrice: number;
  fee: number;
  addedAt: string;
}

interface SearchResult {
  symbol: string;
  name?: string;
  type: "stock" | "fund";
  source?: string;
  market?: string;
  fund_type?: string;
}

type Tab = "watchlist" | "holdings";

// ── localStorage helpers ──

function loadWatchlist(): WatchlistAsset[] {
  try { return JSON.parse(localStorage.getItem("rabot_watchlist") || "[]"); } catch { return []; }
}
function saveWatchlist(items: WatchlistAsset[]) {
  localStorage.setItem("rabot_watchlist", JSON.stringify(items));
}
function loadHoldings(): Holding[] {
  try { return JSON.parse(localStorage.getItem("rabot_holdings") || "[]"); } catch { return []; }
}
function saveHoldings(items: Holding[]) {
  localStorage.setItem("rabot_holdings", JSON.stringify(items));
}

// ── Component ──

export default function WatchlistPage() {
  const [tab, setTab] = useState<Tab>("watchlist");
  // Watchlist
  const [watchlist, setWatchlist] = useState<WatchlistAsset[]>(loadWatchlist);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  // Prices
  const [prices, setPrices] = useState<Record<string, MarketIndexItem>>({});
  // Holdings
  const [holdings, setHoldings] = useState<Holding[]>(loadHoldings);
  const [showAddHolding, setShowAddHolding] = useState(false);
  const [holdingForm, setHoldingForm] = useState({
    searchQuery: "",
    results: [] as SearchResult[],
    selectedAsset: null as SearchResult | null,
    buyDate: new Date().toISOString().slice(0, 10),
    quantity: "",
    buyPrice: "",
    fee: "0",
  });

  // Persist
  useEffect(() => { saveWatchlist(watchlist); }, [watchlist]);
  useEffect(() => { saveHoldings(holdings); }, [holdings]);

  // Fetch prices for watchlist
  useEffect(() => {
    if (watchlist.length === 0) return;
    const symbols = watchlist.map((w) => w.symbol);
    fetchMarketIndexes()
      .then((resp) => {
        const map: Record<string, MarketIndexItem> = {};
        for (const item of resp.items || []) {
          // Also check if any watchlist symbol matches
        }
        // The indexes API returns specific index symbols. For stocks/funds, we need a different approach.
        // Use the watchlist symbols to try to get data
      })
      .catch(() => {});
    // For now, fetch individual stock data for watchlist items that aren't indexes
    const indexSymbols = ["SSE", "CSI300", "CSI500", "CSI1000", "CHINEXT", "STAR50", "HSI", "SP500", "NASDAQ", "NASDAQ100", "DOW", "RUSSELL2000", "VIX", "NIKKEI225", "DAX", "FTSE100", "DXY", "GOLD", "WTI"];
    const stockSymbols = watchlist.filter((w) => !indexSymbols.includes(w.symbol));
    // For non-index items, we'll rely on the index API or skip for now
    // Update: actually fetch indexes and match any
  }, [watchlist]);

  // ── Search ──
  const doSearch = useCallback(async (query: string) => {
    if (query.trim().length < 1) { setSearchResults([]); return; }
    setSearching(true);
    try {
      const [stockRes, fundRes] = await Promise.all([
        searchStocks(query.trim()).catch(() => ({ items: [], warnings: [] } as StockSearchResponse)),
        searchFunds(query.trim()).catch(() => ({ items: [], warnings: [] } as FundSearchResponse)),
      ]);
      const results: SearchResult[] = [
        ...(stockRes.items || []).map((s) => ({ ...s, type: "stock" as const })),
        ...(fundRes.items || []).map((f) => ({ ...f, type: "fund" as const })),
      ];
      setSearchResults(results.slice(0, 15));
    } catch { setSearchResults([]); }
    finally { setSearching(false); }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => doSearch(searchQuery), 400);
    return () => clearTimeout(timer);
  }, [searchQuery, doSearch]);

  // ── Add to watchlist ──
  const addToWatchlist = (item: SearchResult) => {
    if (watchlist.find((w) => w.symbol === item.symbol && w.type === item.type)) return;
    const newItem: WatchlistAsset = {
      id: `${item.type}-${item.symbol}-${Date.now()}`,
      symbol: item.symbol,
      name: item.name || item.symbol,
      type: item.type,
      addedAt: new Date().toISOString(),
    };
    setWatchlist([...watchlist, newItem]);
  };

  const removeFromWatchlist = (id: string) => {
    setWatchlist(watchlist.filter((w) => w.id !== id));
  };

  // ── Holdings search ──
  const doHoldingSearch = useCallback(async (query: string) => {
    if (query.trim().length < 1) { setHoldingForm((f) => ({ ...f, results: [] })); return; }
    try {
      const [stockRes, fundRes] = await Promise.all([
        searchStocks(query.trim()).catch(() => ({ items: [], warnings: [] } as StockSearchResponse)),
        searchFunds(query.trim()).catch(() => ({ items: [], warnings: [] } as FundSearchResponse)),
      ]);
      const results: SearchResult[] = [
        ...(stockRes.items || []).map((s) => ({ ...s, type: "stock" as const })),
        ...(fundRes.items || []).map((f) => ({ ...f, type: "fund" as const })),
      ];
      setHoldingForm((f) => ({ ...f, results: results.slice(0, 10) }));
    } catch { setHoldingForm((f) => ({ ...f, results: [] })); }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => doHoldingSearch(holdingForm.searchQuery), 400);
    return () => clearTimeout(timer);
  }, [holdingForm.searchQuery, doHoldingSearch]);

  const addHolding = () => {
    const { selectedAsset, buyDate, quantity, buyPrice, fee } = holdingForm;
    if (!selectedAsset || !quantity || !buyPrice) return;
    const h: Holding = {
      id: `holding-${Date.now()}`,
      symbol: selectedAsset.symbol,
      name: selectedAsset.name || selectedAsset.symbol,
      type: selectedAsset.type,
      buyDate,
      quantity: parseFloat(quantity),
      buyPrice: parseFloat(buyPrice),
      fee: parseFloat(fee) || 0,
      addedAt: new Date().toISOString(),
    };
    setHoldings([...holdings, h]);
    setShowAddHolding(false);
    setHoldingForm({ searchQuery: "", results: [], selectedAsset: null, buyDate: new Date().toISOString().slice(0, 10), quantity: "", buyPrice: "", fee: "0" });
  };

  const removeHolding = (id: string) => {
    setHoldings(holdings.filter((h) => h.id !== id));
  };

  // ── Calculate portfolio summary ──
  const totalInvested = holdings.reduce((sum, h) => sum + h.quantity * h.buyPrice + h.fee, 0);
  const totalCurrentValue = totalInvested; // Will update when real-time prices are integrated

  return (
    <div className="flex flex-col min-h-screen pb-28">
      {/* Header */}
      <div className="sticky top-0 z-30 glass-strong px-4 py-4">
        <h1 className="text-lg font-semibold mb-3">
          {tab === "watchlist" ? "自选" : "持仓"}
        </h1>

        {/* Tab switcher */}
        <div className="flex gap-1 p-1 rounded-xl bg-[var(--bg-card)] border border-[var(--border-card)]">
          {([ { key: "watchlist" as Tab, label: "自选资产" }, { key: "holdings" as Tab, label: "我的持仓" } ]).map(({ key, label }) => (
            <button
              key={key}
              className={`flex-1 py-1.5 px-4 text-[10px] font-bold uppercase tracking-wider transition-all ${
                tab === key ? "bg-[var(--accent)] text-white" : "text-[var(--ink-dim)] hover:text-[var(--ink-secondary)]"
              }`}
              onClick={() => setTab(key)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* ── Watchlist Tab ── */}
      {tab === "watchlist" && (
        <div className="pt-4 px-4">
          {/* Search bar */}
          <div className="relative mb-3">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--ink-dim)]" />
            <input
              className="w-full h-10 pl-9 pr-4 rounded-xl border border-[var(--border-card)] bg-[var(--bg-card)] text-sm text-[var(--ink-primary)] placeholder:text-[var(--ink-dim)] outline-none focus:border-[var(--accent)] transition-colors"
              placeholder="搜索股票、基金、ETF 代码或名称..."
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setShowSearch(true); }}
              onFocus={() => setShowSearch(true)}
            />
            {searchQuery && (
              <button className="absolute right-3 top-1/2 -translate-y-1/2" onClick={() => { setSearchQuery(""); setSearchResults([]); }}>
                <X size={14} className="text-[var(--ink-dim)]" />
              </button>
            )}
          </div>

          {/* Search results */}
          <AnimatePresence>
            {showSearch && searchResults.length > 0 && (
              <motion.div
                className="mb-4 rounded-2xl border border-[var(--border-card)] bg-[var(--bg-card)] overflow-hidden"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
              >
                <div className="p-2 text-[10px] text-[var(--ink-muted)] uppercase tracking-wider px-3 pt-2">搜索结果</div>
                {searchResults.map((item) => (
                  <button
                    key={`${item.type}-${item.symbol}`}
                    className="w-full flex items-center justify-between px-3 py-3 hover:bg-[var(--bg-elevated)] transition-colors text-left"
                    onClick={() => { addToWatchlist(item); setShowSearch(false); setSearchQuery(""); }}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-semibold truncate">{item.name || item.symbol}</div>
                      <div className="text-[10px] text-[var(--ink-muted)]">{item.symbol} · {item.type === "stock" ? "股票" : "基金"}</div>
                    </div>
                    <Plus size={16} className="text-[var(--accent)] shrink-0" />
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>

          {searching && (
            <div className="mb-4 flex justify-center">
              <div className="skeleton h-16 w-full rounded-2xl" />
            </div>
          )}

          {/* Watchlist items */}
          {watchlist.length === 0 ? (
            <div className="py-20 text-center">
              <Search size={36} className="text-[var(--ink-dim)] mx-auto mb-4" />
              <p className="text-sm text-[var(--ink-muted)]">暂无自选资产</p>
              <p className="text-xs text-[var(--ink-dim)] mt-1">在上方搜索框中搜索并添加</p>
            </div>
          ) : (
            <div className="space-y-1.5">
              {watchlist.map((item, i) => (
                <motion.div
                  key={item.id}
                  className="flex items-center justify-between p-3.5 rounded-xl border border-[var(--border-card)] bg-[var(--bg-card)]"
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.04 }}
                >
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-semibold truncate">{item.name}</div>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-[10px] text-[var(--ink-muted)]">{item.symbol}</span>
                      <span className="px-1.5 py-0.5 rounded text-[9px] bg-[var(--bg-elevated)] text-[var(--ink-muted)]">
                        {item.type === "stock" ? "股票" : item.type === "fund" ? "基金" : "指数"}
                      </span>
                    </div>
                  </div>
                  <button
                    className="w-8 h-8 rounded-lg flex items-center justify-center text-[var(--ink-dim)] hover:text-[var(--up)] transition-colors"
                    onClick={() => removeFromWatchlist(item.id)}
                  >
                    <Trash2 size={14} />
                  </button>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Holdings Tab ── */}
      {tab === "holdings" && (
        <div className="pt-4 px-4">
          {/* Portfolio summary */}
          {holdings.length > 0 && (
            <motion.div
              className="p-4 rounded-2xl border border-[rgba(79,110,247,0.2)] bg-[rgba(79,110,247,0.05)] mb-4"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <div className="text-[10px] font-semibold text-[var(--accent)] uppercase tracking-wider mb-3">持仓汇总</div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <div className="text-[9px] text-[var(--ink-muted)]">持仓数</div>
                  <div className="text-financial text-base font-bold text-[var(--ink-primary)]">{holdings.length}</div>
                </div>
                <div>
                  <div className="text-[9px] text-[var(--ink-muted)]">总投入</div>
                  <div className="text-financial text-base font-bold text-[var(--ink-primary)]">
                    ¥{totalInvested.toLocaleString("zh-CN", { minimumFractionDigits: 2 })}
                  </div>
                </div>
                <div>
                  <div className="text-[9px] text-[var(--ink-muted)]">总手续费</div>
                  <div className="text-financial text-base font-bold text-[var(--ink-primary)]">
                    ¥{holdings.reduce((s, h) => s + h.fee, 0).toFixed(2)}
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* Add holding button */}
          {!showAddHolding && (
            <button
              className="w-full flex items-center justify-center gap-2 py-3.5 rounded-xl border border-dashed border-[var(--border-card)] text-sm text-[var(--ink-muted)] active:bg-[var(--bg-card)] transition-colors mb-4"
              onClick={() => setShowAddHolding(true)}
            >
              <Plus size={16} />
              <span>添加持仓</span>
            </button>
          )}

          {/* Add holding form */}
          <AnimatePresence>
            {showAddHolding && (
              <motion.div
                className="p-4 rounded-2xl border border-[var(--border-card)] bg-[var(--bg-card)] mb-4 space-y-3"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold">添加持仓</span>
                  <button onClick={() => setShowAddHolding(false)}>
                    <X size={16} className="text-[var(--ink-dim)]" />
                  </button>
                </div>

                {/* Asset search */}
                <div>
                  <label className="text-[10px] text-[var(--ink-muted)]">搜索资产</label>
                  <div className="relative mt-1">
                    <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--ink-dim)]" />
                    <input
                      className="w-full h-9 pl-9 pr-3 rounded-lg border border-[var(--border-card)] bg-[var(--bg-elevated)] text-sm outline-none focus:border-[var(--accent)]"
                      placeholder="输入代码搜索..."
                      value={holdingForm.searchQuery}
                      onChange={(e) => setHoldingForm((f) => ({ ...f, searchQuery: e.target.value }))}
                    />
                  </div>
                  {holdingForm.results.length > 0 && !holdingForm.selectedAsset && (
                    <div className="mt-1 rounded-lg border border-[var(--border-card)] bg-[var(--bg-elevated)] overflow-hidden max-h-40 overflow-y-auto">
                      {holdingForm.results.map((r) => (
                        <button
                          key={`${r.type}-${r.symbol}`}
                          className="w-full text-left px-3 py-2 hover:bg-[var(--bg-card)] text-xs transition-colors"
                          onClick={() => setHoldingForm((f) => ({ ...f, selectedAsset: r, results: [], searchQuery: `${r.name || r.symbol} (${r.symbol})` }))}
                        >
                          <span className="font-medium">{r.name || r.symbol}</span>
                          <span className="text-[var(--ink-dim)] ml-1">{r.symbol}</span>
                        </button>
                      ))}
                    </div>
                  )}
                  {holdingForm.selectedAsset && (
                    <div className="mt-1 flex items-center gap-2 px-3 py-2 rounded-lg bg-[var(--accent-soft)] text-xs text-[var(--accent)]">
                      <span className="font-semibold">{holdingForm.selectedAsset.name || holdingForm.selectedAsset.symbol}</span>
                      <span>{holdingForm.selectedAsset.symbol}</span>
                      <button className="ml-auto" onClick={() => setHoldingForm((f) => ({ ...f, selectedAsset: null, searchQuery: "" }))}>
                        <X size={12} />
                      </button>
                    </div>
                  )}
                </div>

                {/* Buy date */}
                <div>
                  <label className="text-[10px] text-[var(--ink-muted)] flex items-center gap-1">
                    <Calendar size={10} /> 买入日期
                  </label>
                  <input
                    type="date"
                    className="w-full h-9 px-3 rounded-lg border border-[var(--border-card)] bg-[var(--bg-elevated)] text-sm mt-1 outline-none focus:border-[var(--accent)]"
                    value={holdingForm.buyDate}
                    onChange={(e) => setHoldingForm((f) => ({ ...f, buyDate: e.target.value }))}
                  />
                </div>

                {/* Quantity and Price row */}
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-[10px] text-[var(--ink-muted)] flex items-center gap-1">
                      <Hash size={10} /> 买入数量（股/份）
                    </label>
                    <input
                      type="number"
                      step="any"
                      className="w-full h-9 px-3 rounded-lg border border-[var(--border-card)] bg-[var(--bg-elevated)] text-sm mt-1 outline-none focus:border-[var(--accent)]"
                      placeholder="100"
                      value={holdingForm.quantity}
                      onChange={(e) => setHoldingForm((f) => ({ ...f, quantity: e.target.value }))}
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-[var(--ink-muted)] flex items-center gap-1">
                      <DollarSign size={10} /> 买入价格
                    </label>
                    <input
                      type="number"
                      step="any"
                      className="w-full h-9 px-3 rounded-lg border border-[var(--border-card)] bg-[var(--bg-elevated)] text-sm mt-1 outline-none focus:border-[var(--accent)]"
                      placeholder="0.00"
                      value={holdingForm.buyPrice}
                      onChange={(e) => setHoldingForm((f) => ({ ...f, buyPrice: e.target.value }))}
                    />
                  </div>
                </div>

                {/* Fee */}
                <div>
                  <label className="text-[10px] text-[var(--ink-muted)] flex items-center gap-1">
                    <Percent size={10} /> 手续费（可选）
                  </label>
                  <input
                    type="number"
                    step="any"
                    className="w-full h-9 px-3 rounded-lg border border-[var(--border-card)] bg-[var(--bg-elevated)] text-sm mt-1 outline-none focus:border-[var(--accent)]"
                    placeholder="0.00"
                    value={holdingForm.fee}
                    onChange={(e) => setHoldingForm((f) => ({ ...f, fee: e.target.value }))}
                  />
                </div>

                {/* Preview */}
                {holdingForm.selectedAsset && holdingForm.quantity && holdingForm.buyPrice && (
                  <div className="p-3 rounded-lg bg-[var(--bg-elevated)] text-xs">
                    <span className="text-[var(--ink-muted)]">投入金额：</span>
                    <span className="text-financial font-semibold text-[var(--ink-primary)]">
                      ¥{(parseFloat(holdingForm.quantity) * parseFloat(holdingForm.buyPrice) + (parseFloat(holdingForm.fee) || 0)).toLocaleString("zh-CN", { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                )}

                <button
                  className="w-full py-2.5 rounded-lg bg-[var(--accent)] text-white text-sm font-semibold disabled:opacity-40 transition-opacity"
                  disabled={!holdingForm.selectedAsset || !holdingForm.quantity || !holdingForm.buyPrice}
                  onClick={addHolding}
                >
                  确认添加
                </button>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Holdings list */}
          {holdings.length === 0 && !showAddHolding ? (
            <div className="py-20 text-center">
              <DollarSign size={36} className="text-[var(--ink-dim)] mx-auto mb-4" />
              <p className="text-sm text-[var(--ink-muted)]">暂无持仓记录</p>
              <p className="text-xs text-[var(--ink-dim)] mt-1">点击上方按钮添加持仓</p>
            </div>
          ) : (
            <div className="space-y-1.5">
              {holdings.map((h, i) => {
                const invested = h.quantity * h.buyPrice;
                const total = invested + h.fee;
                return (
                  <motion.div
                    key={h.id}
                    className="p-3.5 rounded-xl border border-[var(--border-card)] bg-[var(--bg-card)]"
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.04 }}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-semibold truncate">{h.name}</div>
                        <div className="flex items-center gap-2 mt-0.5 text-[10px] text-[var(--ink-muted)]">
                          <span>{h.symbol}</span>
                          <span className="px-1 py-0.5 rounded bg-[var(--bg-elevated)]">{h.type === "stock" ? "股票" : "基金"}</span>
                        </div>
                      </div>
                      <button
                        className="w-7 h-7 rounded-lg flex items-center justify-center text-[var(--ink-dim)] hover:text-[var(--up)] transition-colors"
                        onClick={() => removeHolding(h.id)}
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                    <div className="grid grid-cols-3 gap-2 mt-3 text-center">
                      <div className="p-2 rounded-lg bg-[var(--bg-elevated)]">
                        <div className="text-[9px] text-[var(--ink-muted)]">数量</div>
                        <div className="text-financial text-xs font-bold">{h.quantity}</div>
                      </div>
                      <div className="p-2 rounded-lg bg-[var(--bg-elevated)]">
                        <div className="text-[9px] text-[var(--ink-muted)]">成本</div>
                        <div className="text-financial text-xs font-bold">¥{h.buyPrice.toFixed(2)}</div>
                      </div>
                      <div className="p-2 rounded-lg bg-[var(--bg-elevated)]">
                        <div className="text-[9px] text-[var(--ink-muted)]">投入</div>
                        <div className="text-financial text-xs font-bold">¥{total.toLocaleString("zh-CN", { maximumFractionDigits: 0 })}</div>
                      </div>
                    </div>
                    <div className="mt-2 text-[10px] text-[var(--ink-muted)]">
                      买入日期：{h.buyDate} · 手续费：¥{h.fee.toFixed(2)}
                    </div>
                  </motion.div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
