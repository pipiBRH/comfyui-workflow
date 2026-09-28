"""Family portrait job on the Colab VM. Stages: setup download prepare start gen:<batch.json> faces:<batch.json>
Everything is logged to stdout (redirected to /content/family.log by the launcher)."""
import os, sys, json, time, shutil, subprocess, urllib.request, glob

COMFY, VENV = "/content/ComfyUI", "/content/venv"
PY, HF = f"{VENV}/bin/python", f"{VENV}/bin/hf"
COMFY_COMMIT = "4ef23c34d950eecc37040a21ee1741a49d2e44b1"
URL, COMFY_LOG = "http://127.0.0.1:8188", "/content/comfyui.log"
STATE = "/content/family_state.json"
JOB = "/content/famjob"

def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)

def run(cmd, env=None):
    log("$", cmd[:200])
    p = subprocess.run(cmd, shell=True, env=env)
    if p.returncode != 0:
        raise RuntimeError(f"command failed ({p.returncode}): {cmd[:200]}")

def state(**kw):
    s = json.load(open(STATE)) if os.path.exists(STATE) else {}
    s.update(kw); json.dump(s, open(STATE, "w"), indent=1)

def setup():
    q = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version,compute_cap",
                        "--format=csv,noheader,nounits"], capture_output=True, text=True)
    name, mem, drv, cc = [x.strip() for x in q.stdout.strip().splitlines()[0].split(",")]
    ram = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1e9
    disk = shutil.disk_usage("/content").free / 1e9
    log(f"GPU {name} {float(mem)/1024:.0f}GB driver {drv} cc {cc} | RAM {ram:.0f}GB | disk free {disk:.0f}GB")
    try:
        log("VM country:", json.load(urllib.request.urlopen("https://ipinfo.io/json", timeout=10)).get("country"))
    except Exception as e:
        log("country lookup failed", e)
    drv_major, ccf = int(drv.split(".")[0]), float(cc)
    idx0 = "cu130" if drv_major >= 580 else ("cu128" if ccf >= 10 else "cu126")
    if not os.path.exists(f"{COMFY}/main.py"):
        shutil.rmtree(COMFY, ignore_errors=True)
        run(f"git init -q {COMFY} && cd {COMFY} && git remote add origin https://github.com/Comfy-Org/ComfyUI.git "
            f"&& git fetch -q --depth 1 origin {COMFY_COMMIT} && git checkout -q FETCH_HEAD")
    if shutil.which("uv") is None:
        run("pip install -q uv")
    if not os.path.exists(PY):
        run(f"uv venv -q --python 3.12 {VENV}")
    for idx in dict.fromkeys([idx0, "cu128", "cu126"]):
        try:
            run(f"uv pip install -q --python {PY} torch torchvision --index-url https://download.pytorch.org/whl/{idx}")
            break
        except RuntimeError:
            log(f"torch {idx} failed, trying next")
    run(f"uv pip install -q --python {PY} -r {COMFY}/requirements.txt 'huggingface_hub[hf_xet]'")
    out = subprocess.run([PY, "-c", "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"],
                         capture_output=True, text=True)
    log("torch:", out.stdout.strip(), out.stderr[-300:])
    state(setup="ok", torch=out.stdout.strip())

def hf_get(args):
    # HF rate-limits (429) aggressive parallel xet downloads without a token: retry, then fall back to plain HTTP
    for attempt in range(8):
        env = dict(os.environ, HF_HUB_DISABLE_XET="1") if attempt >= 2 else dict(os.environ)
        try:
            return run(f"{HF} download {args}", env=env)
        except RuntimeError:
            log(f"download attempt {attempt + 1} failed, retrying in {20 * (attempt + 1)} s")
            time.sleep(20 * (attempt + 1))
    raise RuntimeError("download failed: " + args)


def download():
    m = f"{COMFY}/models"
    # Qwen-Image 2.1, the official full-precision release (same model as the GGUF repo, without the uncensored merge)
    hf_get("Comfy-Org/Qwen-Image-2.1 diffusion_models/qwen_image_2.1_bf16.safetensors "
           f"text_encoders/qwen3vl_8b_bf16.safetensors vae/qwen_image_2.1_vae_bf16.safetensors --local-dir {m}")
    run(f"du -sh {m}/diffusion_models {m}/text_encoders {m}/vae")
    state(download="ok")

def prepare():
    inp = f"{COMFY}/input"; os.makedirs(inp, exist_ok=True)
    for f in glob.glob(f"{JOB}/uploads/*"):
        shutil.copy(f, f"{inp}/{os.path.basename(f)}")
    log("inputs:", sorted(os.listdir(inp)))
    state(prepare="ok")

