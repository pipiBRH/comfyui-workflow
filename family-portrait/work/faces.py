"""Face check with insightface buffalo_l (runs on the VM in /content/fvenv).
  faces.py refs                      -> find the 3 people in the 6 family photos, save their mean face embeddings
  faces.py score <png dir|files...>  -> per image: how close each generated face is to the real father / mother / boy
"""
import sys, os, json, glob
import numpy as np, cv2
from insightface.app import FaceAnalysis

app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
app.prepare(ctx_id=-1, det_size=(640, 640))
REF = "/content/famjob/ref_faces.json"

def faces_of(path):
    im = cv2.imread(path)
    out = []
    for f in app.get(im):
        e = f.normed_embedding
        out.append({"box": [int(v) for v in f.bbox], "det": round(float(f.det_score), 2), "age": int(f.age),
                    "sex": "M" if f.gender == 1 else "F", "emb": e.tolist(), "w": int(f.bbox[2] - f.bbox[0])})
    return im.shape, out

if sys.argv[1] == "refs":
    allf = []
    for i in range(1, 7):
        shape, fs = faces_of(f"/content/famjob/uploads/fam_{i}.jpeg")
        for f in fs:
            f["photo"] = i; allf.append(f)
    E = np.array([f["emb"] for f in allf])
    S = E @ E.T
    # greedy clustering: faces of the same person score far higher than faces of different people
    lab = [-1] * len(allf); k = 0
    for i in range(len(allf)):
        if lab[i] < 0:
            for j in range(len(allf)):
                if lab[j] < 0 and S[i, j] > 0.3:
                    lab[j] = k
            k += 1
    people = {}
    for c in range(k):
        idx = [i for i in range(len(allf)) if lab[i] == c]
        # name each group by where that person is in photo 5 (close-up: father left, boy middle, mother right)
        in5 = [allf[i]["box"][0] for i in idx if allf[i]["photo"] == 5]
        if in5:
            name = "father" if in5[0] < 300 else ("boy" if in5[0] < 500 else "mother")
        else:
            name = "dog" if len(idx) >= 2 else f"other{c}"   # the detector also finds the dog's face in photos 1 and 6
        mean = E[idx].mean(0); mean /= np.linalg.norm(mean)
        people.setdefault(name, {"members": [], "mean": None})
        people[name]["members"] += [{"photo": allf[i]["photo"], "box": allf[i]["box"], "w": allf[i]["w"], "age": allf[i]["age"],
                                     "sex": allf[i]["sex"], "sim_to_mean": round(float(E[i] @ mean), 3)} for i in idx]
        people[name]["mean"] = mean.tolist()
    for n, p in people.items():
        print(n)
        for m in p["members"]:
            print("   ", m)
    json.dump(people, open(REF, "w"))
    # how alike two different real photos of the same person are (the best a generated face can hope for)
    for n, p in people.items():
        idx = [i for i in range(len(allf)) if any(allf[i]["photo"] == m["photo"] and allf[i]["box"] == m["box"] for m in p["members"])]
        pair = [float(S[a, b]) for a in idx for b in idx if a < b]
        if pair:
            print(f"{n}: real photo vs real photo similarity  median {np.median(pair):.2f}  min {min(pair):.2f}  max {max(pair):.2f}")
else:
    people = {n: np.array(p["mean"]) for n, p in json.load(open(REF)).items() if n in ("father", "mother", "boy")}
    names = list(people)
    files = []
    for a in sys.argv[2:]:
        files += sorted(glob.glob(f"{a}/*.png")) if os.path.isdir(a) else [a]
    report = {}
    for path in files:
        shape, fs = faces_of(path)
        fs = [f for f in fs if f["det"] > 0.5]
        # only count human faces: the dog's face is sometimes detected too, but looks like none of the three people
        fs = [f for f in fs if max(float(np.array(f["emb"]) @ people[n]) for n in names) >= 0.3]
        # every real person gets the best-matching face (one face per person)
        pairs = sorted(((float(np.array(f["emb"]) @ people[n]), fi, n) for fi, f in enumerate(fs) for n in names), reverse=True)
        used_f, got = set(), {}
        for s, fi, n in pairs:
            if fi in used_f or n in got:
                continue
            used_f.add(fi); got[n] = (round(s, 3), fs[fi]["w"])
        extra = len(fs) - len(got)
        row = {n: got.get(n, (0.0, 0)) for n in names}
        report[os.path.basename(path)] = {"faces": len(fs), "extra_faces": extra, **{n: row[n][0] for n in names},
                                          "min": min(row[n][0] for n in names), "face_px": {n: row[n][1] for n in names}}
        r = report[os.path.basename(path)]
        print(f"{os.path.basename(path):40s} faces={len(fs)} " + " ".join(f"{n}={row[n][0]:.2f}({row[n][1]}px)" for n in names) + f"  min={r['min']:.2f}", flush=True)
    json.dump(report, open("/content/famjob/face_scores.json", "w"), indent=1)
