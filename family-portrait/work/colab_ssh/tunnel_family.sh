#!/bin/sh
# Keep localhost:8188 -> Colab ComfyUI open; reconnect on drops, but never auto-create a VM.
# Makes its own ed25519 key on first use (Colab SSH rejects RSA keys). Only one SSH session is allowed
# per runtime, so this is the ControlMaster; run VM commands through ./fvm.
D=$(cd "$(dirname "$0")" && pwd)
KEY="$D/id_ed25519"; SOCK="$D/fam.sock"
[ -f "$KEY" ] || ssh-keygen -q -t ed25519 -N "" -f "$KEY"
while true; do
  ~/.local/bin/colab status -s family 2>&1 | grep -q "Hardware: A100" || { echo "$(date +%T) session family gone, tunnel loop stops"; break; }
  rm -f "$SOCK"
  ssh -M -S "$SOCK" -N -L 127.0.0.1:8188:127.0.0.1:8188 -o ProxyCommand="$HOME/.local/bin/colab ssh --proxy-mode -s family --identity $KEY" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -o ServerAliveInterval=15 -o ServerAliveCountMax=4 -o ExitOnForwardFailure=yes -o IdentitiesOnly=yes -i "$KEY" root@colab-runtime
  echo "$(date +%T) tunnel exited ($?), reconnecting in 5 s"
  sleep 5
done
