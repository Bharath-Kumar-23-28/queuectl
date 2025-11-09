"""
Worker process implementation
"""
import os
import sys
import time
import signal
import subprocess
import uuid
from typing import Optional
from queuectl.db import get_db, init_db
from queuectl.models import Job, get_utc_now, get_unix_timestamp
from queuectl.config import get_config_int, get_config_float


should_stop = False


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global should_stop
    print(f"\n[Worker {os.getpid()}] Received signal {signum}, initiating graceful shutdown...")
    should_stop = True


def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def claim_job(worker_id: str) -> Optional[Job]:
    """
    Atomically claim a pending job
    
    Args:
        worker_id: Unique worker identifier
    
    Returns:
        Claimed Job object or None if no jobs available
    """
    current_ts = get_unix_timestamp()
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id FROM jobs 
            WHERE state = 'pending' AND run_after <= ?
            ORDER BY created_at
            LIMIT 1
        """, (current_ts,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        job_id = row[0]
        locked_at = get_utc_now()
        
        cursor.execute("""
            UPDATE jobs
            SET state = 'processing',
                locked_by = ?,
                locked_at = ?,
                updated_at = ?
            WHERE id = ? AND state = 'pending'
        """, (worker_id, locked_at, locked_at, job_id))
        
        if cursor.rowcount == 0:
            return None
        
        cursor.execute("""
            SELECT id, command, state, attempts, max_retries, 
                   created_at, updated_at, locked_by, locked_at, 
                   last_error, run_after
            FROM jobs
            WHERE id = ?
        """, (job_id,))
        
        row = cursor.fetchone()
        return Job.from_db_row(row) if row else None


def execute_job(job: Job) -> tuple[bool, str]:
    """
    Execute a job command
    
    Args:
        job: Job to execute
    
    Returns:
        Tuple of (success, output/error message)
    """
    try:
        result = subprocess.run(
            job.command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        success = result.returncode == 0
        output = result.stdout if success else result.stderr
        return success, output or f"Exit code: {result.returncode}"
    
    except subprocess.TimeoutExpired:
        return False, "Job execution timeout (5 minutes)"
    
    except Exception as e:
        return False, f"Execution error: {str(e)}"


def handle_job_result(job: Job, success: bool, output: str, backoff_base: float):
    """
    Update job state based on execution result
    
    Args:
        job: Job that was executed
        success: Whether execution succeeded
        output: Output or error message
        backoff_base: Exponential backoff base for retry delay
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        if success:
            cursor.execute("""
                UPDATE jobs
                SET state = 'completed',
                    updated_at = ?,
                    locked_by = NULL,
                    locked_at = NULL
                WHERE id = ?
            """, (get_utc_now(), job.id))
        
        else:
            new_attempts = job.attempts + 1
            
            if new_attempts < job.max_retries:
                backoff_seconds = int(backoff_base ** new_attempts)
                run_after = get_unix_timestamp() + backoff_seconds
                
                cursor.execute("""
                    UPDATE jobs
                    SET state = 'pending',
                        attempts = ?,
                        run_after = ?,
                        updated_at = ?,
                        last_error = ?,
                        locked_by = NULL,
                        locked_at = NULL
                    WHERE id = ?
                """, (new_attempts, run_after, get_utc_now(), output[:1000], job.id))
            
            else:
                cursor.execute("""
                    UPDATE jobs
                    SET state = 'dead',
                        attempts = ?,
                        updated_at = ?,
                        last_error = ?,
                        locked_by = NULL,
                        locked_at = NULL
                    WHERE id = ?
                """, (new_attempts, get_utc_now(), output[:1000], job.id))


def worker_loop(worker_id: str, backoff_base: float):
    """
    Main worker loop - claim and execute jobs
    
    Args:
        worker_id: Unique worker identifier
        backoff_base: Exponential backoff base for retries
    """
    global should_stop
    
    print(f"[Worker {worker_id}] Started (PID: {os.getpid()})")
    
    while not should_stop:
        try:
            job = claim_job(worker_id)
            
            if job:
                print(f"[Worker {worker_id}] Processing job {job.id}: {job.command}")
                success, output = execute_job(job)
                handle_job_result(job, success, output, backoff_base)
                
                if success:
                    print(f"[Worker {worker_id}] Job {job.id} completed successfully")
                else:
                    print(f"[Worker {worker_id}] Job {job.id} failed (attempt {job.attempts + 1}/{job.max_retries}): {output[:100]}")
            else:
                time.sleep(1)
        
        except KeyboardInterrupt:
            print(f"\n[Worker {worker_id}] Interrupted, shutting down...")
            break
        
        except Exception as e:
            print(f"[Worker {worker_id}] Error in worker loop: {e}")
            time.sleep(1)
    
    print(f"[Worker {worker_id}] Stopped gracefully")


def start_worker(backoff_base: Optional[float] = None):
    """
    Start a worker process
    
    Args:
        backoff_base: Exponential backoff base (from config if not specified)
    """
    init_db()
    setup_signal_handlers()
    
    if backoff_base is None:
        backoff_base = get_config_float('backoff_base', 2.0)
    
    worker_id = f"worker-{os.getpid()}-{uuid.uuid4().hex[:8]}"
    worker_loop(worker_id, backoff_base)
