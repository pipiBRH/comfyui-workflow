# 全家福：Qwen-Image 2.1（ComfyUI）

用幾張家人照片，做出新的全家福。
- **臉和身材**：照參考照片。
- **衣服、場景、姿勢**：都可以換。
- 不用換臉工具，也不用修臉工具。臉是 Qwen-Image 2.1 參考照片直接畫出來的。畫完再用人臉辨識檢查像不像。

兩種 workflow：

| 資料夾 | 做法 |
|---|---|
| `workflow/`（方法 A） | 照片3當底圖，只換衣服和背景，**姿勢不變**。臉最像。範本加 20 組主題。 |
| `workflow/姿勢變化/` | 用照片3這家人拍一張新照片：**新姿勢**、新衣服、新場景。範本加 20 組姿勢。 |

每個 JSON 都是 ComfyUI 的 UI 格式，直接拖進 ComfyUI 就能開。

## 需要的模型（Hugging Face：`Comfy-Org/Qwen-Image-2.1`）

| 放到 `ComfyUI/models/` | 檔案 |
|---|---|
| `diffusion_models/` | `qwen_image_2.1_bf16.safetensors`（14 GB） |
| `text_encoders/` | `qwen3vl_8b_bf16.safetensors`（17.5 GB） |
| `vae/` | `qwen_image_2.1_vae_bf16.safetensors` |

- 需要支援 Qwen-Image 2.1 的 ComfyUI。這裡用的是 commit `4ef23c34`（ComfyUI 0.37）。
- 輸入照片放到 `ComfyUI/input`，檔名與用途見 `work/photos/README.md`。

## workflow 做了什麼

```
UNETLoader ─► QwenImage21Cache ─────────────────────► KSampler ─► VAEDecode ─► SaveImage
CLIPLoader (qwen_image) ─┐                               ▲
VAELoader ───────────────┼─► TextEncodeQwenImage21 ──────┘ (positive / negative / latent)
LoadImage fam_3 (image_1)┤     resolution 2048
LoadImage fam_5 (image_2)┘
```

- **TextEncodeQwenImage21**：同時看提示詞和兩張照片。
  - 照片會給 Qwen3-VL 看懂。
  - 照片也會轉成 VAE latent，直接放進畫圖過程當參考。
  - `resolution 2048`：參考圖放大到約 1664×2496，臉在模型裡比較大，比較像本人。
  - 輸出的空白 latent 跟 `image_1` 一樣大。
- **QwenImage21Cache**：把參考圖的部分先算好存起來，每一步不用重算。只影響速度，不影響畫面。
- **KSampler**：25 步、cfg 1、euler / simple、denoise 1。cfg 1 代表不使用負面提示詞。
- **提示詞寫法**（照 Qwen 官方 prompt enhancer 的原則）：
  - 先說要做什麼操作。
  - 用 `<image1>`、`<image2>` 指出每張圖的用途。
  - 只寫「臉、髮型、身材、身高照參考照片」，不用文字描述長相。用文字描述，AI 會照文字重新想像，反而比較不像。
  - 加一句「三個人加一隻狗，每個只出現一次」，避免有人被畫兩次。

## 臉像不像：自動檢查（不在 ComfyUI 裡）

`work/auto.py` 會重複做下面這些事：
1. 送出一張圖。
2. 畫好後，在 Colab 上用 `work/faces.py`（insightface buffalo_l）檢查：
   - **人數**：必須剛好 3 張人臉。狗臉不算。
   - **相似度**：跟每個人「6 張照片的平均臉」比對，每個人都要 ≥ 0.65。
     - 參考值：同一個人兩張真照片互比，大約是爸爸 0.78、媽媽 0.71、小孩 0.64。
3. 不合格就換 seed 重畫，最多 4 次，最後留分數最高的那張。

這個檢查只負責挑圖，不會改動任何像素。

## 用 Colab CLI 跑（`work/`）

```sh
cd work
./rebuild.sh                        # 開 A100，裝 ComfyUI + torch，下載模型，裝 insightface（約 4 分鐘）
./colab_ssh/tunnel_family.sh &      # localhost:8188 → Colab ComfyUI（第一次會自動產生 ed25519 金鑰）
python3 auto.py                                           # 方法 A：20 組（themes20.py）
python3 auto.py --themes themes_pose --variant a          # 姿勢變化：20 組（themes_pose.py）
python3 make_workflows.py [--pose]  # 產生 UI workflow，並把 workflow 寫進成品 PNG
python3 sheet.py pose_state.json batch_pose sheet.jpg     # 總覽圖
colab stop -s family                # 一定要關機，不然會一直扣 CU
```

| 檔案 | 用途 |
|---|---|
| `family_pipeline.py`、`launch.py`、`mkdirs.py` | 在 VM 上安裝和啟動（stages：setup download prepare start faceenv） |
| `family_graphs.py` | 產生 ComfyUI API graph |
| `comfy_client.py` | 透過通道送 graph、下載結果 |
| `themes20.py`、`themes_pose.py` | 20 組主題的文字 |
| `ui_template_raw.json` | 從 ComfyUI 前端匯出的 UI 範本（`make_workflows.py` 會用到） |

用過的經驗：
- 這個帳號只開得到 A100（`--gpu A100 --high-mem`），約 6.8 CU/小時，一張約 2 分鐘。
- Colab 不能暫停，`stop` 之後 `/content` 裡的東西都會清空。
- Colab SSH 只接受 ed25519 金鑰，而且每台 runtime 只能有一條 SSH 連線，所以用 ControlMaster 共用（`fvm` 走同一條）。
- `colab exec` 在 Jupyter 環境裡跑，`MPLBACKEND` 會讓 insightface 當掉，已經設成 `Agg`。
- Hugging Face 沒帶 token 下載太快會回 429。已經加了重試，並改回一般 HTTP 下載。

## 隱私
repo 裡**沒有**任何照片、生成圖、人臉資料（embedding、分數）或金鑰，`.gitignore` 也擋掉了這些檔案。

## 授權注意
- Qwen-Image 2.1 使用 qwen-research 授權。
- insightface 的 buffalo_l 模型只限非商業研究使用。
