Write-Host "Installing Python dependencies..."
pip install -r backend/requirements.txt

Write-Host "Installing Node dependencies..."
Set-Location frontend
npm install
npm install axios framer-motion lucide-react
