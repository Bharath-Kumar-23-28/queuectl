"""
Job dataclass and helper conversions
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Job:
    """Represents a job in the queue"""
    id: str
    command: str
    state: str  
    attempts: int = 0
    max_retries: int = 3
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    locked_by: Optional[str] = None
    locked_at: Optional[str] = None
    last_error: Optional[str] = None
    run_after: int = 0  # Unix timestamp for delayed/scheduled jobs

    def to_dict(self) -> dict:
        """Convert job to dictionary"""
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> 'Job':
        """Create Job from dictionary"""
        return Job(**data)

    @staticmethod
    def from_db_row(row: tuple) -> 'Job':
        """
        Create Job from SQLite row tuple
        Expected order: id, command, state, attempts, max_retries, 
                       created_at, updated_at, locked_by, locked_at, 
                       last_error, run_after
        """
        return Job(
            id=row[0],
            command=row[1],
            state=row[2],
            attempts=row[3],
            max_retries=row[4],
            created_at=row[5],
            updated_at=row[6],
            locked_by=row[7],
            locked_at=row[8],
            last_error=row[9],
            run_after=row[10]
        )


def get_utc_now() -> str:
    """Get current UTC timestamp in ISO format"""
    return datetime.utcnow().isoformat() + 'Z'


def get_unix_timestamp() -> int:
    """Get current Unix timestamp"""
    return int(datetime.utcnow().timestamp())
