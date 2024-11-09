# YAPOM (Yet Another Performance Optimization Module)

A Python tool for network performance monitoring and command management across multiple platforms using Nornir. YAPOM helps streamline network operations by providing platform-specific command execution and output organization for performance analysis and monitoring.

## Features
- Multi-platform support (Cisco IOS, Arista EOS)
- Platform-specific performance monitoring commands
- Flexible filtering by site, role, platform, or specific devices
- Automated performance data collection and organization
- Environmental variable support for secure credentials
- Standardized output format for performance analysis

## Installation

```bash
# Clone the repository
git clone https://github.com/sshukla90/yapom.git
cd yapom

# Install dependencies using Poetry
poetry install

# Or using pip
pip install -r requirements.txt
```

## Configuration

1. Create a `.env` file in the project root:
```env
NETWORK_USER=your_username
NETWORK_PASSWORD=your_password
```

2. Update the inventory files in `shared/nornir_data/`:
   - hosts.yaml: Device information and platform specifications
   - groups.yaml: Device groups and platform-specific settings
   - config.yaml: Nornir configuration

### Example hosts.yaml
```yaml
clab-vios-lab-vios1:
    hostname: 192.168.106.3
    platform: ios
    groups:
        - cisco_ios_xe
    data:
        role: edge
        site: AUS

arista1:
    hostname: 192.168.106.11
    platform: eos
    groups:
        - arista
    data:
        role: core
        site: AUS
```

## Usage

### Basic Commands

```bash
# Run all performance monitoring tasks
python main.py -t all

# Run specific performance task
python main.py -t system_health

# Monitor specific devices
python main.py -t basic_info -d device1 device2

# Monitor specific site and role
python main.py -t system_health -s AUS -r edge

# Platform-specific monitoring
python main.py -t system_health -p eos

# Comprehensive platform monitoring
python main.py -t all -p eos -s AUS -r core
```

### Available Arguments

```
-t, --task      Task to execute (required)
                Available: basic_info, interface_info, routing_info, system_health, all
-d, --devices   One or more device hostnames
-s, --site      Site name filter (AUS, IND, ALL)
-r, --role      Role filter (edge, ISP, core, ALL)
-p, --platform  Platform filter (ios, nxos, iosxr, eos)
```

### Performance Monitoring Tasks and Platform-Specific Commands

Commands are defined per platform in `shared/services/mod.py`:

```python
PLATFORM_COMMANDS = {
    'ios': {
        "basic_info": [
            "show version",
            "show inventory",
            "show running-config"
        ],
        "system_health": [
            "show processes cpu",  # CPU performance monitoring
            "show memory statistics",  # Memory utilization
            "show logging"  # System logs for performance issues
        ]
    },
    'eos': {
        "basic_info": [
            "show version",
            "show inventory",
            "show running-config"
        ],
        "system_health": [
            "show processes top",    # CPU and process monitoring
            "show memory",          # Memory usage statistics
            "show logging"         # System performance logs
        ]
    }
}
```

### Output Structure

```
output/
└── ALL/
    └── YYYY-MM-DD_HH-MM/
        ├── device1/
        │   ├── show version.txt
        │   ├── show processes cpu.txt
        │   └── show memory statistics.txt
        └── arista1/
            ├── show version.txt
            ├── show processes top.txt
            └── show memory.txt
```

## Adding New Platforms and Performance Metrics

1. Add new platform commands in `shared/services/mod.py`:

```python
PLATFORM_COMMANDS = {
    'new_platform': {
        "system_health": [
            "platform-specific-cpu-command",
            "platform-specific-memory-command"
        ]
    }
}
```

2. Update platform validation in `main.py`:

```python
valid_platforms = {'ios', 'nxos', 'iosxr', 'eos', 'new_platform'}
```

Performance metrics are automatically collected based on the platform commands defined.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/new-metrics`)
3. Commit your changes (`git commit -m 'Add new performance metrics'`)
4. Push to the branch (`git push origin feature/new-metrics`)
5. Open a Pull Request