#!/usr/bin/env python3
"""
Windows Auto-Enumerator
OSCP Helper Tool
"""

import subprocess
import sys
import os
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Colors for output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def banner():
    print(f"""{Colors.CYAN}
    ╦ ╦╦╔╗╔  ╔═╗╔╗╔╦ ╦╔╦╗
    ║║║║║║║  ║╣ ║║║║ ║║║║
    ╚╩╝╩╝╚╝  ╚═╝╝╚╝╚═╝╩ ╩
    Windows Auto-Enumerator
    {Colors.RESET}""")

def print_status(msg, status="info"):
    symbols = {
        "info": f"{Colors.BLUE}[*]{Colors.RESET}",
        "success": f"{Colors.GREEN}[+]{Colors.RESET}",
        "error": f"{Colors.RED}[-]{Colors.RESET}",
        "warning": f"{Colors.YELLOW}[!]{Colors.RESET}",
        "running": f"{Colors.PURPLE}[~]{Colors.RESET}"
    }
    print(f"{symbols.get(status, symbols['info'])} {msg}")

def run_command(cmd, output_file=None, timeout=300):
    """Run a command and optionally save output to file"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        output = result.stdout + result.stderr
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(f"Command: {cmd}\n")
                f.write(f"Time: {datetime.now()}\n")
                f.write("="*50 + "\n\n")
                f.write(output)
        
        return output
    except subprocess.TimeoutExpired:
        return f"[!] Command timed out after {timeout} seconds"
    except Exception as e:
        return f"[!] Error: {str(e)}"

def create_directories(base_path):
    """Create output directory structure"""
    dirs = ['nmap', 'smb', 'web', 'ldap', 'kerberos', 'rpc']
    for d in dirs:
        os.makedirs(os.path.join(base_path, d), exist_ok=True)
    return base_path

def check_tool(tool):
    """Check if a tool is installed"""
    result = subprocess.run(f"which {tool}", shell=True, capture_output=True)
    return result.returncode == 0

def check_dependencies():
    """Check if required tools are installed"""
    tools = ['nmap', 'smbclient', 'netexec', 'gobuster']
    missing = []
    for tool in tools:
        if not check_tool(tool):
            missing.append(tool)
    
    if missing:
        print_status(f"Missing tools: {', '.join(missing)}", "warning")
        return False
    return True

# ============== SCAN FUNCTIONS ==============

def nmap_scan(target, output_dir):
    """Run nmap scans"""
    print_status("Running Nmap TCP scan...", "running")
    
    # Quick scan first
    quick_cmd = f"nmap -sC -sV -oN {output_dir}/nmap/quick.txt {target}"
    run_command(quick_cmd, f"{output_dir}/nmap/quick.txt", timeout=300)
    print_status("Quick scan complete", "success")
    
    # Full port scan
    print_status("Running Nmap full port scan...", "running")
    full_cmd = f"nmap -p- -sC -sV -oN {output_dir}/nmap/full.txt {target}"
    run_command(full_cmd, f"{output_dir}/nmap/full.txt", timeout=600)
    print_status("Full scan complete", "success")
    
    # Parse for open ports
    with open(f"{output_dir}/nmap/quick.txt", 'r') as f:
        content = f.read()
    
    return content

def smb_enum(target, output_dir):
    """Enumerate SMB shares and info"""
    print_status("Enumerating SMB...", "running")
    
    # List shares with null session
    shares_cmd = f"smbclient -L //{target} -N"
    shares_output = run_command(shares_cmd, f"{output_dir}/smb/shares_null.txt")
    
    # NetExec shares
    netexec_cmd = f"netexec smb {target} -u '' -p '' --shares"
    run_command(netexec_cmd, f"{output_dir}/smb/netexec_shares.txt")
    
    # Check for writable shares
    netexec_write = f"netexec smb {target} -u 'guest' -p '' --shares"
    run_command(netexec_write, f"{output_dir}/smb/guest_shares.txt")
    
    print_status("SMB enumeration complete", "success")
    return shares_output

def web_enum(target, output_dir, ports=[80, 443, 8080, 8443]):
    """Enumerate web services if found"""
    print_status("Checking for web services...", "running")
    
    for port in ports:
        # Quick check if port is open
        check = subprocess.run(
            f"nc -zv -w 2 {target} {port}",
            shell=True,
            capture_output=True
        )
        
        if check.returncode == 0:
            print_status(f"Port {port} open - running gobuster...", "running")
            
            protocol = "https" if port in [443, 8443] else "http"
            gobuster_cmd = f"gobuster dir -u {protocol}://{target}:{port} -w /usr/share/wordlists/dirb/common.txt -o {output_dir}/web/gobuster_{port}.txt -t 30 --timeout 20s"
            run_command(gobuster_cmd, timeout=300)
            print_status(f"Gobuster on port {port} complete", "success")
    
    return True

def winrm_check(target, output_dir):
    """Check WinRM access"""
    print_status("Checking WinRM...", "running")
    
    cmd = f"netexec winrm {target} -u '' -p ''"
    output = run_command(cmd, f"{output_dir}/smb/winrm_check.txt")
    
    print_status("WinRM check complete", "success")
    return output

# ============== AD-SPECIFIC FUNCTIONS ==============

def ad_user_enum(target, domain, output_dir):
    """Enumerate AD users"""
    print_status("Enumerating AD users...", "running")
    
    # RID brute force
    rid_cmd = f"netexec smb {target} -u 'guest' -p '' --rid-brute"
    rid_output = run_command(rid_cmd, f"{output_dir}/ldap/rid_brute.txt", timeout=300)
    
    # LDAP anonymous bind
    ldap_cmd = f'ldapsearch -x -H ldap://{target} -b "DC={domain.split(".")[0]},DC={domain.split(".")[1]}" "(objectClass=user)" sAMAccountName'
    run_command(ldap_cmd, f"{output_dir}/ldap/ldap_users.txt")
    
    print_status("AD user enumeration complete", "success")
    
    # Extract usernames for later use
    users = []
    if "SidTypeUser" in rid_output:
        for line in rid_output.split('\n'):
            if "SidTypeUser" in line:
                try:
                    user = line.split('\\')[1].split(' ')[0]
                    users.append(user)
                except:
                    pass
    
    # Save users to file
    if users:
        with open(f"{output_dir}/ldap/users.txt", 'w') as f:
            f.write('\n'.join(users))
        print_status(f"Found {len(users)} users", "success")
    
    return users

def asrep_roast(target, domain, output_dir, users=None):
    """AS-REP Roasting"""
    print_status("Attempting AS-REP Roasting...", "running")
    
    if users:
        # Use discovered users
        user_file = f"{output_dir}/ldap/users.txt"
        cmd = f"impacket-GetNPUsers {domain}/ -dc-ip {target} -usersfile {user_file} -no-pass -format hashcat"
    else:
        # Try common usernames
        cmd = f"impacket-GetNPUsers {domain}/ -dc-ip {target} -no-pass -format hashcat"
    
    output = run_command(cmd, f"{output_dir}/kerberos/asrep.txt")
    
    if "$krb5asrep$" in output:
        print_status("AS-REP hash found! Check kerberos/asrep.txt", "success")
    else:
        print_status("No AS-REP hashes found", "info")
    
    return output

def kerbrute_enum(target, domain, output_dir):
    """Enumerate users with kerbrute"""
    print_status("Running Kerbrute user enumeration...", "running")
    
    wordlist = "/usr/share/seclists/Usernames/Names/names.txt"
    if not os.path.exists(wordlist):
        wordlist = "/usr/share/wordlists/dirb/common.txt"
    
    cmd = f"kerbrute userenum {wordlist} -d {domain} --dc {target} -o {output_dir}/kerberos/kerbrute_users.txt"
    output = run_command(cmd, timeout=300)
    
    print_status("Kerbrute complete", "success")
    return output

def rpc_enum(target, output_dir):
    """RPC enumeration"""
    print_status("Attempting RPC enumeration...", "running")
    
    cmd = f"rpcclient -U '' -N {target} -c 'enumdomusers'"
    output = run_command(cmd, f"{output_dir}/rpc/enumdomusers.txt")
    
    if "NT_STATUS_ACCESS_DENIED" not in output:
        print_status("RPC null session successful!", "success")
    else:
        print_status("RPC null session denied", "info")
    
    return output

# ============== SUMMARY ==============

def generate_summary(target, output_dir, is_ad, domain=None):
    """Generate a summary of findings"""
    summary = f"""
