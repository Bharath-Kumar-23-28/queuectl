# queuectl Usage Guide for Windows

## Installation

```powershell
# Navigate to project directory
cd d:\Python

# Install package
pip install -e .

# Verify installation
queuectl --help
```

## Method 1: Using Python Helper Script (Recommended for Windows)

The easiest way to enqueue jobs on Windows is using the helper script:

```powershell
# Enqueue a simple job
python enqueue.py job1 "echo Hello"

# Enqueue with custom retry count
python enqueue.py job2 "timeout /t 5" 2

# Enqueue a failing job
python enqueue.py fail1 "cmd /c exit 1" 3

# Start workers to process jobs
queuectl worker start --count 1

# Check status
queuectl status

# List jobs
queuectl list

# Stop workers (Ctrl+C or in another terminal)
queuectl worker stop
```

## Method 2: Using PowerShell Helper Functions

Load the PowerShell helper module:

```powershell
# Load helper functions
. .\queuectl_helpers.ps1

# Now you can use friendly PowerShell functions
Enqueue-Job -Id "job1" -Command "echo Hello"
Enqueue-Job -Id "job2" -Command "timeout /t 5" -MaxRetries 2

# Start workers
Start-Workers -Count 2

# Get status
Get-QueueStatus

# List jobs
Get-Jobs
Get-Jobs -State pending

# View DLQ
Get-DeadLetterQueue

# Retry failed job
Retry-DeadJob -JobId "failed-job"

# Stop workers
Stop-Workers
```

## Method 3: Direct CLI (Requires Careful Quoting)

When using the CLI directly with JSON, you need to be careful with PowerShell quoting:

**Option A: Use Python API directly**
```powershell
# Create a Python script
@"
from queuectl.queue import enqueue_job
enqueue_job({"id": "job1", "command": "echo Hello", "max_retries": 3})
"@ | python
```

**Option B: Store JSON in variable**
```powershell
$json = '{"id":"job1","command":"echo Hello"}'
# Then use with single quotes in the command
# (Note: This still may have issues with PowerShell parsing)
```

## Complete Workflow Example

```powershell
# 1. Clean start
Remove-Item queuectl.db* -ErrorAction SilentlyContinue

# 2. Enqueue jobs using Python helper
python enqueue.py success1 "echo Job 1 completed"
python enqueue.py success2 "echo Job 2 completed"
python enqueue.py sleep1 "timeout /t 3 /nobreak" 2
python enqueue.py fail1 "cmd /c exit 1" 2

# 3. Check what's queued
queuectl status
queuectl list --state pending

# 4. Start worker (in foreground - you'll see logs)
queuectl worker start --count 1

# After watching jobs process, press Ctrl+C to stop

# 5. Check results
queuectl list --state completed
queuectl dlq list

# 6. Retry a failed job
# If fail1 is in DLQ:
queuectl dlq retry fail1

# 7. View final status
queuectl status
```

## Common Commands

### Queue Operations

```powershell
# Using Python helper (recommended)
python enqueue.py <job-id> "<command>" [max-retries]

# Examples:
python enqueue.py backup "powershell -File backup.ps1"
python enqueue.py cleanup "del /q temp\*" 1
python enqueue.py report "python generate_report.py"
```

### Worker Management

```powershell
# Start 1 worker in foreground (see logs, Ctrl+C to stop)
queuectl worker start --count 1

# Start 3 workers in foreground
queuectl worker start --count 3

# Start workers with custom backoff
queuectl worker start --count 2 --backoff-base 3

# Start workers in daemon mode (background)
queuectl worker start --count 2 --daemon

# Stop daemon workers
queuectl worker stop
```

### Monitoring

```powershell
# Overall status
queuectl status

# List all jobs
queuectl list

# Filter by state
queuectl list --state pending
queuectl list --state processing
queuectl list --state completed
queuectl list --state dead

# Watch DLQ
queuectl dlq list
```

### Configuration

```powershell
# View config
queuectl config get backoff_base
queuectl config get max_retries

# Update config
queuectl config set backoff_base 3
queuectl config set max_retries 5
```

### Dead Letter Queue

```powershell
# List failed jobs
queuectl dlq list

# Retry a specific job
queuectl dlq retry <job-id>

# Example:
queuectl dlq retry fail1
```

## Real-World Examples

### Example 1: Process Files

```powershell
# Enqueue jobs to process multiple files
$files = Get-ChildItem *.txt
foreach ($file in $files) {
    $jobId = "process-" + $file.BaseName
    $command = "python process.py `"$($file.FullName)`""
    python enqueue.py $jobId $command
}

