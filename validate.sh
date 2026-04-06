#!/usr/bin/env bash
# OpenEnv Hackathon Pre-Submission Validation Script
# Based on Meta x Scaler Hackathon Round 1 Guidelines

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BOLD}Starting Validation...${NC}\n"

# ─────────────────────────────────────────────
# STEP 1: Prerequisite Check
# ─────────────────────────────────────────────
echo -e "${BOLD}Step 1/4: Checking Prerequisites...${NC}"

if ! command -v docker &>/dev/null; then
    echo -e "${RED}[FAIL] Docker command not found. Install it: https://docs.docker.com/get-docker/${NC}"
    exit 1
fi

if ! command -v openenv &>/dev/null; then
    echo -e "${RED}[FAIL] openenv-core not found. Install it: pip install openenv-core${NC}"
    exit 1
fi

echo -e "${GREEN}[PASS] Prerequisites found.${NC}\n"

# ─────────────────────────────────────────────
# STEP 2: Docker Build Check
# ─────────────────────────────────────────────
echo -e "${BOLD}Step 2/4: Running Docker Build...${NC}"

if [ -f "Dockerfile" ]; then
    DOCKER_CONTEXT="."
elif [ -f "server/Dockerfile" ]; then
    DOCKER_CONTEXT="server"
else
    echo -e "${RED}[FAIL] No Dockerfile found in root or server/ directory.${NC}"
    exit 1
fi

docker build -t openenv-validator "$DOCKER_CONTEXT"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}[PASS] Docker build succeeded.${NC}\n"
else
    echo -e "${RED}[FAIL] Docker build failed. Check your Dockerfile.${NC}"
    exit 1
fi

# ─────────────────────────────────────────────
# STEP 3: OpenEnv Spec Validation
# ─────────────────────────────────────────────
echo -e "${BOLD}Step 3/4: Running openenv validate...${NC}"

openenv validate

if [ $? -eq 0 ]; then
    echo -e "${GREEN}[PASS] OpenEnv spec compliance verified (yaml, models, endpoints).${NC}\n"
else
    echo -e "${RED}[FAIL] OpenEnv validation failed. Check openenv.yaml and models.py.${NC}"
    exit 1
fi

# ─────────────────────────────────────────────
# STEP 4: Baseline Inference & Log Format Check
# ─────────────────────────────────────────────
echo -e "${BOLD}Step 4/4: Running Baseline Inference Check...${NC}"

if [ ! -f "inference.py" ]; then
    echo -e "${RED}[FAIL] inference.py NOT found in root directory.${NC}"
    exit 1
fi

# Run inference and capture output to check STDOUT format
OUTPUT=$(python inference.py 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo -e "${RED}[FAIL] inference.py failed to execute without errors.${NC}"
    echo "$OUTPUT"
    exit 1
fi

# Verify mandatory log tags: [START], [STEP], [END]
if [[ "$OUTPUT" == *"[START]"* ]] && [[ "$OUTPUT" == *"[STEP]"* ]] && [[ "$OUTPUT" == *"[END]"* ]]; then
    echo -e "${GREEN}[PASS] Mandatory STDOUT log format ([START], [STEP], [END]) detected.${NC}"
else
    echo -e "${RED}[FAIL] STDOUT format incorrect. Must strictly follow [START], [STEP], [END] lines.${NC}"
    exit 1
fi

# Verify score is within valid 0.0–1.0 range
if [[ "$OUTPUT" =~ "score="([0-9]*\.[0-9]+|[0-9]+) ]]; then
    SCORE=${BASH_REMATCH[1]}
    if awk "BEGIN {exit !($SCORE >= 0.0 && $SCORE <= 1.0)}"; then
        echo -e "${GREEN}[PASS] Score ($SCORE) is within valid 0.0-1.0 range.${NC}"
    else
        echo -e "${RED}[FAIL] Invalid score: $SCORE. Must be between 0.0 and 1.0.${NC}"
        exit 1
    fi
fi

# ─────────────────────────────────────────────
# ALL CHECKS PASSED
# ─────────────────────────────────────────────
echo -e "\n${GREEN}${BOLD}========================================${NC}"
echo -e "${GREEN}${BOLD}  ALL 4/4 CHECKS PASSED!${NC}"
echo -e "${GREEN}${BOLD}  YOUR SUBMISSION IS READY.${NC}"
echo -e "${GREEN}${BOLD}========================================${NC}"
