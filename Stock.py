python
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="NSE 52-Week AI Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 0.5rem;
            padding-bottom: 0rem;
            padding-left: 0.5rem;
            padding-right: 0.5rem;
            max-width: 100%;
        }
        header[data-testid="stHeader"] { display: none; }
    </style>
    """,
    unsafe_allow_html=True,
)

HTML_DASHBOARD = r"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>NSE AI Momentum &amp; 52-Week High/Low Dashboard</title>
  <script src="https://cdn.tailwindcss.com/3.4.17"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <script src="https://unpkg.com/lucide@0.460.0/dist/umd/lucide.min.js"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <style>
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background-color: #0b1120;
      color: #e2e8f0;
    }
    /* Custom subtle scrollbar */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #0f172a; }
    ::-webkit-scrollbar-thumb { background: #334155; border-radius: 9999px; }
    ::-webkit-scrollbar-thumb:hover { background: #475569; }
    input[type="range"] { accent-color: #10b981; }
  </style>
</head>
<body class="min-h-screen antialiased selection:bg-emerald-500/30 selection:text-emerald-200">
  <!-- Toast Notification -->
  <div id="toast" class="fixed bottom-4 right-4 z-50 hidden items-center gap-2 rounded-xl border border-emerald-500/30 bg-slate-900/95 px-4 py-3 text-sm font-medium text-emerald-300 shadow-2xl backdrop-blur-md transition-all">
    <i data-lucide="check-circle-2" class="h-4 w-4 shrink-0 text-emerald-400"></i>
    <span id="toastMsg">Updated</span>
  </div>

  <!-- Top Navigation & Market Pulse -->
  <header class="sticky top-0 z-30 border-b border-slate-800/80 bg-slate-950/90 backdrop-blur-md">
    <div class="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
      <div class="flex items-center gap-3">
        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 text-slate-950 shadow-lg shadow-emerald-500/20">
          <i data-lucide="trending-up" class="h-5 w-5"></i>
        </div>
        <div>
          <h1 class="text-base font-bold tracking-tight text-white sm:text-lg">NSE 52-Week AI Screener</h1>
          <p class="text-xs text-slate-400">NSE Equities &bull; Close Snapshot: 23 Nov 2026 (15:30 IST)</p>
        </div>
      </div>

      <div class="flex flex-wrap items-center gap-2.5">
        <!-- NIFTY 50 Benchmark Pill -->
        <div class="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900/90 px-3 py-1.5 text-xs">
          <span class="font-semibold text-slate-400">NIFTY 50</span>
          <span class="font-bold text-white">25,349.65</span>
          <span class="rounded bg-rose-500/15 px-1.5 py-0.5 font-semibold text-rose-400">-1.75% 1D</span>
          <span class="hidden rounded bg-emerald-500/15 px-1.5 py-0.5 font-semibold text-emerald-400 sm:inline">+0.22% 5D</span>
        </div>

        <!-- CSV Import -->
        <label for="csvInput" class="inline-flex cursor-pointer items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs font-medium text-slate-200 transition hover:border-emerald-500/50 hover:bg-slate-800">
          <i data-lucide="upload" class="h-3.5 w-3.5 text-emerald-400"></i>
          <span>Import CSV</span>
          <input id="csvInput" type="file" accept=".csv" class="hidden" />
        </label>

        <!-- CSV Export -->
        <button id="exportBtn" type="button" class="inline-flex items-center gap-1.5 rounded-lg bg-emerald-500 px-3 py-1.5 text-xs font-semibold text-slate-950 transition hover:bg-emerald-400">
          <i data-lucide="download" class="h-3.5 w-3.5"></i>
          <span>Export Ranked</span>
        </button>
      </div>
    </div>
  </header>

  <main class="mx-auto max-w-7xl space-y-5 px-4 py-5 sm:px-6">
    <!-- KPI Summary Row -->
    <section class="grid grid-cols-2 gap-3 lg:grid-cols-4">
      <div class="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
        <div class="flex items-center justify-between">
          <span class="text-xs font-medium text-slate-400">Breakout Zone (&le; 3% Off High)</span>
          <i data-lucide="flame" class="h-4 w-4 text-emerald-400"></i>
        </div>
        <div class="mt-2 flex items-baseline gap-2">
          <span id="kpiBreakoutCount" class="text-2xl font-bold text-white">0</span>
          <span id="kpiTopLeader" class="text-xs font-medium text-emerald-400">--</span>
        </div>
      </div>

      <div class="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
        <div class="flex items-center justify-between">
          <span class="text-xs font-medium text-slate-400">Avg Distance from 52W High</span>
          <i data-lucide="target" class="h-4 w-4 text-sky-400"></i>
        </div>
        <div class="mt-2 flex items-baseline gap-2">
          <span id="kpiAvgDistHigh" class="text-2xl font-bold text-white">0%</span>
          <span class="text-xs text-slate-400">filtered universe</span>
        </div>
      </div>

      <div class="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
        <div class="flex items-center justify-between">
          <span class="text-xs font-medium text-slate-400">Avg 52W Range Position</span>
          <i data-lucide="gauge" class="h-4 w-4 text-amber-400"></i>
        </div>
        <div class="mt-2 flex items-baseline gap-2">
          <span id="kpiAvgRangePos" class="text-2xl font-bold text-white">0%</span>
          <span class="text-xs text-slate-400">0% Low &ndash; 100% High</span>
        </div>
      </div>

      <div class="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
        <div class="flex items-center justify-between">
          <span class="text-xs font-medium text-slate-400">My Demat Tracked</span>
          <i data-lucide="briefcase" class="h-4 w-4 text-violet-400"></i>
        </div>
        <div class="mt-2 flex items-baseline gap-2">
          <span id="kpiDematCount" class="text-2xl font-bold text-white">0</span>
          <button id="quickDematBtn" type="button" class="text-xs font-medium text-violet-400 underline-offset-2 hover:underline">Filter holdings</button>
        </div>
      </div>
    </section>

    <!-- Charts & AI Inspector Row -->
    <section class="grid grid-cols-1 gap-4 lg:grid-cols-12">
      <!-- Left: 52W High Proximity Leaderboard Chart -->
      <div class="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 lg:col-span-6">
        <div class="mb-3 flex items-center justify-between gap-2">
          <div>
            <h2 class="text-sm font-semibold text-white">Top 10 Nearest to 52-Week High</h2>
            <p class="text-xs text-slate-400">Ranked by % of 52-Week Range (100% = at 52W High)</p>
          </div>
          <span class="rounded-full bg-emerald-500/15 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-400">Priority Leaders</span>
        </div>
        <div class="relative h-72">
          <canvas id="proximityChart"></canvas>
        </div>
      </div>

      <!-- Right: Selected Stock 5-Day Trend & AI Diagnosis -->
      <div class="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 lg:col-span-6">
        <div class="mb-3 flex flex-wrap items-start justify-between gap-2">
          <div>
            <div class="flex items-center gap-2">
              <h2 id="inspSymbol" class="text-sm font-bold text-white">DLF</h2>
              <span id="inspBadge" class="rounded-full bg-emerald-500/15 px-2 py-0.5 text-[11px] font-semibold text-emerald-400">Breakout Zone</span>
              <a id="inspScreenerLink" href="https://www.screener.in/company/DLF/" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1 text-[11px] font-medium text-sky-400 hover:underline">
                Screener <i data-lucide="external-link" class="h-3 w-3"></i>
              </a>
            </div>
            <p id="inspName" class="text-xs text-slate-400">DLF Ltd &bull; Real Estate</p>
          </div>
          <div class="text-right">
            <div id="inspPrice" class="text-base font-bold text-white">&#8377;794.10</div>
            <div id="inspDistHigh" class="text-xs font-medium text-emerald-400">-0.23% from 52W High</div>
          </div>
        </div>

        <div class="relative h-56">
          <canvas id="trendChart"></canvas>
        </div>

        <div id="inspDiagnosis" class="mt-3 rounded-xl border border-slate-800 bg-slate-950/70 p-3 text-xs leading-relaxed text-slate-300">
          Loading AI signal...
        </div>
      </div>
    </section>

    <!-- Filter Toolbar -->
    <section class="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
      <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <!-- View Tabs -->
        <div id="viewTabs" class="flex flex-wrap gap-1.5">
          <button type="button" data-view="all" class="view-tab rounded-lg bg-emerald-500 px-3 py-1.5 text-xs font-semibold text-slate-950 transition">All NSE Equities</button>
          <button type="button" data-view="near_high" class="view-tab rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-300 transition hover:bg-slate-700">Near 52W High (&le; 5%)</button>
          <button type="button" data-view="demat" class="view-tab rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-300 transition hover:bg-slate-700">My Demat Holdings</button>
          <button type="button" data-view="near_low" class="view-tab rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-300 transition hover:bg-slate-700">Near 52W Low</button>
          <button type="button" data-view="watchlist" class="view-tab rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-300 transition hover:bg-slate-700">Watchlist (<span id="watchlistCount">0</span>)</button>
        </div>

        <!-- Search, Sector, Slider, Sort -->
        <div class="flex flex-wrap items-center gap-2.5">
          <div class="relative min-w-[180px] flex-1 sm:flex-initial">
            <i data-lucide="search" class="pointer-events-none absolute left-2.5 top-2 h-3.5 w-3.5 text-slate-400"></i>
            <input id="searchInput" type="text" placeholder="Search symbol or name..." class="w-full rounded-lg border border-slate-700 bg-slate-950 py-1.5 pl-8 pr-3 text-xs text-white placeholder-slate-500 focus:border-emerald-500 focus:outline-none" />
          </div>

          <select id="sectorFilter" class="rounded-lg border border-slate-700 bg-slate-950 px-2.5 py-1.5 text-xs text-slate-200 focus:border-emerald-500 focus:outline-none">
            <option value="ALL">All Sectors</option>
          </select>

          <div class="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-950 px-2.5 py-1">
            <span class="text-[11px] text-slate-400">Max Off High:</span>
            <input id="maxDistSlider" type="range" min="1" max="60" value="60" class="w-20" />
            <span id="maxDistLabel" class="w-8 text-right text-xs font-semibold text-emerald-400">60%</span>
          </div>

          <select id="sortSelect" class="rounded-lg border border-slate-700 bg-slate-950 px-2.5 py-1.5 text-xs text-slate-200 focus:border-emerald-500 focus:outline-none">
            <option value="distHighAsc">Nearest to 52W High</option>
            <option value="scoreDesc">AI Momentum Score</option>
            <option value="chg5dDesc">5-Day Return %</option>
            <option value="rangePosDesc">52W Range Position %</option>
            <option value="peAsc">P/E Ratio (Low &rarr; High)</option>
          </select>
        </div>
      </div>

      <!-- Ranked Table -->
      <div class="mt-4 overflow-x-auto">
        <table class="w-full border-collapse text-left text-xs">
          <thead>
            <tr class="border-b border-slate-800 text-[11px] uppercase tracking-wider text-slate-400">
              <th class="py-2.5 pl-2 pr-3">Rank</th>
              <th class="px-3 py-2.5">Stock / Sector</th>
              <th class="px-3 py-2.5 text-right">LTP (&#8377;)</th>
              <th class="px-3 py-2.5 text-right">5D Chg</th>
              <th class="px-3 py-2.5">52-Week Low &mdash; High Range</th>
              <th class="px-3 py-2.5 text-right">% Off 52W High</th>
              <th class="px-3 py-2.5 text-right">% Above Low</th>
              <th class="px-3 py-2.5 text-right">P/E</th>
              <th class="px-3 py-2.5 text-center">AI Score</th>
              <th class="py-2.5 pl-2 pr-2 text-center">Watch</th>
            </tr>
          </thead>
          <tbody id="stockTableBody" class="divide-y divide-slate-800/70"></tbody>
        </table>
      </div>

      <div id="emptyState" class="hidden py-10 text-center">
        <p class="text-sm font-medium text-slate-400">No NSE stocks match the current filters.</p>
        <button id="resetFiltersBtn" type="button" class="mt-2 rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-medium text-emerald-400 hover:bg-slate-700">Reset Filters</button>
      </div>
    </section>
  </main>

  <script>
    // Verified NSE Equities Dataset (23 Nov 2026 15:30 IST Close via Google Finance & Trendlyne)
    const INITIAL_STOCKS = [
      {
        symbol: "DLF", name: "DLF Ltd", sector: "Real Estate", demat: false, gtt: false,
        ltp: 794.10, high52w: 795.95, low52w: 489.40, chg5d: 4.34, pe: 43.05, eps: 18.44, divYield: 1.01,
        trend5d: [761.10, 764.30, 768.00, 785.00, 794.10]
      },
      {
        symbol: "MARICO", name: "Marico Ltd", sector: "Consumer & FMCG", demat: false, gtt: false,
        ltp: 919.50, high52w: 925.00, low52w: 707.25, chg5d: 0.74, pe: 59.13, eps: 15.55, divYield: 0.44,
        trend5d: [912.75, 906.05, 918.80, 917.00, 919.50]
      },
      {
        symbol: "HONASA", name: "Honasa Consumer Ltd", sector: "Consumer & FMCG", demat: false, gtt: false,
        ltp: 538.45, high52w: 543.00, low52w: 248.40, chg5d: 1.75, pe: 62.27, eps: 8.65, divYield: 0.56,
        trend5d: [529.20, 522.10, 529.80, 524.55, 538.45]
      },
      {
        symbol: "EICHERMOT", name: "Eicher Motors Ltd", sector: "Auto", demat: false, gtt: false,
        ltp: 8172.50, high52w: 8275.00, low52w: 6442.00, chg5d: 5.42, pe: 37.58, eps: 217.44, divYield: 1.00,
        trend5d: [7752.50, 7700.00, 8058.50, 8113.00, 8172.50]
      },
      {
        symbol: "INDHOTEL", name: "Indian Hotels Co Ltd", sector: "Hospitality", demat: false, gtt: false,
        ltp: 906.00, high52w: 917.85, low52w: 565.00, chg5d: 1.25, pe: 58.33, eps: 15.53, divYield: 0.36,
        trend5d: [894.85, 875.05, 889.65, 912.00, 906.00]
      },
      {
        symbol: "APOLLOHOSP", name: "Apollo Hospitals Enterprise", sector: "Healthcare & Pharma", demat: false, gtt: false,
        ltp: 9257.00, high52w: 9410.00, low52w: 6696.50, chg5d: 5.21, pe: 59.41, eps: 155.81, divYield: 0.22,
        trend5d: [8799.00, 8821.00, 8738.00, 9200.00, 9257.00]
      },
      {
        symbol: "COFORGE", name: "Coforge Ltd", sector: "IT & Tech", demat: false, gtt: false,
        ltp: 2142.30, high52w: 2177.80, low52w: 1008.10, chg5d: 5.08, pe: 39.01, eps: 54.91, divYield: 0.56,
        trend5d: [2038.70, 2049.00, 2041.00, 2086.70, 2142.30]
      },
      {
        symbol: "LALPATHLAB", name: "Dr. Lal PathLabs Ltd", sector: "Healthcare & Pharma", demat: false, gtt: false,
        ltp: 2039.00, high52w: 2079.00, low52w: 1272.60, chg5d: 3.29, pe: 58.48, eps: 34.86, divYield: 0.86,
        trend5d: [1974.10, 1965.00, 1960.00, 1989.00, 2039.00]
      },
      {
        symbol: "BHARTIARTL", name: "Bharti Airtel Ltd", sector: "Telecom", demat: false, gtt: false,
        ltp: 2128.50, high52w: 2172.90, low52w: 1726.30, chg5d: -0.51, pe: 41.92, eps: 50.78, divYield: 1.13,
        trend5d: [2139.40, 2132.00, 2144.00, 2161.70, 2128.50]
      },
      {
        symbol: "GLENMARK", name: "Glenmark Pharmaceuticals", sector: "Healthcare & Pharma", demat: false, gtt: false,
        ltp: 2657.00, high52w: 2714.00, low52w: 1825.10, chg5d: 0.91, pe: 41.72, eps: 63.68, divYield: 0.19,
        trend5d: [2633.00, 2646.10, 2608.50, 2648.00, 2657.00]
      },
      {
        symbol: "TVSMOTOR", name: "TVS Motor Company Ltd", sector: "Auto", demat: false, gtt: false,
        ltp: 4528.20, high52w: 4636.10, low52w: 3228.00, chg5d: 1.97, pe: 56.21, eps: 80.55, divYield: 0.00,
        trend5d: [4440.70, 4369.00, 4601.40, 4590.00, 4528.20]
      },
      {
        symbol: "KARURVYSYA", name: "Karur Vysya Bank Ltd", sector: "Banking & Finance", demat: true, gtt: true,
        ltp: 384.10, high52w: 397.85, low52w: 236.63, chg5d: -1.58, pe: 12.55, eps: 30.59, divYield: 0.68,
        trend5d: [390.25, 387.00, 384.00, 377.00, 384.10]
      },
      {
        symbol: "ICICIBANK", name: "ICICI Bank Ltd", sector: "Banking & Finance", demat: false, gtt: false,
        ltp: 1585.50, high52w: 1645.00, low52w: 1187.60, chg5d: -1.08, pe: 19.46, eps: 81.45, divYield: 0.76,
        trend5d: [1602.80, 1601.30, 1608.90, 1640.00, 1585.50]
      },
      {
        symbol: "FEDERALBNK", name: "Federal Bank Ltd", sector: "Banking & Finance", demat: true, gtt: true,
        ltp: 359.80, high52w: 376.20, low52w: 242.30, chg5d: -1.15, pe: 17.55, eps: 20.50, divYield: 0.33,
        trend5d: [364.00, 360.35, 364.50, 373.50, 359.80]
      },
      {
        symbol: "YATHARTH", name: "Yatharth Hospital & Trauma", sector: "Healthcare & Pharma", demat: true, gtt: false,
        ltp: 1087.50, high52w: 1184.00, low52w: 538.25, chg5d: -1.54, pe: 55.23, eps: 19.69, divYield: 0.05,
        trend5d: [1104.55, 1089.85, 1085.00, 1094.00, 1087.50]
      },
      {
        symbol: "STARHEALTH", name: "Star Health & Allied Ins.", sector: "Banking & Finance", demat: true, gtt: false,
        ltp: 564.50, high52w: 624.90, low52w: 416.55, chg5d: 2.33, pe: 29.87, eps: 18.90, divYield: 0.00,
        trend5d: [551.65, 559.00, 569.45, 556.00, 564.50]
      },
      {
        symbol: "WOCKPHARMA", name: "Wockhardt Ltd", sector: "Healthcare & Pharma", demat: true, gtt: false,
        ltp: 2149.00, high52w: 2422.30, low52w: 1086.70, chg5d: 5.40, pe: 85.23, eps: 25.21, divYield: 0.00,
        trend5d: [2038.90, 2025.00, 2186.00, 2178.00, 2149.00]
      },
      {
        symbol: "SUDARSCHEM", name: "Sudarshan Chemical Ind.", sector: "Chemicals", demat: true, gtt: false,
        ltp: 1140.00, high52w: 1347.00, low52w: 726.40, chg5d: -0.24, pe: 104.25, eps: 10.94, divYield: 0.44,
        trend5d: [1142.70, 1140.75, 1145.50, 1155.10, 1140.00]
      },
      {
        symbol: "ELECON", name: "Elecon Engineering Co Ltd", sector: "Capital Goods", demat: true, gtt: false,
        ltp: 438.30, high52w: 579.00, low52w: 352.00, chg5d: -2.37, pe: 40.18, eps: 10.91, divYield: 0.46,
        trend5d: [448.95, 446.60, 452.60, 455.50, 438.30]
      },
      {
        symbol: "TCS", name: "Tata Consultancy Services", sector: "IT & Tech", demat: false, gtt: false,
        ltp: 2460.00, high52w: 3350.00, low52w: 1976.80, chg5d: 2.81, pe: 17.25, eps: 142.63, divYield: 2.68,
        trend5d: [2392.80, 2379.50, 2342.70, 2376.20, 2460.00]
      },
      {
        symbol: "TATASTEEL", name: "Tata Steel Ltd", sector: "Metals", demat: false, gtt: false,
        ltp: 163.00, high52w: 224.40, low52w: 160.06, chg5d: -9.01, pe: 17.52, eps: 9.30, divYield: 2.45,
        trend5d: [179.14, 179.00, 180.89, 178.00, 163.00]
      },
      {
        symbol: "TATAPOWER", name: "Tata Power Company Ltd", sector: "Power & Energy", demat: false, gtt: false,
        ltp: 328.00, high52w: 464.90, low52w: 327.50, chg5d: -4.00, pe: 24.37, eps: 13.46, divYield: 0.76,
        trend5d: [341.65, 338.00, 340.00, 339.70, 328.00]
      },
      {
        symbol: "ATULAUTO", name: "Atul Auto Ltd", sector: "Auto", demat: true, gtt: false,
        ltp: 390.85, high52w: 596.55, low52w: 365.60, chg5d: -0.06, pe: 24.20, eps: 16.15, divYield: 0.77,
        trend5d: [391.10, 393.00, 402.70, 395.55, 390.85]
      },
      {
        symbol: "PIIND", name: "PI Industries Ltd", sector: "Chemicals", demat: false, gtt: false,
        ltp: 1571.00, high52w: 3480.00, low52w: 1570.10, chg5d: -4.49, pe: 27.15, eps: 57.86, divYield: 0.95,
        trend5d: [1644.90, 1624.00, 1630.00, 1597.40, 1571.00]
      }
    ];

    const TREND_LABELS = ["18 Nov", "19 Nov", "20 Nov", "21 Nov", "23 Nov"];

    const state = {
      stocks: [],
      view: "all",
      search: "",
      sector: "ALL",
      maxDistHigh: 60,
      sortBy: "distHighAsc",
      selectedSymbol: "DLF",
      watchlist: new Set(["DLF", "EICHERMOT", "KARURVYSYA", "WOCKPHARMA"])
    };

    let proximityChart = null;
    let trendChart = null;

    function loadWatchlist() {
      try {
        const saved = localStorage.getItem("nse_52w_watchlist");
        if (saved) {
          const arr = JSON.parse(saved);
          if (Array.isArray(arr)) state.watchlist = new Set(arr);
        }
      } catch (e) {}
    }

    function saveWatchlist() {
      try {
        localStorage.setItem("nse_52w_watchlist", JSON.stringify(Array.from(state.watchlist)));
      } catch (e) {}
    }

    function enrichStock(raw) {
      const ltp = Number(raw.ltp) || 0;
      const high = Number(raw.high52w) || ltp;
      const low = Number(raw.low52w) || ltp;
      const chg5d = Number(raw.chg5d) || 0;
      const pctOffHigh = high > 0 ? Math.max(0, ((high - ltp) / high) * 100) : 0;
      const pctAboveLow = low > 0 ? Math.max(0, ((ltp - low) / low) * 100) : 0;
      const span = high - low;
      const rangePos = span > 0 ? Math.min(100, Math.max(0, ((ltp - low) / span) * 100)) : 100;

      // Composite AI Momentum Score (0-100) prioritizing 52W High Proximity
      const proxPts = Math.max(0, 55 * (1 - pctOffHigh / 25));
      const momPts = Math.min(25, Math.max(0, 12.5 + chg5d * 2.2));
      const rangePts = 0.20 * rangePos;
      const aiScore = Math.round(Math.min(100, Math.max(0, proxPts + momPts + rangePts)));

      let signal = "Consolidating";
      let signalTone = "amber";
      if (pctOffHigh <= 2.5) {
        signal = "Breakout Zone";
        signalTone = "emerald";
      } else if (pctOffHigh <= 5.0) {
        signal = "Near 52W High";
        signalTone = "sky";
      } else if (pctAboveLow <= 5.0 || rangePos < 25) {
        signal = "Near 52W Low";
        signalTone = "rose";
      }

      return {
        ...raw,
        ltp, high52w: high, low52w: low, chg5d,
        pctOffHigh, pctAboveLow, rangePos, aiScore, signal, signalTone
      };
    }

    function showToast(msg) {
      const toast = document.getElementById("toast");
      const toastMsg = document.getElementById("toastMsg");
      toastMsg.textContent = msg;
      toast.classList.remove("hidden");
      toast.classList.add("flex");
      clearTimeout(window.__toastTimer);
      window.__toastTimer = setTimeout(() => {
        toast.classList.add("hidden");
        toast.classList.remove("flex");
      }, 2800);
    }

    function populateSectors() {
      const select = document.getElementById("sectorFilter");
      const current = select.value;
      const sectors = Array.from(new Set(state.stocks.map(s => s.sector))).sort();
      select.innerHTML = '<option value="ALL">All Sectors</option>' +
        sectors.map(sec => `<option value="${sec}">${sec}</option>`).join("");
      if (sectors.includes(current)) select.value = current;
    }

    function getFilteredStocks() {
      let list = state.stocks.filter(s => {
        if (state.view === "near_high" && s.pctOffHigh > 5.0) return false;
        if (state.view === "demat" && !s.demat) return false;
        if (state.view === "near_low" && s.pctAboveLow > 5.0 && s.rangePos >= 25) return false;
        if (state.view === "watchlist" && !state.watchlist.has(s.symbol)) return false;
        if (state.sector !== "ALL" && s.sector !== state.sector) return false;
        if (s.pctOffHigh > state.maxDistHigh) return false;
        if (state.search.trim()) {
          const q = state.search.trim().toLowerCase();
          if (!s.symbol.toLowerCase().includes(q) && !s.name.toLowerCase().includes(q)) return false;
        }
        return true;
      });

      list.sort((a, b) => {
        switch (state.sortBy) {
          case "scoreDesc": return b.aiScore - a.aiScore || a.pctOffHigh - b.pctOffHigh;
          case "chg5dDesc": return b.chg5d - a.chg5d;
          case "rangePosDesc": return b.rangePos - a.rangePos;
          case "peAsc": return (a.pe || 999) - (b.pe || 999);
          case "distHighAsc":
          default:
            return a.pctOffHigh - b.pctOffHigh || b.aiScore - a.aiScore;
        }
      });
      return list;
    }

    function fmtINR(val) {
      return Number(val).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    function updateKPIs(filtered) {
      const breakout = filtered.filter(s => s.pctOffHigh <= 3.0);
      document.getElementById("kpiBreakoutCount").textContent = breakout.length;
      if (filtered.length > 0) {
        const sortedByHigh = [...filtered].sort((a, b) => a.pctOffHigh - b.pctOffHigh);
        const top = sortedByHigh[0];
        document.getElementById("kpiTopLeader").textContent = `Top: ${top.symbol} (-${top.pctOffHigh.toFixed(2)}%)`;
        const avgDist = filtered.reduce((acc, s) => acc + s.pctOffHigh, 0) / filtered.length;
        const avgRange = filtered.reduce((acc, s) => acc + s.rangePos, 0) / filtered.length;
        document.getElementById("kpiAvgDistHigh").textContent = `${avgDist.toFixed(2)}%`;
        document.getElementById("kpiAvgRangePos").textContent = `${avgRange.toFixed(1)}%`;
      } else {
        document.getElementById("kpiTopLeader").textContent = "--";
        document.getElementById("kpiAvgDistHigh").textContent = "--";
        document.getElementById("kpiAvgRangePos").textContent = "--";
      }
      document.getElementById("kpiDematCount").textContent = state.stocks.filter(s => s.demat).length;
      document.getElementById("watchlistCount").textContent = state.watchlist.size;
    }

    function renderTable(filtered) {
      const tbody = document.getElementById("stockTableBody");
      const empty = document.getElementById("emptyState");
      if (filtered.length === 0) {
        tbody.innerHTML = "";
        empty.classList.remove("hidden");
        return;
      }
      empty.classList.add("hidden");

      const toneBadge = {
        emerald: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
        sky: "bg-sky-500/15 text-sky-400 border-sky-500/30",
        amber: "bg-amber-500/15 text-amber-400 border-amber-500/30",
        rose: "bg-rose-500/15 text-rose-400 border-rose-500/30"
      };

      tbody.innerHTML = filtered.map((s, idx) => {
        const isSelected = s.symbol === state.selectedSymbol;
        const isWatched = state.watchlist.has(s.symbol);
        const chgClass = s.chg5d >= 0 ? "text-emerald-400" : "text-rose-400";
        const chgSign = s.chg5d >= 0 ? "+" : "";
        const offHighColor = s.pctOffHigh <= 3 ? "text-emerald-400 font-bold" : s.pctOffHigh <= 6 ? "text-sky-400 font-semibold" : "text-slate-300";
        const barColor = s.rangePos >= 85 ? "bg-emerald-400" : s.rangePos >= 50 ? "bg-sky-400" : "bg-rose-400";

        return `
          <tr data-symbol="${s.symbol}" class="stock-row cursor-pointer transition hover:bg-slate-800/60 ${isSelected ? "bg-slate-800/80 ring-1 ring-inset ring-emerald-500/40" : ""}">
            <td class="py-3 pl-2 pr-3 font-mono text-[11px] text-slate-400">#${idx + 1}</td>
            <td class="px-3 py-3">
              <div class="flex flex-wrap items-center gap-1.5">
                <span class="font-bold text-white">${s.symbol}</span>
                ${s.demat ? '<span class="rounded bg-violet-500/20 px-1.5 py-0.5 text-[10px] font-semibold text-violet-300">DEMAT</span>' : ""}
                ${s.gtt ? '<span class="rounded bg-amber-500/20 px-1.5 py-0.5 text-[10px] font-semibold text-amber-300">GTT</span>' : ""}
              </div>
              <div class="mt-0.5 max-w-[200px] truncate text-[11px] text-slate-400">${s.name} &bull; ${s.sector}</div>
            </td>
            <td class="px-3 py-3 text-right font-semibold text-white">&#8377;${fmtINR(s.ltp)}</td>
            <td class="px-3 py-3 text-right font-medium ${chgClass}">${chgSign}${s.chg5d.toFixed(2)}%</td>
            <td class="min-w-[165px] px-3 py-3">
              <div class="flex justify-between text-[10px] text-slate-400">
                <span>&#8377;${fmtINR(s.low52w)}</span>
                <span>&#8377;${fmtINR(s.high52w)}</span>
              </div>
              <div class="relative mt-1 h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
                <div class="h-full rounded-full ${barColor}" style="width: ${s.rangePos.toFixed(1)}%"></div>
              </div>
            </td>
            <td class="px-3 py-3 text-right ${offHighColor}">-${s.pctOffHigh.toFixed(2)}%</td>
            <td class="px-3 py-3 text-right text-slate-300">+${s.pctAboveLow.toFixed(1)}%</td>
            <td class="px-3 py-3 text-right text-slate-300">${s.pe ? s.pe.toFixed(1) : "--"}</td>
            <td class="px-3 py-3 text-center">
              <span class="inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-semibold ${toneBadge[s.signalTone]}">
                ${s.aiScore} &bull; ${s.signal}
              </span>
            </td>
            <td class="py-3 pl-2 pr-2 text-center">
              <button type="button" data-watch="${s.symbol}" class="watch-btn rounded-lg p-1 text-base transition hover:bg-slate-700 ${isWatched ? "text-amber-400" : "text-slate-600"}" title="Toggle Watchlist">
                ${isWatched ? "★" : "☆"}
              </button>
            </td>
          </tr>
        `;
      }).join("");
    }

    function renderProximityChart(filtered) {
      const top10 = [...filtered].sort((a, b) => a.pctOffHigh - b.pctOffHigh).slice(0, 10);
      const ctx = document.getElementById("proximityChart").getContext("2d");
      const labels = top10.map(s => s.symbol);
      const data = top10.map(s => Number(s.rangePos.toFixed(1)));
      const colors = top10.map(s => s.pctOffHigh <= 2.5 ? "#10b981" : s.pctOffHigh <= 5.0 ? "#38bdf8" : "#f59e0b");

      if (proximityChart) proximityChart.destroy();
      proximityChart = new Chart(ctx, {
        type: "bar",
        data: {
          labels,
          datasets: [{
            label: "52W Range Position %",
            data,
            backgroundColor: colors,
            borderRadius: 6,
            barThickness: 16
          }]
        },
        options: {
          indexAxis: "y",
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (item) => {
                  const s = top10[item.dataIndex];
                  return `${s.rangePos.toFixed(1)}% of 52W range (-${s.pctOffHigh.toFixed(2)}% from ₹${fmtINR(s.high52w)})`;
                }
              }
            }
          },
          scales: {
            x: {
              min: 0,
              max: 100,
              grid: { color: "rgba(148,163,184,0.1)" },
              ticks: { color: "#94a3b8", callback: v => v + "%" }
            },
            y: {
              grid: { display: false },
              ticks: { color: "#e2e8f0", font: { weight: "600", size: 11 } }
            }
          }
        }
      });
    }

    function renderInspector() {
      const s = state.stocks.find(item => item.symbol === state.selectedSymbol) || state.stocks[0];
      if (!s) return;

      document.getElementById("inspSymbol").textContent = s.symbol;
      document.getElementById("inspName").textContent = `${s.name} • ${s.sector}`;
      document.getElementById("inspPrice").textContent = `₹${fmtINR(s.ltp)}`;
      document.getElementById("inspDistHigh").textContent = `-${s.pctOffHigh.toFixed(2)}% from 52W High (₹${fmtINR(s.high52w)})`;
      document.getElementById("inspScreenerLink").href = `https://www.screener.in/company/${encodeURIComponent(s.symbol)}/`;

      const badge = document.getElementById("inspBadge");
      badge.textContent = `${s.aiScore} • ${s.signal}`;
      badge.className = "rounded-full px-2 py-0.5 text-[11px] font-semibold " + (
        s.signalTone === "emerald" ? "bg-emerald-500/15 text-emerald-400" :
        s.signalTone === "sky" ? "bg-sky-500/15 text-sky-400" :
        s.signalTone === "rose" ? "bg-rose-500/15 text-rose-400" :
        "bg-amber-500/15 text-amber-400"
      );

      let thesis = "";
      if (s.pctOffHigh <= 2.5) {
        thesis = `<strong>Breakout Watch:</strong> Trading just <strong>${s.pctOffHigh.toFixed(2)}%</strong> below its 52-week high of ₹${fmtINR(s.high52w)} (${s.rangePos.toFixed(1)}% of 52W range). `;
      } else if (s.pctOffHigh <= 5.0) {
        thesis = `<strong>Near High Momentum:</strong> Within <strong>${s.pctOffHigh.toFixed(2)}%</strong> of its 52-week high with ${s.chg5d >= 0 ? "positive" : "soft"} 5-day price action (${s.chg5d >= 0 ? "+" : ""}${s.chg5d.toFixed(2)}%). `;
      } else if (s.pctAboveLow <= 5.0) {
        thesis = `<strong>52-Week Support Test:</strong> Trading only <strong>+${s.pctAboveLow.toFixed(2)}%</strong> above its 52-week low of ₹${fmtINR(s.low52w)}. Watch for base formation before adding. `;
      } else {
        thesis = `<strong>Mid-Range Consolidation:</strong> Sitting at ${s.rangePos.toFixed(1)}% of its 52-week range (₹${fmtINR(s.low52w)} – ₹${fmtINR(s.high52w)}). `;
      }
      thesis += `P/E stands at <strong>${s.pe ? s.pe.toFixed(2) : "N/A"}</strong>, EPS ₹${s.eps ? s.eps.toFixed(2) : "N/A"}, Dividend Yield ${s.divYield ? s.divYield.toFixed(2) : "0.00"}%.`;
      if (s.demat) thesis += ` <span class="text-violet-300 font-semibold">[In Your Demat${s.gtt ? " • GTT Active" : ""}]</span>`;
      document.getElementById("inspDiagnosis").innerHTML = thesis;

      const ctx = document.getElementById("trendChart").getContext("2d");
      const pts = Array.isArray(s.trend5d) && s.trend5d.length ? s.trend5d : [s.ltp, s.ltp, s.ltp, s.ltp, s.ltp];
      const highLine = pts.map(() => s.high52w);

      if (trendChart) trendChart.destroy();
      trendChart = new Chart(ctx, {
        type: "line",
        data: {
          labels: TREND_LABELS,
          datasets: [
            {
              label: `${s.symbol} Close (₹)`,
              data: pts,
              borderColor: s.chg5d >= 0 ? "#10b981" : "#f43f5e",
              backgroundColor: s.chg5d >= 0 ? "rgba(16,185,129,0.12)" : "rgba(244,63,94,0.12)",
              fill: true,
              tension: 0.3,
              pointRadius: 3.5,
              borderWidth: 2
            },
            {
              label: "52W High (₹)",
              data: highLine,
              borderColor: "rgba(56,189,248,0.65)",
              borderDash: [5, 5],
              pointRadius: 0,
              borderWidth: 1.5,
              fill: false
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              labels: { color: "#94a3b8", boxWidth: 12, font: { size: 11 } }
            }
          },
          scales: {
            x: {
              grid: { color: "rgba(148,163,184,0.08)" },
              ticks: { color: "#94a3b8", font: { size: 11 } }
            },
            y: {
              grid: { color: "rgba(148,163,184,0.08)" },
              ticks: { color: "#94a3b8", font: { size: 11 }, callback: v => "₹" + v.toLocaleString("en-IN") }
            }
          }
        }
      });
    }

    function renderAll() {
      const filtered = getFilteredStocks();
      updateKPIs(filtered);
      renderTable(filtered);
      renderProximityChart(filtered);
      renderInspector();
      if (window.lucide) lucide.createIcons();
    }

    function setActiveTab(view) {
      state.view = view;
      document.querySelectorAll(".view-tab").forEach(btn => {
        const active = btn.dataset.view === view;
        btn.className = active
          ? "view-tab rounded-lg bg-emerald-500 px-3 py-1.5 text-xs font-semibold text-slate-950 transition"
          : "view-tab rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-300 transition hover:bg-slate-700";
      });
      renderAll();
    }

    function parseCSVText(text) {
      const lines = text.split(/\r?\n/).filter(l => l.trim());
      if (lines.length < 2) return [];
      const headers = lines[0].split(",").map(h => h.trim().replace(/^"|"$/g, "").toLowerCase());
      const idx = (names) => headers.findIndex(h => names.some(n => h.includes(n)));
      const symI = idx(["symbol", "ticker"]);
      const nameI = idx(["name", "company"]);
      const ltpI = idx(["ltp", "close", "price"]);
      const highI = idx(["52w high", "high52w", "52_week_high", "high"]);
      const lowI = idx(["52w low", "low52w", "52_week_low", "low"]);
      const chgI = idx(["chg", "change", "return", "momentum"]);
      const secI = idx(["sector", "industry"]);
      const peI = idx(["p/e", "pe"]);

      const parsed = [];
      for (let i = 1; i < lines.length; i++) {
        const cols = lines[i].split(",").map(c => c.trim().replace(/^"|"$/g, ""));
        const sym = symI >= 0 ? cols[symI] : "";
        const ltp = ltpI >= 0 ? parseFloat(cols[ltpI]) : NaN;
        if (!sym || isNaN(ltp)) continue;
        const high52w = highI >= 0 && !isNaN(parseFloat(cols[highI])) ? parseFloat(cols[highI]) : ltp;
        const low52w = lowI >= 0 && !isNaN(parseFloat(cols[lowI])) ? parseFloat(cols[lowI]) : ltp;
        const chg5d = chgI >= 0 && !isNaN(parseFloat(cols[chgI])) ? parseFloat(cols[chgI]) : 0;
        const pe = peI >= 0 && !isNaN(parseFloat(cols[peI])) ? parseFloat(cols[peI]) : 0;
        const sector = secI >= 0 && cols[secI] ? cols[secI] : "NSE Equity";
        const name = nameI >= 0 && cols[nameI] ? cols[nameI] : sym;
        parsed.push(enrichStock({
          symbol: sym.toUpperCase(),
          name, sector, demat: false, gtt: false,
          ltp, high52w, low52w, chg5d, pe, eps: 0, divYield: 0,
          trend5d: [ltp, ltp, ltp, ltp, ltp]
        }));
      }
      return parsed;
    }

    function exportRankedCSV() {
      const rows = getFilteredStocks();
      const header = ["Rank", "Symbol", "Company", "Sector", "LTP", "52W_High", "52W_Low", "Pct_Off_52W_High", "Pct_Above_52W_Low", "52W_Range_Pos_Pct", "5D_Change_Pct", "PE", "AI_Score", "Signal"];
      const csvRows = [header.join(",")].concat(rows.map((s, i) => [
        i + 1, s.symbol, `"${s.name}"`, `"${s.sector}"`, s.ltp.toFixed(2), s.high52w.toFixed(2),
        s.low52w.toFixed(2), s.pctOffHigh.toFixed(2), s.pctAboveLow.toFixed(2),
        s.rangePos.toFixed(1), s.chg5d.toFixed(2), s.pe ? s.pe.toFixed(2) : "", s.aiScore, `"${s.signal}"`
      ].join(",")));
      const blob = new Blob([csvRows.join("\n")], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "nse_52w_momentum_ranked.csv";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showToast(`Exported ${rows.length} ranked NSE stocks`);
    }

    function init() {
      loadWatchlist();
      state.stocks = INITIAL_STOCKS.map(enrichStock);
      populateSectors();

      document.getElementById("viewTabs").addEventListener("click", (e) => {
        const btn = e.target.closest(".view-tab");
        if (btn) setActiveTab(btn.dataset.view);
      });

      document.getElementById("quickDematBtn").addEventListener("click", () => setActiveTab("demat"));

      document.getElementById("searchInput").addEventListener("input", (e) => {
        state.search = e.target.value;
        renderAll();
      });

      document.getElementById("sectorFilter").addEventListener("change", (e) => {
        state.sector = e.target.value;
        renderAll();
      });

      document.getElementById("maxDistSlider").addEventListener("input", (e) => {
        state.maxDistHigh = Number(e.target.value);
        document.getElementById("maxDistLabel").textContent = `${state.maxDistHigh}%`;
        renderAll();
      });

      document.getElementById("sortSelect").addEventListener("change", (e) => {
        state.sortBy = e.target.value;
        renderAll();
      });

      document.getElementById("stockTableBody").addEventListener("click", (e) => {
        const watchBtn = e.target.closest(".watch-btn");
        if (watchBtn) {
          e.stopPropagation();
          const sym = watchBtn.dataset.watch;
          if (state.watchlist.has(sym)) {
            state.watchlist.delete(sym);
            showToast(`Removed ${sym} from watchlist`);
          } else {
            state.watchlist.add(sym);
            showToast(`Added ${sym} to watchlist`);
          }
          saveWatchlist();
          renderAll();
          return;
        }
        const row = e.target.closest(".stock-row");
        if (row) {
          state.selectedSymbol = row.dataset.symbol;
          renderAll();
        }
      });

      document.getElementById("resetFiltersBtn").addEventListener("click", () => {
        state.search = "";
        state.sector = "ALL";
        state.maxDistHigh = 60;
        document.getElementById("searchInput").value = "";
        document.getElementById("sectorFilter").value = "ALL";
        document.getElementById("maxDistSlider").value = 60;
        document.getElementById("maxDistLabel").textContent = "60%";
        setActiveTab("all");
      });

      document.getElementById("exportBtn").addEventListener("click", exportRankedCSV);

      document.getElementById("csvInput").addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (ev) => {
          const imported = parseCSVText(ev.target.result);
          if (imported.length === 0) {
            showToast("No valid rows found in CSV");
            return;
          }
          const bySym = new Map(state.stocks.map(s => [s.symbol, s]));
          imported.forEach(item => {
            const existing = bySym.get(item.symbol);
            if (existing) {
              item.demat = existing.demat;
              item.gtt = existing.gtt;
            }
            bySym.set(item.symbol, item);
          });
          state.stocks = Array.from(bySym.values());
          populateSectors();
          renderAll();
          showToast(`Loaded ${imported.length} stocks from ${file.name}`);
        };
        reader.readAsText(file);
        e.target.value = "";
      });

      renderAll();
    }

    window.addEventListener("DOMContentLoaded", init);
  </script>
</body>
</html>
"""

components.html(HTML_DASHBOARD, height=1350, scrolling=True)
