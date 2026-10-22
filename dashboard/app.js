/**
 * 🦥 SlothMesh Interactive Dashboard Application Logic
 * Implements real-time edge RF telemetry simulation, dual-core pipeline visualization,
 * and autonomous open-weight model actuation logs.
 */

const SCENARIOS = [
  {
    id: "s01",
    name: "🌞 Quiet Sunshine",
    sub: "Healthy Link | Clear RF",
    rssi: -55,
    snr: 30,
    per: 1.0,
    retries: 0,
    busy: 15,
    jitter: 5,
    cls: "HEALTHY",
    action: "Remain in Sloth Sleep (35 µA)",
    analysis: "RF link is pristine. Zero packet loss or channel contention. Conserving maximum battery.",
    pipe1: "HEALTHY (Sleep Pacing: 5.0s)",
    pipe2: "Standby (Host SoC Undisturbed)",
    pipe3: "Channel 6 | Diversity Ant 0 (Nominal)"
  },
  {
    id: "s02",
    name: "🌧️ Rain Fade & Multipath",
    sub: "Degrading | High Jitter",
    rssi: -84,
    snr: 8,
    per: 31.0,
    retries: 4,
    busy: 62,
    jitter: 42,
    cls: "DEGRADING",
    action: "Autonomous Diversity Antenna Switch (GPIO 4)",
    analysis: "Multipath attenuation and jitter (42ms) detected by M33. Switched physical diversity antenna to recover gain.",
    pipe1: "DEGRADING (Interrupt Host)",
    pipe2: "Qwen 0.6B Active (Causal Diagnosis in 1.82s)",
    pipe3: "Actuated: Diversity Ant 1 Active"
  },
  {
    id: "s03",
    name: "⚡ RF Blackout / Jam",
    sub: "Critical | Imminent Drop",
    rssi: -95,
    snr: 2,
    per: 72.0,
    retries: 9,
    busy: 91,
    jitter: 120,
    cls: "CRITICAL",
    action: "Emergency Channel Hop (Ch 6 -> 11)",
    analysis: "Co-channel collision storm and extreme packet loss (72%). Executed seamless channel hop to Channel 11. Zero human reboots required.",
    pipe1: "CRITICAL (Immediate Failover Trigger)",
    pipe2: "Local SLM Reasoned: Frequency Jam Confirmed",
    pipe3: "Hopped: Mesh Synchronized on Channel 11"
  },
  {
    id: "s04",
    name: "👥 Channel Congestion",
    sub: "Degrading | 85% Occupancy",
    rssi: -60,
    snr: 25,
    per: 2.0,
    retries: 1,
    busy: 85,
    jitter: 18,
    cls: "DEGRADING",
    action: "Sloth Backoff Pacing Adjusted",
    analysis: "RF signal is strong (-60 dBm), but channel occupancy is saturated at 85%. Tuned carrier-sense threshold and paced transmissions.",
    pipe1: "DEGRADING (Channel Congestion)",
    pipe2: "Open SLM Computed: Paced Backoff Window",
    pipe3: "Active: Adaptive Clear-Channel Assessment"
  }
];

let activeScenarioIndex = 0;

document.addEventListener("DOMContentLoaded", () => {
  renderScenarioButtons();
  setupEventListeners();
  loadScenario(0);
});

function renderScenarioButtons() {
  const container = document.getElementById("scenarioButtons");
  container.innerHTML = "";

  SCENARIOS.forEach((sc, idx) => {
    const btn = document.createElement("button");
    btn.className = `scenario-btn ${idx === activeScenarioIndex ? "active" : ""}`;
    btn.innerHTML = `
      <div class="scenario-btn-title">${sc.name}</div>
      <div class="scenario-btn-sub">${sc.sub}</div>
    `;
    btn.addEventListener("click", () => loadScenario(idx));
    container.appendChild(btn);
  });
}

