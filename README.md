# win-enum
Windows &amp; Active Directory Auto-Enumerator for OSCP

## Installation

```bash
# Make install script executable
chmod +x install.sh

# Run installer (checks and installs all dependencies)
./install.sh

# Make main script executable
chmod +x win-enum.py
```

## Required Tools

The install script will check and install these automatically:

| Tool | Purpose |
|------|---------|
| nmap | Port scanning |
| smbclient | SMB enumeration |
| netexec | SMB/WinRM/LDAP enumeration |
| gobuster | Web directory brute forcing |
| rpcclient | RPC enumeration |
| ldapsearch | LDAP queries |
| kerbrute | Kerberos user enumeration |
| impacket | AS-REP roasting, Kerberoasting |
| evil-winrm | WinRM shell access |
| hashcat | Hash cracking |

## Usage

### Basic Usage
```bash
# Will prompt if target is AD
python3 win-enum.py 192.168.1.100
```

### Active Directory Target
```bash
python3 win-enum.py 192.168.1.100 --ad -d domain.local
```

### Non-AD Windows Target
```bash
python3 win-enum.py 192.168.1.100 --no-ad
```

### Custom Output Directory
```bash
python3 win-enum.py 192.168.1.100 -o ./my-target
```

## Output Structure

```bash
target-ip/
├── nmap/
│   ├── quick.txt       # Top ports scan
│   └── full.txt        # All ports scan
├── smb/
│   ├── shares_null.txt # Null session shares
│   ├── netexec_shares.txt
│   ├── guest_shares.txt
│   └── winrm_check.txt
├── web/
│   └── gobuster_80.txt # Web directory brute force
├── ldap/
│   ├── rid_brute.txt   # RID cycling results
│   ├── ldap_users.txt  # LDAP user query
│   └── users.txt       # Extracted usernames
├── kerberos/
│   ├── kerbrute_users.txt
│   └── asrep.txt       # AS-REP roastable hashes
├── rpc/
│   └── enumdomusers.txt
└── notes.md            # Summary of findings
```

## What It Does

### General Windows (Always Runs)
1. **Nmap scan** - Quick scan + full port scan
2. **SMB enumeration** - Null session, shares, guest access
3. **WinRM check** - Test for remote access
4. **Web enumeration** - Gobuster on ports 80, 443, 8080, 8443

### Active Directory (If --ad)
1. **RPC enumeration** - Null session user enum
2. **RID brute force** - Enumerate users via RID cycling
3. **LDAP queries** - Anonymous bind user enumeration
4. **Kerbrute** - Username enumeration via Kerberos
5. **AS-REP Roasting** - Extract hashes for offline cracking

## Example Workflow

```bash
# 1. Run enumeration
python3 win-enum.py 192.168.235.172 --ad -d vault.offsec

# 2. Check summary
cat 192.168.235.172/notes.md

# 3. Review found users
cat 192.168.235.172/ldap/users.txt

# 4. Check for AS-REP hashes
cat 192.168.235.172/kerberos/asrep.txt

# 5. Crack any hashes found
hashcat -m 18200 192.168.235.172/kerberos/asrep.txt /usr/share/wordlists/rockyou.txt
```

## Tips

- Always review the `notes.md` summary first
- Check SMB shares for sensitive files manually
- Use found usernames for password spraying
- If AS-REP hash found, crack with hashcat mode 18200
- WinRM access means you can use evil-winrm for shell

## Adding to PATH

```bash
# Option 1: Symlink
sudo ln -s $(pwd)/win-enum.py /usr/local/bin/win-enum

# Option 2: Copy
sudo cp win-enum.py /usr/local/bin/win-enum

# Then use from anywhere
win-enum 192.168.1.100 --ad -d domain.local
```
