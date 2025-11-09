"""
CLI entrypoint using Click
"""
import sys
import json
import time
import signal
import os
from multiprocessing import Process
import click
from queuectl.db import init_db, get_db_path
from queuectl.queue import (
    enqueue_job, list_jobs, get_status, list_dlq, retry_dlq_job
)
from queuectl.config import get_config, set_config
from queuectl.worker import start_worker


@click.group()
def cli():
    """
    queuectl - A CLI-based background job queue
    
    Manage background jobs with SQLite persistence, retry logic, and DLQ support.
    """
    init_db()


@cli.command()
@click.argument('job_json')
def enqueue(job_json):
    """
    Enqueue a new job
    
    JOB_JSON must be a JSON string containing at least 'id' and 'command' fields.
    
    Optional fields: 'max_retries' (default: 3), 'run_at' (ISO timestamp)
    
    Examples:
    
        queuectl enqueue '{"id":"job1","command":"echo Hello"}'
    
        queuectl enqueue '{"id":"job2","command":"sleep 5","max_retries":2}'
    """
    try:
        job_data = json.loads(job_json)
        job = enqueue_job(job_data)
        click.echo(f"Enqueued job: {job.id}")
        click.echo(f"  Command: {job.command}")
        click.echo(f"  Max retries: {job.max_retries}")
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


@cli.group()
def worker():
    """Worker management commands"""
    pass


@worker.command('start')
@click.option('--count', default=1, help='Number of worker processes to start')
@click.option('--backoff-base', default=None, type=float, help='Exponential backoff base (default: from config)')
@click.option('--daemon', is_flag=True, help='Run workers as daemon processes')
def worker_start(count, backoff_base, daemon):
    """
    Start worker processes
    
    Workers will process jobs from the queue in the background.
    Use Ctrl+C to stop workers gracefully.
    
    Examples:
    
        queuectl worker start --count 3
    
        queuectl worker start --count 1 --backoff-base 3
    """
    if daemon:
        click.echo(f"Starting {count} worker(s) in daemon mode...")
        processes = []
        pids = []
        
        for i in range(count):
            p = Process(target=start_worker, args=(backoff_base,))
            p.start()
            processes.append(p)
            pids.append(str(p.pid))
            click.echo(f"  Worker {i+1} started (PID: {p.pid})")
        
        set_config('worker_pids', ','.join(pids))
        
        click.echo(f"\n{count} worker(s) started in background")
        click.echo("Use 'queuectl worker stop' to stop them")
    
    else:
        click.echo(f"Starting {count} worker(s) in foreground mode...")
        click.echo("Press Ctrl+C to stop workers gracefully\n")
        
        processes = []
        pids = []
        
        for i in range(count):
            p = Process(target=start_worker, args=(backoff_base,))
            p.start()
            processes.append(p)
            pids.append(str(p.pid))
            click.echo(f"  Worker {i+1} started (PID: {p.pid})")
        
        set_config('worker_pids', ','.join(pids))
        
        try:
            for p in processes:
                p.join()
        except KeyboardInterrupt:
            click.echo("\n\nStopping workers...")
            for p in processes:
                if p.is_alive():
                    p.terminate()
            
            for p in processes:
                p.join(timeout=5)
            
            click.echo("Workers stopped")
        finally:
            set_config('worker_pids', '')


@worker.command('stop')
def worker_stop():
    """
    Stop all running workers
    
    Sends SIGTERM to worker processes for graceful shutdown.
    """
    worker_pids_str = get_config('worker_pids', '')
    
    if not worker_pids_str:
        click.echo("No workers running (no PIDs found in config)")
        return
    
    pids = [pid.strip() for pid in worker_pids_str.split(',') if pid.strip()]
    
    if not pids:
        click.echo("No workers running")
        return
    
    click.echo(f"Stopping {len(pids)} worker(s)...")
    
    for pid_str in pids:
        try:
            pid = int(pid_str)
            os.kill(pid, signal.SIGTERM)
            click.echo(f"  Sent SIGTERM to PID {pid}")
        except (ValueError, ProcessLookupError, OSError) as e:
            click.echo(f"  Could not stop PID {pid_str}: {e}")
    
    set_config('worker_pids', '')
    
    click.echo("Workers stop signal sent")