# Enumeration Summary
Target: {target}
Domain: {domain if is_ad else 'N/A'}
Type: {'Active Directory' if is_ad else 'Standalone Windows'}
Time: {datetime.now()}

## Quick Findings
"""
    
    # Check for interesting findings
    findings = []
    
    # Check SMB null session
    smb_file = f"{output_dir}/smb/shares_null.txt"
    if os.path.exists(smb_file):
        with open(smb_file, 'r') as f:
            if "Sharename" in f.read():
                findings.append("- [!] SMB null session allowed")
    
    # Check for AS-REP hashes
    asrep_file = f"{output_dir}/kerberos/asrep.txt"
    if os.path.exists(asrep_file):
        with open(asrep_file, 'r') as f:
            if "$krb5asrep$" in f.read():
                findings.append("- [!] AS-REP hash found - crack it!")
    
    # Check for users
    users_file = f"{output_dir}/ldap/users.txt"
    if os.path.exists(users_file):
        with open(users_file, 'r') as f:
            users = f.read().strip().split('\n')
            if users and users[0]:
                findings.append(f"- Found {len(users)} domain users")
    
    if findings:
        summary += '\n'.join(findings)
    else:
        summary += "- No quick wins found, manual enumeration needed"
    
    summary += """

## Next Steps
1. Check nmap output for all open ports
2. Review SMB shares for sensitive files
3. Try password spraying with found users
4. Check web directories if web server present
5. Look for service accounts (Kerberoasting)
"""
    
    # Save summary
    with open(f"{output_dir}/notes.md", 'w') as f:
        f.write(summary)
    
    print(f"\n{Colors.CYAN}{'='*50}{Colors.RESET}")
    print(summary)
    print(f"{Colors.CYAN}{'='*50}{Colors.RESET}")
    
    return summary

# ============== MAIN ==============

def main():
    banner()
    
    parser = argparse.ArgumentParser(description="Windows Auto-Enumerator")
    parser.add_argument("target", help="Target IP address")
    parser.add_argument("-d", "--domain", help="Domain name (e.g., vault.offsec)")
    parser.add_argument("-o", "--output", help="Output directory", default=None)
    parser.add_argument("--ad", action="store_true", help="Target is Active Directory")
    parser.add_argument("--no-ad", action="store_true", help="Target is not Active Directory")
    
    args = parser.parse_args()
    
    target = args.target
    
    # Check dependencies
    if not check_dependencies():
        print_status("Install missing tools and try again", "error")
        sys.exit(1)
    
    # Determine if AD
    if args.ad:
        is_ad = True
    elif args.no_ad:
        is_ad = False
    else:
        response = input(f"\n{Colors.YELLOW}[?] Is this an Active Directory target? (y/n): {Colors.RESET}").lower()
        is_ad = response == 'y'
    
    # Get domain if AD
    domain = args.domain
    if is_ad and not domain:
        domain = input(f"{Colors.YELLOW}[?] Enter domain name (e.g., vault.offsec): {Colors.RESET}")
    
    # Setup output directory
    output_dir = args.output or f"./{target}"
    create_directories(output_dir)
    print_status(f"Output directory: {output_dir}", "info")
    
    print(f"\n{Colors.CYAN}{'='*50}{Colors.RESET}")
    print(f"{Colors.BOLD}Starting enumeration on {target}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*50}{Colors.RESET}\n")
    
    # ===== GENERAL WINDOWS SCANS =====
    print(f"\n{Colors.GREEN}[GENERAL WINDOWS ENUMERATION]{Colors.RESET}\n")
    
    # Nmap
    nmap_scan(target, output_dir)
    
    # SMB
    smb_enum(target, output_dir)
    
    # WinRM
    winrm_check(target, output_dir)
    
    # Web
    web_enum(target, output_dir)
    
    # ===== AD-SPECIFIC SCANS =====
    if is_ad:
        print(f"\n{Colors.GREEN}[ACTIVE DIRECTORY ENUMERATION]{Colors.RESET}\n")
        
        # RPC
        rpc_enum(target, output_dir)
        
        # User enumeration
        users = ad_user_enum(target, domain, output_dir)
        
        # Kerbrute
        if check_tool('kerbrute'):
            kerbrute_enum(target, domain, output_dir)
        
        # AS-REP Roasting
        asrep_roast(target, domain, output_dir, users)
    
    # Generate summary
    generate_summary(target, output_dir, is_ad, domain)
    
    print_status(f"Enumeration complete! Check {output_dir}/ for results", "success")

if __name__ == "__main__":
    main()
