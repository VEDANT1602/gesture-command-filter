# Development and conceptual reference

Developed for Vedant Thaker with AI implementation assistance. The problem framing follows Vedant's decision-first approach: define the narrower question, expose the usual failure, implement a boundary, measure it, and state the next decision.

The conceptual starting point is **Hand Tracking using OpenCV**, entry 14 in [AI Project Gallery](https://github.com/KalyanM45/AI-Project-Gallery/blob/04a210263e266c68f8c44546c1007fd8bd85ade1/README.md). The inspected [source README](https://github.com/KalyanM45/Hand-Tracking-Using-Opencv/blob/707047399b367038d529cd0bbd2d36082c8ab384/README.md) is pinned to `707047399b367038d529cd0bbd2d36082c8ab384`. Upstream repository license metadata: `GPL-3.0`. The gallery root has no license file.

Only the topic informed this project. Source code, README wording, data, weights, assets and reported results were not copied or executed. The implementation, fixtures and experiment are original and MIT licensed here. This is not a fork, replacement, endorsement or relicensing of the upstream repository.

Independent redesign: Implement an original deterministic landmark-to-gesture state machine over generated 2D hand landmarks with noise, occlusions and timestamp gaps. Compare raw per-frame triggering with hysteresis, dwell time and cooldown. No webcam capture, pretrained detector, or real-person biometric dataset.

The new public work demonstrates present methods. It does not verify career dates, client engagements, historical resume figures or adoption.