function loadScenario(index) {
  activeScenarioIndex = index;
  const sc = SCENARIOS[index];

  // Update button active state
  document.querySelectorAll(".scenario-btn").forEach((b, i) => {
    b.classList.toggle("active", i === index);
  });

  // Update telemetry values
  updateTelemetryUI(sc.rssi, sc.snr, sc.per, sc.retries, sc.busy, sc.jitter);

  // Update Sliders
  document.getElementById("sliderRssi").value = sc.rssi;
  document.getElementById("lblRssi").textContent = `${sc.rssi} dBm`;
  document.getElementById("sliderJitter").value = sc.jitter;
  document.getElementById("lblJitter").textContent = `${sc.jitter} ms`;

  // Update Sloth State and Pipeline
  updateSlothState(sc);
  updatePipeline(sc);

  // Log to terminal
  logToTerminal(sc);
}

function updateTelemetryUI(rssi, snr, per, retries, busy, jitter) {
  document.getElementById("valRssi").innerHTML = `${rssi} <span class="unit">dBm</span>`;
  document.getElementById("valSnr").innerHTML = `${snr} <span class="unit">dB</span>`;
  document.getElementById("valPer").innerHTML = `${per.toFixed(1)} <span class="unit">%</span>`;
  document.getElementById("valRetries").innerHTML = `${retries} <span class="unit">pkts</span>`;
  document.getElementById("valBusy").innerHTML = `${busy} <span class="unit">%</span>`;
  document.getElementById("valJitter").innerHTML = `${jitter} <span class="unit">ms</span>`;

  // Badge updates
  setBadge("badgeRssi", rssi > -75 ? "Optimal" : rssi > -85 ? "Fair" : "Weak", rssi > -75 ? "optimal" : rssi > -85 ? "warning" : "critical");
  setBadge("badgeSnr", snr > 15 ? "Strong" : snr > 8 ? "Moderate" : "Poor", snr > 15 ? "optimal" : snr > 8 ? "warning" : "critical");
  setBadge("badgePer", per < 5 ? "Minimal" : per < 25 ? "Elevated" : "Severe", per < 5 ? "optimal" : per < 25 ? "warning" : "critical");
  setBadge("badgeRetries", retries < 2 ? "Clean" : retries < 5 ? "Retrying" : "High", retries < 2 ? "optimal" : retries < 5 ? "warning" : "critical");
  setBadge("badgeBusy", busy < 40 ? "Quiet" : busy < 70 ? "Moderate" : "Congested", busy < 40 ? "optimal" : busy < 70 ? "warning" : "critical");
  setBadge("badgeJitter", jitter < 15 ? "Stable" : jitter < 40 ? "Jittery" : "Spike", jitter < 15 ? "optimal" : jitter < 40 ? "warning" : "critical");
}

function setBadge(id, text, type) {
  const el = document.getElementById(id);
  el.textContent = text;
  el.className = `gauge-badge badge-${type}`;
}

function updateSlothState(sc) {
  const avatar = document.getElementById("slothAvatar");
  const title = document.getElementById("slothStateTitle");
  const sub = document.getElementById("slothStateSub");
  const energy = document.getElementById("energySavedMetric");

  if (sc.cls === "HEALTHY") {
    avatar.textContent = "😴";
    title.textContent = "Low-Power Sloth Nap";
    title.className = "sloth-state-title green-text";
    sub.textContent = "Cortex-M33 in deep standby (35 µA). 99% CPU idle. Conserving maximum energy.";
    energy.textContent = "94.8%";
  } else if (sc.cls === "DEGRADING") {
    avatar.textContent = "🥱";
    title.textContent = "Autonomous Self-Healing";
    title.className = "sloth-state-title";
    title.style.color = "var(--accent-yellow)";
    sub.textContent = "Sub-system alerted. Local SLM executed physical antenna diversity switch.";
    energy.textContent = "91.2%";
  } else {
    avatar.textContent = "⚡";
    title.textContent = "Autonomous Channel Failover";
    title.className = "sloth-state-title";
    title.style.color = "var(--accent-red)";
    sub.textContent = "Host SLM executed seamless channel hop. User didn't touch a single button.";
    energy.textContent = "88.6%";
  }
}

