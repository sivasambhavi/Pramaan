$ports = @(8000, 8501)
foreach ($port in $ports) {
    Write-Host "Checking port $port..."
    $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conns) {
        foreach ($c in $conns) {
            Write-Host "Killing Process ID $($c.OwningProcess) on port $port"
            Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    } else {
        Write-Host "Port $port is free."
    }
}
