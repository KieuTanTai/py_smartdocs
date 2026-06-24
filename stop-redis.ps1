# Stop Redis Docker container
# Usage: .\stop-redis.ps1

Write-Host "🛑 Stopping Redis..." -ForegroundColor Yellow

docker-compose down

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Redis stopped successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to stop Redis." -ForegroundColor Red
    exit 1
}

Write-Host "`n💡 To start Redis again, run: .\start-redis.ps1" -ForegroundColor Cyan
