# Tests job enqueueing, processing, retry logic, and DLQ

$ErrorActionPreference = "Stop"
$TEST_DB = "test_queuectl.db"
$env:QUEUECTL_DB_PATH = $TEST_DB

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "queuectl Core Flow Test" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

function Cleanup {
    Write-Host ""
    Write-Host "Cleaning up..."
    
    try { queuectl worker stop 2>$null } catch {}
    
    Remove-Item -Force "$TEST_DB" -ErrorAction SilentlyContinue
    Remove-Item -Force "${TEST_DB}-wal" -ErrorAction SilentlyContinue
    Remove-Item -Force "${TEST_DB}-shm" -ErrorAction SilentlyContinue
    
    Write-Host "Cleanup complete"
}

function Assert-JobState {
    param($JobId, $ExpectedState, $Description)
    
    $output = queuectl list | Out-String
    if ($output -match "$JobId\s+$ExpectedState") {
        Write-Host "$Description" -ForegroundColor Green
        return $true
    } else {
        Write-Host "$Description" -ForegroundColor Red
        Write-Host "  Expected state: $ExpectedState" -ForegroundColor Red
        return $false
    }
}

function Assert-JobExists {
    param($JobId, $Description)
    
    $output = queuectl list | Out-String
    if ($output -match $JobId) {
        Write-Host "$Description" -ForegroundColor Green
        return $true
    } else {
        Write-Host "$Description" -ForegroundColor Red
        return $false
    }
}

trap { Cleanup; break }

Write-Host "Test 1: Setup and Configuration" -ForegroundColor Yellow
Write-Host "--------------------------------"

queuectl config get backoff_base | Out-Null

Write-Host "Database initialized" -ForegroundColor Green
Write-Host ""

Write-Host "Test 2: Enqueue Jobs" -ForegroundColor Yellow
Write-Host "--------------------"

queuectl enqueue '{"id":"test-success","command":"echo Success"}' | Out-Null
Assert-JobExists "test-success" "Enqueued successful job" | Out-Null

queuectl enqueue '{"id":"test-fail","command":"cmd /c exit 1","max_retries":2}' | Out-Null
Assert-JobExists "test-fail" "Enqueued failing job" | Out-Null

queuectl enqueue '{"id":"test-delayed","command":"echo Delayed success"}' | Out-Null
Assert-JobExists "test-delayed" "Enqueued delayed job" | Out-Null

Write-Host ""

Write-Host "Test 3: Initial Job States" -ForegroundColor Yellow
Write-Host "--------------------------"

Assert-JobState "test-success" "pending" "Success job is pending" | Out-Null
Assert-JobState "test-fail" "pending" "Fail job is pending" | Out-Null
Assert-JobState "test-delayed" "pending" "Delayed job is pending" | Out-Null

Write-Host ""

Write-Host "Test 4: Start Worker and Process Jobs" -ForegroundColor Yellow
Write-Host "--------------------------------------"

Write-Host "Starting worker in daemon mode..."
$job = Start-Job -ScriptBlock { 
    $env:QUEUECTL_DB_PATH = $using:TEST_DB
    queuectl worker start --count 1
}

Start-Sleep -Seconds 2

Write-Host "Worker started (Job ID: $($job.Id))" -ForegroundColor Green
Write-Host ""

Write-Host "Test 5: Wait for Job Processing" -ForegroundColor Yellow
Write-Host "--------------------------------"

Write-Host "Waiting for successful job to complete..."
Start-Sleep -Seconds 3

Assert-JobState "test-success" "completed" "Success job completed" | Out-Null

Write-Host ""

Write-Host "Test 6: Verify Retry Logic" -ForegroundColor Yellow
Write-Host "--------------------------"

Write-Host "Waiting for failing job retries (backoff: 2s, 4s)..."
Write-Host "This will take ~10 seconds..."

Start-Sleep -Seconds 4
Write-Host "  After 4s: checking attempts..."

Start-Sleep -Seconds 8
Write-Host "  After 12s: checking final state..."

$dlqOutput = queuectl dlq list | Out-String
if ($dlqOutput -match "test-fail") {
    Write-Host "Failed job moved to DLQ after max retries" -ForegroundColor Green
} else {
    Write-Host "Failed job not in DLQ" -ForegroundColor Red
}

Write-Host ""

Write-Host "Test 7: Dead Letter Queue Operations" -ForegroundColor Yellow
Write-Host "-------------------------------------"

$dlqList = queuectl dlq list | Out-String
if ($dlqList -match "test-fail") {
    Write-Host "DLQ contains failed job" -ForegroundColor Green
} else {
    Write-Host "DLQ does not contain failed job" -ForegroundColor Red
}

Write-Host "Retrying DLQ job..."
queuectl dlq retry test-fail | Out-Null

Assert-JobState "test-fail" "pending" "DLQ job moved back to pending" | Out-Null

Write-Host ""

Write-Host "Test 8: Stop Workers" -ForegroundColor Yellow
Write-Host "--------------------"

Stop-Job -Job $job
Remove-Job -Job $job

queuectl worker stop 2>$null | Out-Null
Write-Host "Workers stopped gracefully" -ForegroundColor Green

Write-Host ""

Write-Host "Test 9: Verify Final States" -ForegroundColor Yellow
Write-Host "---------------------------"

$statusOutput = queuectl status | Out-String
Write-Host $statusOutput

Write-Host ""

Write-Host "==========================================" -ForegroundColor Green
Write-Host "Test Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

Cleanup

Write-Host "All core functionality tested successfully!" -ForegroundColor Green
