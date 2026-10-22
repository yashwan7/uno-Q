"""
Laya System-1 NOULs: Deterministic Network Safety & Decision Engine
Runs on: Arduino UNO Q (Linux Application Processor)

Purpose:
A deterministic, rule-governed safety layer. While open-weight LLMs (Qwen/SmolLM)
provide causal explanations and triage suggestions, Laya enforces absolute safety invariant rules.
No model recommendation can bypass these deterministic bounds.
"""

from typing import Dict, Any, Optional, Tuple

class LayaSafetyEngine:
    # Strict Network Operational Utility Limits (NOULs)
    RSSI_CRITICAL = -88.0    # dBm
    RSSI_DEGRADING = -78.0   # dBm
    SNR_CRITICAL = 6.0       # dB
    SNR_DEGRADING = 12.0     # dB
    PER_CRITICAL = 0.40      # 40% packet error rate
    PER_DEGRADING = 0.15     # 15% packet error rate
    RETRIES_DEGRADING = 3    # Frame retries
    RETRIES_CRITICAL = 7
    JITTER_DEGRADING = 35.0  # ms
    JITTER_CRITICAL = 90.0   # ms

    # Allowed Deterministic Actions
    ACTION_CONTINUE = "CONTINUE_NORMAL_OPERATION"
    ACTION_ANTENNA_SWITCH = "SWITCH_DIVERSITY_ANTENNA"
    ACTION_TRIGGER_FAILOVER = "TRIGGER_CHANNEL_FAILOVER"

    def __init__(self):
        self.audit_log = []

    def evaluate(self, telemetry: Dict[str, Any], llm_recommendation: Optional[str] = None) -> Dict[str, Any]:
        """
        Evaluates physical telemetry deterministically.
        Rejects any invalid or hallucinated LLM recommendations.
        """
        rssi = float(telemetry.get("rssi", -60.0))
        snr = float(telemetry.get("snr", 25.0))
        per = float(telemetry.get("per", 0.02))
        retries = int(telemetry.get("retries", 0))
        busy = float(telemetry.get("busy", 0.20))
        jitter = float(telemetry.get("jitter", 10.0))
        tinyml_class = telemetry.get("tinyml_class", "NORMAL")

        # 1. Deterministic Rule Assessment against NOULs
        critical_flags = []
        degrading_flags = []

        if rssi <= self.RSSI_CRITICAL:
            critical_flags.append(f"RSSI {rssi} dBm below critical limit ({self.RSSI_CRITICAL})")
        elif rssi <= self.RSSI_DEGRADING:
            degrading_flags.append(f"RSSI {rssi} dBm below degraded limit ({self.RSSI_DEGRADING})")

        if snr <= self.SNR_CRITICAL:
            critical_flags.append(f"SNR {snr} dB below critical floor ({self.SNR_CRITICAL})")
        elif snr <= self.SNR_DEGRADING:
            degrading_flags.append(f"SNR {snr} dB below degraded floor ({self.SNR_DEGRADING})")

        if per >= self.PER_CRITICAL:
            critical_flags.append(f"Packet error rate {per*100:.1f}% exceeds critical cap ({self.PER_CRITICAL*100}%)")
        elif per >= self.PER_DEGRADING:
            degrading_flags.append(f"Packet error rate {per*100:.1f}% exceeds degraded threshold ({self.PER_DEGRADING*100}%)")

        if retries >= self.RETRIES_CRITICAL:
            critical_flags.append(f"Frame retries ({retries}) exceeded critical threshold")
        elif retries >= self.RETRIES_DEGRADING:
            degrading_flags.append(f"Elevated frame retries ({retries})")

        if jitter >= self.JITTER_CRITICAL:
            critical_flags.append(f"Jitter {jitter} ms indicates severe packet delay variance")
        elif jitter >= self.JITTER_DEGRADING:
            degrading_flags.append(f"Elevated jitter {jitter} ms")

        # 2. Derive Deterministic State
        if critical_flags or tinyml_class == "CRITICAL":
            state = "CRITICAL"
            allowed_action = self.ACTION_TRIGGER_FAILOVER
            reason = "Critical link collapse detected: " + "; ".join(critical_flags or [f"TinyML class {tinyml_class}"])
        elif degrading_flags or tinyml_class == "DEGRADING":
            state = "DEGRADING"
            allowed_action = self.ACTION_ANTENNA_SWITCH
            reason = "Link degradation in progress: " + "; ".join(degrading_flags or [f"TinyML class {tinyml_class}"])
        else:
            state = "NORMAL"
            allowed_action = self.ACTION_CONTINUE
            reason = "Telemetry strictly nominal. All metrics within optimal NOUL bounds."

        # 3. LLM Recommendation Validation (Safety Check)
        llm_validated = True
        override_reason = None

        if llm_recommendation:
            llm_clean = llm_recommendation.lower()
            if state == "CRITICAL" and "failover" not in llm_clean and "hop" not in llm_clean:
                llm_validated = False
                override_reason = "LLM failed to mandate failover during critical link collapse. Overridden by Laya."
            elif state == "NORMAL" and ("failover" in llm_clean or "alarm" in llm_clean):
                llm_validated = False
                override_reason = "LLM falsely proposed failover on healthy link. Overridden by Laya."

        audit_entry = {
            "state": state,
            "action": allowed_action,
            "reason": reason,
            "llm_validated": llm_validated,
            "override_reason": override_reason
        }
        self.audit_log.append(audit_entry)
        return audit_entry

    def evaluate_dual_model(
        self,
        telemetry: Dict[str, Any],
        smollm_output: Optional[Dict[str, Any]] = None,
        qwen_output: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluates physical telemetry alongside Tier 1 (SmolLM 135M) and Tier 2 (Qwen 0.6B).
        Performs multi-model consensus verification and enforces deterministic NOULs arbitration.
        """
        # Step 1: Compute Ground-Truth Deterministic Decision
        base_decision = self.evaluate(telemetry)
        state = base_decision["state"]
        binding_action = base_decision["action"]
        physics_reason = base_decision["reason"]

        smollm_validated = True
        smollm_override = None
        smollm_action = smollm_output.get("proposed_action", "") if smollm_output else ""
        smollm_text = smollm_output.get("raw_text", "") if smollm_output else ""

        qwen_validated = True
        qwen_override = None
        qwen_action = qwen_output.get("proposed_action", "") if qwen_output else ""
        qwen_content = qwen_output.get("content", "") if qwen_output else ""
        qwen_thinking = qwen_output.get("thinking", "") if qwen_output else ""

        # Step 2: Validate Tier 1 (SmolLM Triage)
        if smollm_output:
            smollm_clean = (smollm_action + " " + smollm_text).lower()
            if state == "CRITICAL" and "failover" not in smollm_clean and "hop" not in smollm_clean and "rerout" not in smollm_clean:
                smollm_validated = False
                smollm_override = "SmolLM missed critical collapse threshold. Overridden by Laya."
            elif state == "NORMAL" and ("failover" in smollm_clean or "alarm" in smollm_clean or "rerout" in smollm_clean):
                smollm_validated = False
                smollm_override = "SmolLM suggested false-alarm reroute on healthy link. Overridden by Laya."

        # Step 3: Validate Tier 2 (Qwen Causal Reasoner)
        if qwen_output:
            qwen_clean = (qwen_action + " " + qwen_content).lower()
            if state == "CRITICAL" and "failover" not in qwen_clean and "hop" not in qwen_clean:
                qwen_validated = False
                qwen_override = "Qwen did not mandate emergency channel hop under severe jamming. Overridden by Laya."
            elif state == "NORMAL" and ("failover" in qwen_clean or "hop" in qwen_clean or "jamming" in qwen_clean):
                qwen_validated = False
                qwen_override = "Qwen hallucinated channel collision on nominal link. Overridden by Laya."

        # Step 4: Determine Multi-Tier Consensus
        if smollm_validated and qwen_validated:
            consensus_mode = "UNANIMOUS_CONSENSUS"
            consensus_badge = "100% UNANIMOUS"
        elif smollm_validated or qwen_validated:
            consensus_mode = "PARTIAL_CONSENSUS"
            consensus_badge = "HYBRID_RESOLVED"
        else:
            consensus_mode = "NOUL_OVERRULED"
            consensus_badge = "HARD_OVERRIDE"

        # Step 5: Synthesize Unified Causal Explanation
        causal_explanation = qwen_content if qwen_content else physics_reason
        if smollm_text and "diagnosing" in smollm_text.lower():
            triage_note = f"SmolLM triage: {smollm_text}"
        else:
            triage_note = f"SmolLM triage: {smollm_action}"

        return {
            "state": state,
            "action": binding_action,
            "physics_reason": physics_reason,
            "consensus_mode": consensus_mode,
            "consensus_badge": consensus_badge,
            "smollm_audit": {
                "validated": smollm_validated,
                "override": smollm_override,
                "action": smollm_action,
                "latency_sec": smollm_output.get("latency_sec", 0.0) if smollm_output else 0.0
            },
            "qwen_audit": {
                "validated": qwen_validated,
                "override": qwen_override,
                "action": qwen_action,
                "thinking_preview": qwen_thinking[:80] + "..." if qwen_thinking else "",
                "latency_sec": qwen_output.get("latency_sec", 0.0) if qwen_output else 0.0
            },
            "causal_explanation": causal_explanation,
            "binding_authority": "LAYA_SYSTEM_1_NOULS"
        }
