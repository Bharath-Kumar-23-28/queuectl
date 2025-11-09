function Enqueue-Job {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Id,
        
        [Parameter(Mandatory=$true)]
        [string]$Command,
        
        [Parameter(Mandatory=$false)]
        [int]$MaxRetries = 3
    )
    
    python enqueue.py $Id $Command $MaxRetries
}

function Start-Workers {
    param(
        [Parameter(Mandatory=$false)]
        [int]$Count = 1,
        
        [Parameter(Mandatory=$false)]
        [double]$BackoffBase = 2,
        
        [Parameter(Mandatory=$false)]
        [switch]$Daemon
    )
    
    $cmd = "queuectl worker start --count $Count --backoff-base $BackoffBase"
    if ($Daemon) {
        $cmd += " --daemon"
    }
    
    Invoke-Expression $cmd
}

function Stop-Workers {
    queuectl worker stop
}

function Get-QueueStatus {
    queuectl status
}

function Get-Jobs {
    param(
        [Parameter(Mandatory=$false)]
        [ValidateSet('pending', 'processing', 'completed', 'failed', 'dead')]
        [string]$State
    )
    
    if ($State) {
        queuectl list --state $State
    } else {
        queuectl list
    }
}

function Get-DeadLetterQueue {
    queuectl dlq list
}

function Retry-DeadJob {
    param(
        [Parameter(Mandatory=$true)]
        [string]$JobId
    )
    
    queuectl dlq retry $JobId
}

function Get-Config {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Key
    )
    
    queuectl config get $Key
}

function Set-Config {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Key,
        
        [Parameter(Mandatory=$true)]
        [string]$Value
    )
    
    queuectl config set $Key $Value
}

Export-ModuleMember -Function @(
    'Enqueue-Job',
    'Start-Workers',
    'Stop-Workers',
    'Get-QueueStatus',
    'Get-Jobs',
    'Get-DeadLetterQueue',
    'Retry-DeadJob',
    'Get-Config',
    'Set-Config'
)

Write-Host "queuectl PowerShell helpers loaded!" -ForegroundColor Green
Write-Host ""
Write-Host "Available commands:" -ForegroundColor Cyan
Write-Host "  Enqueue-Job -Id 'job1' -Command 'echo Hello'"
Write-Host "  Start-Workers -Count 2"
Write-Host "  Stop-Workers"
Write-Host "  Get-QueueStatus"
Write-Host "  Get-Jobs -State pending"
Write-Host "  Get-DeadLetterQueue"
Write-Host "  Retry-DeadJob -JobId 'job1'"
Write-Host "  Get-Config -Key backoff_base"
Write-Host "  Set-Config -Key backoff_base -Value 3"
Write-Host ""
