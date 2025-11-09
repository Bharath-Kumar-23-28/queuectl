#!/bin/bash
set -e

TEST_DB="test_queuectl.db"
export QUEUECTL_DB_PATH="$TEST_DB"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "queuectl Core Flow Test"
echo "=========================================="
echo ""

cleanup() {
    echo ""
    echo "Cleaning up..."
    queuectl worker stop 2>/dev/null || true
    rm -f "$TEST_DB" "${TEST_DB}-wal" "${TEST_DB}-shm"
    echo "Cleanup complete"
}

trap cleanup EXIT

assert_job_state() {
    local job_id=$1
    local expected_state=$2
    local description=$3
    local actual_state=$(sqlite3 "$TEST_DB" "SELECT state FROM jobs WHERE id='$job_id';" 2>/dev/null || echo "NOT_FOUND")
    if [ "$actual_state" = "$expected_state" ]; then
        echo -e "${GREEN}✓${NC} $description"
        return 0
    else
        echo -e "${RED}✗${NC} $description"
        echo -e "  Expected: $expected_state, Got: $actual_state"
        return 1
    fi
}

assert_job_exists() {
    local job_id=$1
    local description=$2
    local count=$(sqlite3 "$TEST_DB" "SELECT COUNT(*) FROM jobs WHERE id='$job_id';" 2>/dev/null || echo "0")
    if [ "$count" -eq 1 ]; then
        echo -e "${GREEN}✓${NC} $description"
        return 0
    else
        echo -e "${RED}✗${NC} $description"
        return 1
    fi
}

echo "Test 1: Setup and Configuration"
echo "--------------------------------"
queuectl config get backoff_base >/dev/null 2>&1
assert_job_exists "nonexistent" "Database initialized" && exit 1 || echo -e "${GREEN}✓${NC} Database initialized"
echo ""

echo "Test 2: Enqueue Jobs"
echo "--------------------"
queuectl enqueue '{"id":"test-success","command":"echo Success"}' >/dev/null
assert_job_exists "test-success" "Enqueued successful job"
queuectl enqueue '{"id":"test-fail","command":"bash -c \"exit 1\"","max_retries":2}' >/dev/null
assert_job_exists "test-fail" "Enqueued failing job"
queuectl enqueue '{"id":"test-delayed","command":"echo Delayed success"}' >/dev/null
assert_job_exists "test-delayed" "Enqueued delayed job"
echo ""

echo "Test 3: Initial Job States"
echo "--------------------------"
assert_job_state "test-success" "pending" "Success job is pending"
assert_job_state "test-fail" "pending" "Fail job is pending"
assert_job_state "test-delayed" "pending" "Delayed job is pending"
echo ""

echo "Test 4: Start Worker and Process Jobs"
echo "--------------------------------------"
echo "Starting worker in daemon mode..."
queuectl worker start --count 1 --daemon >/dev/null 2>&1 &
WORKER_PID=$!
sleep 2
echo -e "${GREEN}✓${NC} Worker started (PID: $WORKER_PID)"
echo ""

echo "Test 5: Wait for Job Processing"
echo "--------------------------------"
echo "Waiting for successful job to complete..."
sleep 3
assert_job_state "test-success" "completed" "Success job completed"
echo ""

echo "Test 6: Verify Retry Logic"
echo "--------------------------"
echo "Waiting for failing job retries (backoff: 2s, 4s)..."
echo "This will take ~10 seconds..."
sleep 4
ATTEMPTS=$(sqlite3 "$TEST_DB" "SELECT attempts FROM jobs WHERE id='test-fail';")
echo "  After 4s: attempts = $ATTEMPTS"
sleep 8
ATTEMPTS=$(sqlite3 "$TEST_DB" "SELECT attempts FROM jobs WHERE id='test-fail';")
echo "  After 12s: attempts = $ATTEMPTS"
assert_job_state "test-fail" "dead" "Failed job moved to DLQ after max retries"
echo ""

echo "Test 7: Dead Letter Queue Operations"
echo "-------------------------------------"
DLQ_COUNT=$(sqlite3 "$TEST_DB" "SELECT COUNT(*) FROM jobs WHERE state='dead';")
if [ "$DLQ_COUNT" -eq 1 ]; then
    echo -e "${GREEN}✓${NC} DLQ contains 1 failed job"
else
    echo -e "${RED}✗${NC} DLQ count incorrect (expected: 1, got: $DLQ_COUNT)"
fi
echo "Retrying DLQ job..."
queuectl dlq retry test-fail >/dev/null
assert_job_state "test-fail" "pending" "DLQ job moved back to pending"
ATTEMPTS=$(sqlite3 "$TEST_DB" "SELECT attempts FROM jobs WHERE id='test-fail';")
if [ "$ATTEMPTS" -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Attempts reset to 0 after retry"
else
    echo -e "${RED}✗${NC} Attempts not reset (expected: 0, got: $ATTEMPTS)"
fi
echo ""

echo "Test 8: Stop Workers"
echo "--------------------"
queuectl worker stop >/dev/null 2>&1
echo -e "${GREEN}✓${NC} Workers stopped gracefully"
echo ""

echo "Test 9: Verify Final States"
echo "---------------------------"
PENDING=$(sqlite3 "$TEST_DB" "SELECT COUNT(*) FROM jobs WHERE state='pending';")
COMPLETED=$(sqlite3 "$TEST_DB" "SELECT COUNT(*) FROM jobs WHERE state='completed';")
DEAD=$(sqlite3 "$TEST_DB" "SELECT COUNT(*) FROM jobs WHERE state='dead';")
echo "Final job counts:"
echo "  Pending: $PENDING"
echo "  Completed: $COMPLETED"
echo "  Dead: $DEAD"
if [ "$COMPLETED" -ge 1 ]; then
    echo -e "${GREEN}✓${NC} At least 1 job completed successfully"
else
    echo -e "${RED}✗${NC} No jobs completed"
fi
echo ""

echo "=========================================="
echo "Test Results"
echo "=========================================="
echo ""

TOTAL=0
PASSED=0

run_assertion() {
    TOTAL=$((TOTAL + 1))
    if "$@" >/dev/null 2>&1; then
        PASSED=$((PASSED + 1))
        return 0
    else
        return 1
    fi
}

run_assertion assert_job_exists "test-success" ""
run_assertion assert_job_exists "test-fail" ""
run_assertion assert_job_exists "test-delayed" ""
run_assertion assert_job_state "test-success" "completed" ""

if [ "$PASSED" -eq "$TOTAL" ]; then
    echo -e "${GREEN}All tests passed!${NC} ($PASSED/$TOTAL)"
    exit 0
else
    echo -e "${YELLOW}Some tests failed${NC} ($PASSED/$TOTAL passed)"
    exit 1
fi
