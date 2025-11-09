import subprocess
import time
import sys
import os

def run_command(cmd, description):
    print(f"\n{description}")
    print(f"Command: {cmd}")
    print("-" * 60)
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        if result.returncode != 0:
            print(f"Command failed with exit code {result.returncode}")
            return False
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def cleanup_db():
    for f in ['queuectl.db', 'queuectl.db-wal', 'queuectl.db-shm']:
        if os.path.exists(f):
            os.remove(f)
            print(f"Removed {f}")

def main():
    print("=" * 60)
    print("queuectl Basic Functionality Test")
    print("=" * 60)
    
    print("\nCleaning up old database...")
    cleanup_db()
    
    print("\n" + "=" * 60)
    print("TEST 1: Enqueue Jobs")
    print("=" * 60)
    
    jobs = [
        ('job1', 'echo Hello from job1'),
        ('job2', 'echo Success job'),
        ('job3', 'cmd /c exit 1')
    ]
    
    for job_id, command in jobs:
        cmd = f'queuectl enqueue \'{{"id":"{job_id}","command":"{command}","max_retries":2}}\''
        if not run_command(cmd, f"Enqueueing {job_id}"):
            print(f"Failed to enqueue {job_id}")
    
    print("\n" + "=" * 60)
    print("TEST 2: Queue Status")
    print("=" * 60)
    run_command("queuectl status", "Checking queue status")
    
    print("\n" + "=" * 60)
    print("TEST 3: List Jobs")
    print("=" * 60)
    run_command("queuectl list", "Listing all jobs")
    
    print("\n" + "=" * 60)
    print("TEST 4: List Pending Jobs")
    print("=" * 60)
    run_command("queuectl list --state pending", "Listing pending jobs")
    
    print("\n" + "=" * 60)
    print("TEST 5: Configuration")
    print("=" * 60)
    run_command("queuectl config get backoff_base", "Get backoff_base config")
    run_command("queuectl config get max_retries", "Get max_retries config")
    
    print("\n" + "=" * 60)
    print("Basic Tests Complete!")
    print("=" * 60)
    print("\nTo test worker functionality:")
    print('  1. Run: queuectl worker start --count 1')
    print('  2. Watch jobs being processed')
    print('  3. Press Ctrl+C to stop workers')
    print("\nTo view completed jobs:")
    print('  queuectl list --state completed')
    print("\nTo view DLQ:")
    print('  queuectl dlq list')
    
if __name__ == '__main__':
    main()
