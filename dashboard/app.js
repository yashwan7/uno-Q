/**
 * RESq MESH // SlothMesh Tactical CAD & Leaflet Engine
 * Location: Sir M. Visvesvaraya Institute of Technology (Sir MVIT), Bengaluru
 * Coordinates: 13.151128, 77.608432
 */

// Sir MVIT Campus Focal Point
const SIR_MVIT_COORDS = [13.151128, 77.608432];

// Mesh Nodes Distributed across Sir MVIT Campus
const MESH_NODES = [
  {
    id: "GATEWAY",
    name: "Arduino UNO Q Base Station",
    role: "Central Gateway & Local Qwen 0.6B Host",
    coords: [13.151128, 77.608432], // Central Lab Block
    color: "#00ff88",
    icon: "📟"
  },
  {
    id: "NXP_M33",
    name: "NXP FRDM-MCXN236 Sentinel",
    role: "Cortex-M33 TinyML RF Classifier",
    coords: [13.152450, 77.607520], // Gate 1 / Tower Block
    color: "#00f0ff",
    icon: "🛡️"
  },
  {
    id: "ESP32_ALPHA",
    name: "ESP32 Node Alpha (Relay 1)",
    role: "Telemetry Forwarder / Mech Dept",
    coords: [13.153100, 77.609400], // Mech Block
    color: "#ffb703",
    icon: "⚡"
  },
  {
    id: "ESP32_BETA",
    name: "ESP32 Node Beta (Fringe)",
    role: "Perimeter Link / Sports Ground",
    coords: [13.149200, 77.606800], // South Perimeter
    color: "#bd00ff",
    icon: "📡"
  }
];

let mapInstance = null;
let currentTileLayer = null;
let nodeMarkers = {};
let meshPolylines = [];
let coverageCircle = null;

const TILES = {
  satellite: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
  dark: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
  osm: "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
};

document.addEventListener("DOMContentLoaded", () => {
  initTacticalMap();
  setupSimulationInterval();
});

function initTacticalMap() {
  const mapDiv = document.getElementById("cad_leaflet_map");
  if (!mapDiv) return;

  mapInstance = L.map("cad_leaflet_map", {
    center: SIR_MVIT_COORDS,
    zoom: 16,
    zoomControl: false
  });

  L.control.zoom({ position: "topright" }).addTo(mapInstance);

  // Default to Tactical Satellite Layer
  setMapLayer("satellite");

  // Add Coverage Zone around Sir MVIT
  coverageCircle = L.circle(SIR_MVIT_COORDS, {
    radius: 350,
    color: "#00f0ff",
    weight: 1,
    fillColor: "#00f0ff",
    fillOpacity: 0.06,
    dashArray: "4, 6"
  }).addTo(mapInstance);

  // Plot Tactical Nodes (Square Sharp Markers)
  MESH_NODES.forEach((n) => {
    const markerHtml = `
      <div style="
        background: #05080f; 
        border: 2px solid ${n.color}; 
        width: 32px; 
        height: 32px; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        color: #fff; 
        font-size: 15px; 
        box-shadow: 0 0 14px ${n.color};
      ">${n.icon}</div>
    `;
    const customIcon = L.divIcon({
      html: markerHtml,
      className: "tactical-node-icon",
      iconSize: [32, 32],
      iconAnchor: [16, 16]
    });

    const marker = L.marker(n.coords, { icon: customIcon }).addTo(mapInstance);
    marker.bindPopup(`
      <div style="font-family: 'JetBrains Mono', monospace; font-size: 12px; background:#05080f; color:#fff; padding:6px; border:1px solid ${n.color};">
        <b style="color:${n.color};">${n.name}</b><br>
        Role: ${n.role}<br>
        GPS: ${n.coords[0].toFixed(6)}, ${n.coords[1].toFixed(6)}<br>
        Campus: Sir MVIT, Bengaluru
      </div>
    `);
    nodeMarkers[n.id] = marker;
  });

  // Draw Initial RF Mesh Links
  drawMeshLinks("NORMAL");
}

function setMapLayer(type) {
  if (currentTileLayer) {
    mapInstance.removeLayer(currentTileLayer);
  }

  const url = TILES[type] || TILES.satellite;
  const attrib = type === "satellite" ? "Tiles &copy; Esri &mdash; Sir MVIT" : "Map tiles &copy; OpenStreetMap";

  currentTileLayer = L.tileLayer(url, {
    attribution: attrib,
    maxZoom: 19
  }).addTo(mapInstance);

  document.querySelectorAll(".map-layer-btn").forEach((btn) => btn.classList.remove("active"));
  const activeBtn = document.getElementById(`btnLayer${type.charAt(0).toUpperCase() + type.slice(1)}`);
  if (activeBtn) activeBtn.classList.add("active");
}

