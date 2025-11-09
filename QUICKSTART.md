# queuectl Installation and Quick Start Guide 

## Installation 

### Windows (PowerShell)
powershell
# Navigate to the project directory
cd d:\Python

# Install in development mode
pip install -e .

# Verify installation
queuectl --help
### Linux/Mac (Bash)
bash
# Navigate to the project directory
cd /path/to/Python

# Install in development mode
pip install -e .

# Verify installation
queuectl --help
## Quick Start Examples ### Example 1: Simple Job
powershell
# Enqueue a simple echo job
queuectl enqueue '{"id":"hello","command":"echo Hello, World!"}'

# Start a worker to process it
queuectl worker start --count 1

# Press Ctrl+C to stop the worker after job completes
### Example 2: Multiple Jobs
powershell
# Enqueue several jobs
queuectl enqueue '{"id":"job1","command":"echo Job 1"}'
queuectl enqueue '{"id":"job2","command":"echo Job 2"}'
queuectl enqueue '{"id":"job3","command":"echo Job 3"}'

# Start 2 workers
queuectl worker start --count 2
### Example 3: Failing Job with Retry
powershell
# Enqueue a job that will fail
queuectl enqueue '{"id":"fail-test","command":"cmd /c exit 1","max_retries":3}'

# Start worker
queuectl worker start --count 1

# Watch it retry with exponential backoff (2s, 4s, 8s)
# After 3 failed attempts, it moves to DLQ

# Check DLQ
queuectl dlq list

# Retry the job
queuectl dlq retry fail-test
### Example 4: Check Status
powershell
# View queue status
queuectl status

# List all jobs
queuectl list

# List only pending jobs
queuectl list --state pending

# List completed jobs
queuectl list --state completed
### Example 5: Configuration
powershell
# View current backoff base
queuectl config get backoff_base

# Set slower backoff (3^attempts instead of 2^attempts)
queuectl config set backoff_base 3

# Set default max retries
queuectl config set max_retries 5
## Running the Demo ### Windows:
powershell
.\run_demo.ps1
### Linux/Mac:
bash
bash run_demo.sh
## Running Tests ### Windows:
powershell
.\tests\test_core_flow.ps1
### Linux/Mac:
bash
bash tests/test_core_flow.sh
## Common Commands | Command | Description | |---------|-------------| | queuectl enqueue '<json>' | Add a new job to the queue | | queuectl worker start --count N | Start N worker processes | | queuectl worker stop | Stop all workers | | queuectl status | View queue status | | queuectl list | List all jobs | | queuectl list --state <state> | Filter jobs by state | | queuectl dlq list | View failed jobs | | queuectl dlq retry <job_id> | Retry a failed job | | queuectl config get <key> | Get config value | | queuectl config set <key> <value> | Set config value | ## Troubleshooting ### "queuectl: command not found" Make sure you've installed the package:
powershell
pip install -e .
And that your Python Scripts directory is in your PATH. ### Workers not processing jobs 1. Check if workers are running: queuectl status 2. Check if jobs are pending: queuectl list --state pending 3. Try starting workers in foreground mode to see logs: queuectl worker start --count 1 ### Database locked errors This is rare with WAL mode enabled, but if it happens: - Reduce the number of concurrent workers - Make sure no other processes are holding the database ### Need to reset everything
powershell
# Stop workers
queuectl worker stop

# Delete the database
Remove-Item queuectl.db*

# Start fresh - database will be recreated automatically
queuectl status
## Architecture Overview
┌─────────────┐
│   CLI Tool  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  SQLite DB  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Workers   │
└─────────────┘



Jobs flow: **pending** → **processing** → **completed** ↓ **dead** (DLQ) For complete documentation, see README.md.
