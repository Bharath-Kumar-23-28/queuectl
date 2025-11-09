Demo Recording Guide

Files Created

demo_recording.ps1 - Full version with pauses (good for practicing)

demo_recording_smooth.ps1 - Smooth version without pauses (for actual recording)

show_db.py - Database inspection helper

Quick Start

Practice version (with pauses)

.\demo_recording.ps1

Smooth recording version

.\demo_recording_smooth.ps1

Database Inspection Commands

python show_db.py tables # Show table names
python show_db.py schema # Show table structure
python show_db.py jobs # Show all jobs (simple view)
python show_db.py detailed # Show jobs with worker info
python show_db.py config # Show configuration
python show_db.py pending # Show pending jobs with backoff timing
python show_db.py dlq # Show dead letter queue
python show_db.py stats # Show job counts by state
python show_db.py all # Show jobs + stats

Recording Flow Summary

Scene | Duration | Action | DB Inspection

Intro | 30s | Show CLI help | -

Init | 45s | Create database | tables, schema

Enqueue | 45s | Add 4 jobs | jobs

Status | 30s | Show queue | -

Process | 90s | Start worker, Ctrl+C | detailed, pending

Retry | 60s | Start worker, Ctrl+C | jobs

DLQ | 30s | Show failed jobs | dlq

DLQ Retry | 45s | Retry from DLQ | dlq, pending

Config | 30s | Update config | config

Multi-worker | 90s | 3 workers, Ctrl+C | jobs, detailed

Final | 30s | Final status | stats, jobs

Summary | 20s | Wrap up | -
TOTAL: 8–10 minutes

Key Moments to Highlight

Database Changes to Show

After Enqueue: All jobs in PENDING state
python show_db.py jobs

During Processing: locked_by field shows active worker
python show_db.py detailed

After First Failure: attempts=1, run_after timestamp set
python show_db.py pending

After Max Retries: state=dead
python show_db.py dlq

After DLQ Retry: state=pending, attempts=0
python show_db.py pending

Config Change: backoff_base updated
python show_db.py config

Multi-worker: Different locked_by for each job
python show_db.py detailed

Recording Tips

Terminal Setup

Font size: 14–16pt

Window size: at least 120x30

Use high contrast theme

Clear the screen before starting

Timing

Let worker logs run for 2–3 seconds before pressing Ctrl+C

Allow time for viewers to read database output (pause 2 seconds)

Speak while commands execute

Narration Points

Scene 5 (Processing):
"Watch jobs transition from pending to processing to completed. The locked_by field shows which worker claimed each job. The failing job increments attempts and returns to pending with a backoff delay."

Scene 6 (Retry):
"The run_after timestamp implements exponential backoff. First retry after 2 seconds, second after 4 seconds. This prevents hammering failed services."

Scene 7 (DLQ):
"After exhausting max retries, jobs move to the dead state. The last_error field preserves the failure reason for debugging."

Scene 10 (Multi-worker):
"Three workers process jobs in parallel. Each worker atomically claims jobs using SQL updates. Notice each job has a different locked_by value - no duplicates."

Pre-Recording Checklist

[ ] Clean database: Remove-Item queuectl.db*
[ ] Terminal font size readable
[ ] Recording software ready
[ ] Microphone tested
[ ] Script reviewed
[ ] Practice run completed
[ ] Timer ready for Ctrl+C moments

Worker Stop Times

Scene | Start Command | Wait Time | Stop
5. Process | worker start --count 1 | 15–18s | Ctrl+C
6. Retry | worker start --count 1 | 10–12s | Ctrl+C
10. Multi | worker start --count 3 | 8–10s | Ctrl+C

Scene-by-Scene Narration

Scene 1
"queuectl is a production-ready background job queue. It provides a simple CLI for managing jobs with retry logic and failure handling."

Scene 2
"The system uses SQLite with two tables: jobs for queue state and config for settings. All state persists across restarts."

Scene 3
"Let's enqueue four jobs — three that succeed and one that will fail. Notice all jobs start in pending state with zero attempts."

Scene 5
"The worker atomically claims jobs and executes them. Successful jobs move to completed. The failing job retries with exponential backoff."

Scene 7
"Jobs that exhaust their retries move to the Dead Letter Queue. This prevents infinite retry loops while preserving failed jobs for inspection."

Scene 10
"Multiple workers can run concurrently. Atomic SQL updates ensure each job is processed exactly once, even with parallel workers."

Quick Commands Reference

Clean start

Remove-Item queuectl.db* -ErrorAction SilentlyContinue
Clear-Host

Run smooth demo

.\demo_recording_smooth.ps1

Quick DB check at any time

python show_db.py all

Common Issues

Issue: Database doesn't exist
Fix: Run queuectl status first

Issue: Jobs not processing
Fix: Check with python show_db.py pending

Issue: Can't stop worker
Fix: Press Ctrl+C once, wait 2 seconds

Post-Recording

Optional edits:

Speed up waiting sections (2x)

Add text overlays for key concepts

Highlight database fields (locked_by, run_after, state)

Add captions for narration

File Cleanup After Recording

Remove-Item queuectl.db*