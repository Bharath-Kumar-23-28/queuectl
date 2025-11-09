# queuectl - Getting Started Welcome to **queuectl** - a robust, SQLite-backed background job queue for Python! ##  Quick Start 
powershell
# 1. Install
pip install -e .

# 2. Enqueue a job
python enqueue.py test1 "echo Hello World"

# 3. Process it
queuectl worker start --count 1

# 4. Check status
queuectl status
##  Documentation Guide Choose your path based on your needs: ###  New Users **Start here:** [QUICKSTART.md](QUICKSTART.md) - Installation steps - Basic commands - Common usage patterns - Troubleshooting ###  Windows Users **Read this:** [WINDOWS_GUIDE.md](WINDOWS_GUIDE.md) - PowerShell-specific instructions - Helper functions - Real-world Windows examples - Service setup ###  Complete Reference **Read this:** [README.md](README.md) - Full architecture documentation - All features explained - Design decisions - API reference ###  See It In Action **Run this:** python demo_interactive.py - Interactive demonstration - Step-by-step walkthrough - All features showcased ###  Project Overview **Read this:** [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - What was built - Features checklist - Testing results - Success metrics ##  Common Tasks ### Enqueue Jobs
powershell
# Easiest way (Windows)
python enqueue.py job1 "echo Hello"
python enqueue.py job2 "timeout /t 5" 3

# Using PowerShell helpers
. .\queuectl_helpers.ps1
Enqueue-Job -Id "job1" -Command "echo Hello"
### Process Jobs
powershell
# Foreground (see logs, Ctrl+C to stop)
queuectl worker start --count 1

# Background (daemon mode)
queuectl worker start --count 2 --daemon
queuectl worker stop
### Monitor Queue
powershell
# Status overview
queuectl status

# List all jobs
queuectl list

# Filter by state
queuectl list --state completed
queuectl list --state pending
queuectl list --state dead

# View failed jobs
queuectl dlq list
### Configure
powershell
# View settings
queuectl config get backoff_base
queuectl config get max_retries

# Update settings
queuectl config set backoff_base 3
queuectl config set max_retries 5
##  Testing ### Run Automated Tests
powershell
# Direct API test (recommended)
python test_api.py

# PowerShell integration test
.\tests\test_core_flow.ps1

# Bash integration test (Git Bash/WSL)
bash tests/test_core_flow.sh
### Run Interactive Demo
powershell
python demo_interactive.py
### Run Basic Tests
powershell
python test_basic.py
## Project Structure
d:\Python/
├── queuectl/              # Main package
│   ├── __init__.py       # Package init
│   ├── cli.py            # CLI commands
│   ├── db.py             # Database layer
│   ├── models.py         # Data models
│   ├── worker.py         # Worker logic
│   ├── queue.py          # Queue operations
│   └── config.py         # Configuration
│
├── tests/                 # Test scripts
│   ├── test_core_flow.sh # Bash tests
│   └── test_core_flow.ps1# PowerShell tests
│
├── Documentation
│   ├── README.md         # Complete docs
│   ├── QUICKSTART.md     # Quick guide
│   ├── WINDOWS_GUIDE.md  # Windows-specific
│   ├── PROJECT_SUMMARY.md# What was built
│   └── INDEX.md          # This file
│
├── Helper Scripts
│   ├── enqueue.py        # Easy job enqueueing
│   ├── queuectl_helpers.ps1  # PowerShell functions
│   ├── test_api.py       # API test
│   ├── test_basic.py     # Basic test
│   ├── demo_interactive.py   # Interactive demo
│   ├── run_demo.sh       # Bash demo
│   └── run_demo.ps1      # PowerShell demo
│
├── Configuration
│   ├── setup.py          # Package setup
│   └── requirements.txt  # Dependencies
│
└── Database (auto-created)
    └── queuectl.db       # SQLite database
##  Learning Path 1. **Install** (5 min)
powershell
   pip install -e .
   queuectl --help
2. **Try Basic Commands** (5 min)
powershell
   python enqueue.py test "echo test"
   queuectl status
   queuectl list
