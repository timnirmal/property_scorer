# score/scorer.py

from __future__ import annotations
import logging
import math
import statistics
from typing import Dict, Any, List, Optional

import numpy as np  # for percentile calculations

logger = logging.getLogger(__name__)


def _weighted_average(values: List[float], weights: List[float]) -> float:
    """Return the weighted average of `values` with corresponding `weights`."""
    total_w = sum(weights)
    return sum(v * w for v, w in zip(values, weights)) / total_w if total_w else statistics.mean(values)


def _decay_weights(vals: List[float], cfg: Dict[str, Any]) -> List[float]:
    """
    Compute per-value decay weights based on distance from target.

    Args:
        vals: List of raw values.
        cfg:  Factor config, must contain:
              - "target": float
              - "lower", "upper": float
              - "decay_function": Optional[str] ("linear", "exp", "quadratic")
              - "decay_rate": float

    Returns:
        A list of floats in [0.0, 1.0] representing decay-based weights.
    """
    fn   = cfg.get("decay_function", "linear")
    rate = float(cfg.get("decay_rate", 1.0))
    t, l, u = cfg["target"], cfg["lower"], cfg["upper"]
    rng = max(u - l, 1e-12)

    # Normalize distances from target into [0,1]
    dists = [abs(v - t) / rng for v in vals]

    if fn == "exp":
        return [math.exp(-rate * d) for d in dists]
    if fn == "quadratic":
        return [max(0.0, 1.0 - (rate * d) ** 2) for d in dists]

    # default linear
    return [max(0.0, 1.0 - rate * d) for d in dists]


