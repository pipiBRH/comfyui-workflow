"""contact sheet of the passing (or best so far) image per theme -> sheet_best.jpg"""
import json, cv2, numpy as np, os, sys
# usage: sheet.py [state.json batch_dir out.jpg]
STATE, BATCH, OUT = sys.argv[1:4] if len(sys.argv) > 3 else ("auto_state.json", "batch20", "sheet_best.jpg")
st = json.load(open(STATE))
tiles = []
for k, v in sorted(st.items()):
    done = [x for x in v["tries"] if x["score"]]
    if not done:
        continue
    b = max(done, key=lambda x: (x["score"]["faces"] == 3, x["score"]["min"]))
    p = f"{BATCH}/{b['name']}.png"
    if not os.path.exists(p):
        continue
    im = cv2.resize(cv2.imread(p), (400, 600), interpolation=cv2.INTER_AREA)
    s = b["score"]
    cv2.putText(im, f"{k} s{b['seed']} f{s['faces']} {s['min']:.2f}", (8, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    tiles.append(im)
while len(tiles) % 5:
    tiles.append(np.zeros_like(tiles[0]))
cv2.imwrite(OUT, np.concatenate([np.concatenate(tiles[i:i + 5], 1) for i in range(0, len(tiles), 5)], 0), [cv2.IMWRITE_JPEG_QUALITY, 80])
print(len(tiles))