# Process with 4 workers
queuectl worker start --count 4
```

### Example 2: Scheduled Backup

```powershell
# Enqueue backup job
python enqueue.py daily-backup "powershell -File backup.ps1" 2

# Start a dedicated worker for backups
queuectl worker start --count 1
```

### Example 3: Retry Failed API Calls

```powershell
# Enqueue API sync job with 5 retries and slower backoff
queuectl config set backoff_base 3
python enqueue.py api-sync "python sync_api.py" 5

queuectl worker start --count 1
```

### Example 4: Bulk Email Sending

```powershell
# Read recipients from CSV
$recipients = Import-Csv recipients.csv
foreach ($recipient in $recipients) {
    $jobId = "email-" + $recipient.Id
    $command = "python send_email.py `"$($recipient.Email)`""
    python enqueue.py $jobId $command 3
}

# Send with 2 workers to avoid rate limits
queuectl worker start --count 2
```

## Monitoring and Debugging

### Watch Queue in Real-Time

```powershell
# In one terminal: Start worker
queuectl worker start --count 1

# In another terminal: Watch status
while ($true) {
    Clear-Host
    queuectl status
    Write-Host "`n---`n"
    queuectl list --state processing
    Start-Sleep -Seconds 2
}
```

### Check Job Details

```powershell
# View all jobs with state
queuectl list

# Check if specific job completed
queuectl list | Select-String "job1"

# View DLQ with errors
queuectl dlq list
```

### Database Location

```powershell
# Default location
ls queuectl.db

# Custom location via environment variable
$env:QUEUECTL_DB_PATH = "C:\data\myqueue.db"
queuectl status
```

## Troubleshooting

### Issue: "queuectl: command not found"

```powershell
# Check if installed
pip show queuectl

# Reinstall
pip install -e .

# Check Python Scripts in PATH
$env:PATH -split ";" | Select-String "Python"
```

### Issue: Jobs not processing

```powershell
# Check worker is running
queuectl status

# Check jobs are pending
queuectl list --state pending

# Start worker with logs visible
queuectl worker start --count 1
```

### Issue: Jobs stuck in "processing"

This happens if worker crashes. Jobs remain locked.

```powershell
# Currently no automatic recovery - manual DB update needed
# Or implement a cleanup script
```

### Issue: Database locked

```powershell
# Stop all workers
queuectl worker stop

# Close any DB browsers
# Restart workers
queuectl worker start --count 1
```

### Reset Everything

```powershell
# Stop workers
queuectl worker stop

# Remove database
Remove-Item queuectl.db*

# Start fresh
queuectl status  # Creates new DB
```

## Best Practices

1. **Use Python Helper for Enqueueing**: Avoids PowerShell quoting issues
   ```powershell
   python enqueue.py job-id "command here"
   ```

2. **Start Workers in Foreground First**: See logs and debug
   ```powershell
   queuectl worker start --count 1
   ```

3. **Set Appropriate Retries**: Based on job type
   ```powershell
   python enqueue.py critical-job "important-cmd" 5
   python enqueue.py best-effort "optional-cmd" 1
   ```

4. **Monitor DLQ Regularly**: Check for persistent failures
   ```powershell
   queuectl dlq list
   ```

5. **Use Multiple Workers Carefully**: Balance throughput vs resource usage
   ```powershell
   queuectl worker start --count 2  # Start small
   ```

6. **Configure Backoff for External APIs**: Avoid hammering failed services
   ```powershell
   queuectl config set backoff_base 3  # Slower: 3s, 9s, 27s...
   ```

## Performance Tips

- **SQLite limits**: Good for single machine, ~100 jobs/sec
- **Worker count**: Start with 2-4, increase based on CPU
- **Backoff tuning**: Lower for transient errors, higher for external deps
- **Job granularity**: Prefer many small jobs over few large ones

## Advanced: Running as Windows Service

To run workers as a Windows service, consider:

1. **NSSM** (Non-Sucking Service Manager)
2. **Task Scheduler** with "At startup" trigger
3. **Python Windows Service** using `pywin32`

Example with Task Scheduler:
```powershell
# Create a startup script
@"
cd d:\Python
queuectl worker start --count 2 --daemon
"@ | Out-File -FilePath start-workers.bat

# Add to Task Scheduler with "At startup" trigger
```

## Getting Help

```powershell
# General help
queuectl --help

# Command-specific help
queuectl enqueue --help
queuectl worker --help
queuectl list --help
queuectl dlq --help
queuectl config --help
```

---

**For more details, see README.md**
do the same thing 
with a single code
