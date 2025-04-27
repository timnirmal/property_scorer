# scorer.py
from typing import Dict, Optional

class PropertyScorer:
    def __init__(self,
                 profile: Dict[str, Dict[str, float]],
                 max_quality: int = 5):
        """
        profile: {
          factor_name: {
            "mode":      "must_have" | "nice_to_have" | "irrelevant",
            "target":     float,
            "lower":      float,       # optional, defaults to target
            "upper":      float,       # optional, defaults to target
            "direction": -1 | +1,
            "weight":     float
          }, ...
        }
        """
        self.profile     = profile
        self.max_quality = max_quality

        # Check validity of profile
        for factor, cfg in self.profile.items():
            t = cfg["target"]
            l = cfg.get("lower", t)
            u = cfg.get("upper", t)
            d = int(cfg["direction"])

            if not (l <= t <= u):
                raise ValueError(
                    f"[Invalid margins for '{factor}']: "
                    f"Margins must satisfy lower ≤ target ≤ upper, "
                    f"but got lower={l}, target={t}, upper={u}."
                )

    def _raw_score(self,
                   x: float,
                   cfg: Dict[str, float]) -> Optional[float]:
        mode = cfg["mode"]
        if mode == "irrelevant":
            return None

        t = cfg["target"]
        l = cfg.get("lower", t)
        u = cfg.get("upper", t)
        d = int(cfg["direction"])

        # — must-have: hard cutoff
        if mode == "must_have":
            # smaller-is-better (d<0): want x ≤ t
            if d < 0:
                return 1.0 if x <= t else 0.0
            # larger-is-better (d>0): want x ≥ t
            else:
                return 1.0 if x >= t else 0.0


        # — nice-to-have: linear decay
        if d < 0:  # smaller is better
            if   x <= t: return 1.0
            elif x >= u: return 0.0
            else:        return 1.0 - (x - t)/(u - t)
        else:      # larger is better
            if   x >= t: return 1.0
            elif x <= l: return 0.0
            else:        return 1.0 - (t - x)/(t - l)

    def _qual_score(self, q: float) -> float:
        raw_norm = (q - 1) / (self.max_quality - 1)
        return 0.1 + 0.9 * raw_norm

    def score_property(self,
                       raw: Dict[str, float],
                       quality: Dict[str, float],
                       verbose: bool = False) -> float:
        """
        Compute final score ∈ [0,1].  
        If verbose=True, prints each step.
        """
        weighted_sum = 0.0
        total_weight = 0.0

        if verbose:
            print("\n─── Scoring new property ───")

        for factor, cfg in self.profile.items():
            x = raw[factor]
            q = quality[factor]
            w = cfg["weight"]

            if verbose:
                print(f"\nFactor: {factor}")
                print(f" Raw value         = {x}")
                print(f" Mode              = {cfg['mode']}")
                print(f" Target            = {cfg['target']}")
                print(f" Lower margin      = {cfg.get('lower', cfg['target'])}")
                print(f" Upper margin      = {cfg.get('upper', cfg['target'])}")
                print(f" Direction         = {cfg['direction']}")
                print(f" Priority weight   = {w}")

            r = self._raw_score(x, cfg)
            if r is None:
                if verbose:
                    print(" → Irrelevant, skipping factor.")
                continue

            if verbose:
                print(f" Raw-match score r = {r:.3f}")

            # must-have fail?
            if cfg["mode"] == "must_have" and r == 0.0:
                if verbose:
                    print(" → Must-have FAILED, property score = 0.0\n")
                return 0.0

            q_norm = self._qual_score(q)
            if verbose:
                print(f" Quality rating    = {q} → normalized = {q_norm:.3f}")

            factor_score = r * q_norm
            if verbose:
                print(f" Factor score      = r * q_norm = {factor_score:.3f}")

            contrib = w * factor_score
            weighted_sum += contrib
            total_weight += w

            if verbose:
                print(f" Weighted contrib  = {w} * {factor_score:.3f} = {contrib:.3f}")
                print(f" Accumulated sum   = {weighted_sum:.3f}, total weight = {total_weight}")

        # handle “no factors” case
        if total_weight == 0.0:
            if verbose:
                print(" → No relevant factors, final score = 0.0")
            return 0.0

        final = weighted_sum / total_weight
        if verbose:
            print(f"\nFinal score = weighted_sum / total_weight = "
                  f"{weighted_sum:.3f} / {total_weight:.3f} = {final:.3f}\n")
        return final
