"""Temporal command admission over synthetic post-detector hand landmarks."""
import math
import random


def finite(value, label):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
        raise ValueError(label+" must be finite numeric data")
    return float(value)


def pinch_ratio(frame):
    confidence=finite(frame["confidence"],"confidence")
    if not 0<=confidence<=1:
        raise ValueError("confidence outside [0,1]")
    points=frame["landmarks"]
    if points is None or confidence<.8:
        return None
    if not isinstance(points,list) or len(points)!=21 or any(not isinstance(p,list) or len(p)!=2 for p in points):
        raise ValueError("21 two-dimensional landmarks required")
    points=[(finite(x,"landmark x"),finite(y,"landmark y")) for x,y in points]
    distance=lambda a,b:math.hypot(points[a][0]-points[b][0],points[a][1]-points[b][1])
    palm=distance(0,9)
    return distance(4,8)/palm if palm>1e-9 else None


def validate_frames(frames):
    previous=-math.inf
    for frame in frames:
        now=finite(frame["time"],"time")
        if now<0 or now<=previous:
            raise ValueError("frame times must be nonnegative and strictly increasing")
        pinch_ratio(frame)
        previous=now


def raw_edges(frames):
    validate_frames(frames)
    active=False; events=[]
    for frame in frames:
        ratio=pinch_ratio(frame)
        below=ratio is not None and ratio<.25
        if below and not active: events.append(frame["time"])
        active=below
    return events


def filtered(frames,enter=.20,exit=.30,dwell=.12,release=.10,max_gap=.15,cooldown=.30):
    validate_frames(frames)
    for value,name in [(enter,"enter"),(exit,"exit"),(dwell,"dwell"),(release,"release"),(max_gap,"max_gap"),(cooldown,"cooldown")]:
        if finite(value,name)<=0: raise ValueError(name+" must be positive")
    if enter>=exit: raise ValueError("entry threshold must be below exit threshold")
    active=False; candidate=None; released=None; last_valid=None; events=[];last_command=-math.inf
    for frame in frames:
        now=frame["time"]; ratio=pinch_ratio(frame)
        if ratio is None:
            candidate=None; released=None
            continue
        if last_valid is not None and now-last_valid>max_gap:
            candidate=None; released=None
        last_valid=now
        if active:
            if ratio>=exit:
                if released is None: released=now
                if now-released>=release:
                    active=False; candidate=None; released=None
            else: released=None
        elif ratio<=enter:
            if candidate is None: candidate=now
            if now-candidate>=dwell and now-last_command>=cooldown:
                events.append(now); active=True; candidate=None;last_command=now
        else: candidate=None
    return events


def generate():
    rng=random.Random(1602)
    episodes=[]
    for episode in range(60):
        windows=[[.7,1.7],[2.5,3.3]] if episode%3 else []
        frames=[]
        for i in range(120):
            time=i/30
            pinched=any(start<=time<=end for start,end in windows)
            ratio=(.12 if pinched else .50)+rng.gauss(0,.045 if episode<40 else .065)
            if not pinched and rng.random()<.04: ratio=.08  # a short false detection
            points=[[.1*j,.01*j] for j in range(21)]
            points[0]=[0.,0.];points[9]=[0.,1.]
            points[4]=[.2,.5];points[8]=[.2+max(.01,ratio),.5]
            points=[[round(x,8),round(y,8)] for x,y in points]
            missing=rng.random()<(.04 if episode<40 else .09)
            frames.append({"time":time,"landmarks":None if missing else points,
                           "confidence":.5 if missing else .95})
        episodes.append({"id":f"episode-{episode:02d}","split":"development" if episode<40 else "test",
                         "gesture_windows":windows,"frames":frames})
    return {"episodes":episodes,"seed":1602,"time_unit":"seconds"}


def score(events,windows):
    matched=set(); false=0; delays=[]
    for event in events:
        candidates=[i for i,(start,end) in enumerate(windows) if start<=event<=end and i not in matched]
        if candidates:
            index=candidates[0];matched.add(index);delays.append(event-windows[index][0])
        else:false+=1
    return {"true_commands":len(matched),"false_or_duplicate_commands":false,
            "missed_gestures":len(windows)-len(matched),"delays_seconds":delays}


def experiment(data):
    test=[e for e in data["episodes"] if e["split"]=="test"]
    raw=[]; totals={name:{"true_commands":0,"false_or_duplicate_commands":0,"missed_gestures":0,"delays_seconds":[]}
                   for name in ["raw_edges","filtered"]}
    for episode in test:
        row={"id":episode["id"],"gesture_windows":episode["gesture_windows"]}
        for name,fn in [("raw_edges",raw_edges),("filtered",filtered)]:
            events=fn(episode["frames"]);result=score(events,episode["gesture_windows"])
            row[name]={"events_seconds":events,**result}
            for key,value in result.items():
                if key=="delays_seconds":totals[name][key].extend(value)
                else:totals[name][key]+=value
        raw.append(row)
    metrics={"development_episodes":40,"test_episodes":len(test),"test_gestures":sum(len(e['gesture_windows']) for e in test),
             "thresholds_predeclared":{"enter":.20,"exit":.30,"dwell_seconds":.12,"release_seconds":.10,"cooldown_seconds":.30}}
    for name,value in totals.items():
        delays=value.pop("delays_seconds")
        tp,fp,miss=value['true_commands'],value['false_or_duplicate_commands'],value['missed_gestures']
        metrics[name]={**value,"command_precision":tp/(tp+fp) if tp+fp else None,
                       "gesture_recall":tp/(tp+miss) if tp+miss else None,
                       "mean_matched_activation_delay_seconds":sum(delays)/len(delays) if delays else None}
    delay=metrics['filtered']['mean_matched_activation_delay_seconds']
    delay_text=f"{delay:.3f}s" if delay is not None else "N/A"
    report=f"""# Gesture command admission

Topic: vision interfaces. Decision: turn one held pinch into one command while withholding commands during uncertain detections.

The baseline triggers on each raw threshold edge and resets on a missing frame. My temporal state machine requires sustained entry, uses a separate release threshold, and preserves an active latch through occlusion until release is actually observed. This adds delay and can miss short gestures.

On {len(test)} held-out synthetic episodes containing {metrics['test_gestures']} gestures, raw edges emit {metrics['raw_edges']['false_or_duplicate_commands']} false/duplicate commands and match {metrics['raw_edges']['true_commands']} gestures. Filtering emits {metrics['filtered']['false_or_duplicate_commands']} false/duplicate commands and matches {metrics['filtered']['true_commands']}, with {delay_text} mean matched activation delay. Every emitted timestamp is retained in decisions.json.

These are post-detector geometric fixtures, not measured OpenCV/MediaPipe recognition, camera FPS, real-person robustness or accessibility validation. The threshold contract is fixed before test evaluation. Next, I would collect consented landmark streams and test the safety-versus-delay tradeoff across users and camera conditions.
"""
    return metrics,raw,None,report
