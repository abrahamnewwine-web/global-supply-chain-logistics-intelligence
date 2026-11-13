const charts = {};
Chart.defaults.animation = false;

function upsert(id, cfg) {
  if (charts[id]) charts[id].destroy();
  charts[id] = new Chart(document.getElementById(id).getContext("2d"), cfg);
}

function getQs() {
  const qs = new URLSearchParams();
  const pairs = [
    ["year", "fYear"], ["quarter", "fQuarter"], ["month", "fMonth"],
    ["origin_port", "fOrigin"], ["transport_mode", "fMode"],
    ["product_category", "fCat"], ["weather_condition", "fWeather"],
  ];
  pairs.forEach(([k, id]) => {
    const v = document.getElementById(id).value;
    if (v && v !== "All") qs.set(k, v);
  });
  return qs;
}

async function refresh() {
  const res = await fetch(`/api/dashboard?${getQs().toString()}`);
  const d = await res.json();
  const k = d.kpis;

  document.getElementById("kTotal").textContent = k.total_shipments.toLocaleString();
  document.getElementById("kVolMom").textContent = `${k.volume_mom_pct >= 0 ? "+" : ""}${k.volume_mom_pct}% MoM volume`;
  document.getElementById("kDisrupt").textContent = `${k.disruption_rate_pct.toFixed(2)}%`;
  document.getElementById("kDisMom").textContent = `${k.disrupted_shipments.toLocaleString()} disrupted`;
  document.getElementById("kSuccess").textContent = `${k.success_rate_pct.toFixed(2)}%`;
  document.getElementById("kSuccessCnt").textContent = `${k.successful_shipments.toLocaleString()} on-time`;
  document.getElementById("kLead").textContent = `${k.avg_lead_time_days.toFixed(2)} Days`;
  document.getElementById("kReliable").textContent = k.reliable_shipments >= 1000 ? `${(k.reliable_shipments / 1000).toFixed(2)}K` : k.reliable_shipments;
  document.getElementById("kRelPct").textContent = `${k.carrier_reliability_pct.toFixed(1)}% compliant`;
  document.getElementById("kRiskIdx").textContent = k.avg_risk_index.toFixed(2);
  document.getElementById("kFuel").textContent = `$${k.avg_fuel_price_usd.toFixed(2)}`;
  document.getElementById("kHighRiskPct").textContent = `${k.high_risk_rate_pct.toFixed(2)}%`;
  document.getElementById("kHighRiskCnt").textContent = `${k.high_risk_shipments.toLocaleString()} high-risk`;

  const topWeather = d.by_weather[0] ? d.by_weather[0].weather_condition : "N/A";
  const crit = d.critical_route;
  document.getElementById("insMomentum").textContent = `${k.total_shipments.toLocaleString()} shipments analyzed; latest monthly volume shift ${k.volume_mom_pct >= 0 ? "+" : ""}${k.volume_mom_pct}%.`;
  document.getElementById("insDisruption").textContent = `${k.disruption_rate_pct.toFixed(2)}% disruption rate led by ${topWeather} conditions (${k.disruption_mom_pp >= 0 ? "+" : ""}${k.disruption_mom_pp} pp MoM).`;
  document.getElementById("insPerformance").textContent = `Success rate stands at ${k.success_rate_pct.toFixed(2)}% with ${k.carrier_reliability_pct.toFixed(1)}% carrier reliability and ${k.avg_lead_time_days.toFixed(2)}d avg lead time.`;
  document.getElementById("insRisk").textContent = crit ? `${k.high_risk_rate_pct.toFixed(2)}% high-risk exposure; critical lane ${crit.route_name} averages ${crit.avg_risk_index} risk.` : "No matching corridors.";

  const activeFilters = Object.entries(d.filters).filter(([, v]) => v !== null && v !== "All").map(([key, v]) => `${key}=${v}`);
  document.getElementById("scopeTag").textContent = activeFilters.length ? `Scope: ${activeFilters.join(" · ")}` : "Scope: All 5,000 Shipments (2024–2025)";

  // Trends
  const mt = d.monthly_trends;
  upsert("cVolTrend", {
    type: "line",
    data: { labels: mt.map(r => r.year_month), datasets: [{ label: "Shipments", data: mt.map(r => r.total_shipments), borderColor: "#38bdf8", tension: 0.35, pointRadius: 2 }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { ticks: { color: "#94a3b8", font: { size: 9 } }, grid: { display: false } }, y: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(148,163,184,0.12)" } } } },
  });
  upsert("cDisTrend", {
    type: "line",
    data: { labels: mt.map(r => r.year_month), datasets: [{ label: "Disruption %", data: mt.map(r => r.disruption_rate_pct), borderColor: "#ef4444", tension: 0.35, pointRadius: 2 }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { ticks: { color: "#94a3b8", font: { size: 9 } }, grid: { display: false } }, y: { ticks: { color: "#94a3b8", callback: v => `${v}%` }, grid: { color: "rgba(148,163,184,0.12)" } } } },
  });

  // 4 mid charts
  upsert("cMode", {
    type: "bar",
    data: { labels: d.by_transport_mode.map(r => r.transport_mode), datasets: [{ data: d.by_transport_mode.map(r => r.shipment_volume), backgroundColor: ["#38bdf8", "#22c55e", "#eab308", "#7e22ce"] }] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { ticks: { color: "#e2e8f0" }, grid: { display: false } }, y: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(148,163,184,0.12)" } } } },
  });
  upsert("cCategory", {
    type: "bar",
    data: { labels: d.by_product_category.map(r => r.category_name), datasets: [{ data: d.by_product_category.map(r => r.shipment_volume), backgroundColor: "#3b82f6" }] },
    options: { indexAxis: "y", responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(148,163,184,0.12)" } }, y: { ticks: { color: "#e2e8f0", font: { size: 10.5 } }, grid: { display: false } } } },
  });
  upsert("cWeather", {
    type: "bar",
    data: { labels: d.by_weather.map(r => r.weather_condition), datasets: [{ data: d.by_weather.map(r => r.disrupted_shipments), backgroundColor: "#dc2626" }] },
    options: { indexAxis: "y", responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(148,163,184,0.12)" } }, y: { ticks: { color: "#e2e8f0", font: { size: 10.5 } }, grid: { display: false } } } },
  });
  upsert("cRegion", {
    type: "bar",
    data: { labels: d.by_region.map(r => r.region), datasets: [{ data: d.by_region.map(r => r.total_shipments), backgroundColor: ["#7e22ce", "#22c55e", "#eab308", "#a855f7"] }] },
    options: { indexAxis: "y", responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { ticks: { color: "#94a3b8" }, grid: { color: "rgba(148,163,184,0.12)" } }, y: { ticks: { color: "#e2e8f0", font: { size: 10.5 } }, grid: { display: false } } } },
  });

  // Table & Critical Route
  document.getElementById("routesBody").innerHTML = d.top_routes.map(r => `
    <tr><td>${r.route_name}</td><td>${r.total_shipments}</td><td>${r.avg_risk_index.toFixed(2)}</td><td>${r.avg_lead_time_days.toFixed(2)}</td><td>${r.disruption_rate_pct.toFixed(1)}%</td></tr>
  `).join("");

  if (crit) {
    document.getElementById("critRouteName").textContent = crit.route_name;
    document.getElementById("critRisk").textContent = crit.avg_risk_index.toFixed(2);
    document.getElementById("critDisrupt").textContent = `${crit.disruption_rate_pct.toFixed(2)}%`;
    document.getElementById("critLead").textContent = crit.avg_lead_time_days.toFixed(2);
    document.getElementById("critRegionNote").textContent = `${crit.region} Corridor · ${crit.total_shipments} shipments`;
  }

  upsert("cHighRiskGauge", {
    type: "doughnut",
    data: { datasets: [{ data: [k.high_risk_rate_pct, Math.max(0, 100 - k.high_risk_rate_pct)], backgroundColor: ["#dc2626", "#1e293b"], borderWidth: 0 }] },
    options: { responsive: true, maintainAspectRatio: false, rotation: -90, circumference: 180, cutout: "70%", plugins: { legend: { display: false }, tooltip: { enabled: false } } },
  });
}

["fYear", "fQuarter", "fMonth", "fOrigin", "fMode", "fCat", "fWeather"].forEach(id => {
  document.getElementById(id).addEventListener("change", refresh);
});
document.getElementById("btnReset").addEventListener("click", () => {
  ["fYear", "fQuarter", "fMonth"].forEach(id => document.getElementById(id).value = "");
  ["fOrigin", "fMode", "fCat", "fWeather"].forEach(id => document.getElementById(id).value = "All");
  refresh();
});
document.getElementById("btnExport").addEventListener("click", () => {
  window.location.href = `/api/export/routes-csv?${getQs().toString()}`;
});
window.addEventListener("DOMContentLoaded", refresh);
