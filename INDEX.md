queuectl - Getting Started

Welcome to queuectl - a robust, SQLite-backed background job queue for Python!

Quick Start

pip install -e .
python enqueue.py test1 "echo Hello World"
queuectl worker start --count 1
queuectl status

Documentation Guide

New Users
Start here: QUICKSTART.md
- Installation steps
- Basic commands
- Common usage patterns
- Troubleshooting

Windows Users
Read this: WINDOWS_GUIDE.md
- PowerShell-specific instructions
- Helper functions
- Real-world Windows examples
- Service setup

Complete Reference
Read this: README.md
- Full architecture documentation
- All features explained
- Design decisions
- API reference

See It In Action
Run this: python demo_interactive.py
- Interactive demonstration
- Step-by-step walkthrough
- All features showcased

Project Overview
Read this: PROJECT_SUMMARY.md
- What was built
- Features checklist
- Testing results
- Success metrics

Common Tasks

Enqueue Jobs

python enqueue.py job1 "echo Hello"
python enqueue.py job2 "timeout /t 5" 3
. .\queuectl_helpers.ps1
Enqueue-Job -Id "job1" -Command "echo Hello"

Process Jobs

queuectl worker start --count 1
queuectl worker start --count 2 --daemon
queuectl worker stop

Monitor Queue

queuectl status
queuectl list
queuectl list --state completed
queuectl list --state pending
queuectl list --state dead
queuectl dlq list

Configure

queuectl config get backoff_base
queuectl config get max_retries
queuectl config set backoff_base 3
queuectl config set max_retries 5

Testing

Run Automated Tests

python test_api.py
.\tests\test_core_flow.ps1
bash tests/test_core_flow.sh

Run Interactive Demo

python demo_interactive.py

Run Basic Tests

python test_basic.py

Project Structure

d:\Python/
├── queuectl/
│   ├── __init__.py
│   ├── cli.py
│   ├── db.py
│   ├── models.py
│   ├── worker.py
│   ├── queue.py
│   └── config.py
│
├── tests/
│   ├── test_core_flow.sh
│   └── test_core_flow.ps1
│
├── Documentation
│   ├── README.md
│   ├── QUICKSTART.md
│   ├── WINDOWS_GUIDE.md
│   ├── PROJECT_SUMMARY.md
│   └── INDEX.md
│
├── Helper Scripts
│   ├── enqueue.py
│   ├── queuectl_helpers.ps1
│   ├── test_api.py
│   ├── test_basic.py
│   ├── demo_interactive.py
│   ├── run_demo.sh
│   └── run_demo.ps1
│
├── Configuration
│   ├── setup.py
│   └── requirements.txt
│
└── Database (auto-created)
    └── queuectl.db

Learning Path

Install

pip install -e .
queuectl --help

Try Basic Commands

python enqueue.py test "echo test"
queuectl status
queuectl list

Run Interactive Demo

python demo_interactive.py

Read Quick Start
Open QUICKSTART.md
Try example commands

Explore Windows Guide
Open WINDOWS_GUIDE.md
Try PowerShell helpers
Review examples

Deep Dive into Architecture
Read README.md
Understand design decisions
Learn about internals

Troubleshooting

Issue: "queuectl: command not found"

pip install -e .
queuectl --help

Issue: PowerShell JSON quoting problems

python enqueue.py job1 "echo Hello"
. .\queuectl_helpers.ps1
Enqueue-Job -Id "job1" -Command "echo Hello"

Issue: Workers not processing

queuectl status
queuectl worker start --count 1
queuectl list --state pending

Issue: Need to reset everything

queuectl worker stop
Remove-Item queuectl.db*
queuectl status

Use Cases

Batch Processing

$files = Get-ChildItem *.txt
foreach ($file in $files) {
    python enqueue.py "process-$($file.Name)" "python process.py $file"
}
queuectl worker start --count 4

Scheduled Tasks

python enqueue.py daily-backup "powershell -File backup.ps1" 2
queuectl worker start --count 1

API Rate Limiting

queuectl config set backoff_base 3
python enqueue.py api-sync "python sync_api.py" 5
queuectl worker start --count 1

Email Queue

$users = Import-Csv users.csv
foreach ($user in $users) {
    python enqueue.py "email-$($user.id)" "python send_email.py $($user.email)" 3
}
queuectl worker start --count 2

Features at a Glance

Feature | Status | Description
SQLite Storage | Yes | Persistent job queue
Multiple Workers | Yes | Parallel processing
Exponential Backoff | Yes | Smart retry delays
Dead Letter Queue | Yes | Failed job management
Atomic Job Claiming | Yes | No duplicate processing
Graceful Shutdown | Yes | Finish current jobs
Scheduled Jobs | Yes | Delay execution
Configuration | Yes | Persistent settings
CLI Interface | Yes | Easy management
Windows Support | Yes | PowerShell helpers

Getting Help

Read README.md
Check WINDOWS_GUIDE.md
See QUICKSTART.md
Run python demo_interactive.py
Read PROJECT_SUMMARY.md

Next Steps

Read the Windows Guide for advanced usage
Try the interactive demo
Explore real-world examples
Run the test suite
Integrate into your project

Quick Reference Card

python enqueue.py <id> "<command>" [retries]
queuectl worker start --count N
queuectl worker stop
queuectl status
queuectl list [--state STATE]
queuectl dlq list
queuectl dlq retry <job-id>
queuectl config get <key>
queuectl config set <key> <value>

Ready to start? Run: python demo_interactive.py
Need help? Read: QUICKSTART.md
Want details? Read: README.md

queuectl - Simple, Reliable, Background Job Processing
