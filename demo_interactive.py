"""
Interactive demonstration of queuectl features
"""
import time
import sys
from multiprocessing import Process
from queuectl.db import reset_db
from queuectl.queue import enqueue_job, get_status, list_jobs, list_dlq, retry_dlq_job
from queuectl.worker import start_worker

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_status():
    status = get_status()
    print(f"\nQueue Status:")
    print(f"   Total jobs: {status['total_jobs']}")
    for state, count in sorted(status['state_counts'].items()):
        if count > 0:
            print(f"   {state}: {count}")
    print()

def main():
    print_header("queuectl Interactive Demo")
    print("\nThis demo will showcase all features of queuectl:")
    print("  Job enqueueing")
    print("  Worker processing")
    print("  Retry with exponential backoff")
    print("  Dead Letter Queue (DLQ)")
    print("  DLQ retry")
    print("\nPress Enter to start...")
    input()
    
    print_header("Step 1: Clean Slate")
    print("Resetting database...")
    reset_db()
    print("Database reset complete")
    input("\nPress Enter to continue...")
    
    print_header("Step 2: Enqueue Jobs")
    
    print("\nEnqueueing successful jobs...")
    enqueue_job({"id": "demo-1", "command": "echo Job 1 completed"})
    print("   demo-1: echo success")
    
    enqueue_job({"id": "demo-2", "command": "echo Job 2 completed"})
    print("   demo-2: echo success")
    
    enqueue_job({"id": "demo-3", "command": "echo Job 3 completed"})
    print("   demo-3: echo success")
    
    print("\nEnqueueing a failing job...")
    enqueue_job({"id": "demo-fail", "command": "cmd /c exit 1", "max_retries": 2})
    print("   demo-fail: will fail and retry 2 times")
    
    print_status()
    input("Press Enter to continue...")
    
    print_header("Step 3: Start Worker")
    print("\nStarting worker process...")
    print("   Watch the jobs being processed below:\n")
    
    worker = Process(target=start_worker, args=(2.0,))
    worker.start()
    print(f"Worker started (PID: {worker.pid})\n")
    
    print("Waiting 5 seconds for initial processing...")
    time.sleep(5)
    
    print_status()
    
    completed = list_jobs(state='completed')
    if completed:
        print("Completed jobs:")
        for job in completed:
            print(f"   {job.id}")
    
    input("\nPress Enter to continue...")
    
    print_header("Step 4: Retry Logic & Exponential Backoff")
    print("\nThe failing job will retry with exponential backoff:")
    print("   Attempt 1: fails, retry after 2^1 = 2 seconds")
    print("   Attempt 2: fails, retry after 2^2 = 4 seconds")
    print("   Attempt 3: fails, moves to DLQ (Dead Letter Queue)")
    
    print("\nWaiting 10 seconds to observe retries...")
    
    for i in range(10):
        time.sleep(1)
        sys.stdout.write(f"\r   {i+1}/10 seconds elapsed...")
        sys.stdout.flush()
    
    print("\n")
    print_status()
    input("\nPress Enter to continue...")
    
    print_header("Step 5: Dead Letter Queue (DLQ)")
    
    dlq_jobs = list_dlq()
    print(f"\nJobs in DLQ: {len(dlq_jobs)}")
    
    if dlq_jobs:
        for job in dlq_jobs:
            print(f"\n   Job ID: {job.id}")
            print(f"   Attempts: {job.attempts}/{job.max_retries}")
            print(f"   State: {job.state}")
            if job.last_error:
                print(f"   Error: {job.last_error[:80]}")
    
    input("\nPress Enter to continue...")
    
    print_header("Step 6: Retry Failed Job from DLQ")
    
    if dlq_jobs:
        job_to_retry = dlq_jobs[0].id
        print(f"\nRetrying job: {job_to_retry}")
        
        retried = retry_dlq_job(job_to_retry)
        print(f"Job moved back to: {retried.state}")
        print(f"   Attempts reset to: {retried.attempts}")
        
        print("\nWaiting 3 seconds for retry processing...")
        time.sleep(3)
        
        final_job = [j for j in list_jobs() if j.id == job_to_retry][0]
        print(f"\n   Final state: {final_job.state}")
        print(f"   (Still fails because command is 'exit 1')")
    
    input("\nPress Enter to continue...")
    
    print_header("Step 7: Final Status")
    print_status()
    
    all_jobs = list_jobs()
    print("All jobs:")
    for job in all_jobs:
        print(f"   {job.id}: {job.state} ({job.attempts}/{job.max_retries} attempts)")
    
    print_header("Cleanup")
    print("\nStopping worker...")
    worker.terminate()
    worker.join(timeout=5)
    print("Worker stopped")
    
    print_header("Demo Complete")
    print("\nYou have seen:")
    print("   Job enqueueing")
    print("   Successful job execution")
    print("   Failed job retry with exponential backoff")
    print("   Dead Letter Queue (DLQ)")
    print("   DLQ job retry")
    print("   Graceful worker shutdown")
    
    print("\nTry it yourself:")
    print('   python enqueue.py mytest "echo Hello"')
    print('   queuectl worker start --count 1')
    print('   queuectl status')
    print('   queuectl list')
    
    print("\nFor more information:")
    print("   README.md - Complete documentation")
    print("   WINDOWS_GUIDE.md - Windows-specific usage")
    print("   QUICKSTART.md - Quick reference")
    
    print("\n" + "=" * 70)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
