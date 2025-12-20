// ============================================================
// Dashboard JS — Enhanced (KPIs + Strength + Caching)
// CSS-safe | API-aligned | No backend changes
// ============================================================

(() => {
  // -----------------------------
  // CONFIG
  // -----------------------------
  const CACHE_TTL_MS = 120 * 1000; // 2 minutes
  const DEFAULT_PERIOD = "3mo";

  // -----------------------------
  // STATE
  // -----------------------------
  let currentPeriod = DEFAULT_PERIOD;
  let activeChart = null;

  // -----------------------------
  // DOM
  // -----------------------------
  const grid = document.getElementById("dashboardGrid");
  const modal = document.getElementById("chartModal");
  const chartTitle = document.getElementById("chartTitle");
  const chartCanvas = document.getElementById("priceChart");
  const chartClose = document.getElementById("chartClose");

  if (!grid) return;

  // -----------------------------
  // CACHE HELPERS
  // -----------------------------
  function cacheKey(url) {
    return `bf_cache:${url}`;
  }

  function getCached(url) {
    try {
      const raw = localStorage.getItem(cacheKey(url));
      if (!raw) return null;

      const { timestamp, data } = JSON.parse(raw);
      if (Date.now() - timestamp > CACHE_TTL_MS) {
        localStorage.removeItem(cacheKey(url));
        return null;
      }
      return data;
    } catch {
      return null;
    }
  }

  function setCached(url, data) {
    try {
      localStorage.setItem(
        cacheKey(url),
        JSON.stringify({ timestamp: Date.now(), data })
      );
    } catch {
      /* ignore quota issues */
    }
  }

  // -----------------------------
  // API
  // -----------------------------
  async function fetchJSON(url) {
    const cached = getCached(url);
    if (cached) return cached;

    const res = await fetch(url);
    if (!res.ok) throw new Error(`API error: ${res.status}`);

    const data = await res.json();
    setCached(url, data);
    return data;
  }

  // -----------------------------
  // STRENGTH SCORE (0–100)
  // -----------------------------
  function computeStrength(info) {
    const trendStrength = Number(info.trend_strength || 0); // %
    const momentum = Number(info.momentum || 0);
    const volatility = Math.max(Number(info.volatility || 0), 0.01);

    // Normalize components
    const trendScore = Math.max(-1, Math.min(1, trendStrength / 2));
    const momentumScore = Math.max(-1, Math.min(1, momentum / 10));
    const volPenalty = Math.min(1, volatility / 50);

    const raw =
      trendScore * 0.5 +
      momentumScore * 0.4 -
      volPenalty * 0.3;

    const score = Math.round(50 + raw * 50);
    return Math.max(0, Math.min(100, score));
  }

// -----------------------------
// MARKET REGIME
// -----------------------------
function computeRegime(info, strength) {
  if (info.signal === "Strong Bullish" && strength >= 65) {
    return { label: "Risk-On", className: "regime-on" };
  }

  if (info.signal === "Strong Bearish" && strength <= 35) {
    return { label: "Risk-Off", className: "regime-off" };
  }

  return { label: "Transitional", className: "regime-neutral" };
}


  // -----------------------------
  // DASHBOARD RENDER
  // -----------------------------
  async function loadDashboard() {
    grid.innerHTML = "";

    try {
      const url = `/api/market?period=${encodeURIComponent(currentPeriod)}`;
      const data = await fetchJSON(url);

      Object.entries(data).forEach(([symbol, info]) => {
        const trendClass =
          info.trend === "Bullish" ? "is-bull" : "is-bear";

        const strength = computeStrength(info);
        const regime = computeRegime(info, strength);


        const card = document.createElement("div");
        card.className = `dashboard-card ${trendClass}`;
        card.dataset.symbol = symbol;

        card.innerHTML = `
            <div class="dash-top">
                <h3>${symbol}</h3>
                <span class="dash-pill">${info.signal}</span>
            </div>

            <div class="metric">
                <span class="dash-muted">Price</span>
                <strong>$${info.price}</strong>
            </div>

            <div class="metric">
                <span class="dash-muted">Return</span>
                <strong>${info.total_return}%</strong>
            </div>

            <div class="metric">
                <span class="dash-muted">Volatility</span>
                <strong>${info.volatility}</strong>
            </div>

        <div class="metric">
            <span class="dash-muted">Strength</span>
            <strong>${strength}/100</strong>

            <div class="strength-bar">
                <div
                    class="strength-fill"
                    style="width:${strength}%"
                    aria-label="Strength ${strength} out of 100">
                </div>
            </div>
        </div>

        <div class="metric">
            <span class="dash-muted">Regime</span>
            <strong class="regime ${regime.className}">
                ${regime.label}
            </strong>
        </div>

        <div class="view-details">View details →</div>
      `;


        grid.appendChild(card);
      });
    } catch (err) {
      console.error(err);
      grid.innerHTML =
        `<p class="dash-error">Failed to load market data.</p>`;
    }
  }

  // -----------------------------
  // CHART MODAL
  // -----------------------------
  async function openChart(symbol) {
    try {
      const url =
        `/api/series/${symbol}?period=${encodeURIComponent(currentPeriod)}`;
      const series = await fetchJSON(url);

      if (activeChart) activeChart.destroy();

      activeChart = new Chart(chartCanvas, {
        type: "line",
        data: {
          labels: series.labels,
          datasets: [
            { label: "Close", data: series.close, borderWidth: 2, pointRadius: 0 },
            { label: "MA10", data: series.ma10, borderWidth: 2, pointRadius: 0 },
            { label: "MA30", data: series.ma30, borderWidth: 2, pointRadius: 0 }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { labels: { color: "#fff" } } },
          scales: {
            x: {
              ticks: { color: "#ddd" },
              grid: { color: "rgba(255,255,255,0.06)" }
            },
            y: {
              ticks: { color: "#ddd" },
              grid: { color: "rgba(255,255,255,0.06)" }
            }
          }
        }
      });

      chartTitle.textContent =
        `${symbol} — Price & Moving Averages`;
      modal.classList.add("open");
    } catch (err) {
      console.error("Chart load failed", err);
    }
  }

  // -----------------------------
  // EVENTS
  // -----------------------------
  document.addEventListener("click", (e) => {
    const card = e.target.closest(".dashboard-card");
    if (card?.dataset.symbol) {
      openChart(card.dataset.symbol);
    }
  });

  chartClose.onclick = () => modal.classList.remove("open");
  modal.onclick = (e) => {
    if (e.target === modal) modal.classList.remove("open");
  };

  document.querySelectorAll(".dash-btn").forEach((btn) => {
    btn.onclick = () => {
      document
        .querySelectorAll(".dash-btn")
        .forEach((b) => b.classList.remove("active"));

      btn.classList.add("active");
      currentPeriod = btn.dataset.period;
      loadDashboard();
    };
  });

  // -----------------------------
  // INIT
  // -----------------------------
  loadDashboard();
})();
