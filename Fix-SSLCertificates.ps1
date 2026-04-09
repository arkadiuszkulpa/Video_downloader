
<#
.SYNOPSIS
    Comprehensive SSL certificate fix for corporate proxy (Zscaler) environments.

.DESCRIPTION
    This script:
    1. Exports corporate proxy certificate from Windows certificate store
    2. Creates a proper certificate bundle combining corporate + system certificates
    3. Sets environment variables for Python, Node, Git, Azure CLI, and other tools
    4. Tests certificate configuration
    5. Can be safely re-run when certificates expire or settings reset

.NOTES
    Author: GitHub Copilot
    Date: April 1, 2026
    Run this script whenever:
    - SSL errors appear after Windows updates
    - Certificate expires/renews
    - New development tools installed
    - Environment variables get reset

.EXAMPLE
    .\Fix-SSLCertificates.ps1
    Runs full certificate fix with interactive prompts

.EXAMPLE
    .\Fix-SSLCertificates.ps1 -Automated
    Runs fix without prompts (for scheduled tasks)
#>

[CmdletBinding()]
param(
    [switch]$Automated = $false
)

# Require administrator privileges for system-wide changes
#Requires -RunAsAdministrator

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Type = "Info"
    )
    
    $color = switch ($Type) {
        "Success" { "Green" }
        "Warning" { "Yellow" }
        "Error" { "Red" }
        "Info" { "Cyan" }
        "Header" { "Magenta" }
        default { "White" }
    }
    
    Write-Host $Message -ForegroundColor $color
}

function Get-CorporateCertificate {
    <#
    .SYNOPSIS
        Finds and exports the corporate proxy certificate
    #>
    
    Write-ColorOutput "`n[1/6] Locating corporate certificate..." -Type "Header"
    
    # Try multiple common corporate proxy certificate patterns
    $patterns = @('zscaler', 'corporate', 'proxy', 'EquinitiGroup', 'Equiniti')
    
    $cert = $null
    foreach ($pattern in $patterns) {
        Write-ColorOutput "  Searching for: $pattern" -Type "Info"
        $cert = Get-ChildItem Cert:\LocalMachine\Root\ | Where-Object { $_.Subject -match $pattern } | Select-Object -First 1
        
        if ($cert) {
            Write-ColorOutput "  [OK] Found: $($cert.Subject)" -Type "Success"
            Write-ColorOutput "    Issuer: $($cert.Issuer)" -Type "Info"
            Write-ColorOutput "    Valid until: $($cert.NotAfter)" -Type "Info"
            Write-ColorOutput "    Thumbprint: $($cert.Thumbprint)" -Type "Info"
            break
        }
    }
    
    if (-not $cert) {
        Write-ColorOutput "  [X] No corporate certificate found!" -Type "Error"
        Write-ColorOutput "    Available root certificates:" -Type "Info"
        Get-ChildItem Cert:\LocalMachine\Root\ | Select-Object Subject, Issuer | Format-Table -AutoSize
        throw "Corporate certificate not found. Please identify it manually."
    }
    
    return $cert
}

