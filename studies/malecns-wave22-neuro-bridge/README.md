# MaleCNS v1.0 Connectome x Neuro-Model Routing Cross-Pollination & Septal Firewall (`EXP-Q43a` & `EXP-Q43b`)

This directory provides a self-contained, pure-Python stdlib (`int`/`Fraction`) and pure-`Init` Lean `4.36.0` verification bundle bridging the FlyEM *Drosophila* MaleCNS v1.0 connectome with loopy belief propagation stability, Ibn al-Nafis's septal cavity firewall, and five-operator routing tomography.

## Scope & Contents

- **Pure-$\mathbb{Q}$ Oracle (`s162_malecns_neuro_bridge_oracle.py`):** Exact integer/rational arithmetic (`0` IEEE-754 production floats, `0` unseeded RNG calls, deterministic 64-bit integer LCG with logged seeds), consuming the pinned pure-integer connectome anchor `s102_malecns_anchor.json` (`0` `.feather` files or model weights committed).
- **Zone-B Hardened Verifier (`verify_s162_malecns_neuro_bridge.py`):** Recomputes the full certificate from scratch (`s162_malecns_neuro_bridge_certificate.json`), runs secondary mathematical cross-audits (`EXP-Q43a` Bethe-Hessian/Cayley-Routh damping & septal firewall conservation; `EXP-Q43b` 5-operator separation & tail stability), enforces SHA-256 pins and static Lean 4 trust-escape checks, and supports isolated `TemporaryDirectory` `--live-lean` kernel verification (`0` `.lake/` residue).
- **Pure-`Init` Lean `4.36.0` Companion (`MaleCNSNeuroBridge.lean`):** `16/16` universal `forall` theorems (`0` external imports, `0` `sorry`, `0` `Classical.choice`, axioms `[propext, Quot.sound]` only), with `lakefile.toml`, `lake-manifest.json`, and `lean-toolchain`.
- **R5 Adversarial Suite (`test_s162_malecns_neuro_bridge_r5.py`):** `9` assertion-free R5 and Zone-B/forgery/RO-Lean tests (`0` bare `assert`s, `0` skips).
- **Technical Report (`REPORT.md`):** Complete quantitative tables, theorem index, and methodological disclosures (including `UNCONTROLLED_LAPTOP_NOT_CLAIMED` energy policy and external benchmark confound disclosures).

## Quick Verification (3-Mode Isolated `-I` Parity & Live Lean)

```bash
# Verify certificate + full oracle replay across all 3 isolated R4 modes
for flags in "-I -B" "-I -O -B" "-I -B -W error"; do
  CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 python3 ${flags} \
    studies/malecns-wave22-neuro-bridge/verify_s162_malecns_neuro_bridge.py --check --json
  CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 python3 ${flags} \
    studies/malecns-wave22-neuro-bridge/test_s162_malecns_neuro_bridge_r5.py
done

# Live Lean 4.36.0 build & axiom check (tempdir-staged, read-only safe, zero .lake/ residue)
CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 python3 -I -B \
  studies/malecns-wave22-neuro-bridge/verify_s162_malecns_neuro_bridge.py --check --json --live-lean
```
