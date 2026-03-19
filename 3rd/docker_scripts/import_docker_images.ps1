# NecoRAG Docker Images Import Script for Windows PowerShell
# Usage: .\import_docker_images.ps1

#Requires -Version 5.1

# Command line parameters (must be at the top)
param(
    [switch]$h,
    [switch]$Help,
    [switch]$l,
    [switch]$List,
    [switch]$o,
    [switch]$Optional,
    [switch]$v,
    [switch]$Verbose
)

# Registry configuration
$script:docker_hub_registry = "docker.io"
$script:aliyun_registry = "registry.cn-hangzhou.aliyuncs.com"
$script:SELECTED_REGISTRY = $null
$script:USE_ALIYUN = $true

# China mirror registries (2024 verified working mirrors)
$script:CHINA_MIRRORS = @(
    "https://docker.1panel.live",
    "https://hub.rat.dev",
    "https://docker.chenby.cn",
    "https://docker.m.daocloud.io",
    "https://dockerhub.icu",
    "https://docker.hlyun.org",
    "https://docker.udayun.com",
    "https://docker.awsl9527.cn",
    "https://dockerpull.org",
    "https://docker.rainbond.cc"
)

# Image sizes (MB)
$script:IMAGE_SIZES = @{
    # Required images
    "redis:7-alpine"         = 25
    "qdrant/qdrant:latest"   = 500
    "neo4j:5-community"      = 1200
    "ollama/ollama:latest"   = 2000
    "grafana/grafana:latest" = 300
    # Optional images (original)
    "milvusdb/milvus:v2.3.0" = 707
    "memgraph/memgraph:latest" = 203
    "prom/prometheus:latest" = 146
    "apache/superset:latest" = 643
    # Additional images from README.md
    "langchain/langgraph:latest" = 500
    "infiniflow/ragflow:latest"   = 2500
    "vllm/vllm-openai:latest"     = 8000
    "streamlit/streamlit:latest"  = 200
    "elasticsearch:8.12.0"        = 1200
    "kibana:8.12.0"               = 800
    "mysql:8.0"                   = 500
    "minio/minio:latest"          = 100
    "apache/tika:latest"          = 400
    "quay.io/coreos/prometheus-operator:latest" = 100
}

# Required images list
$script:IMAGES = @(
    # === Core Storage (L1/L2/L3) ===
    "redis:7-alpine"                    # L1 Working Memory & Cache
    "qdrant/qdrant:latest"              # L2 Vector Database
    "neo4j:5-community"                 # L3 Graph Database
    
    # === AI/ML Model Services ===
    "ollama/ollama:latest"              # Local LLM Inference Server
    
    # === Monitoring ===
    "grafana/grafana:latest"            # Monitoring Dashboard
)

# Optional images list
$script:OPTIONAL_IMAGES = @(
    # === High-Performance LLM ===
    "vllm/vllm-openai:latest"           # vLLM High-Performance LLM Server
    
    # === Document Processing ===
    "infiniflow/ragflow:latest"         # RAGFlow Deep Document Parsing
    
    # === Orchestration Engine ===
    "langchain/langgraph:latest"        # LangGraph State Machine
    
    # === Frontend ===
    "streamlit/streamlit:latest"        # Streamlit Frontend
    
    # === Metadata & File Storage ===
    "mysql:8.0"                         # Metadata Storage
    "minio/minio:latest"                # File Object Storage
    
    # === Full-Text Search ===
    "elasticsearch:8.12.0"              # Elasticsearch Full-Text Search
    "kibana:8.12.0"                     # Kibana Visualization
    
    # === Alternative Storage ===
    "milvusdb/milvus:v2.3.0"            # Milvus Vector DB (Alternative)
    "memgraph/memgraph:latest"          # Memgraph Graph DB (Alternative)
    
    # === Monitoring ===
    "prom/prometheus:latest"            # Prometheus Metrics Collection
    "apache/superset:latest"            # Superset Visualization
    
    # === Document Processing ===
    "apache/tika:latest"                # Apache Tika Document Parsing
)

# Selected images
$script:SELECTED_IMAGES = @()
$script:DOWNLOAD_OPTIONAL = $false

# Log functions
function Write-LogInfo {
    param([string]$Message)
    Write-Host "[INFO] " -ForegroundColor Blue -NoNewline
    Write-Host $Message
}

function Write-LogSuccess {
    param([string]$Message)
    Write-Host "[SUCCESS] " -ForegroundColor Green -NoNewline
    Write-Host $Message
}

function Write-LogWarning {
    param([string]$Message)
    Write-Host "[WARNING] " -ForegroundColor Yellow -NoNewline
    Write-Host $Message
}

