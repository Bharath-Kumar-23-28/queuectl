queuectl Installation and Quick Start Guide

Installation

Windows (PowerShell)

cd d:\Python
pip install -e .
queuectl --help

Linux/Mac (Bash)

cd /path/to/Python
pip install -e .
queuectl --help

Quick Start Examples

Example 1: Simple Job

queuectl enqueue '{"id":"hello","command":"echo Hello, World!"}'
queuectl worker start --count 1
Press Ctrl+C to stop the worker after job completes

Example 2: Multiple Jobs

queuectl enqueue '{"id":"job1","command":"echo Job 1"}'
queuectl enqueue '{"id":"job2","command":"echo Job 2"}'
queuectl enqueue '{"id":"job3","command":"echo Job 3"}'
queuectl worker start --count 2

Example 3: Failing Job with Retry

queuectl enqueue '{"id":"fail-test","command":"cmd /c exit 1","max_retries":3}'
queuectl worker start --count 1
The job will retry with exponential backoff (2s, 4s, 8s).
After 3 failed attempts, it moves to the DLQ.

Check DLQ:
queuectl dlq list

Retry the job:
queuectl dlq retry fail-test

Example 4: Check Status

queuectl status
queuectl list
queuectl list --state pending
queuectl list --state completed

Example 5: Configuration

queuectl config get backoff_base
queuectl config set backoff_base 3
queuectl config set max_retries 5

Running the Demo

Windows:
.\run_demo.ps1

Linux/Mac:
bash run_demo.sh

Running Tests

Windows:
.\tests\test_core_flow.ps1

Linux/Mac:
bash tests/test_core_flow.sh

Common Commands

queuectl enqueue '<json>' - Add a new job to the queue
queuectl worker start --count N - Start N worker processes
queuectl worker stop - Stop all workers
queuectl status - View queue status
queuectl list - List all jobs
queuectl list --state <state> - Filter jobs by state
queuectl dlq list - View failed jobs
queuectl dlq retry <job_id> - Retry a failed job
queuectl config get <key> - Get config value
queuectl config set <key> <value> - Set config value

Troubleshooting

"queuectl: command not found"
Ensure you have installed the package:
pip install -e .
Make sure your Python Scripts directory is in your PATH.

Workers not processing jobs

Check if workers are running: queuectl status

Check if jobs are pending: queuectl list --state pending

Start a worker in foreground mode to see logs: queuectl worker start --count 1

Database locked errors
This is rare with WAL mode, but if it happens:

Reduce the number of concurrent workers

Ensure no other processes are using the database

Need to reset everything

queuectl worker stop
Remove-Item queuectl.db*
queuectl status

Architecture Overview

CLI Tool (queuectl commands)
↓
SQLite Database (queuectl.db - stores job state and config)
↓
Workers (multiple processes claiming and executing jobs)

Job states: pending → processing → completed
Failed jobs move to: dead (DLQ)

For complete documentation, see README.md