function updatePipeline(sc) {
  const s1 = document.getElementById("stage1Status");
  const s2 = document.getElementById("stage2Status");
  const s3 = document.getElementById("stage3Status");

  s1.textContent = `Status: ${sc.pipe1}`;
  s2.textContent = `Host: ${sc.pipe2}`;
  s3.textContent = `Action: ${sc.pipe3}`;

  document.getElementById("pipeStage1").classList.toggle("active", true);
  document.getElementById("pipeStage2").classList.toggle("active", sc.cls !== "HEALTHY");
  document.getElementById("pipeStage3").classList.toggle("active", sc.cls !== "HEALTHY");
}

function logToTerminal(sc) {
  const body = document.getElementById("terminalBody");
  const now = new Date().toTimeString().split(" ")[0];

  const log1 = document.createElement("div");
  log1.className = `log-line ${sc.cls === "HEALTHY" ? "success" : sc.cls === "DEGRADING" ? "warn" : "critical"}`;
  log1.textContent = `[${now}] 📡 Cortex-M33 TinyML: Class ${sc.cls} (RSSI=${sc.rssi}dBm, PER=${sc.per}%, Jitter=${sc.jitter}ms)`;
  body.appendChild(log1);

  const log2 = document.createElement("div");
  log2.className = "log-line info";
  log2.textContent = `[${now}] 🧠 Open-Weight SLM: ${sc.analysis}`;
  body.appendChild(log2);

  const log3 = document.createElement("div");
  log3.className = "log-line success";
  log3.textContent = `[${now}] 🦥 Autonomous Actuation: ${sc.action} | Human effort: 0 min`;
  body.appendChild(log3);

  body.scrollTop = body.scrollHeight;
}

function setupEventListeners() {
  // Clear log
  document.getElementById("btnClearLog").addEventListener("click", () => {
    document.getElementById("terminalBody").innerHTML = "";
  });

  // Slider RSSI
  document.getElementById("sliderRssi").addEventListener("input", (e) => {
    const val = parseInt(e.target.value);
    document.getElementById("lblRssi").textContent = `${val} dBm`;
    customInference();
  });

  // Slider Jitter
  document.getElementById("sliderJitter").addEventListener("input", (e) => {
    const val = parseInt(e.target.value);
    document.getElementById("lblJitter").textContent = `${val} ms`;
    customInference();
  });

  // Tab switching
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      e.target.classList.add("active");

      const tab = e.target.getAttribute("data-tab");
      document.getElementById("tabSummary").style.display = tab === "summary" ? "block" : "none";
      document.getElementById("tabDetails").style.display = tab === "details" ? "block" : "none";
    });
  });
}

function customInference() {
  const rssi = parseInt(document.getElementById("sliderRssi").value);
  const jitter = parseInt(document.getElementById("sliderJitter").value);

  let cls = "HEALTHY";
  if (rssi < -88 || jitter > 80) {
    cls = "CRITICAL";
  } else if (rssi < -78 || jitter > 30) {
    cls = "DEGRADING";
  }

  const simulatedSc = {
    name: "Custom Realtime Adjustment",
    sub: `RSSI: ${rssi}dBm | Jitter: ${jitter}ms`,
    rssi: rssi,
    snr: Math.max(2, Math.round(30 + (rssi + 55) * 0.5)),
    per: Math.min(85, Math.max(1, Math.round((rssi < -80 ? 30 : 2) + jitter * 0.3))),
    retries: rssi < -85 ? 6 : rssi < -75 ? 3 : 0,
    busy: rssi < -80 ? 75 : 25,
    jitter: jitter,
    cls: cls,
    action: cls === "CRITICAL" ? "Trigger Immediate Channel Failover" : cls === "DEGRADING" ? "Adjust Diversity Antenna" : "Conserve Power in Sleep",
    analysis: `Dynamic user telemetry injected. Model classified state as ${cls}. Handled autonomously with zero human intervention.`,
    pipe1: `${cls} (Inference: 1.18 ms)`,
    pipe2: cls === "HEALTHY" ? "Standby" : "Causal Explanation Generated",
    pipe3: cls === "CRITICAL" ? "Channel Hop Executed" : cls === "DEGRADING" ? "Antenna Switched" : "Nominal"
  };

  updateTelemetryUI(simulatedSc.rssi, simulatedSc.snr, simulatedSc.per, simulatedSc.retries, simulatedSc.busy, simulatedSc.jitter);
  updateSlothState(simulatedSc);
  updatePipeline(simulatedSc);
}