function Write-LogError {
    param([string]$Message)
    Write-Host "[ERROR] " -ForegroundColor Red -NoNewline
    Write-Host $Message
}

# Show title
function Show-Title {
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  NecoRAG Docker Images Import Tool" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
}

# Check Docker installation
function Test-Docker {
    try {
        $null = Get-Command docker -ErrorAction Stop
    }
    catch {
        Write-LogError "Docker is not installed! Please install Docker Desktop first."
        Write-Host "Installation guide: https://docs.docker.com/desktop/install/windows-install/"
        exit 1
    }
    
    try {
        $null = docker info 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Docker not running"
        }
    }
    catch {
        Write-LogError "Docker is not running! Please start Docker Desktop."
        exit 1
    }
    
    Write-LogSuccess "Docker check passed"
}

# Select registry - Always use China mirror
function Select-Registry {
    Write-LogInfo "Using China mirror for faster download..."
    $script:SELECTED_REGISTRY = $script:CHINA_MIRRORS[0]
    $script:USE_ALIYUN = $true
    Write-LogSuccess "Selected mirror: $($script:SELECTED_REGISTRY)"
    Write-Host ""
}

# Format size display
function Format-Size {
    param([int]$SizeMB)
    
    if ($SizeMB -ge 1024) {
        return "{0:N2} GB" -f ($SizeMB / 1024)
    }
    else {
        return "{0} MB" -f $SizeMB
    }
}

# Calculate total size
function Get-TotalSize {
    param([string[]]$Images)
    
    $total_mb = 0
    foreach ($image in $Images) {
        if ($script:IMAGE_SIZES.ContainsKey($image)) {
            $total_mb += $script:IMAGE_SIZES[$image]
        }
    }
    
    return $total_mb
}

# Check disk space
function Test-DiskSpace {
    param([int]$RequiredMB)
    
    # Get Docker data directory drive
    $dockerInfo = docker info 2>&1 | Select-String "Docker Root Dir"
    $drive = "C:"
    
    if ($dockerInfo) {
        $dockerRoot = ($dockerInfo -split ": ")[1].Trim()
        if ($dockerRoot -match "^([A-Z]:)") {
            $drive = $matches[1]
        }
    }
    
    $disk = Get-WmiObject Win32_LogicalDisk -Filter "DeviceID='$drive'" -ErrorAction SilentlyContinue
    
    if (-not $disk) {
        Write-LogWarning "Cannot get disk space info, skipping check"
        return $true
    }
    
    $availableMB = [math]::Round($disk.FreeSpace / 1MB)
    $recommendedMB = [math]::Round($RequiredMB * 1.2)
    
    Write-Host ""
    Write-LogInfo "Disk space check"
    Write-Host "   Required: $(Format-Size $RequiredMB)"
    Write-Host "   Recommended: $(Format-Size $recommendedMB) (with 20% buffer)"
    Write-Host "   Available: $(Format-Size $availableMB)"
    
    if ($availableMB -lt $RequiredMB) {
        Write-LogError "Insufficient disk space!"
        Write-Host "   Shortage: $(Format-Size ($RequiredMB - $availableMB))"
        Write-Host ""
        Write-Host "Suggestions:"
        Write-Host "   1. Clean unused Docker images: docker image prune -a"
        Write-Host "   2. Clean stopped containers: docker container prune"
        Write-Host "   3. Clean build cache: docker builder prune"
        return $false
    }
    elseif ($availableMB -lt $recommendedMB) {
        Write-LogWarning "Disk space is tight but sufficient"
        Write-Host "   Remaining: $(Format-Size ($availableMB - $RequiredMB))"
        Write-Host ""
        
        $reply = Read-Host "Continue? (y/n)"
        if ($reply -notmatch "^[Yy]$") {
            return $false
        }
    }
    else {
        Write-LogSuccess "Disk space is sufficient"
        Write-Host "   Remaining: $(Format-Size ($availableMB - $RequiredMB))"
    }
    
    return $true
}

