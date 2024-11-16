# YAPOM (Yet Another performance optimization manager)

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

# Install libs
pip install <lib name>

## Configuration

1. Set up your credentials:
   - Interactive prompt will ask for password
   - Username provided via command line argument (-pu)

2. Update the inventory files in `shared/nornir_data/`:
   ```
   shared/
   └── nornir_data/
       ├── config.yaml   # Nornir configuration
       ├── defaults.yaml # Default settings
       ├── groups.yaml   # Device groups
       └── hosts.yaml    # Device inventory
   ```

3. Example hosts.yaml configuration:
   ```
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

### Basic Commands

```bash
# Run all tasks
python main.py -t all -pu admin

# Run specific task
python main.py -t basic_info -pu admin

# Run for specific devices
python main.py -t basic_info -d device1 device2 -pu admin

# Run for specific site and role
python main.py -t basic_info -s NYC -r edge -pu admin

# Run for specific platform
python main.py -t basic_info -p ios -pu admin
```

### Command Line Arguments

```
-t, --task        Task to execute (required)
-pu, --login_user Login username (required)
-d, --devices     One or more device hostnames
-s, --site        Site name filter
-r, --role        Role filter
-p, --platform    Platform filter (ios, nxos, junos, eos)
```

### Supported Platforms and Tasks

The tool supports the following platforms with platform-specific commands:
- Cisco IOS/IOS-XE (ios)
- Cisco NX-OS (nxos)
- Juniper JunOS (junos)
- Arista EOS (eos)

Available tasks for all platforms:
1. basic_info
2. interface_info
3. routing_info
4. system_health

Platform-specific commands are defined in `shared/services/mod.py`

### Output Structure

```
output/
└── ALL/
    └── YYYY-MM-DD_HH-MM/
        ├── device1/
        │   ├── show_version.txt
        │   └── show_interfaces.txt
        └── device2/
            ├── show_version.txt
            └── show_interfaces.txt
```

## Extending Functionality

### Adding New Vendor Support

Add vendor commands in `shared/services/mod.py`:

```python
VENDOR_COMMANDS = {
    "new_vendor": {
        "basic_info": [
            "command1",
            "command2"
        ],
        "interface_info": [
            "command3",
            "command4"
        ]
        # ... other task categories
    }
}
```

### Adding New Tasks

Add new task category in `shared/services/mod.py`:

```python
VENDOR_COMMANDS = {
    "ios": {
        "new_task_name": [
            "command1",
            "command2"
        ]
    },
    "nxos": {
        "new_task_name": [
            "command1",
            "command2"
        ]
    }
    # ... repeat for other vendors
}
```

## Example Command Outputs

### Cisco IOS
```
basic_info:
  - show version
  - show inventory
  - show running-config

interface_info:
  - show ip interface brief
  - show interfaces
  - show ip protocols
```

### Cisco NXOS
```
basic_info:
  - show version
  - show inventory
  - show running-config

system_health:
  - show system resources
  - show processes cpu sort
  - show logging last 100
```

### Juniper JunOS
```
basic_info:
  - show version
  - show chassis hardware
  - show configuration | display set

interface_info:
  - show interfaces terse
  - show interfaces detail
  - show protocols
```

### Arista EOS
```
basic_info:
  - show version
  - show inventory
  - show running-config

system_health:
  - show processes top
  - show memory
  - show logging last 100
```

## Error Handling

The script provides:
- Connectivity verification before task execution
- Platform-specific command validation
- Detailed error messages for failed commands
- Output saved even for partially successful executions

## Dependencies

- nornir
- nornir-scrapli
- scrapli
- pathlib
- poetry

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request