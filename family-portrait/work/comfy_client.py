"""Tiny ComfyUI client used from the Mac through the SSH tunnel (localhost:8188 -> Colab)."""
import json, time, uuid, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"

def _get(path):
    return json.load(urllib.request.urlopen(URL + path, timeout=60))

def upload(path, name):
    """POST /upload/image (multipart) so LoadImage can use `name`."""
    b = uuid.uuid4().hex
    data = open(path, "rb").read()
    body = (f"--{b}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{name}\"\r\nContent-Type: image/png\r\n\r\n").encode() + data + \
           f"\r\n--{b}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n--{b}--\r\n".encode()
    req = urllib.request.Request(URL + "/upload/image", data=body, headers={"Content-Type": f"multipart/form-data; boundary={b}"})
    return json.load(urllib.request.urlopen(req, timeout=120))

def submit(graph):
    req = urllib.request.Request(URL + "/prompt", data=json.dumps({"prompt": graph}).encode(), headers={"Content-Type": "application/json"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=60))["prompt_id"]
    except urllib.error.HTTPError as e:
        raise RuntimeError(e.read().decode()[:3000])

def wait(pids, every=5, label=""):
    """Wait for {name: prompt_id}; returns {name: [image dicts]} and prints errors."""
    todo, out, t0 = dict(pids), {}, time.time()
    while todo:
        time.sleep(every)
        for name, pid in list(todo.items()):
            h = _get(f"/history/{pid}")
            if pid not in h:
                continue
            st = h[pid]["status"]
            del todo[name]
            if st.get("status_str") != "success":
                msgs = [m[1] for m in st.get("messages", []) if m[0] == "execution_error"]
                print("ERROR", name, json.dumps(msgs)[:1500]); continue
            out[name] = [im for node in h[pid]["outputs"].values() for im in node.get("images", [])]
            print(f"{label}done {name} after {time.time() - t0:.0f} s", flush=True)
    return out

def fetch(im, dest):
    q = urllib.parse.urlencode({"filename": im["filename"], "subfolder": im["subfolder"], "type": im["type"]})
    open(dest, "wb").write(urllib.request.urlopen(f"{URL}/view?{q}", timeout=300).read())
    return dest
