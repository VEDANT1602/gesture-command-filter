from pathlib import Path
import hashlib
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import core

class ArtifactContracts(unittest.TestCase):
    def test_source_and_artifact_digests(self):
        manifest = json.loads((ROOT / "results/manifest.json").read_text())
        for rel, digest in manifest["source_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT / rel).read_bytes()).hexdigest(), digest, rel)
        for rel, digest in manifest["artifact_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT / "results" / rel).read_bytes()).hexdigest(), digest, rel)

    def test_generator_reproduces_committed_inputs(self):
        self.assertEqual(core.generate(), json.loads((ROOT / "data/dataset.json").read_text()))

import copy

def frames(ratios):
    out=[]
    for i,ratio in enumerate(ratios):
        p=[[0.,0.] for _ in range(21)];p[9]=[0.,1.];p[4]=[.2,.5];p[8]=[.2+(ratio or .1),.5]
        out.append({"time":i*.05,"confidence":.95,"landmarks":None if ratio is None else p})
    return out

class GestureContracts(unittest.TestCase):
    def test_held_gesture_produces_one_delayed_command(self):
        events=core.filtered(frames([.1]*30))
        self.assertEqual(1,len(events));self.assertGreaterEqual(events[0],.12)

    def test_occlusion_does_not_rearm_a_held_command(self):
        data=frames([.1]*8+[None]*5+[.1]*15)
        self.assertEqual(2,len(core.raw_edges(data)))
        self.assertEqual(1,len(core.filtered(data)))

    def test_short_spikes_do_not_meet_dwell(self):
        data=frames([.5,.1,.5,.1,.5,.5])
        self.assertEqual([],core.filtered(data))
        self.assertEqual(2,len(core.raw_edges(data)))

    def test_observed_release_permits_second_gesture(self):
        self.assertEqual(2,len(core.filtered(frames([.1]*10+[.5]*10+[.1]*10))))

    def test_timestamp_order_and_nonfinite_fail_closed(self):
        data=frames([.1]*10);data[2]["time"]=data[1]["time"]
        with self.assertRaises(ValueError):core.filtered(data)
        for value in [True,float("nan"),float("inf")]:
            data=frames([.1]*10);data[2]["time"]=value
            with self.assertRaises(ValueError):core.filtered(data)

    def test_invalid_landmark_and_threshold_rejected(self):
        data=frames([.1]*10);data[0]["landmarks"][1][0]=float("nan")
        with self.assertRaises(ValueError):core.filtered(data)
        with self.assertRaises(ValueError):core.filtered(frames([.1]*5),enter=.5,exit=.3)
        with self.assertRaises(ValueError):core.filtered(frames([.1]*5),dwell=True)

    def test_palm_normalization_is_scale_invariant(self):
        data=frames([.15]*10);scaled=copy.deepcopy(data)
        for frame in scaled:
            frame["landmarks"]=[[3*x+4,3*y-2] for x,y in frame["landmarks"]]
        self.assertAlmostEqual(core.pinch_ratio(data[0]),core.pinch_ratio(scaled[0]))
        self.assertEqual(core.filtered(data),core.filtered(scaled))

    def test_raw_score_reconciles_fixture_totals(self):
        raw=json.loads((ROOT/"results/decisions.json").read_text())
        metrics=json.loads((ROOT/"results/metrics.json").read_text())
        for name in ["raw_edges","filtered"]:
            self.assertEqual(sum(row[name]["true_commands"] for row in raw),metrics[name]["true_commands"])
            self.assertEqual(sum(row[name]["false_or_duplicate_commands"] for row in raw),metrics[name]["false_or_duplicate_commands"])
