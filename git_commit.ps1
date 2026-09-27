$git = Join-Path $env:LOCALAPPDATA "MinGit\cmd\git.exe"
Write-Host "Using Git at: $git"

& $git init
& $git config user.name "mirthikam2008-stack"
& $git config user.email "mirthikam2008-stack@users.noreply.github.com"
& $git add .
& $git commit -m "feat: complete PocketSmart AI architecture with 8 real-world optimizers, frontend, backend, tests, and docs"
& $git branch -M main
& $git remote remove origin 2>$null
& $git remote add origin https://github.com/mirthikam2008-stack/pocketsmart-ai.git
& $git remote -v
& $git status