3. **Run Interactive Demo** (10 min)
powershell
   python demo_interactive.py
4. **Read Quick Start** (10 min) - Open [QUICKSTART.md](QUICKSTART.md) - Try example commands 5. **Explore Windows Guide** (15 min) - Open [WINDOWS_GUIDE.md](WINDOWS_GUIDE.md) - Try PowerShell helpers - Review real-world examples 6. **Deep Dive into Architecture** (30 min) - Read [README.md](README.md) - Understand design decisions - Learn about internals ##  Troubleshooting ### Issue: "queuectl: command not found"
powershell
# Reinstall
pip install -e .

# Verify
queuectl --help
### Issue: PowerShell JSON quoting problems
powershell
# Use Python helper instead
python enqueue.py job1 "echo Hello"

# Or load PowerShell module
. .\queuectl_helpers.ps1
Enqueue-Job -Id "job1" -Command "echo Hello"
### Issue: Workers not processing
powershell
# Check status
queuectl status

# Start worker with visible logs
queuectl worker start --count 1

# Check for pending jobs
queuectl list --state pending
### Issue: Need to reset everything
powershell
# Stop workers
queuectl worker stop

# Remove database
Remove-Item queuectl.db*

# Restart
queuectl status  # Creates fresh DB
## Use Cases ### Batch Processing
powershell
# Process multiple files
$files = Get-ChildItem *.txt
foreach ($file in $files) {
    python enqueue.py "process-$($file.Name)" "python process.py $file"
}
queuectl worker start --count 4
### Scheduled Tasks
powershell
# Daily backup
python enqueue.py daily-backup "powershell -File backup.ps1" 2
queuectl worker start --count 1
### API Rate Limiting
powershell
# Slow backoff for API calls
queuectl config set backoff_base 3
python enqueue.py api-sync "python sync_api.py" 5
queuectl worker start --count 1
### Email Queue
powershell
# Send emails with retry
$users = Import-Csv users.csv
foreach ($user in $users) {
    python enqueue.py "email-$($user.id)" "python send_email.py $($user.email)" 3
}
queuectl worker start --count 2
##  Features at a Glance | Feature | Status | Description | |---------|--------|-------------| | SQLite Storage |  | Persistent job queue | | Multiple Workers |  | Parallel processing | | Exponential Backoff |  | Smart retry delays | | Dead Letter Queue |  | Failed job management | | Atomic Job Claiming |  | No duplicate processing | | Graceful Shutdown |  | Finish current jobs | | Scheduled Jobs | | Delay execution | | Configuration | | Persistent settings | | CLI Interface |  | Easy management | | Windows Support |  | PowerShell helpers | ##  Getting Help - **Questions?** Read [README.md](README.md) - **Windows issues?** Check [WINDOWS_GUIDE.md](WINDOWS_GUIDE.md) - **Quick reference?** See [QUICKSTART.md](QUICKSTART.md) - **Want examples?** Run python demo_interactive.py - **Architecture details?** Read [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) ##  Next Steps After completing the quick start: 1.  Read the Windows Guide for advanced usage 2.  Try the interactive demo 3.  Explore real-world examples 4.  Run the test suite 5.  Integrate into your project ##  Quick Reference Card
powershell
# ENQUEUE
python enqueue.py <id> "<command>" [retries]

# WORKERS
queuectl worker start --count N      # Start N workers
queuectl worker stop                 # Stop all workers

# MONITOR
queuectl status                      # Show overview
queuectl list [--state STATE]        # List jobs

# DLQ
queuectl dlq list                    # View failed jobs
queuectl dlq retry <job-id>          # Retry failed job

# CONFIG
queuectl config get <key>            # Get value
queuectl config set <key> <value>    # Set value
--- **Ready to start?** Run: python demo_interactive.py **Need help?** Read: [QUICKSTART.md](QUICKSTART.md) **Want details?** Read: [README.md](README.md) --- *queuectl - Simple, Reliable, Background Job Processing* remove emotes and comments, and what is this md file
