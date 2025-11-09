"""
Queue operations: enqueue, list, status, DLQ retry
"""
import json
from typing import List, Optional, Dict
from datetime import datetime
from queuectl.db import get_db
from queuectl.models import Job, get_utc_now, get_unix_timestamp
from queuectl.config import get_config_int


def enqueue_job(job_data: dict) -> Job:
    """
    Enqueue a new job
    
    Args:
        job_data: Dictionary with at least 'id' and 'command' fields
                 Optional: 'max_retries', 'run_at' (ISO string)
    
    Returns:
        Created Job object
    """
    if 'id' not in job_data or 'command' not in job_data:
        raise ValueError("Job must contain 'id' and 'command' fields")
    
    job_id = job_data['id']
    command = job_data['command']
    max_retries = job_data.get('max_retries', get_config_int('max_retries', 3))
    
    run_after = 0
    if 'run_at' in job_data:
        try:
            run_at_dt = datetime.fromisoformat(job_data['run_at'].replace('Z', '+00:00'))
            run_after = int(run_at_dt.timestamp())
        except (ValueError, AttributeError):
            run_after = 0
    
    created_at = get_utc_now()
    
    job = Job(
        id=job_id,
        command=command,
        state='pending',
        attempts=0,
        max_retries=max_retries,
        created_at=created_at,
        updated_at=created_at,
        run_after=run_after
    )
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO jobs (id, command, state, attempts, max_retries, 
                            created_at, updated_at, locked_by, locked_at, 
                            last_error, run_after)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job.id, job.command, job.state, job.attempts, job.max_retries,
            job.created_at, job.updated_at, job.locked_by, job.locked_at,
            job.last_error, job.run_after
        ))
    
    return job


def list_jobs(state: Optional[str] = None) -> List[Job]:
    """
    List jobs, optionally filtered by state
    
    Args:
        state: Optional state filter (pending, processing, completed, failed, dead)
    
    Returns:
        List of Job objects
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        if state:
            cursor.execute("""
                SELECT id, command, state, attempts, max_retries, 
                       created_at, updated_at, locked_by, locked_at, 
                       last_error, run_after
                FROM jobs
                WHERE state = ?
                ORDER BY created_at DESC
            """, (state,))
        else:
            cursor.execute("""
                SELECT id, command, state, attempts, max_retries, 
                       created_at, updated_at, locked_by, locked_at, 
                       last_error, run_after
                FROM jobs
                ORDER BY created_at DESC
            """)
        
        rows = cursor.fetchall()
        return [Job.from_db_row(row) for row in rows]


def get_job(job_id: str) -> Optional[Job]:
    """Get a single job by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, command, state, attempts, max_retries, 
                   created_at, updated_at, locked_by, locked_at, 
                   last_error, run_after
            FROM jobs
            WHERE id = ?
        """, (job_id,))
        
        row = cursor.fetchone()
        return Job.from_db_row(row) if row else None


def get_status() -> Dict:
    """
    Get queue status with job counts per state and active workers
    
    Returns:
        Dictionary with status information
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT state, COUNT(*) 
            FROM jobs 
            GROUP BY state
        """)
        
        state_counts = {}
        for row in cursor.fetchall():
            state_counts[row[0]] = row[1]
        
        cursor.execute("SELECT value FROM config WHERE key = 'worker_pids'")
        row = cursor.fetchone()
        worker_pids = row[0] if row and row[0] else ""
        
        return {
            "state_counts": state_counts,
            "worker_pids": [pid.strip() for pid in worker_pids.split(',') if pid.strip()],
            "total_jobs": sum(state_counts.values())
        }


def list_dlq() -> List[Job]:
    """List jobs in the dead letter queue (state='dead')"""
    return list_jobs(state='dead')


def retry_dlq_job(job_id: str) -> Job:
    """
    Retry a job from the DLQ by moving it back to pending state
    
    Args:
        job_id: ID of the job to retry
    
    Returns:
        Updated Job object
    
    Raises:
        ValueError: If job not found or not in dead state
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT state FROM jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        
        if not row:
            raise ValueError(f"Job {job_id} not found")
        
        if row[0] != 'dead':
            raise ValueError(f"Job {job_id} is not in dead state (current: {row[0]})")
        
        updated_at = get_utc_now()
        cursor.execute("""
            UPDATE jobs
            SET state = 'pending',
                attempts = 0,
                updated_at = ?,
                locked_by = NULL,
                locked_at = NULL,
                run_after = 0
            WHERE id = ?
        """, (updated_at, job_id))
    
    job = get_job(job_id)
    if not job:
        raise ValueError(f"Failed to retrieve job {job_id} after retry")
    
    return job


def update_job_state(job_id: str, state: str, **kwargs):
    """
    Update job state and other fields
    
    Args:
        job_id: Job ID
        state: New state
        **kwargs: Additional fields to update (attempts, last_error, etc.)
    """
    updated_at = get_utc_now()
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        fields = ["state = ?", "updated_at = ?"]
        values = [state, updated_at]
        
        for key, value in kwargs.items():
            fields.append(f"{key} = ?")
            values.append(value)
        
        values.append(job_id)
        
        query = f"UPDATE jobs SET {', '.join(fields)} WHERE id = ?"
        cursor.execute(query, values)
