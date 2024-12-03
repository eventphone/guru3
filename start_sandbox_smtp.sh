#!/bin/bash
set +x
THISDIR="$( cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd )"

bwrap --ro-bind /usr /usr --ro-bind /bin /bin --ro-bind /lib64 /lib64 --ro-bind /lib /lib \
      --proc /proc --tmpfs /tmp --dir /var \
      --unshare-user --unshare-pid \
      --ro-bind "${THISDIR}" "/app" --ro-bind /sbin /sbin \
      "/app/venv/bin/python3" "/app/smtp_register_bridge.py"