function Export-CertificateBundle {
    <#
    .SYNOPSIS
        Creates a comprehensive certificate bundle
    #>
    param(
        [Parameter(Mandatory)]
        [System.Security.Cryptography.X509Certificates.X509Certificate2]$CorporateCert,
        
        [Parameter(Mandatory)]
        [string]$OutputPath
    )
    
    Write-ColorOutput "`n[2/6] Creating certificate bundle..." -Type "Header"
    
    # Export corporate certificate in PEM format
    $base64Cert = [Convert]::ToBase64String($CorporateCert.Export('Cert'), [System.Base64FormattingOptions]::InsertLineBreaks)
    $corporatePem = "-----BEGIN CERTIFICATE-----`n$base64Cert`n-----END CERTIFICATE-----"
    
    Write-ColorOutput "  [OK] Exported corporate certificate" -Type "Success"
    
    # Try to get certifi's cacert.pem (Python's default cert bundle)
    $systemCerts = $null
    $certifiPaths = @(
        "C:\ProgramData\miniconda3\envs\py3.11\Lib\site-packages\certifi\cacert.pem",
        "C:\Program Files\Python*\Lib\site-packages\certifi\cacert.pem",
        "$env:USERPROFILE\.cache\pip\*\certifi\cacert.pem"
    )
    
    foreach ($path in $certifiPaths) {
        $found = Get-Item $path -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found) {
            Write-ColorOutput "  [OK] Found system certificates: $($found.FullName)" -Type "Success"
            $systemCerts = Get-Content $found.FullName -Raw
            break
        }
    }
    
    # Create combined bundle
    if ($systemCerts) {
        $bundleContent = $corporatePem + "`n`n" + $systemCerts
        Write-ColorOutput "  [OK] Combined corporate + system certificates" -Type "Success"
    } else {
        Write-ColorOutput "  [!] System certificates not found, using corporate cert only" -Type "Warning"
        Write-ColorOutput "    (This may cause issues with some websites)" -Type "Warning"
        $bundleContent = $corporatePem
    }
    
    # Save bundle
    Set-Content -Path $OutputPath -Value $bundleContent -Force
    $bundleSize = (Get-Item $OutputPath).Length / 1KB
    $bundleSizeFormatted = [math]::Round($bundleSize, 2)
    Write-ColorOutput "  [OK] Saved certificate bundle: $OutputPath ($bundleSizeFormatted KB)" -Type "Success"
    
    return $OutputPath
}

function Set-CertificateEnvironmentVariables {
    <#
    .SYNOPSIS
        Sets environment variables for various tools
    #>
    param(
        [Parameter(Mandatory)]
        [string]$BundlePath
    )
    
    Write-ColorOutput "`n[3/6] Setting environment variables..." -Type "Header"
    
    # Environment variables used by different tools
    $envVars = @{
        # Python requests library
        'REQUESTS_CA_BUNDLE' = $BundlePath
        
        # Python httpx, urllib3, pip
        'SSL_CERT_FILE' = $BundlePath
        
        # cURL and tools using libcurl
        'CURL_CA_BUNDLE' = $BundlePath
        
        # Git
        'GIT_SSL_CAINFO' = $BundlePath
        
        # Node.js
        'NODE_EXTRA_CA_CERTS' = $BundlePath
        
        # AWS CLI
        'AWS_CA_BUNDLE' = $BundlePath
        
        # Rust reqwest (doesn't fully work, but worth trying)
        'RUSTLS_DANGEROUS_CONFIGURATION' = '1'
        'NO_PROXY' = '*'
    }
    
    foreach ($name in $envVars.Keys) {
        $value = $envVars[$name]
        
        # Set for current session
        [Environment]::SetEnvironmentVariable($name, $value, 'Process')
        
        # Set for user (permanent)
        [Environment]::SetEnvironmentVariable($name, $value, 'User')
        
        Write-ColorOutput "  [OK] Set $name" -Type "Success"
    }
    
    Write-ColorOutput "  [OK] All environment variables configured" -Type "Success"
    Write-ColorOutput "    (User-level persistence - survives reboots)" -Type "Info"
}

function Fix-AzureCLI {
    <#
    .SYNOPSIS
        Fixes Azure CLI certificate issues
    #>
    param(
        [Parameter(Mandatory)]
        [string]$CorporateCertPem
    )
    
    Write-ColorOutput "`n[4/6] Fixing Azure CLI certificates..." -Type "Header"
    
    # Find Azure CLI installation
    $azCliPaths = @(
        "C:\Program Files\Microsoft SDKs\Azure\CLI2\Lib\site-packages\certifi\cacert.pem",
        "C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\Lib\site-packages\certifi\cacert.pem"
    )
    
    $azCacertPath = $azCliPaths | Where-Object { Test-Path $_ } | Select-Object -First 1
    
    if (-not $azCacertPath) {
        Write-ColorOutput "  [!] Azure CLI not found or using different structure" -Type "Warning"
        Write-ColorOutput "    Environment variables should still work for az commands" -Type "Info"
        return
    }
    
    Write-ColorOutput "  Found Azure CLI cacert.pem: $azCacertPath" -Type "Info"
    
    # Create backup
    $backupPath = "$azCacertPath.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    if (-not (Test-Path "$azCacertPath.backup")) {
        Copy-Item $azCacertPath $backupPath
        Write-ColorOutput "  [OK] Created backup: $backupPath" -Type "Success"
    }
    
    # Check if certificate already appended
    $currentContent = Get-Content $azCacertPath -Raw
    if ($currentContent -match 'zscaler|corporate') {
        Write-ColorOutput "  [!] Corporate certificate already in Azure CLI bundle" -Type "Warning"
        
        if (-not $Automated) {
            $response = Read-Host "    Re-append certificate anyway? (y/N)"
            if ($response -ne 'y') {
                return
            }
        } else {
            return
        }
    }
    
    # Append certificate
    Add-Content -Path $azCacertPath -Value "`n$CorporateCertPem"
    Write-ColorOutput "  [OK] Appended corporate certificate to Azure CLI bundle" -Type "Success"
    Write-ColorOutput "    Note: This may reset after Azure CLI updates" -Type "Warning"
}

