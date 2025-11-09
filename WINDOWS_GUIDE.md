queuectl Usage Guide for Windows

Installation

Navigate to project directory:
cd d:\Python

Install package:
pip install -e .

Verify installation:
queuectl --help

Method 1: Using Python Helper Script (Recommended for Windows)

The easiest way to enqueue jobs on Windows is using the helper script:

Enqueue a simple job:
python enqueue.py job1 "echo Hello"

Enqueue with custom retry count:
python enqueue.py job2 "timeout /t 5" 2

Enqueue a failing job:
python enqueue.py fail1 "cmd /c exit 1" 3

Start workers to process jobs:
queuectl worker start --count 1

Check status:
queuectl status

List jobs:
queuectl list

Stop workers (Ctrl+C or in another terminal):
queuectl worker stop

Method 2: Using PowerShell Helper Functions

Load the PowerShell helper module:

. .\queuectl_helpers.ps1

Now you can use friendly PowerShell functions:

Enqueue-Job -Id "job1" -Command "echo Hello"
Enqueue-Job -Id "job2" -Command "timeout /t 5" -MaxRetries 2

Start workers:
Start-Workers -Count 2

Get status:
Get-QueueStatus

List jobs:
Get-Jobs
Get-Jobs -State pending

View DLQ:
Get-DeadLetterQueue

Retry failed job:
Retry-DeadJob -JobId "failed-job"

Stop workers:
Stop-Workers

Method 3: Direct CLI (Requires Careful Quoting)

When using the CLI directly with JSON, you need to be careful with PowerShell quoting.

Option A: Use Python API directly:
@"
from queuectl.queue import enqueue_job
enqueue_job({"id": "job1", "command": "echo Hello", "max_retries": 3})
"@ | python

Option B: Store JSON in variable:
$json = '{"id":"job1","command":"echo Hello"}'

Then use with single quotes in the command
(Note: This still may have issues with PowerShell parsing)

Complete Workflow Example

Remove-Item queuectl.db* -ErrorAction SilentlyContinue
python enqueue.py success1 "echo Job 1 completed"
python enqueue.py success2 "echo Job 2 completed"
python enqueue.py sleep1 "timeout /t 3 /nobreak" 2
python enqueue.py fail1 "cmd /c exit 1" 2
queuectl status
queuectl list --state pending
queuectl worker start --count 1

After watching jobs process, press Ctrl+C to stop

queuectl list --state completed
queuectl dlq list
queuectl dlq retry fail1
queuectl status

Common Commands

Queue Operations
python enqueue.py <job-id> "<command>" [max-retries]

Examples:
python enqueue.py backup "powershell -File backup.ps1"
python enqueue.py cleanup "del /q temp*" 1
python enqueue.py report "python generate_report.py"

Worker Management
queuectl worker start --count 1
queuectl worker start --count 3
queuectl worker start --count 2 --backoff-base 3
queuectl worker start --count 2 --daemon
queuectl worker stop

Monitoring
queuectl status
queuectl list
queuectl list --state pending
queuectl list --state processing
queuectl list --state completed
queuectl list --state dead
queuectl dlq list

Configuration
queuectl config get backoff_base
queuectl config get max_retries
queuectl config set backoff_base 3
queuectl config set max_retries 5

Dead Letter Queue
queuectl dlq list
queuectl dlq retry <job-id>
queuectl dlq retry fail1

Real-World Examples

Example 1: Process Files
$files = Get-ChildItem *.txt
foreach ($file in $files) {
$jobId = "process-" + $file.BaseName
$command = "python process.py "$($file.FullName)""
python enqueue.py $jobId $command
}
queuectl worker start --count 4

Example 2: Scheduled Backup
python enqueue.py daily-backup "powershell -File backup.ps1" 2
queuectl worker start --count 1

Example 3: Retry Failed API Calls
queuectl config set backoff_base 3
python enqueue.py api-sync "python sync_api.py" 5
queuectl worker start --count 1

Example 4: Bulk Email Sending
$recipients = Import-Csv recipients.csv
foreach ($recipient in $recipients) {
$jobId = "email-" + $recipient.Id
$command = "python send_email.py "$($recipient.Email)""
python enqueue.py $jobId $command 3
}
queuectl worker start --count 2

Monitoring and Debugging

Watch Queue in Real-Time

Terminal 1:

queuectl worker start --count 1

Terminal 2:

while ($true) {
Clear-Host
queuectl status
Write-Host "n---n"
queuectl list --state processing
Start-Sleep -Seconds 2
}

Check Job Details
queuectl list
queuectl list | Select-String "job1"
queuectl dlq list

Database Location
ls queuectl.db
$env:QUEUECTL_DB_PATH = "C:\data\myqueue.db"
queuectl status

Troubleshooting

Issue: "queuectl: command not found"
pip show queuectl
pip install -e .
$env:PATH -split ";" | Select-String "Python"

Issue: Jobs not processing
queuectl status
queuectl list --state pending
queuectl worker start --count 1

Issue: Jobs stuck in "processing"

Happens if worker crashes. Manual DB update may be needed.

Issue: Database locked
queuectl worker stop

Close DB browsers

queuectl worker start --count 1

Reset Everything
queuectl worker stop
Remove-Item queuectl.db*
queuectl status

Best Practices

Use Python Helper for Enqueueing:
python enqueue.py job-id "command here"

Start Workers in Foreground First:
queuectl worker start --count 1

Set Appropriate Retries:
python enqueue.py critical-job "important-cmd" 5
python enqueue.py best-effort "optional-cmd" 1

Monitor DLQ Regularly:
queuectl dlq list

Use Multiple Workers Carefully:
queuectl worker start --count 2

Configure Backoff for External APIs:
queuectl config set backoff_base 3

Performance Tips

SQLite limits: good for single machine, ~100 jobs/sec
Worker count: start with 2–4, increase gradually
Backoff tuning: lower for transient errors, higher for external APIs
Job granularity: prefer many small jobs over few large ones

Advanced: Running as Windows Service

To run workers as a Windows service:

Use NSSM (Non-Sucking Service Manager)

Or Task Scheduler with "At startup" trigger

Or Python Windows Service (pywin32)

Example with Task Scheduler:
@"
cd d:\Python
queuectl worker start --count 2 --daemon
"@ | Out-File -FilePath start-workers.bat

Getting Help

queuectl --help
queuectl enqueue --help
queuectl worker --help
queuectl list --help
queuectl dlq --help
queuectl config --help

For more details, see README.md