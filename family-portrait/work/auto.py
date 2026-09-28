"""Make one good image per theme: generate, check the faces on the VM, and re-roll the seed until it passes.

A result passes when insightface finds exactly 3 faces (nobody drawn twice) and every person scores >= MIN_SIM
against the real photos. Results so far are kept in auto_state.json, so the script can be restarted.
usage: auto.py                         20 option-A themes (themes20 -> batch20/, auto_state.json)
       auto.py --themes themes_pose --variant a --only P02,P03
                                      pose themes (-> batch_pose/, pose_state.json)
Runs until every theme passed or used MAX_TRIES seeds.
"""
import os, re, json, time, subprocess, sys, argparse, importlib
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ".")
from comfy_client import submit, _get, fetch
from family_graphs import graph

ap = argparse.ArgumentParser()
ap.add_argument("--themes", default="themes20")
ap.add_argument("--variant", default="a", help="reference set of the themes module (themes_pose: a = photos 3+5, b = 3+5+2)")
ap.add_argument("--only", default="", help="comma list of theme keys")
ap.add_argument("--tag", default="", help="suffix for the file names, e.g. the variant")
ap.add_argument("--max-tries", type=int, default=4)
args = ap.parse_args()
mod = importlib.import_module(args.themes)
if hasattr(mod, "VARIANT"):
    mod.VARIANT = args.variant
THEMES, prompt = mod.THEMES, mod.prompt
refs_of = getattr(mod, "refs", lambda t: ["fam_3.jpeg", "fam_5.jpeg"])
if args.only:
    THEMES = [t for t in THEMES if t[0] in args.only.split(",")]
OUT, STATE, SUB = ("batch20", "auto_state.json", "family") if args.themes == "themes20" else ("batch_pose", f"pose_state{args.tag}.json", "family_pose")

MIN_SIM, MAX_TRIES = 0.65, args.max_tries
SEEDS = [201, 301, 401, 501, 601]
FVM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "colab_ssh", "fvm")
os.makedirs(OUT, exist_ok=True); os.makedirs("api", exist_ok=True)
st = json.load(open(STATE)) if os.path.exists(STATE) else {}


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def save():
    json.dump(st, open(STATE, "w"), ensure_ascii=False, indent=1)


def score(vm_path):
    out = subprocess.run([FVM, f"cd /content/famjob && /content/fvenv/bin/python faces.py score '{vm_path}' 2>/dev/null | grep faces="],
                         capture_output=True, text=True, timeout=300).stdout
    m = re.search(r"faces=(\d+) boy=([\d.-]+).*mother=([\d.-]+).*father=([\d.-]+).*min=([\d.-]+)", out)
    if not m:
        return None
    n, boy, mom, dad, mn = m.groups()
    return {"faces": int(n), "boy": float(boy), "mother": float(mom), "father": float(dad), "min": float(mn)}


def ok(s):
    return s is not None and s["faces"] == 3 and s["min"] >= MIN_SIM


def launch(t, seed):
    name = f"{t[0]}{args.tag}_{t[1]}_s{seed}"
    g = graph(name, prompt(t), refs_of(t), seed, resolution=2048)
    g["60"]["inputs"]["filename_prefix"] = f"{SUB}/{name}"
    json.dump(g, open(f"api/{name}.json", "w"), ensure_ascii=False, indent=1)
    st[t[0] + args.tag]["tries"].append({"seed": seed, "name": name, "pid": submit(g), "score": None, "refs": refs_of(t)})
    save(); log("queued", name)


for t in THEMES:
    st.setdefault(t[0] + args.tag, {"theme": t[1], "tries": []})
    tries = st[t[0] + args.tag]["tries"]
    if not any(ok(x["score"]) for x in tries) and not any(x["score"] is None for x in tries) and len(tries) < MAX_TRIES:
        launch(t, next(s for s in SEEDS if s not in [x["seed"] for x in tries]))

while True:
    mine = {t[0] + args.tag: t for t in THEMES}
    pending = [(k, x) for k, v in st.items() if k in mine for x in v["tries"] if x["score"] is None]
    if not pending:
        break
    time.sleep(15)
    for k, x in pending:
        h = _get(f"/history/{x['pid']}")
        if x["pid"] not in h:
            continue
        ims = [im for n in h[x["pid"]]["outputs"].values() for im in n.get("images", [])]
        if not ims:
            x["score"] = {"faces": 0, "boy": 0, "mother": 0, "father": 0, "min": 0, "error": True}; save(); continue
        im = ims[0]
        fetch(im, f"{OUT}/{x['name']}.png")
        s = score(f"/content/ComfyUI/output/{im['subfolder']}/{im['filename']}") or {"faces": -1, "boy": 0, "mother": 0, "father": 0, "min": 0}
        x["score"] = s; save()
        verdict = "PASS" if ok(s) else "retry"
        log(f"{x['name']}: faces={s['faces']} boy={s['boy']:.2f} mother={s['mother']:.2f} father={s['father']:.2f} -> {verdict}")
        t = mine[k]
        if not ok(s) and len(st[k]["tries"]) < MAX_TRIES and not any(ok(y["score"]) for y in st[k]["tries"]):
            launch(t, next(sd for sd in SEEDS if sd not in [y["seed"] for y in st[k]["tries"]]))

# pick the best try per theme: nobody drawn twice first, then the weakest face score
for k, v in st.items():
    if not v["tries"] or any(x["score"] is None for x in v["tries"]):
        continue
    best = max(v["tries"], key=lambda x: (x["score"]["faces"] == 3, x["score"]["min"]))
    v["best"] = best["name"]
save()
log("ALL DONE")
for k, v in st.items():
    if "best" not in v:
        continue
    b = next(x for x in v["tries"] if x["name"] == v["best"])
    print(k, v["best"], b["score"], "PASS" if ok(b["score"]) else "best-effort")
