# 輸入照片（不放在 repo 裡）

把自己的照片放進這個資料夾，檔名固定如下。`rebuild.sh` 會把它們上傳到 Colab。

| 檔名 | 內容 | 用途 |
|---|---|---|
| `fam_3.jpeg` | 全家福全身照：爸爸、媽媽、小孩、狗狗，大家看鏡頭 | workflow 的 `image_1`：主要參考（姿勢不變版也當底圖） |
| `fam_5.jpeg` | 三人臉部特寫（左爸爸、中小孩、右媽媽） | workflow 的 `image_2`：幫忙對臉 |
| `fam_1.jpeg`、`fam_2.jpeg`、`fam_4.jpeg`、`fam_6.jpeg` | 同一家人的其他照片 | 只給 `faces.py refs` 算每個人的「平均臉」，用來打分數 |

注意：
- `faces.py` 會依照 `fam_5.jpeg` 裡臉的左右位置，分出爸爸、小孩、媽媽。
- 換了照片，就要調整 `faces.py` 裡的位置規則，以及提示詞裡對照片的描述（`themes20.py`、`themes_pose.py`）。
