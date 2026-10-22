#!/usr/bin/env python3
"""
🦥 SlothMesh: Edge SLM Telemetry Verification & Factual Benchmark Harness
Target: Local Open-Weight Models on Arduino UNO Q (Ollama / Qualcomm AI Hub / Llama.cpp)

Challenge: Hacktoberfest 2026 Open-Source AI Challenge - "Slow and Steady"

Evaluates:
1. Strict Factual Faithfulness: Checks if the SLM invents hallucinated numbers.
2. Metric Comprehensiveness: Ensures all degraded RF telemetry metrics are addressed.
3. Decision Alignment: Verifies recommendation strictly mirrors the fixed TinyML state.
4. Response Latency: Measures execution time on low-power hardware.
"""

import os
import sys
import json
import re
import time
import requests

SCENARIOS_FILE = os.path.join(os.path.dirname(__file__), "scenarios.json")
RESULTS_OUTPUT = os.path.join(os.path.dirname(__file__), "benchmark_results.json")

SEVERITY = {
    "HEALTHY": "low",
    "DEGRADING": "medium",
    "CRITICAL": "high"
}

DECISION = {
    "HEALTHY": "CONTINUE_NORMAL_OPERATION",
    "DEGRADING": "MONITOR_AND_EVALUATE_FAILOVER",
    "CRITICAL": "TRIGGER_FAILOVER"
}

MUST_SAY = {
    "HEALTHY": "normal",
    "DEGRADING": "failover",
    "CRITICAL": "failover"
}

ORDER = [
    ("signal-to-noise", "SNR"), ("snr", "SNR"),
    ("rssi", "RSSI"), ("signal", "RSSI"),
    ("packet error", "Packet error rate"), ("error rate", "Packet error rate"),
    ("retr", "Retries"),
    ("busy", "Channel busy ratio"),
    ("jitter", "Jitter")
]

WORDS = {
    "RSSI": ["rssi", "signal"],
    "SNR": ["snr", "noise"],
    "Packet error rate": ["packet", "error"],
    "Retries": ["retr"],
    "Channel busy ratio": ["busy", "channel"],
    "Jitter": ["jitter"]
}

def load_scenarios():
    with open(SCENARIOS_FILE, "r") as f:
        return json.load(f)

def facts(s):
    return {
        "RSSI": (f"{s['rssi']} dBm", "weak" if s["rssi"] < -80 else "ok"),
        "SNR": (f"{s['snr']} dB", "low" if s["snr"] < 10 else "ok"),
        "Packet error rate": (s["per"], "high" if s["per"] > 0.1 else "ok"),
        "Retries": (s["retries"], "elevated" if s["retries"] >= 3 else "ok"),
        "Channel busy ratio": (s["busy"], "high" if s["busy"] > 0.5 else "ok"),
        "Jitter": (f"{s['jitter']} ms", "elevated" if s["jitter"] > 30 else "ok"),
    }

def check_hallucinations(s, out, F):
    text = out["reason"] + " " + out["recommendation"]
    low = text.lower()
    flags = []

    # Numbers in telemetry that are permitted
    allowed = set(re.findall(r"\d+(?:\.\d+)?", " ".join(str(v[0]) for v in F.values())))

    # Extract all numbers from generated text and check against telemetry
    for x in re.findall(r"\d+(?:\.\d+)?", text):
        if x not in allowed:
            flags.append(f"Number not in telemetry: {x}")

    # Check if any abnormal metric was omitted
    for n, (v, lab) in F.items():
        if lab != "ok" and not any(w in low for w in WORDS[n]):
            flags.append(f"Omits abnormal metric: {n} ({lab})")

    # Check if recommendation has required decision keyword
    if MUST_SAY[s["cls"]] not in low:
        flags.append(f"Recommendation lacks required keyword '{MUST_SAY[s['cls']]}'")

    return flags

SCHEMA = {
    "type": "object",
    "properties": {
        "reason": {"type": "string"},
        "recommendation": {"type": "string"}
    },
    "required": ["reason", "recommendation"]
}

def ask_ollama(model, prompt):
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "format": SCHEMA,
        "stream": False,
        "options": {"temperature": 0.0}
    }
    r = requests.post("http://localhost:11434/api/chat", json=payload, timeout=60)
    r.raise_for_status()
    content = r.json()["message"]["content"]
    return json.loads(content)

def run_benchmark(models):
    print("=" * 70)
    print(" 🦥 SlothMesh: Local Open-Weight SLM Edge Telemetry Benchmark")
    print("=" * 70)

    scenarios = load_scenarios()
    results = {}

    for model in models:
        print(f"\n--> Benchmarking Model: {model}")
        try:
            ask_ollama(model, 'Reply with {"reason":"ok","recommendation":"ok"}')
        except Exception as e:
            print(f"    [Warning] Could not connect to Ollama for {model}: {e}")
            print(f"    (Make sure `ollama serve` is running on localhost:11434)")
            continue

        rows = []
        for s in scenarios:
            F = facts(s)
            ft = "\n".join(f"- {k}: {v} ({lab})" for k, (v, lab) in F.items())

            prompt = f"""You are the SlothMesh autonomous network sentinel assistant.
Explain this edge RF event in simple, calm language in 2-3 sentences.
Use ONLY the facts below, with their exact labels.
Never call a metric good, stable, acceptable, or minimal unless its label is "ok".
Do not invent numbers. Do not change the fixed decision.

Facts:
{ft}

TinyML Cortex-M33 Classifier Output: {s['cls']}
Decision (Fixed): {DECISION[s['cls']]}

Write JSON with "reason" and "recommendation". The recommendation must restate the fixed decision in plain words."""

            t0 = time.time()
            try:
                out = ask_ollama(model, prompt)
                secs = time.time() - t0
                out["severity"] = SEVERITY[s["cls"]]
                flags = check_hallucinations(s, out, F)
                rows.append({
                    "scenario": s["id"],
                    "scenario_name": s["name"],
                    "secs": round(secs, 2),
                    "flags": flags,
                    "output": out
                })
                flag_str = f"{len(flags)} issues" if flags else "✅ CLEAN"
                print(f"    {s['id']:32} {flag_str:12} {secs:.2f}s")
                for fl in flags:
                    print(f"       ⚠️  {fl}")
            except Exception as e:
                print(f"    Error evaluating {s['id']}: {e}")

        results[model] = rows

    print("\n" + "=" * 70)
    print(" 📊 BENCHMARK SUMMARY TABLE")
    print(f" {'Model':15} | {'Clean / 8':10} | {'Total Flags':12} | {'Avg Latency':12}")
    print("-" * 60)
    for m, rows in results.items():
        if not rows:
            continue
        clean = sum(1 for r in rows if not r["flags"])
        tot_flags = sum(len(r["flags"]) for r in rows)
        avg_time = sum(r["secs"] for r in rows) / len(rows)
        print(f" {m:15} | {clean}/8       | {tot_flags:12} | {avg_time:10.2f}s")
    print("=" * 70)

    with open(RESULTS_OUTPUT, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved detailed results to {RESULTS_OUTPUT}")
    return results

if __name__ == "__main__":
    target_models = sys.argv[1:] or ["qwen3:0.6b", "qwen3:4b"]
    run_benchmark(target_models)
