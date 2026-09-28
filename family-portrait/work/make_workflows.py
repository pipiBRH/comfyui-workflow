"""Back up the ComfyUI workflows (UI format, drag into ComfyUI to load).

- workflow/全家福_A_範本.json : the option-A graph with theme 01, a Chinese note, fixed seed
- workflow/<theme>.json       : the exact graph (prompt + seed) of each delivered picture
- the same UI workflow is written into each delivered PNG, so dragging the picture into ComfyUI also loads it
usage: make_workflows.py                  option A (auto_state.json, batch20/ -> 20組/, workflow/)
       make_workflows.py --pose           new poses (pose_state.json, batch_pose/ -> 20組_姿勢變化/, workflow/姿勢變化/)
"""
import json, os, copy, sys
from PIL import Image, PngImagePlugin
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the folder that holds work/, 20組/, workflow/
os.chdir(os.path.dirname(os.path.abspath(__file__)))
tpl = json.load(open("ui_template_raw.json"))

POSE = "--pose" in sys.argv
NOTE_HEAD = ("## 全家福（姿勢變化）\n照片3是全家人的參考，照片5幫忙對臉；姿勢、衣服、場景都是新的。\n\n" if POSE else
             "## 全家福（方法 A）\n照片3當底圖，只換衣服和背景，姿勢不變；照片5幫忙對臉。\n\n")
NOTE = (NOTE_HEAD +
        "1. 把 `fam_3.jpeg`（全家福全身照：爸爸、媽媽、小孩、狗狗）和 `fam_5.jpeg`（三人臉部特寫）放進 ComfyUI/input，或在 Load Image 上傳\n" +
        ("2. 在 Text Encode Qwen Image 2.1 改文字：`New pose: …`（姿勢）、`Outfits: …`（衣服）、`Setting: …`（場景）\n" if POSE else
         "2. 在 Text Encode Qwen Image 2.1 改文字：`Dress the father in …, the mother in …, the boy in …` 和 `Replace the white studio room with …`\n") +
        "3. 想要同一套衣服的不同版本：改 KSampler 的 seed\n\n"
        "模型（Comfy-Org/Qwen-Image-2.1）：\n"
        "- diffusion_models/qwen_image_2.1_bf16.safetensors\n"
        "- text_encoders/qwen3vl_8b_bf16.safetensors\n"
        "- vae/qwen_image_2.1_vae_bf16.safetensors\n\n"
        "設定：resolution 2048、25 steps、cfg 1、euler / simple。A100 一張約 2 分鐘。")


def tidy(wf):
    """readable layout + fixed seed + usage note"""
    pos = {1: (100, 130), 2: (420, 130), 3: (100, 280), 4: (100, 440), 11: (100, 560), 12: (100, 920),
           20: (420, 280), 40: (1000, 130), 50: (1320, 130), 60: (1320, 230)}
    size = {20: (540, 560), 60: (560, 900), 11: (280, 330), 12: (280, 330)}
    for n in wf["nodes"]:
        if n["id"] in pos:
            n["pos"] = list(pos[n["id"]])
        if n["id"] in size:
            n["size"] = list(size[n["id"]])
        if n["type"] == "KSampler":
            n["widgets_values"][1] = "fixed"
    wf["nodes"] = [n for n in wf["nodes"] if n["type"] != "MarkdownNote"]
    nid = max(n["id"] for n in wf["nodes"]) + 1
    wf["nodes"].append({"id": nid, "type": "MarkdownNote", "pos": [420, 880], "size": [540, 420], "flags": {}, "order": 0,
                        "mode": 0, "inputs": [], "outputs": [], "properties": {}, "widgets_values": [NOTE],
                        "title": "使用說明", "color": "#432", "bgcolor": "#653"})
    wf["last_node_id"] = max(wf.get("last_node_id", 0), nid)
    return wf


def variant(api):
    """the template with the prompt / seed / file name of one API graph"""
    wf = tidy(copy.deepcopy(tpl))
    for n in wf["nodes"]:
        if n["type"] == "TextEncodeQwenImage21":
            n["widgets_values"][0] = api["20"]["inputs"]["prompt"]
            n["widgets_values"][2] = api["20"]["inputs"]["resolution"]
        elif n["type"] == "KSampler":
            n["widgets_values"][0] = api["40"]["inputs"]["seed"]
        elif n["type"] == "SaveImage":
            n["widgets_values"][0] = api["60"]["inputs"]["filename_prefix"]
        elif n["type"] == "LoadImage":
            n["widgets_values"][0] = api[str(n["id"])]["inputs"]["image"]
    return wf


if __name__ == "__main__":
    state, batch, out_dir, wf_dir, tpl_name = (("pose_state.json", "batch_pose", f"{BASE}/20組_姿勢變化", f"{BASE}/workflow/姿勢變化", "全家福_姿勢變化_範本.json")
                                               if POSE else ("auto_state.json", "batch20", f"{BASE}/20組", f"{BASE}/workflow", "全家福_A_範本.json"))
    os.makedirs(wf_dir, exist_ok=True)
    st = json.load(open(state))
    first = json.load(open(f"api/{sorted(st.items())[0][1]['best']}.json"))
    json.dump(variant(first) if POSE else tidy(copy.deepcopy(tpl)), open(f"{wf_dir}/{tpl_name}", "w"), ensure_ascii=False, indent=1)
    os.makedirs(out_dir, exist_ok=True)
    for k, v in sorted(st.items()):
        name = v["best"]
        api = json.load(open(f"api/{name}.json"))
        wf = variant(api)
        json.dump(wf, open(f"{wf_dir}/{k}_{v['theme']}.json", "w"), ensure_ascii=False, indent=1)
        # copy the picture with the UI workflow + API prompt in the PNG text chunks (pixels untouched)
        im = Image.open(f"{batch}/{name}.png")
        meta = PngImagePlugin.PngInfo()
        meta.add_text("prompt", json.dumps(api, ensure_ascii=False))
        meta.add_text("workflow", json.dumps(wf, ensure_ascii=False))
        im.save(f"{out_dir}/{k}_{v['theme']}.png", pnginfo=meta)
        print("wrote", k, v["theme"], "from", name)