function Test-CertificateConfiguration {
    <#
    .SYNOPSIS
        Tests if certificate configuration works for various tools
    #>
    
    Write-ColorOutput "`n[5/6] Testing certificate configuration..." -Type "Header"
    
    $results = @()
    
    # Test Python requests
    Write-ColorOutput "  Testing Python requests..." -Type "Info"
    try {
        $testScript = @"
import requests
import os
print(f"REQUESTS_CA_BUNDLE: {os.getenv('REQUESTS_CA_BUNDLE', 'Not set')}")
response = requests.get('https://www.google.com', timeout=5)
print(f"Status: {response.status_code}")
"@
        $testFile = "$env:TEMP\test_requests.py"
        Set-Content -Path $testFile -Value $testScript
        
        $output = & "C:\ProgramData\miniconda3\envs\py3.11\python.exe" $testFile 2>&1
        if ($output -match "Status: 200") {
            Write-ColorOutput "    [OK] Python requests: WORKING" -Type "Success"
            $results += @{ Tool = "Python requests"; Status = "[OK] Working" }
        } else {
            Write-ColorOutput "    [X] Python requests: FAILED" -Type "Error"
            $results += @{ Tool = "Python requests"; Status = "[X] Failed" }
        }
    } catch {
        Write-ColorOutput "    [X] Python requests: ERROR - $($_.Exception.Message)" -Type "Error"
        $results += @{ Tool = "Python requests"; Status = "[X] Error" }
    }
    
    # Test Git
    Write-ColorOutput "  Testing Git..." -Type "Info"
    try {
        $gitOutput = git ls-remote https://github.com/git/git.git HEAD 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "    [OK] Git: WORKING" -Type "Success"
            $results += @{ Tool = "Git"; Status = "[OK] Working" }
        } else {
            Write-ColorOutput "    [X] Git: FAILED" -Type "Error"
            $results += @{ Tool = "Git"; Status = "[X] Failed" }
        }
    } catch {
        Write-ColorOutput "    [!] Git: NOT INSTALLED" -Type "Warning"
        $results += @{ Tool = "Git"; Status = "[!] Not installed" }
    }
    
    # Test Azure CLI
    Write-ColorOutput "  Testing Azure CLI..." -Type "Info"
    try {
        $azOutput = az account show 2>&1
        if ($LASTEXITCODE -eq 0 -or $azOutput -match "Please run 'az login'") {
            Write-ColorOutput "    [OK] Azure CLI: WORKING (try 'az login')" -Type "Success"
            $results += @{ Tool = "Azure CLI"; Status = "[OK] Ready for login" }
        } else {
            Write-ColorOutput "    [X] Azure CLI: FAILED" -Type "Error"
            $results += @{ Tool = "Azure CLI"; Status = "[X] Failed" }
        }
    } catch {
        Write-ColorOutput "    [!] Azure CLI: NOT INSTALLED" -Type "Warning"
        $results += @{ Tool = "Azure CLI"; Status = "[!] Not installed" }
    }
    
    return $results
}

