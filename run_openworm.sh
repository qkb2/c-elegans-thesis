#!/bin/bash
set -ex

version=$(<VERSION) # Read version of Dockerfile from file VERSION

C302_PART=""

#from: https://unix.stackexchange.com/a/129401
while getopts ":d:c:n" opt; do
  case "${opt}" in
    d) duration="$OPTARG"
    ;;
    c) configuration="$OPTARG"
    ;;
    n) C302_PART="-e NOC302=1"
    ;;
    *) echo "Usage: $0 [-d duration_in_ms] [-c configuration] [-n]" >&2
       exit 1
    ;;
  esac
done

OW_OUT_DIR=/home/ow/shared
HOST_OUT_DIR=$PWD

xhost + || true # allow connections to X server, don't throw an error if it fails

if [ -z "$duration" ]
then
    DURATION_PART=""
else
    DURATION_PART="-e DURATION=$duration"
fi

if [ -z "$configuration" ]
then
    CONFIGURATION_PART=""
else
    CONFIGURATION_PART="-e CONFIGURATION=$configuration"
fi

echo "Running OpenWorm Docker container. Additional options: $DURATION_PART $CONFIGURATION_PART $C302_PART"

# Check and get list of all running containers
output=$(docker ps -a)

# Check if the openworm container is already running
if echo "$output" | grep -q "openworm_$version"; then
    echo -e "\n**************\n  Docker container openworm_$version is already running.\n  Please stop and remove it before running a new one (run: ./stop.sh).\n**************"
    exit 1
fi

echo "Running Docker container for OpenWorm v${version}"

CONTAINER_NAME="openworm_$version"

# --------------------------------------------------------------------
# Start wall-clock timer
# --------------------------------------------------------------------

START_TIME=$(date +%s.%N)

docker run -d \
--name "$CONTAINER_NAME" \
--device=/dev/dri:/dev/dri \
-e DISPLAY="$DISPLAY" \
$CONFIGURATION_PART \
$DURATION_PART \
$C302_PART \
-e OW_OUT_DIR="$OW_OUT_DIR" \
-v /tmp/.X11-unix:/tmp/.X11-unix:rw \
--privileged \
-v "$HOST_OUT_DIR:$OW_OUT_DIR:rw" \
"openworm/openworm:$version" \
bash -c "DISPLAY=:44 python3 master_openworm.py"

echo "Container started: $CONTAINER_NAME"

# --------------------------------------------------------------------
# Locate/create RAM log
# --------------------------------------------------------------------

mkdir -p "$HOST_OUT_DIR/measurements"

TIMESTAMP=$(date '+%Y-%m-%d_%H-%M-%S')

RAM_LOG="$HOST_OUT_DIR/measurements/ram_usage_${version}_${TIMESTAMP}.csv"

echo "timestamp,memory_bytes,memory_mb" > "$RAM_LOG"

# --------------------------------------------------------------------
# RAM monitoring
# --------------------------------------------------------------------

