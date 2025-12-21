// ============================================================
// Dashboard JS — Stable + Sorting Enabled
// ============================================================

console.log("✅ dashboard.js loaded", window.location.pathname);

(function () {
  function initDashboard() {
    console.log("✅ initDashboard() firing");

    const grid = document.getElementById("dashboardGrid");
    const modal = document.getElementById("chartModal");
    const chartTitle = document.getElementById("chartTitle");
    const chartCanvas = document.getElementById("priceChart");
    const chartClose = document.getElementById("chartClose");

    if (!grid) return;

    if (grid.dataset.bound === "1") return;
    grid.dataset.bound = "1";

    // -----------------------------
    // STATE
    // -----------------------------
    let currentPeriod = "3mo";
    let activeChart = null;

    let currentSort = null;
    let currentData = [];

    let sortDirection = "desc"; // default

    // -----------------------------
    // RESTORE SAVED PREFERENCES
    // -----------------------------
    const saved = JSON.parse(localStorage.getItem("dashboard_prefs") || "{}");

    if (saved.period) currentPeriod = saved.period;
    if (saved.sort) currentSort = saved.sort;
    if (saved.direction) sortDirection = saved.direction;

    // -----------------------------
    // STEP 3 — APPLY DEFAULT SORT IF NONE SAVED
    // -----------------------------
    if (!saved.sort && saved.period) {
        const preset = defaultSortForPeriod(saved.period);
        currentSort = preset.sort;
        sortDirection = preset.direction;
    }



    // -----------------------------
    // API
    // -----------------------------
    async function fetchJSON(url) {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      return res.json();
    }

    // -----------------------------
    // HELPERS
    // -----------------------------
    function computeStrength(info) {
      return Math.min(Math.abs(info.trend_strength || 0) * 2, 100);
    }

    function renderMarketRegime(regime) {
      const el = document.getElementById("marketRegime");
      if (!el || !regime) return;

      el.className = "market-regime";

      if (regime.label === "Risk-On") el.classList.add("risk-on");
      else if (regime.label === "Risk-Off") el.classList.add("risk-off");
      else el.classList.add("transitional");

      el.textContent = `Market Regime: ${regime.label}`;
    }
    function defaultSortForPeriod(period) {
        if (period === "5d") {
            return { sort: "strength", direction: "desc" };
        }
        if (period === "1mo") {
            return { sort: "return", direction: "desc" };
        }
        if (period === "3mo") {
            return { sort: "strength", direction: "desc" };
        }
        if (period === "6mo") {
            return { sort: "volatility", direction: "desc" };
        }
            return { sort: null, direction: "desc" };
    }


    // -----------------------------
    // DASHBOARD LOAD
    // -----------------------------
    async function loadDashboard() {
      grid.innerHTML = "";

      try {
        const payload = await fetchJSON(
          `/api/market?period=${encodeURIComponent(currentPeriod)}`
        );

        renderMarketRegime(payload.regime);

        const entries = Object.entries(payload.assets || {});

        if (entries.length === 0) {
          grid.innerHTML = `
            <div class="dash-error">
              <strong>Not enough data for this timeframe.</strong><br>
              Try 3M or 6M.
            </div>
          `;
          return;
        }

        currentData = entries.map(([symbol, info]) => ({ symbol, info }));
        renderCards();

      } catch (err) {
        console.error(err);
        grid.innerHTML = `<div class="dash-error">Failed to load data.</div>`;
      }
    }

    // -----------------------------
    // CARD RENDER + SORT
    // -----------------------------
    function renderCards() {
      grid.innerHTML = "";

      let data = [...currentData];
      const dir = sortDirection === "asc" ? 1 : -1;

      if (currentSort === "return") {
        data.sort((a, b) =>
            dir * ((a.info.total_return || 0) - (b.info.total_return || 0)))
        ;
      }

      if (currentSort === "strength") {
        data.sort((a, b) =>
            dir * (computeStrength(a.info) - computeStrength(b.info)))
        ;
      }

      if (currentSort === "volatility") {
        data.sort((a, b) =>
            dir * ((a.info.volatility || 0) - (b.info.volatility || 0)))
        ;
      }

      data.forEach(({ symbol, info }) => {
        const trendClass = info.trend === "Bullish" ? "is-bull" : "is-bear";
        const strength = Math.round(computeStrength(info));

        const card = document.createElement("div");
        card.className = `dashboard-card ${trendClass}`;
        card.dataset.symbol = symbol;

        card.onclick = () => openChart(symbol);

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
            <span class="dash-muted">Strength</span>
            <strong>${strength}/100</strong>
            <div class="strength-bar">
              <div class="strength-fill" style="width:${strength}%"></div>
            </div>
          </div>

          <div class="metric">
            <span class="dash-muted">Volatility</span>
            <strong>${info.volatility}</strong>
          </div>

          <div class="view-details">View details →</div>
        `;

        grid.appendChild(card);
      });
    }

    // -----------------------------
    // CHART MODAL
    // -----------------------------
    async function openChart(symbol) {
      try {
        const series = await fetchJSON(
          `/api/series/${symbol}?period=${encodeURIComponent(currentPeriod)}`
        );

        if (activeChart) activeChart.destroy();

        activeChart = new Chart(chartCanvas, {
          type: "line",
          data: {
            labels: series.labels,
            datasets: [
              { label: "Close", data: series.close, borderWidth: 2, pointRadius: 0 },
              { label: "MA10", data: series.ma10, borderWidth: 2, pointRadius: 0 },
              { label: "MA30", data: series.ma30, borderWidth: 2, pointRadius: 0 },
            ],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { labels: { color: "#fff" } } },
            scales: {
              x: { ticks: { color: "#ddd" } },
              y: { ticks: { color: "#ddd" } },
            },
          },
        });

        chartTitle.textContent = `${symbol} — Price & Moving Averages`;
        modal.classList.add("open");
      } catch (err) {
        console.error("Chart load failed", err);
      }
    }

    // -----------------------------
    // EVENTS
    // -----------------------------
    if (chartClose) chartClose.onclick = () => modal.classList.remove("open");
    modal.onclick = (e) => e.target === modal && modal.classList.remove("open");

    document.querySelectorAll(".dash-btn").forEach(btn => {
        btn.onclick = () => {
            document.querySelectorAll(".dash-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            currentPeriod = btn.dataset.period;

            // Apply smart default sort for this timeframe
            const preset = defaultSortForPeriod(currentPeriod);
            currentSort = preset.sort;
            sortDirection = preset.direction;

            // Update sort UI
            document.querySelectorAll(".dash-sort button").forEach(b => {
                b.classList.remove("active", "asc", "desc");
                if (b.dataset.sort === currentSort) {
                    b.classList.add("active", sortDirection);
                }
            });

            // Persist
            localStorage.setItem("dashboard_prefs", JSON.stringify({
                period: currentPeriod,
                sort: currentSort,
                direction: sortDirection
            }));

            loadDashboard();
        };

    });

    // Sort buttons (Return / Strength / Volatility)
    document.querySelectorAll(".dash-sort button").forEach(btn => {
        btn.onclick = () => {
            if (currentSort === btn.dataset.sort) {
                // Toggle direction
                sortDirection = sortDirection === "desc" ? "asc" : "desc";
            } else {
                currentSort = btn.dataset.sort;
                sortDirection = "desc";
            }

            document.querySelectorAll(".dash-sort button").forEach(b => {
                b.classList.remove("active", "asc", "desc");
            });

            btn.classList.add("active", sortDirection);

            // Save preference
            localStorage.setItem("dashboard_prefs", JSON.stringify({
                period: currentPeriod,
                sort: currentSort,
                direction: sortDirection
            }));

            renderCards();
        };
     });

    // -----------------------------
    // INIT
    // -----------------------------
    loadDashboard();
  }

  document.addEventListener("DOMContentLoaded", initDashboard);
  window.addEventListener("pageshow", initDashboard);
})();
