# scorer.py
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class PropertyScorer:
    def __init__(self,
                 profile: Dict[str, Dict[str, float]],
                 max_quality: int = 5,
                 quality_floor: float = 0.1,
                 quality_weight: float = 0.8,
                 must_have_tolerance: float = 0.0,
                 margin_epsilon: float = 1e-6):
        """
        profile: {
          factor: {
            "mode":      "must_have" | "nice_to_have" | "irrelevant",
            "target":     float,
            "lower":      float,  # optional
            "upper":      float,  # optional
            "direction": -1 | +1,
            "weight":     float
          }, ...
        }
        max_quality: highest possible quality rating (e.g. 5)
        must_have_tolerance: if >0, allow a “soft” zone past target of ±tol
        margin_epsilon: small auto-nudge when upper==target or lower==target
        quality_floor: minimum normalized quality (0…1)
        """
        self.profile = profile
        self.max_quality = max_quality
        self.tol = must_have_tolerance
        self.eps = margin_epsilon
        self.q_floor = quality_floor
        self.q_weight = quality_weight

        self._validate_and_autonudge()

    def _validate_and_autonudge(self):
        for factor, cfg in self.profile.items():
            # 1) required keys
            req = {"mode","target","direction","weight"}
            if missing := req - cfg.keys():
                raise ValueError(f"[{factor}] missing keys: {missing}")

            mode = cfg["mode"]
            if mode not in ("must_have","nice_to_have","irrelevant"):
                raise ValueError(f"[{factor}] invalid mode: {mode}")

            d = cfg["direction"]
            if d not in (-1,1):
                raise ValueError(f"[{factor}] direction must be -1 or +1, got {d}")

            w = cfg["weight"]
            if w <= 0:
                raise ValueError(f"[{factor}] weight must be >0, got {w}")

            # 2) margins default
            t = cfg["target"]
            l = cfg.get("lower", t)
            u = cfg.get("upper", t)

            # 3) auto-nudge for nice_to_have zero margins
            if mode == "nice_to_have":
                if u <= t:
                    new_u = t + self.eps
                    logger.warning(f"[{factor}] auto-nudging upper {u}→{new_u}")
                    u = new_u
                if l >= t:
                    new_l = t - self.eps
                    logger.warning(f"[{factor}] auto-nudging lower {l}→{new_l}")
                    l = new_l

            # 4) final ordering check
            if not (l <= t <= u):
                raise ValueError(
                    f"[{factor}] require lower ≤ target ≤ upper, "
                    f"got lower={l},target={t},upper={u}"
                )

            cfg["lower"], cfg["upper"] = l, u

    def _raw_score(self, x: float, cfg: Dict[str, float]) -> Optional[float]:
        mode = cfg["mode"]
        if mode == "irrelevant":
            return None

        t, l, u = cfg["target"], cfg["lower"], cfg["upper"]
        d = cfg["direction"]
        tol = self.tol

        # — must-have (hard or soft)
        if mode == "must_have":
            if d < 0:      # smaller is better
                if x <= t:       return 1.0
                if tol>0 and x <= t+tol:
                    return 1.0 - (x-t)/tol
                return 0.0
            else:          # larger is better
                if x >= t:       return 1.0
                if tol>0 and x >= t-tol:
                    return 1.0 - (t-x)/tol
                return 0.0

        # — nice-to-have
        if d < 0:  # smaller is better
            if   x <= t: return 1.0
            if   x >= u: return 0.0
            return 1.0 - (x - t)/(u - t)
        else:      # larger is better
            if   x >= t: return 1.0
            if   x <= l: return 0.0
            return 1.0 - (t - x)/(t - l)

    def _qual_score(self, q: float) -> float:
        # clamp to [1, max_quality]
        qc = max(1, min(q, self.max_quality))
        raw = (qc - 1)/(self.max_quality - 1)
        # apply floor
        return self.q_floor + (1-self.q_floor)*raw

    def score_property(self,
                       raw: Dict[str, float],
                       quality: Dict[str, float],
                       verbose: bool = False) -> float:
        total_w, weighted_sum = 0.0, 0.0
        if verbose:
            print("\n── Starting scoring ──")

        for factor, cfg in self.profile.items():
            x = raw.get(factor)
            q = quality.get(factor)
            w = cfg["weight"]

            if x is None or q is None:
                if verbose: print(f"{factor}: missing data → skip")
                continue
            if x < 0:
                if verbose: print(f"{factor}: raw < 0 ({x}) → skip")
                continue

            r = self._raw_score(x, cfg)
            if r is None:
                if verbose: print(f"{factor}: irrelevant → skip")
                continue

            if verbose:
                print(f"\n{factor}: raw={x} mode={cfg['mode']} → r={r:.3f}")

            # hard must-have
            if cfg["mode"]=="must_have" and r==0.0:
                if verbose: print(f"{factor}: must-have FAILED → final score=0\n")
                return 0.0

            # compute normalized quality
            qn = self._qual_score(q)
            if verbose:
                print(f"{factor}: quality={q} → qn={qn:.3f}")

            # —— blend raw & quality ⟵ FIXED here
            fs = (1 - self.q_weight)*r + self.q_weight*qn
            if verbose:
                print(f"{factor}: blended score fs = "
                      f"{(1-self.q_weight):.2f}*{r:.3f} + "
                      f"{self.q_weight:.2f}*{qn:.3f} = {fs:.3f}")

            contrib = w * fs
            total_w     += w
            weighted_sum += contrib

            if verbose:
                print(f"{factor}: contrib = {w} * {fs:.3f} = {contrib:.3f}")
                print(f" Accum sum = {weighted_sum:.3f}, total_w = {total_w:.3f}")

        if total_w == 0:
            if verbose: print("No weighted factors → score=0")
            return 0.0

        final = weighted_sum / total_w
        if verbose:
            print(f"\nFinal score = {weighted_sum:.3f}/{total_w:.3f} = {final:.3f}\n")
        return final

