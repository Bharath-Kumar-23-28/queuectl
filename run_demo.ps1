Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "queuectl Demo" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Clean up any existing database
if (Test-Path "queuectl.db") {
    Write-Host "Cleaning up old database..."
    Remove-Item -Force "queuectl.db" -ErrorAction SilentlyContinue
    Remove-Item -Force "queuectl.db-wal" -ErrorAction SilentlyContinue
    Remove-Item -Force "queuectl.db-shm" -ErrorAction SilentlyContinue
    Write-Host ""
}

Write-Host "Step 1: Enqueue jobs" -ForegroundColor Yellow
Write-Host "--------------------"
queuectl enqueue '{"id":"demo-success","command":"echo Hello from successful job"}'
queuectl enqueue '{"id":"demo-sleep","command":"timeout /t 3 /nobreak && echo Done sleeping"}'
queuectl enqueue '{"id":"demo-fail","command":"cmd /c \"echo This will fail && exit 1\"","max_retries":2}'
Write-Host ""

Write-Host "Step 2: Check status before processing" -ForegroundColor Yellow
Write-Host "---------------------------------------"
queuectl status
Write-Host ""

Write-Host "Step 3: List pending jobs" -ForegroundColor Yellow
Write-Host "-------------------------"
queuectl list --state pending
Write-Host ""

Write-Host "Step 4: Start worker in background" -ForegroundColor Yellow
Write-Host "-----------------------------------"
Write-Host "Starting 1 worker process..."
queuectl worker start --count 1 --daemon
Write-Host ""

Write-Host "Step 5: Wait for jobs to process (15 seconds)" -ForegroundColor Yellow
Write-Host "----------------------------------------------"
Write-Host "Waiting..."
Start-Sleep -Seconds 15
Write-Host ""

Write-Host "Step 6: Check status after processing" -ForegroundColor Yellow
Write-Host "--------------------------------------"
queuectl status
Write-Host ""

Write-Host "Step 7: List completed jobs" -ForegroundColor Yellow
Write-Host "---------------------------"
queuectl list --state completed
Write-Host ""

Write-Host "Step 8: Check Dead Letter Queue" -ForegroundColor Yellow
Write-Host "--------------------------------"
queuectl dlq list
Write-Host ""

Write-Host "Step 9: Retry a DLQ job" -ForegroundColor Yellow
Write-Host "-----------------------"
$dlqList = queuectl dlq list | Out-String
if ($dlqList -match "demo-fail") {
    Write-Host "Retrying demo-fail job..."
    queuectl dlq retry demo-fail
    Write-Host ""
    
    Write-Host "Job moved back to pending:"
    queuectl list --state pending
    Write-Host ""
} else {
    Write-Host "No failed jobs in DLQ yet (may need more time)"
    Write-Host ""
}

Write-Host "Step 10: Stop workers" -ForegroundColor Yellow
Write-Host "---------------------"
queuectl worker stop
Write-Host ""

Write-Host "==========================================" -ForegroundColor Green
Write-Host "Demo Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Try these commands yourself:"
Write-Host '  queuectl enqueue ''{"id":"test","command":"echo test"}'''
Write-Host "  queuectl worker start --count 2"
Write-Host "  queuectl status"
Write-Host "  queuectl list"
Write-Host "  queuectl dlq list"
Write-Host ""
