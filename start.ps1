$backendProcess = Start-Process -FilePath "python" -ArgumentList "-m uvicorn backend.main:app --reload --port 8000" -PassThru -NoNewWindow
Write-Host "Backend started with PID $($backendProcess.Id)"

Set-Location frontend
Write-Host "Starting Frontend..."
npm run dev