# Show image selection menu
function Show-ImageSelectionMenu {
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  Image Selection" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Show required images
    Write-Host "[Required Images]" -ForegroundColor Yellow
    Write-Host "  No.    Image Name                           Size"
    Write-Host "  ------------------------------------------------------------"
    
    $index = 1
    foreach ($image in $script:IMAGES) {
        $size = if ($script:IMAGE_SIZES.ContainsKey($image)) { $script:IMAGE_SIZES[$image] } else { 0 }
        Write-Host ("  {0,-6} {1,-36} {2}" -f $index, $image, "$(Format-Size $size)")
        $index++
    }
    
    # Show optional images
    Write-Host ""
    Write-Host "[Optional Images]" -ForegroundColor Yellow
    Write-Host "  No.    Image Name                           Size"
    Write-Host "  ------------------------------------------------------------"
    
    $index = 1
    foreach ($image in $script:OPTIONAL_IMAGES) {
        $size = if ($script:IMAGE_SIZES.ContainsKey($image)) { $script:IMAGE_SIZES[$image] } else { 0 }
        Write-Host ("  {0,-6} {1,-36} {2}" -f $index, $image, "$(Format-Size $size)")
        $index++
    }
    
    Write-Host ""
}

# Get user selection
function Get-UserSelection {
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  Download Options" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Select images to download:"
    Write-Host "  1) Required images only (~4.03GB)"
    Write-Host "  2) All images (required + optional, ~20GB) [DEFAULT]"
    Write-Host "  3) Custom selection"
    Write-Host ""
    
    $download_choice = Read-Host "Enter option (1/2/3) [default: 2]"
    
    # Default to option 2 if empty input
    if ([string]::IsNullOrWhiteSpace($download_choice)) {
        $download_choice = "2"
    }
    
    switch ($download_choice) {
        "1" {
            $script:DOWNLOAD_OPTIONAL = $false
            $script:SELECTED_IMAGES = $script:IMAGES
        }
        "2" {
            $script:DOWNLOAD_OPTIONAL = $true
            $script:SELECTED_IMAGES = $script:IMAGES + $script:OPTIONAL_IMAGES
        }
        "3" {
            Write-Host ""
            Write-Host "Select optional images to download (comma-separated):"
            Write-Host ""
            
            $index = 1
            foreach ($image in $script:OPTIONAL_IMAGES) {
                $size = if ($script:IMAGE_SIZES.ContainsKey($image)) { $script:IMAGE_SIZES[$image] } else { 0 }
                Write-Host ("  {0}) {1,-36} {2}" -f $index, $image, "$(Format-Size $size)")
                $index++
            }
            Write-Host "  0) Skip optional images"
            Write-Host ""
            
            $optional_selection = Read-Host "Enter selection (e.g., 1,3 or 0)"
            
            $custom_optional = @()
            $selections = $optional_selection -split "[,\s]+" | Where-Object { $_ -match "^\d+$" }
            
            foreach ($sel in $selections) {
                $selInt = [int]$sel
                if ($selInt -ge 1 -and $selInt -le $script:OPTIONAL_IMAGES.Count) {
                    $custom_optional += $script:OPTIONAL_IMAGES[$selInt - 1]
                }
            }
            
            if ($custom_optional.Count -gt 0) {
                $script:DOWNLOAD_OPTIONAL = $true
                $script:SELECTED_IMAGES = $script:IMAGES + $custom_optional
            }
            else {
                $script:DOWNLOAD_OPTIONAL = $false
                $script:SELECTED_IMAGES = $script:IMAGES
            }
        }
        default {
            Write-LogInfo "Using default option: All images"
            $script:DOWNLOAD_OPTIONAL = $true
            $script:SELECTED_IMAGES = $script:IMAGES + $script:OPTIONAL_IMAGES
        }
    }
    
    # Calculate total size
    $total_size = Get-TotalSize -Images $script:SELECTED_IMAGES
    
    Write-Host ""
    Write-LogInfo "Selected images"
    Write-Host "   Required images: $($script:IMAGES.Count)"
    
    if ($script:DOWNLOAD_OPTIONAL) {
        Write-Host "   Optional images: $($script:SELECTED_IMAGES.Count - $script:IMAGES.Count)"
    }
    else {
        Write-Host "   Optional images: 0"
    }
    
    Write-Host "   Total: $($script:SELECTED_IMAGES.Count) images"
    Write-Host "   Total size: $(Format-Size $total_size)"
    Write-Host ""
    
    return $total_size
}