function drawMeshLinks(status) {
  // Clear existing lines
  meshPolylines.forEach((l) => mapInstance.removeLayer(l));
  meshPolylines = [];

  let lineColor = "#00ff88"; // Normal
  let lineDash = null;

  if (status === "DEGRADING") {
    lineColor = "#ffb703";
    lineDash = "6, 6";
  } else if (status === "CRITICAL" || status === "TIMEOUT") {
    lineColor = "#ff3366";
    lineDash = "3, 6";
  }

  // Links: NXP -> Gateway, ESP32 Alpha -> Gateway, ESP32 Beta -> Gateway
  const links = [
    [MESH_NODES[1].coords, MESH_NODES[0].coords],
    [MESH_NODES[2].coords, MESH_NODES[0].coords],
    [MESH_NODES[3].coords, MESH_NODES[0].coords]
  ];

  links.forEach((pts) => {
    const pl = L.polyline(pts, {
      color: lineColor,
      weight: 2,
      opacity: 0.85,
      dashArray: lineDash
    }).addTo(mapInstance);
    meshPolylines.push(pl);
  });
}

/**
 * Scenario Injector for Live Hackathon Demonstrations
 */
function injectScenario(type) {
  document.querySelectorAll(".tactical-btn").forEach((b) => b.classList.remove("active"));

  const now = new Date().toTimeString().split(" ")[0];
  const body = document.getElementById("consoleBody");

  if (type === "normal") {
    document.querySelectorAll(".tactical-btn")[0].classList.add("active");
    updateUI("NORMAL", -62.0, 24.0, 1.0, 0, 18, 6.0, "CONTINUE_NORMAL_OPERATION", "All metrics within optimal NOUL bounds. Zero packet loss.", true,
      { latency: "0.08s · VALID", action: "CONTINUE_NORMAL_OPERATION", status: "VALID" },
      { latency: "1.82s · CoT VALID", causal: "All RF metrics nominal. Paced energy preservation active." },
      "100% UNANIMOUS"
    );
    drawMeshLinks("NORMAL");
    addLog(`[${now}] 🌞 Scenario: Quiet Sunshine nominal link restored across Sir MVIT campus.`, "normal");
  } else if (type === "degrading") {
    document.querySelectorAll(".tactical-btn")[1].classList.add("active");
    updateUI("DEGRADING", -82.0, 9.0, 28.0, 4, 62, 38.0, "SWITCH_DIVERSITY_ANTENNA", "Multipath fading & 38ms jitter detected by M33. Toggled diversity antenna pin (GPIO 4).", true,
      { latency: "0.14s · VALID", action: "SWITCH_DIVERSITY_ANTENNA", status: "VALID" },
      { latency: "1.95s · CoT VALID", causal: "Multipath fading & delay spread at Sir MVIT perimeter resolved by antenna diversity." },
      "100% UNANIMOUS"
    );
    drawMeshLinks("DEGRADING");
    addLog(`[${now}] 🌧️ Scenario: Rain Fade / Jitter spike detected. Laya switched diversity antenna.`, "warning");
    addLog(`[${now}] ⚡ SmolLM2 135M [0.14s]: Rapid triage classified link as DEGRADING.`, "info");
    addLog(`[${now}] 🧠 Qwen3 0.6B [1.95s]: Physical cause verified as multipath ground reflections.`, "info");
  } else if (type === "critical") {
    document.querySelectorAll(".tactical-btn")[2].classList.add("active");
    updateUI("CRITICAL", -95.0, 2.0, 74.0, 9, 91, 120.0, "TRIGGER_CHANNEL_FAILOVER", "Severe RF jamming & 74% packet collapse. Laya executed emergency channel hop (Ch 6 -> 11).", false,
      { latency: "0.11s · OVERRULED", action: "CONTINUE_NORMAL (OVERRULED)", status: "OVERRULED" },
      { latency: "1.78s · CoT VALID", causal: "Co-channel interference collapse confirmed. Channel shifted to 11." },
      "HARD_OVERRIDE"
    );
    drawMeshLinks("CRITICAL");
    addLog(`[${now}] ⚡ Scenario: RF Jamming / Link Collapse detected at Gate 1.`, "critical");
    addLog(`[${now}] ⚠️ SmolLM proposed CONTINUE -> OVERRULED by Laya System-1 NOULs.`, "warning");
    addLog(`[${now}] 🛡️ Laya executed binding emergency Channel Hop (Ch 6 -> 11).`, "critical");
  } else if (type === "timeout") {
    document.querySelectorAll(".tactical-btn")[3].classList.add("active");
    updateUI("TIMEOUT_CRITICAL", -105.0, 0.0, 100.0, 12, 100, 200.0, "TRIGGER_CHANNEL_FAILOVER", "Node-01 missed heartbeat (>3.5s). Marked unreachable by UNO Q sentinel.", true,
      { latency: "0.05s · TIMEOUT", action: "TRIGGER_FAILOVER", status: "VALID" },
      { latency: "1.45s · TIMEOUT", causal: "Transceiver silence exceeded 3.5s safety threshold." },
      "NOUL_OVERRIDE"
    );
    drawMeshLinks("CRITICAL");
    addLog(`[${now}] 🚨 ALERT: Node-01 heartbeat timeout exceeded (3.5s) at Gate 1 Tower!`, "critical");
  }
}