def comfy_up():
    try:
        return urllib.request.urlopen(f"{URL}/system_stats", timeout=5).status == 200
    except Exception:
        return False

def start():
    if not comfy_up():
        subprocess.Popen([PY, "main.py", "--listen", "127.0.0.1", "--port", "8188", "--disable-auto-launch"],
                         cwd=COMFY, stdout=open(COMFY_LOG, "a"), stderr=subprocess.STDOUT, start_new_session=True,
                         env=dict(os.environ, PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"))
        for _ in range(240):
            if comfy_up():
                break
            time.sleep(2)
    assert comfy_up(), open(COMFY_LOG).read()[-3000:]
    log("ComfyUI is up")
    state(comfy="up")


def last_progress():
    try:
        with open(COMFY_LOG, "rb") as f:
            f.seek(max(0, os.path.getsize(COMFY_LOG) - 4000)); tail = f.read().decode(errors="ignore")
    except OSError:
        return ""
    import re
    bits = [b.strip() for b in re.split(r"[\r\n]", tail) if re.search(r"\d+/\d+ \[", b)]
    return bits[-1][-80:] if bits else ""

def gen(batch):
    """Queue every graph of a batch file ({name: api_graph}), wait for all, copy the images to /content/outputs/<batch>/."""
    jobs = json.load(open(f"{JOB}/{batch}"))
    tag = os.path.splitext(batch)[0]
    out_dir = f"/content/outputs/{tag}"; os.makedirs(out_dir, exist_ok=True)
    pids = {}
    for name, g in jobs.items():
        req = urllib.request.Request(f"{URL}/prompt", data=json.dumps({"prompt": g}).encode(), headers={"Content-Type": "application/json"})
        try:
            pids[name] = json.load(urllib.request.urlopen(req))["prompt_id"]
        except urllib.error.HTTPError as e:
            log("VALIDATION ERROR", name, e.read().decode()[:2000]); state(job="validation_error"); raise
    log(f"queued {len(pids)} graphs from {batch}"); state(job="running", batch=batch, total=len(pids), done=0)
    t0, done, errors, last = time.time(), {}, {}, 0
    while len(done) + len(errors) < len(pids):
        time.sleep(5)
        for name, pid in pids.items():
            if name in done or name in errors:
                continue
            h = json.load(urllib.request.urlopen(f"{URL}/history/{pid}"))
            if pid not in h:
                continue
            st = h[pid]["status"]
            if st.get("status_str") != "success":
                errors[name] = [m[1] for m in st.get("messages", []) if m[0] == "execution_error"]
                log("EXECUTION ERROR", name, json.dumps(errors[name])[:1500]); continue
            for node in h[pid]["outputs"].values():
                for im in node.get("images", []):
                    if im.get("type") == "output":
                        shutil.copy(f"{COMFY}/output/{im['subfolder']}/{im['filename']}", f"{out_dir}/{name}.png")
                        done[name] = f"{out_dir}/{name}.png"
            log(f"done {name} ({len(done)}/{len(pids)}) {(time.time()-t0)/60:.1f} min")
            state(done=len(done))
        if time.time() - last > 60:
            log(f"progress {len(done)}/{len(pids)} | {last_progress()}"); last = time.time()
    log(f"DONE {batch} in {(time.time()-t0)/60:.1f} min: {len(done)} ok, {len(errors)} errors")
    state(job="done" if not errors else "error", minutes=round((time.time()-t0)/60, 1))

def faceenv():
    """separate venv with insightface (buffalo_l) for the face-likeness check"""
    run("uv venv -q --python 3.12 /content/fvenv && uv pip install -q --python /content/fvenv/bin/python "
        "insightface==0.7.3 onnxruntime opencv-python-headless numpy scipy")
    # colab exec runs inside Jupyter, whose MPLBACKEND (inline) breaks matplotlib outside a notebook
    os.environ["MPLBACKEND"] = "Agg"
    run("/content/fvenv/bin/python -c \"from insightface.app import FaceAnalysis; FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])\"")
    run(f"cd {JOB} && /content/fvenv/bin/python faces.py refs")   # mean face of each real person -> ref_faces.json
    state(faceenv="ok")

if __name__ == "__main__":
    for stage in sys.argv[1:]:
        log("===== stage", stage)
        name, *args = stage.split(":")
        {"setup": setup, "download": download, "prepare": prepare, "start": start, "gen": gen, "faceenv": faceenv}[name](*args)
    log("===== all stages finished")