class PropertyScorer:
    """
    Blend raw‐match and subjective quality to produce a single property score.

    This scorer supports:
      • must_have / nice_to_have / irrelevant modes
      • multi-POI factors with filtering and aggregation:
        – mean, median, min, max
        – k_nearest / k_farthest (with nearest_k, farthest_k)
        – percentile (with percentile parameter)
        – optional weighted‐decay aggregation (decay_function, decay_rate)
      • quality warping via exponent (qual_exp)
      • geometric blending of raw and quality scores (quality_weight)

    Args:
        profile (Dict[str, Dict[str, Any]]):
            Mapping factor_key → config dict with:
              - mode (str): "must_have" | "nice_to_have" | "irrelevant"
              - target (float): ideal value
              - lower, upper (float, optional): band for nice_to_have decay
              - direction (int): -1 (smaller better) or +1 (larger better)
              - weight (float): relative importance
              - multi (bool, optional): treat raw values as List[float]
              - aggregation (str, optional): how to collapse multi-list
              - nearest_k, farthest_k, percentile (optional): parameters for aggregation
              - decay_function, decay_rate (optional): for weighted-decay
        max_quality (int, default=5):
            Top of subjective quality scale (1…max_quality).
        quality_floor (float, default=0.10):
            Minimum normalized quality score (so even lowest raw maps ≥ this).
        quality_weight (float, default=0.80):
            Blend factor: 0 = raw-only, 1 = quality-only.
        qual_exp (float, default=1.0):
            Exponent for warping normalized quality (1.0 = linear).
        raw_floor (float, default=0.05):
            Minimum raw-match inside nice_to_have band.
        must_have_tolerance (float, default=0.0):
            Soft band width ± tol for must_have before failing.
        margin_epsilon (float, default=1e-6):
            Tiny epsilon to auto-nudge lower/upper when equal to target.
    """

    ALLOWED_AGG = {
        "mean", "median", "min", "max",
        "k_nearest", "k_farthest", "percentile"
    }

    def __init__(self,
                 profile: Dict[str, Dict[str, Any]],
                 *,
                 max_quality: int = 5,
                 quality_floor: float = 0.10,
                 quality_weight: float = 0.80,
                 qual_exp: float = 1.0,
                 raw_floor: float = 0.05,
                 must_have_tolerance: float = 0.0,
                 margin_epsilon: float = 1e-6):
        # Core parameters
        self.profile     = profile
        self.max_quality = max_quality
        self.q_floor     = max(0.0, min(quality_floor, 1.0))
        self.q_weight    = max(0.0, min(quality_weight, 1.0))
        self.qual_exp    = max(0.0, qual_exp)
        self.r_floor     = max(0.0, min(raw_floor, 1.0))
        self.tol         = must_have_tolerance
        self.eps         = margin_epsilon

        # Validate + auto-nudge any bounds issues
        self._validate()

    def _validate(self) -> None:
        """Ensure every factor config is complete and consistent."""
        for factor, cfg in self.profile.items():
            required = {"mode", "target", "direction", "weight"}
            missing = required - cfg.keys()
            if missing:
                raise ValueError(f"[{factor}] missing keys: {missing}")

            if cfg["mode"] not in ("must_have", "nice_to_have", "irrelevant"):
                raise ValueError(f"[{factor}] invalid mode={cfg['mode']}")

            if cfg["direction"] not in (-1, 1):
                raise ValueError(f"[{factor}] direction must be -1 or +1")

            if cfg["weight"] <= 0:
                raise ValueError(f"[{factor}] weight must be > 0")

            # target/lower/upper consistency
            t = cfg["target"]
            l = cfg.get("lower", t)
            u = cfg.get("upper", t)
            if cfg["mode"] == "nice_to_have":
                # auto-nudge if bounds coincide
                if u <= t:
                    u = t + self.eps
                    logger.debug(f"[{factor}] nudged upper to {u}")
                if l >= t:
                    l = t - self.eps
                    logger.debug(f"[{factor}] nudged lower to {l}")
            if not (l <= t <= u):
                raise ValueError(f"[{factor}] require lower ≤ target ≤ upper ({l}, {t}, {u})")
            cfg["lower"], cfg["upper"] = l, u

            # multi-POI aggregation defaults
            if cfg.get("multi"):
                agg = cfg.get("aggregation")
                if agg not in self.ALLOWED_AGG:
                    raise ValueError(f"[{factor}] invalid aggregation={agg}")
                # set defaults if missing
                cfg.setdefault("nearest_k", 1)
                cfg.setdefault("farthest_k", 1)
                cfg.setdefault("percentile", 0.5)

    def _aggregate(self, vals: List[float], cfg: Dict[str, Any]) -> Optional[float]:
        """
        Filter `vals` to [lower,upper] then aggregate.
        Returns None if no values remain in the band.
        """
        l, u = cfg["lower"], cfg["upper"]
        in_band = [v for v in vals if l <= v <= u]
        if not in_band:
            return None

        # weighted-decay aggregation?
        if cfg.get("decay_function"):
            weights = _decay_weights(in_band, cfg)
            return _weighted_average(in_band, weights)

        # flat aggregations
        agg = cfg.get("aggregation")
        if agg == "mean":
            return statistics.mean(in_band)
        if agg == "median":
            return statistics.median(in_band)
        if agg == "min":
            return min(in_band)
        if agg == "max":
            return max(in_band)
        if agg == "k_nearest":
            k = cfg["nearest_k"]
            return statistics.mean(sorted(in_band)[:k])
        if agg == "k_farthest":
            k = cfg["farthest_k"]
            return statistics.mean(sorted(in_band, reverse=True)[:k])
        if agg == "percentile":
            p = cfg["percentile"] * 100
            return float(np.percentile(in_band, p))

        # fallback
        return statistics.mean(in_band)

    def _raw(self, x: float, cfg: Dict[str, Any]) -> float:
        """
        Compute the raw-match score r ∈ [0,1] for a single value x.
        - must_have: pass/fail with optional soft tolerance
        - nice_to_have: linear decay inside [lower,upper]
        """
        m, d, t, l, u = cfg["mode"], cfg["direction"], cfg["target"], cfg["lower"], cfg["upper"]

        if m == "must_have":
            if d < 0:
                if x <= t:
                    return 1.0
                if self.tol and x <= t + self.tol:
                    return 1.0 - (x - t) / self.tol
                return 0.0
            else:
                if x >= t:
                    return 1.0
                if self.tol and x >= t - self.tol:
                    return 1.0 - (t - x) / self.tol
                return 0.0

        # nice_to_have
        if x < l or x > u:
            return 0.0

        if d < 0:
            raw = 1.0 if x <= t else 1.0 - (x - t) / (u - t)
        else:
            raw = 1.0 if x >= t else 1.0 - (t - x) / (t - l)

        return max(self.r_floor, raw)

    def _qual(self, q: float) -> float:
        """
        Warp raw quality rating q ∈ [1,max_quality] into [q_floor,1]
        using an exponential curve if qual_exp != 1.0.
        """
        qc = max(1.0, min(q, self.max_quality))
        norm = (qc - 1.0) / (self.max_quality - 1.0)
        if self.qual_exp != 1.0:
            norm = (math.exp(self.qual_exp * norm) - 1.0) / (math.exp(self.qual_exp) - 1.0)
        return self.q_floor + (1.0 - self.q_floor) * norm

    def score_property(self,
                       raw: Dict[str, Any],
                       quality: Dict[str, float],
                       verbose: bool = False) -> float:
        """
        Compute the final blended score for one property.

        Args:
            raw:     Dict factor_key → raw numeric or list of numerics
            quality: Dict factor_key → subjective rating (1…max_quality)
            verbose: if True, print per-factor debug output

        Returns:
            A float in [0.0,1.0].
        """
        total_weight = 0.0
        weighted_sum = 0.0

        if verbose:
            print("\n── Scoring property ──")

        for factor, cfg in self.profile.items():
            if cfg["mode"] == "irrelevant":
                if verbose:
                    print(f"{factor}: irrelevant → skip")
                continue

            val = raw.get(factor)
            if val is None:
                if verbose:
                    print(f"{factor}: missing raw → skip")
                continue

            # handle multi-POI vs scalar
            if cfg.get("multi"):
                if not isinstance(val, list):
                    if verbose:
                        print(f"{factor}: expected list → skip")
                    continue

                x_agg = self._aggregate(val, cfg)
                r = 0.0 if x_agg is None else self._raw(x_agg, cfg)
                if verbose:
                    if x_agg is None:
                        print(f"{factor}: no in-band → r=0")
                    else:
                        print(f"{factor}: aggregated x={x_agg:.3f} → r={r:.3f}")
            else:
                x = float(val)
                r = self._raw(x, cfg)
                if verbose:
                    print(f"{factor}: x={x:.3f} → r={r:.3f}")

            # must_have fail short-circuits to zero
            if cfg["mode"] == "must_have" and r == 0.0:
                if verbose:
                    print(f"{factor}: must_have failed → total=0")
                return 0.0

            qv = quality.get(factor)
            if qv is None:
                fs = r  # raw-only
                if verbose:
                    print(f"    raw-only → fs={fs:.3f}")
            else:
                fs = (r ** (1 - self.q_weight)) * (self._qual(qv) ** self.q_weight)
                if verbose:
                    print(f"    blended with q={qv} → fs={fs:.3f}")

            weighted_sum += cfg["weight"] * fs
            total_weight += cfg["weight"]

        return weighted_sum / total_weight if total_weight else 0.0
