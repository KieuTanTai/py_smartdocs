# Start Redis with Docker Compose
# Usage: .\start-redis.ps1

Write-Host "🐳 Starting Redis with Docker..." -ForegroundColor Cyan

# Check if Docker is running
try {
    docker ps | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Docker is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Download Docker Desktop from: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Docker is running" -ForegroundColor Green

# Start Redis with docker-compose
Write-Host "`n🚀 Starting Redis container..." -ForegroundColor Cyan
docker-compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Redis started successfully!" -ForegroundColor Green
    
    # Wait for Redis to be ready
    Write-Host "`n⏳ Waiting for Redis to be ready..." -ForegroundColor Cyan
    Start-Sleep -Seconds 3
    
    # Test connection
    Write-Host "`n🔍 Testing Redis connection..." -ForegroundColor Cyan
    $result = docker exec smartdocs_redis redis-cli ping
    
    if ($result -eq "PONG") {
        Write-Host "✅ Redis is ready and responding!" -ForegroundColor Green
        
        # Show container info
        Write-Host "`n📊 Redis Container Info:" -ForegroundColor Cyan
        docker-compose ps
        
        Write-Host "`n✨ Redis is now running on localhost:6379" -ForegroundColor Green
        Write-Host "📝 You can now start your Django server with: python manage.py runserver" -ForegroundColor Yellow
        
    } else {
        Write-Host "⚠️  Redis started but not responding yet. Please wait a moment." -ForegroundColor Yellow
    }
    
} else {
    Write-Host "❌ Failed to start Redis. Check the error above." -ForegroundColor Red
    Write-Host "`n💡 Common fixes:" -ForegroundColor Yellow
    Write-Host "   1. Make sure Docker Desktop is running" -ForegroundColor White
    Write-Host "   2. Check if port 6379 is already in use: netstat -ano | findstr :6379" -ForegroundColor White
    Write-Host "   3. Try: docker-compose down && docker-compose up -d" -ForegroundColor White
    exit 1
}

Write-Host "`n📚 Useful commands:" -ForegroundColor Cyan
Write-Host "   Stop Redis:    docker-compose down" -ForegroundColor White
Write-Host "   View logs:     docker-compose logs -f redis" -ForegroundColor White
Write-Host "   Restart:       docker-compose restart" -ForegroundColor White
Write-Host "   Redis CLI:     docker exec -it smartdocs_redis redis-cli" -ForegroundColor White