# Pull image
function Pull-Image {
    param(
        [string]$Image,
        [bool]$IsOptional = $false
    )
    
    Write-LogInfo "Pulling image: $Image"
    
    # Check if image exists
    $existing = docker image inspect $Image 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-LogSuccess "Image already exists, skipping: $Image"
        return $true
    }
    
    # Pull directly from Docker Hub
    # Note: Configure mirror in Docker Desktop settings for faster download
    # Docker Desktop -> Settings -> Docker Engine -> Add registry-mirrors
    Write-LogInfo "Pulling from Docker Hub (configure mirror in Docker Desktop for faster download)..."
    $result = docker pull $Image 2>&1
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -eq 0) {
        Write-LogSuccess "Image pulled successfully: $Image"
        return $true
    }
    else {
        if ($IsOptional) {
            Write-LogWarning "Optional image pull failed (skipped): $Image"
            Write-Host $result
            return $false
        }
        else {
            Write-LogError "Image pull failed: $Image"
            Write-Host $result
            Write-Host ""
            Write-Host "Tip: Configure Docker mirror in Docker Desktop for faster download:" -ForegroundColor Yellow
            Write-Host "  1. Open Docker Desktop" -ForegroundColor Yellow
            Write-Host "  2. Go to Settings -> Docker Engine" -ForegroundColor Yellow
            Write-Host "  3. Add registry-mirrors in the JSON config:" -ForegroundColor Yellow
            Write-Host '     {' -ForegroundColor Cyan
            Write-Host '       "registry-mirrors": [' -ForegroundColor Cyan
            Write-Host '         "https://docker.1panel.live",' -ForegroundColor Cyan
            Write-Host '         "https://hub.rat.dev",' -ForegroundColor Cyan
            Write-Host '         "https://docker.chenby.cn",' -ForegroundColor Cyan
            Write-Host '         "https://docker.m.daocloud.io",' -ForegroundColor Cyan
            Write-Host '         "https://dockerhub.icu",' -ForegroundColor Cyan
            Write-Host '         "https://docker.hlyun.org",' -ForegroundColor Cyan
            Write-Host '         "https://dockerpull.org",' -ForegroundColor Cyan
            Write-Host '         "https://docker.rainbond.cc"' -ForegroundColor Cyan
            Write-Host '       ]' -ForegroundColor Cyan
            Write-Host '     }' -ForegroundColor Cyan
            Write-Host "  4. Click Apply & Restart" -ForegroundColor Yellow
            return $false
        }
    }
}

# Show image info
function Show-ImageInfo {
    param([string]$Image)
    
    Write-Host ""
    Write-Host "Image info:"
    docker images $Image --format "table {{.Repository}}`t{{.Tag}}`t{{.Size}}`t{{.CreatedAt}}"
    Write-Host ""
}

# Show help
function Show-Help {
    Write-Host "Usage: .\import_docker_images.ps1 [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -h, -Help       Show help"
    Write-Host "  -l, -List       List all images"
    Write-Host "  -o, -Optional   Pull optional images only"
    Write-Host "  -v, -Verbose    Verbose output"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\import_docker_images.ps1           # Pull required images"
    Write-Host "  .\import_docker_images.ps1 -l        # List images"
    Write-Host "  .\import_docker_images.ps1 -o        # Pull optional images"
    Write-Host ""
}

# List images
function Show-ImageList {
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  NecoRAG Docker Images List" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "[Required Images]" -ForegroundColor Yellow
    Write-Host "Image Name                                    Description"
    Write-Host "--------------------------------------------------------------------"
    Write-Host "{0,-44} {1}" -f "redis:7-alpine", "L1 Working Memory & Cache (~25MB)"
    Write-Host "{0,-44} {1}" -f "qdrant/qdrant:latest", "L2 Vector Database (~500MB)"
    Write-Host "{0,-44} {1}" -f "neo4j:5-community", "L3 Graph Database (~1.2GB)"
    Write-Host "{0,-44} {1}" -f "ollama/ollama:latest", "Local LLM Server (~2GB)"
    Write-Host "{0,-44} {1}" -f "grafana/grafana:latest", "Monitoring Dashboard (~300MB)"
    Write-Host ""
    Write-Host "[Optional Images - AI/ML]" -ForegroundColor Yellow
    Write-Host "Image Name                                    Description"
    Write-Host "--------------------------------------------------------------------"
    Write-Host "{0,-44} {1}" -f "vllm/vllm-openai:latest", "vLLM High-Performance LLM (~8GB)"
    Write-Host "{0,-44} {1}" -f "infiniflow/ragflow:latest", "RAGFlow Document Parsing (~2.5GB)"
    Write-Host "{0,-44} {1}" -f "langchain/langgraph:latest", "LangGraph State Machine (~500MB)"
    Write-Host "{0,-44} {1}" -f "streamlit/streamlit:latest", "Streamlit Frontend (~200MB)"
    Write-Host ""
    Write-Host "[Optional Images - Storage]" -ForegroundColor Yellow
    Write-Host "Image Name                                    Description"
    Write-Host "--------------------------------------------------------------------"
    Write-Host "{0,-44} {1}" -f "mysql:8.0", "Metadata Storage (~500MB)"
    Write-Host "{0,-44} {1}" -f "minio/minio:latest", "File Object Storage (~100MB)"
    Write-Host "{0,-44} {1}" -f "elasticsearch:8.12.0", "Full-Text Search (~1.2GB)"
    Write-Host "{0,-44} {1}" -f "kibana:8.12.0", "Search Visualization (~800MB)"
    Write-Host ""
    Write-Host "[Optional Images - Alternative & Monitoring]" -ForegroundColor Yellow
    Write-Host "Image Name                                    Description"
    Write-Host "--------------------------------------------------------------------"
    Write-Host "{0,-44} {1}" -f "milvusdb/milvus:v2.3.0", "Milvus Vector DB (~707MB)"
    Write-Host "{0,-44} {1}" -f "memgraph/memgraph:latest", "Memgraph Graph DB (~203MB)"
    Write-Host "{0,-44} {1}" -f "prom/prometheus:latest", "Prometheus Metrics (~146MB)"
    Write-Host "{0,-44} {1}" -f "apache/superset:latest", "Superset Visualization (~643MB)"
    Write-Host "{0,-44} {1}" -f "apache/tika:latest", "Apache Tika Parsing (~400MB)"
    Write-Host ""
    Write-Host "Total Required: 5 images (~4.03GB)" -ForegroundColor Green
    Write-Host "Total Optional: 14 images (~16GB)" -ForegroundColor Yellow
    Write-Host ""
}

