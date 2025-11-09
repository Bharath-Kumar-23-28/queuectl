# queuectl - CLI-based Background Job Queue

A robust, SQLite-backed background job queue with retry logic, exponential backoff, and dead letter queue (DLQ) support. Built with Python 3.10+ for simplicity and reliability.

# DEMO RECORD
[Watch CLI Demo Recording](https://drive.google.com/file/d/1JCp_WLH2kz85t8iae4fPK7Zw3sBPZlIL/view?usp=drive_link)

## Features

- **SQLite Persistence**: All job state persists across restarts
- **Atomic Job Claiming**: Multiple workers safely process jobs without conflicts
- **Exponential Backoff**: Configurable retry delays for failed jobs
- **Dead Letter Queue (DLQ)**: Failed jobs can be inspected and retried
- **Graceful Shutdown**: Workers finish current jobs before stopping
- **Simple CLI**: Easy-to-use commands powered by Click
- **Scheduled Jobs**: Support for delayed/scheduled execution via `run_at`

## Architecture

### Job States

Jobs flow through the following states:

```
pending → processing → completed
    ↓          ↓
    └──(retry)─┘
         ↓
       dead (DLQ)
```

- **pending**: Job waiting to be processed
- **processing**: Job currently being executed by a worker
- **completed**: Job finished successfully
- **failed**: Job failed but may retry (transient state)
- **dead**: Job exceeded max retries and moved to DLQ

### Concurrency Model

- **Workers**: Independent Python `multiprocessing.Process` instances
- **Job Locking**: Atomic SQL `UPDATE ... WHERE state='pending'` prevents duplicate processing
- **Database**: SQLite with WAL mode for better concurrent access
- **No Centralized Broker**: Workers directly claim jobs from the database

### Retry Logic

When a job fails (non-zero exit code or exception):

1. Increment `attempts` counter
2. If `attempts < max_retries`:
   - Set `state='pending'` 
   - Calculate backoff: `delay = backoff_base ** attempts` seconds
   - Set `run_after = now + delay`
   - Store error in `last_error`
3. If `attempts >= max_retries`:
   - Set `state='dead'`
   - Job moves to DLQ for manual inspection/retry

**Default Configuration**:
- `backoff_base = 2` (exponential backoff: 2, 4, 8, 16... seconds)
- `max_retries = 3`

### Database Schema

**Table: `jobs`**
```sql
id TEXT PRIMARY KEY
command TEXT NOT NULL
state TEXT NOT NULL
attempts INTEGER NOT NULL DEFAULT 0
max_retries INTEGER NOT NULL DEFAULT 3
created_at TEXT NOT NULL
updated_at TEXT
locked_by TEXT
locked_at TEXT
last_error TEXT
run_after INTEGER DEFAULT 0  -- Unix timestamp
```

**Table: `config`**
```sql
key TEXT PRIMARY KEY
value TEXT
```

## Setup

### Prerequisites

- Python 3.10 or higher
- pip

### Installation

```bash
# Clone or navigate to the project directory
cd d:\Python

# Install in development mode
pip install -e .

# Verify installation
queuectl --help
```

### Dependencies

All dependencies are listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

Required packages:
- `click>=8.0` - CLI framework
- `python-dotenv>=0.20` - Optional environment variable support

## Usage

### Basic Workflow

```bash
# 1. Enqueue some jobs
queuectl enqueue '{"id":"job1","command":"echo Hello from job1"}'
queuectl enqueue '{"id":"job2","command":"sleep 5 && echo Done"}'
queuectl enqueue '{"id":"job3","command":"exit 1","max_retries":2}'

# 2. Start workers (foreground mode)
queuectl worker start --count 2

# In another terminal:

# 3. Check status
queuectl status

# 4. List jobs by state
queuectl list --state pending
queuectl list --state completed

# 5. View DLQ
queuectl dlq list

# 6. Retry a failed job
queuectl dlq retry job3
```

### CLI Commands

#### Enqueue Jobs

```bash
# Basic job
queuectl enqueue '{"id":"job1","command":"echo Hello"}'

# Job with custom max retries
queuectl enqueue '{"id":"job2","command":"bash -c \"exit 1\"","max_retries":5}'

# Scheduled job (run at specific time)
queuectl enqueue '{"id":"job3","command":"echo Delayed","run_at":"2025-11-08T12:00:00Z"}'
```

**Required JSON fields**:
- `id` (string): Unique job identifier
- `command` (string): Shell command to execute

**Optional JSON fields**:
- `max_retries` (int): Override default max retries
- `run_at` (ISO string): Schedule job for future execution

#### Worker Management

```bash
# Start workers in foreground (Ctrl+C to stop)
queuectl worker start --count 3

# Start with custom backoff
queuectl worker start --count 1 --backoff-base 3

# Start in daemon mode (background)
queuectl worker start --count 2 --daemon

# Stop daemon workers
queuectl worker stop
```

#### Status and Listing

```bash
# Show queue status
queuectl status

# List all jobs
queuectl list

# Filter by state
queuectl list --state pending
queuectl list --state processing
queuectl list --state completed
queuectl list --state dead
```

**Example Output**:
```
Queue Status
========================================
Total jobs: 10

Jobs by state:
  pending     : 2
  processing  : 1
  completed   : 5
  failed      : 0
  dead        : 2

Active workers: 2
  PIDs: 12345, 12346

Database: queuectl.db
```

#### Dead Letter Queue (DLQ)

```bash
# List jobs in DLQ
queuectl dlq list

# Retry a specific job
queuectl dlq retry job_id_here
```

#### Configuration

```bash
# View configuration
queuectl config get backoff_base
queuectl config get max_retries

# Update configuration
queuectl config set backoff_base 3
queuectl config set max_retries 5
```

## Testing

### Run Automated Tests

```bash
# Run the core flow test
bash tests/test_core_flow.sh
```

The test script validates:
-  Job enqueueing
-  Successful job execution
- Failed job retry with backoff
- DLQ movement after max retries
- Worker graceful shutdown

### Run Demo

```bash
# Run the interactive demo
bash run_demo.sh
```

The demo showcases:
- Enqueueing various job types
- Starting workers
- Viewing status and job lists
- DLQ inspection and retry

## Design Decisions & Trade-offs

### Choices Made

1. **SQLite over Redis/RabbitMQ**
   - No external dependencies
   - Simple deployment
   -  Built-in persistence
   -  Limited to single-machine deployments

2. **Multiprocessing over Threading**
   -  True parallelism (no GIL)
   - Process isolation
   - Higher memory overhead

3. **Atomic SQL Updates for Locking**
   - No race conditions
   - No distributed lock manager needed
   - Automatic cleanup (no stale locks)

4. **Exponential Backoff**
   - Reduces load on failing resources
   - Increases success probability
   - Can delay recovery

5. **WAL Mode for SQLite**
   - Better concurrent reads/writes
   - Creates additional files (-wal, -shm)

### Assumptions

- **Single Machine**: Workers run on the same machine as the database
- **Command Trust**: Commands are trusted (no sandboxing)
- **Timeout**: Jobs have a 5-minute execution timeout
- **Error Storage**: Only first 1000 chars of error messages stored
- **PID Tracking**: Worker PIDs stored in config for stop command

### Limitations

- **No Distributed Workers**: All workers must access same SQLite file
- **No Job Priority**: Jobs processed FIFO by creation time
- **No Job Cancellation**: Running jobs cannot be canceled mid-execution
- **No Job Dependencies**: Jobs are independent (no DAG support)
- **Limited Observability**: Basic console logging only

## Project Structure

```
d:\Python/
├── queuectl/
│   ├── __init__.py       # Package initialization
│   ├── cli.py            # Click-based CLI commands
│   ├── db.py             # SQLite wrapper and schema
│   ├── models.py         # Job dataclass
│   ├── worker.py         # Worker process logic
│   ├── queue.py          # Queue operations (enqueue, list, status)
│   └── config.py         # Configuration helpers
├── tests/
│   └── test_core_flow.sh # Integration test script
├── requirements.txt      # Python dependencies
├── setup.py              # Package installation config
├── run_demo.sh           # Demo script
└── README.md             # This file
```

## Advanced Usage

### Custom Backoff Strategy

```bash
# Set backoff base to 3 for slower retry escalation
queuectl config set backoff_base 3

# Attempts will delay: 3s, 9s, 27s, 81s...
```

### Scheduled Jobs

```bash
# Schedule a job for future execution
queuectl enqueue '{"id":"scheduled1","command":"echo Morning report","run_at":"2025-11-09T08:00:00Z"}'
```

### Environment Variables

```bash
# Use custom database location
export QUEUECTL_DB_PATH=/path/to/custom/queuectl.db
queuectl status
```

### Monitoring Workers

```bash
# Check worker PIDs
queuectl config get worker_pids

# Monitor worker processes (Linux/Mac)
ps aux | grep queuectl

# Monitor worker processes (Windows PowerShell)
Get-Process | Where-Object {$_.ProcessName -like "*python*"}
```

## Troubleshooting

### Workers Not Processing Jobs

1. Check workers are running: `queuectl status`
2. Verify jobs are pending: `queuectl list --state pending`
3. Check for stuck processing jobs: `queuectl list --state processing`
4. Review database: `sqlite3 queuectl.db "SELECT * FROM jobs;"`

### Database Locked Errors

- SQLite WAL mode reduces this, but under heavy load:
  - Reduce number of concurrent workers
  - Increase `busy_timeout` in `db.py`

### Jobs Stuck in Processing

- If worker crashes, jobs may remain in `processing` state
- Manual recovery: Update state in database or implement cleanup script

### Permission Errors on Windows

- Run terminal as Administrator for process signaling
- Or use foreground worker mode without `--daemon`

## Contributing

To extend `queuectl`:

1. **Add New Job States**: Modify `models.py` and state transition logic
2. **Custom Retry Logic**: Extend `worker.handle_job_result()`
3. **Metrics**: Add prometheus/statsd integration in `worker.py`
4. **Web UI**: Build Flask/FastAPI dashboard reading from `queuectl.db`

## License

MIT License - feel free to use and modify as needed.

---

**Questions or Issues?** Check the test scripts in `tests/` for working examples.
