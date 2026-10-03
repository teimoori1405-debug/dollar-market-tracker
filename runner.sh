#!/data/data/com.termux/files/usr/bin/bash

LOG_FILE="/data/data/com.termux/files/home/projects/dollar-db/runner.log"
SCRIPT="/data/data/com.termux/files/home/projects/dollar-db/tracker_with_eitaa.py"

echo "=== Runner started at $(date) ===" >> "$LOG_FILE"

while true; do
    HOUR=$(date +%H)

    # فقط بین ساعت 9 تا 14 (9,10,11,12,13)
    if [ "$HOUR" -ge 9 ] && [ "$HOUR" -lt 14 ]; then
        echo "--- Run at $(date) ---" >> "$LOG_FILE"
        python "$SCRIPT" >> "$LOG_FILE" 2>&1
    else
        echo "--- Skip at $(date) (outside 9-14) ---" >> "$LOG_FILE"
    fi

    sleep 1800
done
