#!/bin/bash

# setup the sandbox
if [[ $# -ne 4 ]]; then
    echo "Usage: ${0} <input_dir> <output_dir_ringback> <output_dir_plain> <file_to_process>"
    exit 1
fi

THISDIR="$( cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd )"

bwrap --ro-bind /usr /usr --ro-bind /bin /bin --ro-bind /lib64 /lib64 --ro-bind /lib /lib \
      --proc /proc --tmpfs /tmp --dir /var \
      --unshare-user --unshare-net --unshare-pid \
      --ro-bind "${THISDIR}" "/tools" --ro-bind "${1}" "/input" --bind "${2}" "/output_ringback" \
      --bind "${3}" "/output_plain" \
      "/tools/process_ringback.sh" "${4}"