# Main function
function Main {
    # Show title
    Show-Title
    
    # Check Docker
    Test-Docker
    
    # Select registry
    Select-Registry
    
    # Show menu and get selection
    Show-ImageSelectionMenu
    $total_size = Get-UserSelection
    
    # Check disk space
    if (-not (Test-DiskSpace -RequiredMB $total_size)) {
        Write-LogError "Disk space check failed, aborting"
        exit 1
    }
    
    Write-Host ""
    
    # Confirm download (auto-confirm with y)
    Write-LogInfo "Auto-confirming download..."
    $reply = "y"
    
    Write-Host ""
    
    # Statistics
    $total = 0
    $success = 0
    $failed = 0
    
    # Download images
    Write-LogInfo "Starting image download..."
    Write-Host ""
    
    foreach ($image in $script:SELECTED_IMAGES) {
        $total++
        
        # Check if optional
        $is_optional = $script:OPTIONAL_IMAGES -contains $image
        
        if (Pull-Image -Image $image -IsOptional $is_optional) {
            $success++
            Show-ImageInfo -Image $image
        }
        else {
            $failed++
            if ($is_optional) {
                Write-LogWarning "Optional image pull failed (skipped): $image"
            }
            else {
                Write-LogError "Required image pull failed, may affect system!"
                
                $reply = Read-Host "Continue with other images? (y/n)"
                if ($reply -notmatch "^[Yy]$") {
                    break
                }
            }
        }
    }
    
    Write-Host ""
    Write-LogInfo "Image pull completed"
    Write-Host ""
    
    # Summary report
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  Import Summary" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-LogInfo "Total attempted: $total images"
    Write-LogSuccess "Success: $success"
    
    if ($failed -gt 0) {
        Write-LogError "Failed: $failed"
    }
    
    Write-LogInfo "Downloaded: $success images ($(Format-Size $total_size))"
    Write-Host ""
    
    # Show pulled images
    Write-LogInfo "Current NecoRAG related images:"
    docker images --format "table {{.Repository}}`t{{.Tag}}`t{{.Size}}`t{{.CreatedAt}}" | Select-String -Pattern "redis|qdrant|neo4j|ollama|grafana|milvus|prom"
    Write-Host ""
    
    # Next steps
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  Next Steps" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Verify images:"
    Write-Host "   docker images"
    Write-Host ""
    Write-Host "2. Start services:"
    Write-Host "   cd devops; docker-compose up -d"
    Write-Host ""
    Write-Host "3. Check status:"
    Write-Host "   docker-compose ps"
    Write-Host ""
    Write-Host "4. View logs:"
    Write-Host "   docker-compose logs -f"
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Exit code
    if ($failed -gt 0) {
        exit 1
    }
    else {
        exit 0
    }
}

# Process command line arguments
if ($v -or $Verbose) {
    $VerbosePreference = "Continue"
}

if ($h -or $Help) {
    Show-Help
    exit 0
}

if ($l -or $List) {
    Show-ImageList
    exit 0
}

if ($o -or $Optional) {
    # Pull optional images only
    Show-Title
    Test-Docker
    Select-Registry
    
    foreach ($image in $script:OPTIONAL_IMAGES) {
        Pull-Image -Image $image -IsOptional $true
    }
    exit 0
}

# Run main
Main