(
    while docker inspect -f '{{.State.Running}}' "$CONTAINER_NAME" 2>/dev/null | grep -q true
    do
        timestamp=$(date '+%Y-%m-%dT%H:%M:%S')

        memory_bytes=$(docker stats "$CONTAINER_NAME" \
            --no-stream \
            --format '{{.MemUsage}}' 2>/dev/null |
            awk '
            {
                split($1, a, /[[:space:]]*\//)
                value=a[1]

                if (value ~ /GiB$/) {
                    sub(/GiB$/, "", value)
                    print value * 1024 * 1024 * 1024
                }
                else if (value ~ /MiB$/) {
                    sub(/MiB$/, "", value)
                    print value * 1024 * 1024
                }
                else if (value ~ /KiB$/) {
                    sub(/KiB$/, "", value)
                    print value * 1024
                }
                else if (value ~ /B$/) {
                    sub(/B$/, "", value)
                    print value
                }
            }')

        if [ -n "$memory_bytes" ]; then
            memory_mb=$(awk "BEGIN {printf \"%.3f\", $memory_bytes / 1024 / 1024}")
            echo "$timestamp,$memory_bytes,$memory_mb" >> "$RAM_LOG"
        fi

        sleep 1
    done
) &

RAM_MONITOR_PID=$!

echo "RAM monitor PID: $RAM_MONITOR_PID"

# --------------------------------------------------------------------
# Attach to container logs
# --------------------------------------------------------------------

echo "Set running running Docker container with Sibernetic in detached mode. Attaching to logs now..."

docker logs -f "$CONTAINER_NAME" || true

# --------------------------------------------------------------------
# Stop timers / RAM monitor
# --------------------------------------------------------------------

wait "$RAM_MONITOR_PID" || true

END_TIME=$(date +%s.%N)

# Calculate elapsed time in seconds and minutes
ELAPSED_SECONDS=$(awk "BEGIN {printf \"%.3f\", $END_TIME - $START_TIME}")
ELAPSED_MINUTES=$(awk "BEGIN {printf \"%.3f\", $ELAPSED_SECONDS / 60}")

echo
echo "Finished running the Docker container"

# --------------------------------------------------------------------
# RAM statistics
# --------------------------------------------------------------------

if [ -f "$RAM_LOG" ] && [ "$(wc -l < "$RAM_LOG")" -gt 1 ]; then

    ram_stats=$(awk -F',' '
    NR > 1 {
        values[++n] = $3
        sum += $3
    }

    END {
        if (n == 0) {
            exit 1
        }

        avg = sum / n

        # Sort values numerically.
        for (i = 1; i <= n; i++) {
            for (j = i + 1; j <= n; j++) {
                if (values[j] < values[i]) {
                    tmp = values[i]
                    values[i] = values[j]
                    values[j] = tmp
                }
            }
        }

        if (n % 2 == 1) {
            median = values[(n + 1) / 2]
        } else {
            median = (values[n / 2] + values[n / 2 + 1]) / 2
        }

        printf "%.3f %.3f %d\n", avg, median, n
    }' "$RAM_LOG")

    read AVG_RAM MEDIAN_RAM SAMPLE_COUNT <<< "$ram_stats"

else
    AVG_RAM="N/A"
    MEDIAN_RAM="N/A"
    SAMPLE_COUNT=0
fi

# --------------------------------------------------------------------
# Print final benchmark statistics
# --------------------------------------------------------------------

echo
echo "=========================================="
echo "OpenWorm simulation statistics"
echo "=========================================="
echo "Runtime:       ${ELAPSED_MINUTES} min"
echo "Runtime:       ${ELAPSED_SECONDS} sec"
echo "RAM samples:   ${SAMPLE_COUNT}"
echo "Average RAM:   ${AVG_RAM} MB"
echo "Median RAM:    ${MEDIAN_RAM} MB"
echo "RAM log:       ${RAM_LOG}"
echo "=========================================="
echo

# --------------------------------------------------------------------
# Save summary
# --------------------------------------------------------------------

SUMMARY_FILE="${RAM_LOG%.csv}_stats.txt"

cat > "$SUMMARY_FILE" <<EOF
OpenWorm simulation statistics
==========================================
Runtime:       ${ELAPSED_MINUTES} min
Runtime:       ${ELAPSED_SECONDS} sec
RAM samples:   ${SAMPLE_COUNT}
Average RAM:   ${AVG_RAM} MB
Median RAM:    ${MEDIAN_RAM} MB
RAM log:       ${RAM_LOG}
==========================================
EOF

echo "Statistics saved to: $SUMMARY_FILE"

# --------------------------------------------------------------------
# Check simulation result
# --------------------------------------------------------------------

last_dir=$(ls -td output/*/ 2>/dev/null | head -n 1)

echo "Last created simulation directory: $last_dir"

if [ -n "$last_dir" ] && grep -q "ompleted successfully" "$last_dir/report.json"; then
    echo "Simulation has completed successfully."
else
    echo "Simulation has exited with an error."
    exit 1
fi
