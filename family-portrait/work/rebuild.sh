#!/bin/sh
# Rebuild the family-portrait setup on a fresh Colab A100 and (re)make the 20 option-A pictures.
#   usage: ./rebuild.sh            then:  ./colab_ssh/tunnel_family.sh &   and   python3 auto.py
# Everything the VM needs is uploaded from this folder. When finished:  colab stop -s family
set -e
cd "$(dirname "$0")"
S=family
C=$(command -v colab || echo "$HOME/.local/bin/colab")
"$C" new -s $S --gpu A100 --high-mem
"$C" exec -s $S -f mkdirs.py
for f in family_pipeline.py launch.py faces.py; do "$C" upload -s $S "$f" "/content/famjob/$f"; done
for i in 1 2 3 4 5 6; do "$C" upload -s $S "photos/fam_$i.jpeg" "/content/famjob/uploads/fam_$i.jpeg"; done
# installs ComfyUI + torch, downloads Qwen-Image 2.1 (bf16), starts ComfyUI, installs insightface for the face check
"$C" exec -s $S --env FAM_STAGES="setup download prepare start faceenv" -f launch.py
echo "started: about 4 min of setup. Then open the tunnel (./colab_ssh/tunnel_family.sh &),"
echo "then run 'python3 auto.py' here (delete auto_state.json first to start from scratch)."
