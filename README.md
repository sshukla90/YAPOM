# YAPOM (Yet Another performance optimization module)

A Python tool for multi-vendor network device command management using Nornir and Scrapli.

## Installation

```bash
# Clone the repository
git clone https://github.com/sshukla90/yapom.git
cd yapom

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install dependencies using Poetry
pip install < lib name > 
```

## Configuration

Update the inventory files in `shared/nornir_data/`:
```
shared/
└── nornir_data/
    ├── config.yaml   # Nornir configuration
    ├── defaults.yaml # Default settings
    ├── groups.yaml   # Device groups
    └── hosts.yaml    # Device inventory
```

### Host Configuration Example
```yaml
# hosts.yaml
device1:
  hostname: 192.168.1.10
  platform: ios
  groups:
    - cisco_ios_xe
  data:
    role: edge
    site: NYC

device2:
  hostname: 192.168.1.20
  platform: nxos
  groups:
    - cisco_nxos
  data:
    role: core
    site: LAX
```

## Usage

### Command Structure
```bash
python main.py -t  -pu  [-d  | -s ] [-r ] [-p ]
```

### Required Arguments
- `-t, --task`: Task to execute (use 'all' for all tasks)
- `-pu, --login_user`: Login username

### Device Selection (One Required)
- `-d, --devices`: List of specific devices
- `-s, --site`: Site name (use 'ALL' for all sites)

### Optional Arguments
- `-r, --role`: Role filter (only used with -s)
- `-p, --platform`: Platform filter (ios, nxos, junos, eos)

### Example Commands

1. Run all tasks for all devices:
```bash
python main.py -t all -s ALL -pu admin
```

2. Run specific task for all devices:
```bash
python main.py -t basic_info -s ALL -pu admin
```

3. Run task for specific devices:
```bash
python main.py -t basic_info -d device1 device2 -pu admin
```

4. Run task for specific site (all roles):
```bash
python main.py -t basic_info -s NYC -pu admin
```

5. Run task for specific site and role:
```bash
python main.py -t basic_info -s NYC -r edge -pu admin
```

6. Run task for specific platform:
```bash
python main.py -t basic_info -s ALL -p ios -pu admin
```

## Available Tasks and Commands

### Basic Info
```yaml
ios/eos:
  - show version
  - show inventory
  - show running-config

nxos:
  - show version
  - show inventory
  - show running-config

junos:
  - show version
  - show chassis hardware
  - show configuration | display set
```

### Interface Info
```yaml
ios/eos:
  - show ip interface brief
  - show interfaces
  - show ip protocols

nxos:
  - show ip interface brief
  - show interface status
  - show interface

junos:
  - show interfaces terse
  - show interfaces detail
  - show protocols
```

### Routing Info
```yaml
ios/eos:
  - show ip route
  - show ip protocols
  - show ip ospf neighbor

nxos:
  - show ip route
  - show ip ospf neighbors
  - show ip protocols

junos:
  - show route
  - show ospf neighbor
  - show protocols
```

### System Health
```yaml
ios:
  - show processes cpu
  - show memory statistics
  - show logging

nxos:
  - show system resources
  - show processes cpu sort
  - show logging last 100

junos:
  - show system processes extensive
  - show system memory
  - show log messages | last 100

eos:
  - show processes top
  - show memory
  - show logging last 100
```

## Output Structure

```
output/
└── <SITE>/
    └── YYYY-MM-DD_HH-MM/
        ├── device1/
        │   ├── show_version.txt
        │   ├── show_interfaces.txt
        │   └── ...
        └── device2/
            ├── show_version.txt
            ├── show_interfaces.txt
            └── ...
```

## Features

1. Multi-vendor Support:
   - Cisco IOS/IOS-XE
   - Cisco NX-OS
   - Juniper JunOS
   - Arista EOS

2. Task-based Execution:
   - Predefined command sets
   - Platform-specific commands
   - Multiple tasks in single run

3. Flexible Device Selection:
   - By specific devices
   - By site
   - By role
   - By platform

4. Structured Output:
   - Timestamp-based directories
   - Device-specific folders
   - Command-specific files

5. Error Handling:
   - Connectivity verification
   - Command execution validation
   - Detailed error reporting

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request