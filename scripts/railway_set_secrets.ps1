Param()

$ErrorActionPreference = 'Stop'

function Assert-CommandExists {
	param(
		[string]$Command
	)
	if (-not (Get-Command $Command -ErrorAction SilentlyContinue)) {
		Write-Error "Required command '$Command' not found. Install Railway CLI: https://docs.railway.app/develop/cli";
		exit 1
	}
}

function Set-VariableIfPresent {
	param(
		[string]$Key
	)
	$val = [Environment]::GetEnvironmentVariable($Key)
	if ($null -ne $val -and $val.Trim().Length -gt 0) {
		Write-Host "Setting $Key" -ForegroundColor Cyan
		railway variables set "$Key=$val" | Out-Host
	} else {
		Write-Host "Skipping $Key (not set in environment)" -ForegroundColor DarkYellow
	}
}

Write-Host "Railway secrets setup (staging)" -ForegroundColor Green
Assert-CommandExists -Command "railway"

if ($env:RAILWAY_TOKEN) {
	Write-Host "Using RAILWAY_TOKEN from environment" -ForegroundColor DarkGray
}

# Core backend secrets (must be provided from your password manager or CI secrets)
Set-VariableIfPresent -Key "DATABASE_URL"
Set-VariableIfPresent -Key "NEO4J_URI"
Set-VariableIfPresent -Key "NEO4J_USER"
Set-VariableIfPresent -Key "NEO4J_PASSWORD"
Set-VariableIfPresent -Key "LLM_API_KEY"
Set-VariableIfPresent -Key "EMBEDDING_API_KEY"

# App config
Set-VariableIfPresent -Key "API_BASE_URL"          # e.g. https://staging.api.fisiorag.app
Set-VariableIfPresent -Key "CORS_ALLOWED_ORIGINS"  # e.g. https://staging.fisiorag.app,https://fisiorag.vercel.app

Write-Host "Done. Verify variables in Railway dashboard or via 'railway variables list'." -ForegroundColor Green

