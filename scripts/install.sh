#!/bin/bash
# OTIS Installation Script
# Installs and configures the OTIS optimization system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root for system modifications
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "Running as root. This is recommended for system optimization."
    else
        log_info "Running as regular user. Some optimizations may require sudo."
    fi
}

# Detect Linux distribution
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        VERSION=$VERSION_ID
    else
        log_error "Cannot detect Linux distribution"
        exit 1
    fi
    
    log_info "Detected distribution: $DISTRO $VERSION"
}

# Install system dependencies
install_dependencies() {
    log_info "Installing system dependencies..."
    
    case $DISTRO in
        ubuntu|debian)
            apt update
            apt install -y \
                python3 \
                python3-pip \
                python3-venv \
                zram-tools \
                wine-staging \
                mesa-utils \
                vulkan-tools \
                build-essential \
                linux-headers-$(uname -r) \
                git \
                curl \
                wget
            ;;
        fedora)
            dnf update -y
            dnf install -y \
                python3 \
                python3-pip \
                zram-generator \
                wine \
                mesa-utils \
                vulkan-tools \
                kernel-devel \
                git \
                curl \
                wget
            ;;
        arch)
            pacman -Syu --noconfirm
            pacman -S --noconfirm \
                python \
                python-pip \
                zram-generator \
                wine-staging \
                mesa-utils \
                vulkan-tools \
                linux-headers \
                git \
                curl \
                wget
            ;;
        *)
            log_warning "Unsupported distribution: $DISTRO"
            log_info "Please install dependencies manually:"
            log_info "- Python 3.8+"
            log_info "- pip"
            log_info "- zram-tools"
            log_info "- wine-staging"
            log_info "- mesa-utils"
            log_info "- vulkan-tools"
            ;;
    esac
    
    log_success "System dependencies installed"
}

# Install DXVK
install_dxvk() {
    log_info "Installing DXVK..."
    
    # Create wine prefix if it doesn't exist
    if [ ! -d "$HOME/.wine" ]; then
        log_info "Creating Wine prefix..."
        WINEPREFIX="$HOME/.wine" winecfg
    fi
    
    # Download and install DXVK
    DXVK_VERSION="2.3.1"
    DXVK_URL="https://github.com/doitsujin/dxvk/releases/download/v${DXVK_VERSION}/dxvk-${DXVK_VERSION}.tar.gz"
    
    cd /tmp
    wget -O dxvk.tar.gz "$DXVK_URL"
    tar -xzf dxvk.tar.gz
    cd dxvk-*
    
    # Install DXVK
    WINEPREFIX="$HOME/.wine" ./setup_dxvk.sh install
    
    log_success "DXVK installed"
}

# Setup Python virtual environment
setup_python_env() {
    log_info "Setting up Python environment..."
    
    # Create virtual environment
    python3 -m venv ~/.otis-env
    source ~/.otis-env/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install OTIS
    pip install -e .
    
    log_success "Python environment setup complete"
}

# Configure system optimizations
configure_system() {
    log_info "Configuring system optimizations..."
    
    # Enable zRAM module
    if ! lsmod | grep -q zram; then
        modprobe zram
        echo "zram" >> /etc/modules-load.d/otis.conf
    fi
    
    # Configure KSM
    if [ -d /sys/kernel/mm/ksm ]; then
        echo 1 > /sys/kernel/mm/ksm/run
        echo "echo 1 > /sys/kernel/mm/ksm/run" >> /etc/rc.local
    fi
    
    # Set up systemd service
    cat > /etc/systemd/system/otis.service << EOF
[Unit]
Description=OTIS Optimization System
After=multi-user.target

[Service]
Type=simple
User=root
ExecStart=/home/$SUDO_USER/.otis-env/bin/otis start --mode auto
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable otis.service
    
    log_success "System configuration complete"
}

# Create desktop entry
create_desktop_entry() {
    log_info "Creating desktop entry..."
    
    cat > ~/.local/share/applications/otis.desktop << EOF
[Desktop Entry]
Name=OTIS Optimizer
Comment=Linux Performance Optimization and Windows Compatibility
Exec=/home/$USER/.otis-env/bin/otis-gui
Icon=applications-system
Terminal=false
Type=Application
Categories=System;Settings;
EOF
    
    log_success "Desktop entry created"
}

# Main installation function
main() {
    echo "🚀 OTIS Installation Script"
    echo "=========================="
    
    check_root
    detect_distro
    
    log_info "Starting OTIS installation..."
    
    # Install dependencies
    install_dependencies
    
    # Install DXVK
    install_dxvk
    
    # Setup Python environment
    setup_python_env
    
    # Configure system (requires root)
    if [[ $EUID -eq 0 ]]; then
        configure_system
    else
        log_warning "Skipping system configuration (requires root)"
        log_info "Run 'sudo ./scripts/install.sh' for full system integration"
    fi
    
    # Create desktop entry
    create_desktop_entry
    
    log_success "🎉 OTIS installation complete!"
    echo ""
    echo "Next steps:"
    echo "1. Reboot your system for all optimizations to take effect"
    echo "2. Run 'otis start' to begin optimization"
    echo "3. Run 'otis-gui' to open the graphical interface"
    echo "4. Check status with 'otis status'"
    echo ""
    echo "For help: otis --help"
    echo "Documentation: https://docs.otis-optimizer.com"
}

# Run main function
main "$@"