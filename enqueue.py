"""
Helper script to enqueue jobs from Windows PowerShell
Usage: python enqueue.py <job_id> <command> [max_retries]
"""
import sys
import json
from queuectl.queue import enqueue_job

def main():
    if len(sys.argv) < 3:
        print("Usage: python enqueue.py <job_id> <command> [max_retries]")
        print("\nExamples:")
        print('  python enqueue.py job1 "echo Hello"')
        print('  python enqueue.py job2 "timeout /t 5" 3')
        print('  python enqueue.py failing "cmd /c exit 1" 2')
        sys.exit(1)
    
    job_id = sys.argv[1]
    command = sys.argv[2]
    max_retries = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    
    job_data = {
        "id": job_id,
        "command": command,
        "max_retries": max_retries
    }
    
    try:
        job = enqueue_job(job_data)
        print(f"✓ Enqueued job: {job.id}")
        print(f"  Command: {job.command}")
        print(f"  Max retries: {job.max_retries}")
        print(f"  State: {job.state}")
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
