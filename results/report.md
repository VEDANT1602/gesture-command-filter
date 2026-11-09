# Gesture command admission

Topic: vision interfaces. Decision: turn one held pinch into one command while withholding commands during uncertain detections.

The baseline triggers on each raw threshold edge and resets on a missing frame. My temporal state machine requires sustained entry, uses a separate release threshold, and preserves an active latch through occlusion until release is actually observed. This adds delay and can miss short gestures.

On 20 held-out synthetic episodes containing 28 gestures, raw edges emit 129 false/duplicate commands and match 28 gestures. Filtering emits 0 false/duplicate commands and matches 27, with 0.289s mean matched activation delay. Every emitted timestamp is retained in decisions.json.

These are post-detector geometric fixtures, not measured OpenCV/MediaPipe recognition, camera FPS, real-person robustness or accessibility validation. The threshold contract is fixed before test evaluation. Next, I would collect consented landmark streams and test the safety-versus-delay tradeoff across users and camera conditions.
