# YAPOM (Yet Another Package for Operations Management)

A Python tool for managing and executing network device commands using Nornir.

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/yapom.git
cd yapom

# Install dependencies
pip install -r requirements.txt
```

## Configuration

1. Create a `.env` file in the project root:
```env
NETWORK_USER=your_username
NETWORK_PASSWORD=your_password
```

2. Update the inventory files in `shared/nornir_data/`:
   - hosts.yaml: Device information
   - groups.yaml: Device groups
   - config.yaml: Nornir configuration

## Usage

### Basic Commands

```bash
# Run all available tasks
python main.py -t all

# Run specific task
python main.py -t basic_info

# Run for specific devices
python main.py -t basic_info -d device1 device2

# Run for specific site
python main.py -t basic_info -s NYC

# Run for specific role
python main.py -t basic_info -r edge
```

### Available Arguments

```
-t, --task      Task to execute (required)
                Available: basic_info, interface_info, routing_info, system_health, all
-d, --devices   One or more device hostnames
-s, --site      Site name filter
-r, --role      Role filter
-p, --platform  Platform filter
```

### Available Tasks

1. basic_info:
   - show version
   - show inventory
   - show running-config

2. interface_info:
   - show ip interface brief
   - show interfaces
   - show ip protocols

3. routing_info:
   - show ip route
   - show ip protocols
   - show ip ospf neighbor

4. system_health:
   - show processes cpu
   - show memory statistics
   - show logging

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

## Adding New Tasks

Add new tasks in `shared/services/mod.py`:

```python
AVAILABLE_TASKS = {
    "your_new_task": [
        "command1",
        "command2"
    ]
}
```