# Gesture Command Filter

**A single gesture should produce a single command, even when detections flicker.**

I narrowed hand tracking to the boundary between a landmark stream and a UI action. A raw distance threshold emits repeated edges after brief occlusions and short noisy pinches. My framework is **normalize geometry → require sustained entry → latch one command → observe sustained release → re-arm**.

The original state machine uses entry/release hysteresis, a dwell requirement and a cooldown. Low-confidence frames withhold evidence; they do not count as an observed release. [The experiment](results/report.md) compares command quality and activation delay against a raw edge detector on held-out synthetic episodes.


## Recorded result

On **20 held-out episodes / 28 gestures**, filtering matches **27** gestures with **0** false or duplicate commands. Raw edges match **28** with **129** false or duplicate commands. Filtering misses **1** gesture and has **0.289 seconds** mean matched activation delay. This retains the delay and missed-gesture cost.

## Reproduce and inspect

Python 3.11, CPU only. No API keys, paid services, provider calls, customer records or external data download.

```bash
python -m venv .venv
# Activate the environment for your shell.
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python run.py --output runs/local
```

`core.py` contains the generator and actual comparison. `data/dataset.json` is the committed original input. `results/decisions.json` preserves the evaluated rows/traces. `results/metrics.json` and `results/report.md` state the measured outcomes. `results/manifest.json` binds core source, input, and output bytes with SHA-256. A fresh run writes to the requested directory and leaves committed results available for comparison.

This is a new independent portfolio experiment. Its results do not establish historical employer/client outcomes, production adoption, or service scale. Read the [data card](docs/data-card.md) and [provenance](docs/provenance.md) before interpreting the numbers.
