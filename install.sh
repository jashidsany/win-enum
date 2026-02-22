#!/bin/bash

# Win-Enum Installation Script
# Installs all required tools for the Windows Auto-Enumerator

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
echo "╦ ╦╦╔╗╔  ╔═╗╔╗╔╦ ╦╔╦╗"
echo "║║║║║║║  ║╣ ║║║║ ║║║║"
echo "╚╩╝╩╝╚╝  ╚═╝╝╚╝╚═╝╩ ╩"
echo "Installation Script"
echo -e "${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}[!] Some installations may require sudo${NC}"
fi

echo -e "\n${GREEN}[*] Checking and installing required tools...${NC}\n"

# Function to check if tool exists
check_tool() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}[+] $1 is installed${NC}"
        return 0
    else
        echo -e "${RED}[-] $1 is NOT installed${NC}"
        return 1
    fi
}

# Function to install tool
install_tool() {
    echo -e "${YELLOW}[*] Installing $1...${NC}"
    sudo apt install -y $1 > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[+] $1 installed successfully${NC}"
    else
        echo -e "${RED}[-] Failed to install $1${NC}"
    fi
}

echo "================================"
echo "Required Tools"
echo "================================"

# Nmap
check_tool nmap || install_tool nmap

# Smbclient
check_tool smbclient || install_tool smbclient

# NetExec (formerly CrackMapExec)
if ! check_tool netexec; then
    echo -e "${YELLOW}[*] Installing netexec via pipx...${NC}"
    sudo apt install -y pipx > /dev/null 2>&1
    pipx install netexec > /dev/null 2>&1
    pipx ensurepath > /dev/null 2>&1
    echo -e "${GREEN}[+] netexec installed - restart terminal or run 'source ~/.bashrc'${NC}"
fi

# Gobuster
check_tool gobuster || install_tool gobuster

# Rpcclient (part of smbclient)
check_tool rpcclient || install_tool smbclient

# Ldapsearch
check_tool ldapsearch || install_tool ldap-utils

# Netcat
check_tool nc || install_tool netcat-openbsd

# Evil-WinRM
if ! check_tool evil-winrm; then
    echo -e "${YELLOW}[*] Installing evil-winrm...${NC}"
    sudo gem install evil-winrm > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[+] evil-winrm installed successfully${NC}"
    else
        echo -e "${RED}[-] Failed to install evil-winrm${NC}"
    fi
fi

echo ""
echo "================================"
echo "Optional Tools (Recommended)"
echo "================================"

# Kerbrute
if ! check_tool kerbrute; then
    echo -e "${YELLOW}[*] Installing kerbrute...${NC}"
    # Try apt first
    sudo apt install -y kerbrute > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        # Download from GitHub
        wget -q https://github.com/ropnop/kerbrute/releases/latest/download/kerbrute_linux_amd64 -O /tmp/kerbrute
        sudo mv /tmp/kerbrute /usr/local/bin/kerbrute
        sudo chmod +x /usr/local/bin/kerbrute
        echo -e "${GREEN}[+] kerbrute installed from GitHub${NC}"
    fi
fi

# Impacket
if ! check_tool impacket-GetNPUsers; then
    echo -e "${YELLOW}[*] Installing impacket-scripts...${NC}"
    sudo apt install -y python3-impacket impacket-scripts > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[+] impacket installed successfully${NC}"
    else
        echo -e "${RED}[-] Failed to install impacket - try: pip3 install impacket${NC}"
    fi
fi

# Enum4linux-ng
if ! check_tool enum4linux-ng; then
    echo -e "${YELLOW}[*] Installing enum4linux-ng...${NC}"
    sudo apt install -y enum4linux-ng > /dev/null 2>&1 || pip3 install enum4linux-ng > /dev/null 2>&1
fi

# Hashcat
check_tool hashcat || install_tool hashcat

# John
check_tool john || install_tool john

echo ""
echo "================================"
echo "Wordlists"
echo "================================"

# SecLists
if [ -d "/usr/share/seclists" ]; then
    echo -e "${GREEN}[+] SecLists is installed${NC}"
else
    echo -e "${YELLOW}[*] Installing SecLists...${NC}"
    sudo apt install -y seclists > /dev/null 2>&1
fi

# Rockyou
if [ -f "/usr/share/wordlists/rockyou.txt" ]; then
    echo -e "${GREEN}[+] rockyou.txt is available${NC}"
elif [ -f "/usr/share/wordlists/rockyou.txt.gz" ]; then
    echo -e "${YELLOW}[*] Extracting rockyou.txt...${NC}"
    sudo gunzip /usr/share/wordlists/rockyou.txt.gz
    echo -e "${GREEN}[+] rockyou.txt extracted${NC}"
else
    echo -e "${RED}[-] rockyou.txt not found${NC}"
fi

echo ""
echo "================================"
echo "Python Dependencies"
echo "================================"

# Check Python3
check_tool python3

echo ""
echo "================================"
echo -e "${GREEN}Installation Complete!${NC}"
echo "================================"
echo ""
echo "Usage:"
echo "  python3 win-enum.py <target-ip>"
echo "  python3 win-enum.py <target-ip> --ad -d domain.local"
echo ""
echo "If netexec was just installed, run:"
echo "  source ~/.bashrc"
echo ""
