#!/bin/bash
set -e

if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: $0 <iterations> <prd-file>"
  echo "Example: $0 10 docs/PRD-3.md"
  exit 1
fi

ITERATIONS="$1"
PRD_FILE="$2"

# Derive progress file from PRD filename: plans/PRD-3.md → plans/PRD-3-progress.txt
PRD_BASENAME=$(basename "$PRD_FILE" .md)
PRD_DIR=$(dirname "$PRD_FILE")
PROGRESS_FILE="${PRD_DIR}/${PRD_BASENAME}-progress.txt"

# Create progress file if it doesn't exist
touch "$PROGRESS_FILE"

PROMPT="@${PRD_FILE} @${PROGRESS_FILE} \
1. Find the highest-priority task and implement it using RED/GREEN TDD. \
2. Run your tests and type checks. \
3. Update the PRD with what was done. \
4. Append your progress to progress.txt. \
5. Commit your changes. \
ONLY WORK ON A SINGLE TASK. \
If the PRD is complete, output <promise>COMPLETE</promise>."

for ((i=1; i<=$ITERATIONS; i++)); do
  echo "[$(date '+%H:%M:%S')] Starting iteration $i/$ITERATIONS"

  tmpfile=$(mktemp)
  docker sandbox run claude . -- --permission-mode acceptEdits --model claude-sonnet-4-5-20250929 -p "$PROMPT" | tee "$tmpfile"
  result=$(cat "$tmpfile")
  rm -f "$tmpfile"

  echo "[$(date '+%H:%M:%S')] Iteration $i finished"

  if [[ "$result" == *"<promise>COMPLETE</promise>"* ]]; then
    echo "PRD complete after $i iterations."
    exit 0
  fi
done
