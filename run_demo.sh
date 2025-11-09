#!/bin/bash

set -e

echo "=========================================="
echo "queuectl Demo"
echo "=========================================="
echo ""

if [ -f "queuectl.db" ]; then
    echo "Cleaning up old database..."
    rm -f queuectl.db queuectl.db-wal queuectl.db-shm
    echo ""
fi

echo "Step 1: Enqueue jobs"
echo "--------------------"
queuectl enqueue '{"id":"demo-success","command":"echo Hello from successful job"}'
queuectl enqueue '{"id":"demo-sleep","command":"sleep 3 && echo Done sleeping"}'
queuectl enqueue '{"id":"demo-fail","command":"bash -c \"echo This will fail && exit 1\"","max_retries":2}'
echo ""

echo "Step 2: Check status before processing"
echo "---------------------------------------"
queuectl status
echo ""

echo "Step 3: List pending jobs"
echo "-------------------------"
queuectl list --state pending
echo ""

echo "Step 4: Start worker in background"
echo "-----------------------------------"
echo "Starting 1 worker process..."
queuectl worker start --count 1 --daemon
echo ""

echo "Step 5: Wait for jobs to process (15 seconds)"
echo "----------------------------------------------"
echo "Waiting..."
sleep 15
echo ""

echo "Step 6: Check status after processing"
echo "--------------------------------------"
queuectl status
echo ""

echo "Step 7: List completed jobs"
echo "---------------------------"
queuectl list --state completed
echo ""

echo "Step 8: Check Dead Letter Queue"
echo "--------------------------------"
queuectl dlq list
echo ""

echo "Step 9: Retry a DLQ job"
echo "-----------------------"
if queuectl dlq list | grep -q "demo-fail"; then
    echo "Retrying demo-fail job..."
    queuectl dlq retry demo-fail
    echo ""
    
    echo "Job moved back to pending:"
    queuectl list --state pending
    echo ""
else
    echo "No failed jobs in DLQ yet (may need more time)"
    echo ""
fi

echo "Step 10: Stop workers"
echo "---------------------"
queuectl worker stop
echo ""

echo "=========================================="
echo "Demo Complete!"
echo "=========================================="
echo ""
echo "Try these commands yourself:"
echo "  queuectl enqueue '{\"id\":\"test\",\"command\":\"echo test\"}'"
echo "  queuectl worker start --count 2"
echo "  queuectl status"
echo "  queuectl list"
echo "  queuectl dlq list"
echo ""