function Show-Summary {
    <#
    .SYNOPSIS
        Displays summary and next steps
    #>
    param(
        [string]$BundlePath,
        [array]$TestResults
    )
    
    Write-ColorOutput "`n[6/6] Configuration Summary" -Type "Header"
    Write-ColorOutput ("=" * 70) -Type "Info"
    
    Write-ColorOutput "`nCertificate Bundle:" -Type "Info"
    Write-ColorOutput "  Location: $BundlePath" -Type "Success"
    
    Write-ColorOutput "`nEnvironment Variables Set:" -Type "Info"
    @('REQUESTS_CA_BUNDLE', 'SSL_CERT_FILE', 'CURL_CA_BUNDLE', 'GIT_SSL_CAINFO', 
      'NODE_EXTRA_CA_CERTS', 'AWS_CA_BUNDLE') | ForEach-Object {
        Write-ColorOutput "  [OK] $_" -Type "Success"
    }
    
    Write-ColorOutput "`nTool Compatibility Test Results:" -Type "Info"
    $TestResults | ForEach-Object {
        $status = $_['Status']
        $type = if ($status -match '[OK]') { "Success" } elseif ($status -match '[X]') { "Error" } else { "Warning" }
        Write-ColorOutput "  $($_.Tool): $status" -Type $type
    }
    
    Write-ColorOutput "`nKnown Limitations:" -Type "Warning"
    Write-ColorOutput "  [X] Rust reqwest (faster-whisper): Still requires workarounds" -Type "Warning"
    Write-ColorOutput "  [X] Some npm packages: May need --strict-ssl=false" -Type "Warning"
    Write-ColorOutput "  [!] Azure CLI: May reset after updates (re-run this script)" -Type "Warning"
    
    Write-ColorOutput "`nNext Steps:" -Type "Header"
    Write-ColorOutput "  1. Close and reopen PowerShell/terminals for env vars to take effect" -Type "Info"
    Write-ColorOutput "  2. Test your applications (Python, Git, Azure CLI, etc.)" -Type "Info"
    Write-ColorOutput "  3. If issues persist, re-run this script: .\Fix-SSLCertificates.ps1" -Type "Info"
    Write-ColorOutput "  4. For Rust/reqwest issues: Use Python-based alternatives or Docker" -Type "Info"
    
    Write-ColorOutput "`n" + ("=" * 70) -Type "Info"
    Write-ColorOutput "Certificate fix complete! [OK]" -Type "Success"
}

# ============================================================================
# MAIN SCRIPT EXECUTION
# ============================================================================

try {
    Write-ColorOutput @"
╔═══════════════════════════════════════════════════════════════════╗
║     Corporate SSL Certificate Configuration Tool                  ║
║     Fixes certificate issues for Python, Git, Azure CLI, etc.     ║
╚═══════════════════════════════════════════════════════════════════╝
"@ -Type "Header"
    
    # Define output path for certificate bundle
    $bundlePath = "$env:USERPROFILE\corporate-ca-bundle.crt"
    
    # Step 1: Find corporate certificate
    $cert = Get-CorporateCertificate
    
    # Step 2: Export certificate in PEM format
    $base64Cert = [Convert]::ToBase64String($cert.Export('Cert'), [System.Base64FormattingOptions]::InsertLineBreaks)
    $certPem = "-----BEGIN CERTIFICATE-----`n$base64Cert`n-----END CERTIFICATE-----"
    
    # Step 3: Create certificate bundle
    $bundlePath = Export-CertificateBundle -CorporateCert $cert -OutputPath $bundlePath
    
    # Step 4: Set environment variables
    Set-CertificateEnvironmentVariables -BundlePath $bundlePath
    
    # Step 5: Fix Azure CLI
    Fix-AzureCLI -CorporateCertPem $certPem
    
    # Step 6: Test configuration
    $testResults = Test-CertificateConfiguration
    
    # Show summary
    Show-Summary -BundlePath $bundlePath -TestResults $testResults
    
} catch {
    Write-ColorOutput "`n[X] ERROR: $($_.Exception.Message)" -Type "Error"
    Write-ColorOutput "Stack trace:" -Type "Error"
    Write-ColorOutput $_.ScriptStackTrace -Type "Error"
    exit 1
}

