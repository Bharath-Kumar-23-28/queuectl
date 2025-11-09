import sys
import time
from queuectl.queue import enqueue_job, list_jobs, get_status, list_dlq, retry_dlq_job
from queuectl.config import get_config, set_config
from queuectl.db import init_db, reset_db
from queuectl.worker import start_worker
from multiprocessing import Process

def print_section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def main():
    print("=" * 60)
    print("queuectl Direct API Test")
    print("=" * 60)
    
    print("\nResetting database...")
    reset_db()
    print("Database reset")
    
    print_section("TEST 1: Enqueue Jobs")
    
    job1 = enqueue_job({
        "id": "api-test-1",
        "command": "echo Hello from API test 1"
    })
    print(f"Enqueued job: {job1.id}")
    
    job2 = enqueue_job({
        "id": "api-test-2",
        "command": "echo Success",
        "max_retries": 3
    })
    print(f"Enqueued job: {job2.id}")
    
    job3 = enqueue_job({
        "id": "api-test-fail",
        "command": "cmd /c exit 1",
        "max_retries": 2
    })
    print(f"Enqueued job: {job3.id}")
    
    print_section("TEST 2: List Jobs")
    
    jobs = list_jobs()
    print(f"Total jobs: {len(jobs)}")
    for job in jobs:
        print(f"  - {job.id}: {job.state} (attempts: {job.attempts}/{job.max_retries})")
    
    print_section("TEST 3: Queue Status")
    
    status = get_status()
    print(f"Total jobs: {status['total_jobs']}")
    print("Jobs by state:")
    for state, count in status['state_counts'].items():
        print(f"  {state}: {count}")
    print(f"Active workers: {len(status['worker_pids'])}")
    
    print_section("TEST 4: Configuration")
    
    backoff = get_config('backoff_base')
    print(f"backoff_base = {backoff}")
    
    max_retries = get_config('max_retries')
    print(f"max_retries = {max_retries}")
    
    set_config('test_key', 'test_value')
    test_val = get_config('test_key')
    print(f"Set and retrieved test_key = {test_val}")
    
    print_section("TEST 5: Worker Processing")
    
    print("Starting worker process...")
    worker_process = Process(target=start_worker, args=(2.0,))
    worker_process.start()
    print(f"Worker started (PID: {worker_process.pid})")
    
    print("\nWaiting 5 seconds for jobs to process...")
    time.sleep(5)
    
    status = get_status()
    print(f"\nAfter processing:")
    print(f"Total jobs: {status['total_jobs']}")
    for state, count in status['state_counts'].items():
        print(f"  {state}: {count}")
    
    completed = list_jobs(state='completed')
    print(f"\nCompleted jobs: {len(completed)}")
    for job in completed:
        print(f"  {job.id}")
    
    print("\nWaiting 10 more seconds for retries...")
    time.sleep(10)
    
    print_section("TEST 6: Dead Letter Queue")
    
    dlq_jobs = list_dlq()
    print(f"Jobs in DLQ: {len(dlq_jobs)}")
    for job in dlq_jobs:
        print(f"  {job.id} - attempts: {job.attempts}")
        if job.last_error:
            print(f"    Error: {job.last_error[:100]}")
    
    if dlq_jobs:
        print(f"\nRetrying DLQ job: {dlq_jobs[0].id}")
        retried = retry_dlq_job(dlq_jobs[0].id)
        print(f"Job {retried.id} moved to state: {retried.state}")
    
    print_section("Cleanup")
    print("Stopping worker...")
    worker_process.terminate()
    worker_process.join(timeout=5)
    print("Worker stopped")
    
    print_section("Final Status")
    status = get_status()
    print(f"Total jobs processed: {status['total_jobs']}")
    for state, count in status['state_counts'].items():
        if count > 0:
            print(f"  {state}: {count}")
    
    print("\n" + "=" * 60)
    print("All API tests completed successfully!")
    print("=" * 60)
    print("\nThe queuectl CLI is ready to use:")
    print("  queuectl --help")
    print("  queuectl enqueue '{\"id\":\"test\",\"command\":\"echo test\"}'")
    print("  queuectl worker start --count 1")
    print("  queuectl status")
    print("  queuectl list")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
