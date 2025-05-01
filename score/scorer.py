# score/scorer.py

import logging
import math
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class PropertyScorer:
    def __init__(self,
                 profile: Dict[str, Dict[str, float]],
                 *,
                 max_quality:        int   = 5,
                 quality_floor:      float = 0.10,
                 quality_weight:     float = 0.80,
                 qual_exp:           float = 1.0,
                 raw_floor:          float = 0.05,
                 must_have_tolerance: float = 0.0,
                 margin_epsilon:     float = 1e-6):
        """
        profile: factor → {mode, target, lower?, upper?, direction, weight}

        max_quality    — top of your quality scale (e.g. 5)
        quality_floor  — minimum normalized quality (so rating=1 still ≥ this)
        quality_weight — how much quality vs raw to blend (0=raw only, 1=quality only)
        qual_exp       — exponent to warp the quality‐norm (1.0 = linear, >1 convex)
        raw_floor      — minimum raw‐match inside a nice_to_have band
        must_have_tol  — “soft” band width for must_have mode
        margin_epsilon — for nudging nice_to_have lower/upper if you forgot to
        """
        self.profile     = profile
        self.max_quality = max_quality
        self.q_floor     = max(0.0, min(quality_floor, 1.0))
        self.q_weight    = max(0.0, min(quality_weight, 1.0))
        self.qual_exp    = max(0.0, qual_exp)
        self.r_floor     = max(0.0, min(raw_floor, 1.0))
        self.tol         = must_have_tolerance
        self.eps         = margin_epsilon

        self._validate_and_autonudge()

    def _validate_and_autonudge(self) -> None:
        for factor, cfg in self.profile.items():
            need = {"mode", "target", "direction", "weight"}
            if missing := need - cfg.keys():
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
                # ensure a proper interval
                if u <= t:
                    u = t + self.eps
                    logger.warning(f"[{factor}] auto-nudged upper → {u}")
                if l >= t:
                    l = t - self.eps
                    logger.warning(f"[{factor}] auto-nudged lower → {l}")

            if not (l <= t <= u):
                raise ValueError(f"[{factor}] require lower ≤ target ≤ upper "
                                 f"(got {l}, {t}, {u})")

            cfg["lower"], cfg["upper"] = l, u

    def _raw_score(self, x: float, cfg: Dict[str, float]) -> Optional[float]:
        mode = cfg["mode"]
        if mode == "irrelevant":
            return None

        t, l, u = cfg["target"], cfg["lower"], cfg["upper"]
        d       = cfg["direction"]
        tol     = self.tol

        # --------------------
        # 1) must_have
        # --------------------
        if mode == "must_have":
            # smaller is better
            if d < 0:
                if x <= t: return 1.0
                if tol and x <= t + tol:
                    return 1.0 - (x - t) / tol
                return 0.0
            # larger is better
            else:
                if x >= t: return 1.0
                if tol and x >= t - tol:
                    return 1.0 - (t - x) / tol
                return 0.0

        # --------------------
        # 2) nice_to_have with hard cutoff outside [l,u]
        # --------------------
        if mode == "nice_to_have":
            # smaller is better
            if d < 0:
                if x < l or x > u:
                    return 0.0
                # x in [l,u]
                raw = 1.0 if x <= t else 1.0 - (x - t) / (u - t)
                return max(self.r_floor, raw)

            # larger is better
            else:
                if x < l or x > u:
                    return 0.0
                raw = 1.0 if x >= t else 1.0 - (t - x) / (t - l)
                return max(self.r_floor, raw)

        # unreachable
        return None

    def _qual_score(self, q: float) -> float:
        """
        Normalize q∈[1,max_quality] → [q_floor,1], then warp under exp curve.
        """
        qc   = max(1.0, min(q, self.max_quality))
        norm = (qc - 1.0) / (self.max_quality - 1.0)

        # warp
        if self.qual_exp != 1.0:
            norm = (math.exp(self.qual_exp * norm) - 1.0) / (math.exp(self.qual_exp) - 1.0)

        return self.q_floor + (1.0 - self.q_floor) * norm

    def _blend(self, r: float, q: float) -> float:
        """
        Geometric interpolation between raw-match r and qual-score qn.
        """
        qn = self._qual_score(q)
        α  = self.q_weight
        return (r ** (1 - α)) * (qn ** α)

    def score_property(self,
                       raw: Dict[str, float],
                       quality: Dict[str, float],
                       verbose: bool = False) -> float:

        total_w      = 0.0
        weighted_sum = 0.0
        if verbose:
            print("\n── Scoring property ──")

        for factor, cfg in self.profile.items():
            x = raw.get(factor)
            if x is None or x < 0:
                if verbose: print(f"{factor}: no raw → skip")
                continue

            r = self._raw_score(x, cfg)
            if r is None:
                if verbose: print(f"{factor}: irrelevant → skip")
                continue

            # a must-have failure kills the whole property
            if cfg["mode"] == "must_have" and r == 0.0:
                if verbose:
                    print(f"{factor}: must-have failed → total=0")
                return 0.0

            q = quality.get(factor)
            if q is None:
                # raw-only
                fs = r
                if verbose:
                    print(f"{factor}: x={x}, r={r:.3f}, no q → fs={fs:.3f},"
                          f" w={cfg['weight']} → contrib={cfg['weight']*fs:.3f}")
            else:
                fs = self._blend(r, q)
                qn = self._qual_score(q)
                if verbose:
                    print(f"{factor}: x={x}, r={r:.3f}, q={q}→qn={qn:.3f},"
                          f" fs={fs:.3f}, w={cfg['weight']} → contrib={cfg['weight']*fs:.3f}")

            weighted_sum += cfg["weight"] * fs
            total_w      += cfg["weight"]

        return (weighted_sum / total_w) if total_w else 0.0
