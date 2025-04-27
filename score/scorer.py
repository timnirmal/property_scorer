# scorer.py
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class PropertyScorer:
    def __init__(self,
                 profile: Dict[str, Dict[str, float]],
                 *,
                 max_quality:      int   = 5,
                 quality_floor:    float = 0.10,
                 quality_weight:   float = 0.80,
                 raw_floor:        float = 0.05,
                 must_have_tolerance: float = 0.0,
                 margin_epsilon:   float = 1e-6):
        """
        quality_weight  ∈ [0,1]   — how much quality influences each factor
        raw_floor       ∈ [0,1]   — minimum raw-match inside user’s band
        """
        self.profile      = profile
        self.max_quality  = max_quality
        self.q_floor      = quality_floor
        self.q_weight     = max(0.0, min(quality_weight, 1.0))
        self.r_floor      = max(0.0, min(raw_floor, 1.0))
        self.tol          = must_have_tolerance
        self.eps          = margin_epsilon
        self._validate_and_autonudge()

    # ------------------------------------------------------------
    #  Validation & auto-nudge
    # ------------------------------------------------------------
    def _validate_and_autonudge(self) -> None:
        for factor, cfg in self.profile.items():
            req = {"mode", "target", "direction", "weight"}
            if missing := req - cfg.keys():
                raise ValueError(f"[{factor}] missing keys: {missing}")

            if cfg["mode"] not in {"must_have", "nice_to_have", "irrelevant"}:
                raise ValueError(f"[{factor}] invalid mode={cfg['mode']}")

            if cfg["direction"] not in (-1, 1):
                raise ValueError(f"[{factor}] direction must be -1 or +1")

            if cfg["weight"] <= 0:
                raise ValueError(f"[{factor}] weight must be > 0")

            t = cfg["target"]
            l = cfg.get("lower", t)
            u = cfg.get("upper", t)

            if cfg["mode"] == "nice_to_have":
                if u <= t:
                    u = t + self.eps
                    logger.warning(f"[{factor}] auto-nudged upper to {u}")
                if l >= t:
                    l = t - self.eps
                    logger.warning(f"[{factor}] auto-nudged lower to {l}")

            if not (l <= t <= u):
                raise ValueError(f"[{factor}] require lower ≤ target ≤ upper "
                                 f"(got {l}, {t}, {u})")

            cfg["lower"], cfg["upper"] = l, u

    # ------------------------------------------------------------
    #  Raw-match score
    # ------------------------------------------------------------
    def _raw_score(self, x: float, cfg: Dict[str, float]) -> Optional[float]:
        mode = cfg["mode"]
        if mode == "irrelevant":
            return None

        t, l, u  = cfg["target"], cfg["lower"], cfg["upper"]
        d, tol   = cfg["direction"], self.tol

        # --- must-have (hard / soft) ---
        if mode == "must_have":
            if d < 0:                     # smaller is better
                if x <= t: return 1.0
                if tol and x <= t + tol:  # soft band
                    return 1.0 - (x - t) / tol
                return 0.0
            else:                         # larger is better
                if x >= t: return 1.0
                if tol and x >= t - tol:
                    return 1.0 - (t - x) / tol
                return 0.0

        # --- nice-to-have (linear decay) ---
        if d < 0:                                 # smaller better
            if   x <= t: raw = 1.0
            elif x <= u: raw = 1.0 - (x - t) / (u - t)   # in band
            else:        raw = 0.0                       # out of band
            if x <= u:                                   # inclusive band
                raw = max(self.r_floor, raw)
        else:                                           # larger better
            if   x >= t: raw = 1.0
            elif x >= l: raw = 1.0 - (t - x) / (t - l)
            else:        raw = 0.0
            if x >= l:
                raw = max(self.r_floor, raw)

        return raw

    # ------------------------------------------------------------
    #  Quality normalization
    # ------------------------------------------------------------
    def _qual_score(self, q: float) -> float:
        q = max(1, min(q, self.max_quality))
        norm = (q - 1) / (self.max_quality - 1)
        return self.q_floor + (1 - self.q_floor) * norm

    # ------------------------------------------------------------
    #  Aggregate score
    # ------------------------------------------------------------
    def score_property(self,
                       raw: Dict[str, float],
                       quality: Dict[str, float],
                       verbose: bool = False) -> float:

        total_w = weighted_sum = 0.0
        if verbose:
            print("\n── Scoring property ──")

        for factor, cfg in self.profile.items():
            x = raw.get(factor);  q = quality.get(factor);  w = cfg["weight"]

            if x is None or q is None or x < 0:
                if verbose: print(f"{factor}: missing / invalid → skip")
                continue

            r = self._raw_score(x, cfg)
            if r is None:
                if verbose: print(f"{factor}: irrelevant → skip")
                continue

            if cfg["mode"] == "must_have" and r == 0:
                if verbose: print(f"{factor}: must-have failed → overall 0.0")
                return 0.0

            qn = self._qual_score(q)

            # Gate: if raw-match is zero, factor contributes zero.
            fs = 0.0 if r == 0 else (1 - self.q_weight) * r + self.q_weight * qn

            weighted_sum += w * fs
            total_w      += w

            if verbose:
                print(f"{factor}: x={x}, r={r:.3f}, qn={qn:.3f}, fs={fs:.3f}, "
                      f"w={w} → contrib={w*fs:.3f}")

        if total_w == 0:
            return 0.0
        return weighted_sum / total_w
