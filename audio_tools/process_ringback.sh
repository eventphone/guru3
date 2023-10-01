#!/bin/bash
set -e
# config
music_dB="-5.0"
beep_dB="-15.0"

INFILE1="/input/${1}"
INFILE2="/tools/1TR110-freiton.mp3"
INHASH=$(sha512sum  "${INFILE1}" | gawk '{print $1}')
OUTFILE="/output_ringback/${INHASH}.slin"
OUTFILE_PLAIN="/output_plain/${INHASH}.slin"
duration1=$(sox "${INFILE1}" -n stat 2>&1 | sed -n 's#^Length (seconds):[^0-9]*\([0-9.]*\)$#\1#p')
duration2=$(sox "${INFILE2}" -n stat 2>&1 | sed -n 's#^Length (seconds):[^0-9]*\([0-9.]*\)$#\1#p')

echo "Music Duration:    ${duration1}"
echo "Beepfile Duration: ${duration2}"

# prepare tmp files
mixtmp1=$(mktemp --suffix=.wav)
mixtmp2=$(mktemp --suffix=.wav)
mixtmp3=$(mktemp --suffix=.wav)

sox -q "${INFILE2}" --norm=${beep_dB} -c 1 -r 48000 "${mixtmp2}"                     # normalize ringtone and monoize file
sox -q "${INFILE1}" --norm=${music_dB} -c 1 -r 48000 "${mixtmp1}"                    # normalize music and monoize file
sox -q "${mixtmp1}" -t raw -r 8000 -c 1 "${OUTFILE_PLAIN}"                           # output plain file without ringtone
sox -q -t sox "|sox \"${mixtmp1}\" -p repeat 100" "${mixtmp3}" trim 0 "${duration2}" # repeat the music file 100 times and trim when INFILE2 ends
sox -q -m "${mixtmp2}" "${mixtmp3}" -t raw -r 8000 -c 1 "${OUTFILE}"                 # mix da files
rm "${mixtmp1}" "${mixtmp2}" "${mixtmp3}"                                            # cleanup temp files
