# Gesture Command Filter

A pinch that lasts across five missing frames should trigger one action. Treating a low-confidence observation as a release makes the same held pinch fire again when tracking returns. The [occlusion test](tests/test_contracts.py#L36) feeds that exact sequence to both detectors.

The [filter](core.py) normalizes landmark geometry, waits 120 ms for entry, then latches the action until it observes a sustained release. Across 20 synthetic test episodes, the raw edge detector caught all 28 gestures and emitted another 129 false or duplicate commands. The filter caught 27, missed one and emitted no extra commands.

That reduction in extra commands costs time. Matched gestures took **0.289 seconds on average** to activate with the filter, versus **0.002 seconds** with the raw threshold. The saved [episode decisions](results/decisions.json) and [thresholds and scores](results/metrics.json) allow both effects to be examined on the same generated streams. Camera and device latency are outside this experiment.

## Replay the episodes

The generated landmark streams run with Python 3.11 on CPU.

```bash
python -m unittest discover -s tests -v
python run.py --output runs/local
```

[Data card](docs/data-card.md) · [Run manifest](results/manifest.json) · [Source and contribution notes](docs/provenance.md)