@cli.command()
def status():
    """
    Show queue status
    
    Displays job counts by state and active worker PIDs.
    """
    status_data = get_status()
    
    click.echo("Queue Status")
    click.echo("=" * 40)
    click.echo(f"Total jobs: {status_data['total_jobs']}")
    click.echo("\nJobs by state:")
    
    for state in ['pending', 'processing', 'completed', 'failed', 'dead']:
        count = status_data['state_counts'].get(state, 0)
        click.echo(f"  {state:12s}: {count}")
    
    click.echo(f"\nActive workers: {len(status_data['worker_pids'])}")
    if status_data['worker_pids']:
        click.echo(f"  PIDs: {', '.join(status_data['worker_pids'])}")
    
    click.echo(f"\nDatabase: {get_db_path()}")


@cli.command('list')
@click.option('--state', type=click.Choice(['pending', 'processing', 'completed', 'failed', 'dead']), 
              help='Filter by job state')
def list_cmd(state):
    """
    List jobs
    
    Optionally filter by state: pending, processing, completed, failed, dead
    
    Examples:
    
        queuectl list
    
        queuectl list --state pending
    """
    jobs = list_jobs(state)
    
    if not jobs:
        click.echo("No jobs found")
        return
    
    click.echo(f"{'ID':<20} {'State':<12} {'Attempts':<10} {'Max Retries':<12} {'Command':<40}")
    click.echo("=" * 100)
    
    for job in jobs:
        cmd_preview = job.command[:37] + '...' if len(job.command) > 40 else job.command
        attempts_str = f"{job.attempts}/{job.max_retries}"
        click.echo(f"{job.id:<20} {job.state:<12} {attempts_str:<10} {job.max_retries:<12} {cmd_preview:<40}")
    
    click.echo(f"\nTotal: {len(jobs)} job(s)")


@cli.group()
def dlq():
    """Dead Letter Queue (DLQ) management"""
    pass


@dlq.command('list')
def dlq_list():
    """
    List jobs in the Dead Letter Queue
    
    Shows jobs that have exceeded max retries.
    """
    jobs = list_dlq()
    
    if not jobs:
        click.echo("No jobs in DLQ")
        return
    
    click.echo(f"{'ID':<20} {'Attempts':<10} {'Last Error':<50} {'Command':<30}")
    click.echo("=" * 115)
    
    for job in jobs:
        cmd_preview = job.command[:27] + '...' if len(job.command) > 30 else job.command
        error_preview = (job.last_error or '')[:47] + '...' if job.last_error and len(job.last_error) > 50 else (job.last_error or '')
        click.echo(f"{job.id:<20} {job.attempts:<10} {error_preview:<50} {cmd_preview:<30}")
    
    click.echo(f"\nTotal: {len(jobs)} job(s) in DLQ")


@dlq.command('retry')
@click.argument('job_id')
def dlq_retry(job_id):
    """
    Retry a job from the DLQ
    
    Moves the job back to pending state and resets attempts to 0.
    
    JOB_ID is the ID of the job to retry.
    
    Example:
    
        queuectl dlq retry job1
    """
    try:
        job = retry_dlq_job(job_id)
        click.echo(f"Job {job.id} moved back to pending state")
        click.echo(f"  Attempts reset to 0")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


@cli.group()
def config():
    """Configuration management"""
    pass


@config.command('get')
@click.argument('key')
def config_get(key):
    """
    Get configuration value
    
    KEY is the configuration key to retrieve.
    
    Example:
    
        queuectl config get backoff_base
    """
    value = get_config(key)
    
    if value is None:
        click.echo(f"Configuration key '{key}' not found", err=True)
        sys.exit(1)
    
    click.echo(f"{key} = {value}")


@config.command('set')
@click.argument('key')
@click.argument('value')
def config_set(key, value):
    """
    Set configuration value
    
    KEY is the configuration key, VALUE is the value to set.
    
    Common keys: backoff_base, max_retries
    
    Example:
    
        queuectl config set backoff_base 3
    """
    set_config(key, value)
    click.echo(f"Set {key} = {value}")


if __name__ == '__main__':
    cli()