function updateUI(status, rssi, snr, per, retries, busy, jitter, action, cause, llmValid, smollm, qwen, consensus) {
  // KPI Header
  const kpi1 = document.getElementById("kpiNode1Status");
  kpi1.textContent = status;
  kpi1.className = `kpi-status ${status === "NORMAL" ? "green-text" : status === "DEGRADING" ? "yellow-text" : "red-text"}`;
  document.getElementById("kpiNode1Rssi").textContent = `${rssi.toFixed(0)} dBm`;

  document.getElementById("kpiLayaAction").textContent = action.replace(/_/g, " ");

  // Matrix Gauges
  document.getElementById("dispRssi").innerHTML = `${rssi.toFixed(1)} <small>dBm</small>`;
  document.getElementById("dispSnr").innerHTML = `${snr.toFixed(1)} <small>dB</small>`;
  document.getElementById("dispPer").innerHTML = `${per.toFixed(1)} <small>%</small>`;
  document.getElementById("dispRetries").innerHTML = `${retries} <small>pkts</small>`;
  document.getElementById("dispBusy").innerHTML = `${busy} <small>%</small>`;
  document.getElementById("dispJitter").innerHTML = `${jitter.toFixed(1)} <small>ms</small>`;

  // Badges
  const badgeClass = status === "NORMAL" ? "badge-normal" : status === "DEGRADING" ? "badge-warning" : "badge-critical";
  document.getElementById("badgeRssi").className = `m-badge ${badgeClass}`;
  document.getElementById("badgeRssi").textContent = rssi > -75 ? "NOMINAL" : rssi > -88 ? "DEGRADED" : "CRITICAL";

  // Dual-Model Elements
  if (smollm) {
    const smLat = document.getElementById("dispSmollmLatency");
    if (smLat) {
      smLat.textContent = smollm.latency;
      smLat.className = `m-badge ${smollm.status === "VALID" ? "badge-normal" : "badge-critical"}`;
    }
    const smAct = document.getElementById("dispSmollmAction");
    if (smAct) smAct.textContent = smollm.action;
  }

  if (qwen) {
    const qwLat = document.getElementById("dispQwenLatency");
    if (qwLat) qwLat.textContent = qwen.latency;
    const qwCau = document.getElementById("dispQwenCausal");
    if (qwCau) qwCau.textContent = qwen.causal;
  }

  const consBadge = document.getElementById("auditConsensusBadge");
  if (consBadge && consensus) {
    consBadge.textContent = consensus;
    consBadge.style.color = consensus.includes("UNANIMOUS") ? "var(--accent-green)" : consensus.includes("HARD") ? "var(--accent-red)" : "var(--accent-yellow)";
  }

  // Audit Box
  const auditAct = document.getElementById("auditAction");
  if (auditAct) {
    auditAct.textContent = action;
    auditAct.className = `a-val ${status === "NORMAL" ? "green-text" : status === "DEGRADING" ? "yellow-text" : "red-text"}`;
  }
  const auditC = document.getElementById("auditCause");
  if (auditC) auditC.textContent = cause;
}

function addLog(msg, type) {
  const body = document.getElementById("consoleBody");
  const line = document.createElement("div");
  line.className = `c-line ${type}`;
  line.textContent = msg;
  body.appendChild(line);
  body.scrollTop = body.scrollHeight;
}

function clearConsole() {
  document.getElementById("consoleBody").innerHTML = "";
}

function setupSimulationInterval() {
  // Subtle real-world jitter fluctuation on normal link
  setInterval(() => {
    const kpiStatus = document.getElementById("kpiNode1Status").textContent;
    if (kpiStatus === "NORMAL") {
      const fluc = (Math.random() * 2 - 1).toFixed(1);
      const curRssi = -62.0 + parseFloat(fluc);
      document.getElementById("dispRssi").innerHTML = `${curRssi.toFixed(1)} <small>dBm</small>`;
    }
  }, 2500);
}
