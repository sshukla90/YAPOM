
VENDOR_COMMANDS = {
    "ios": {
        "basic_info": [
            "show version",
            "show inventory",
            "show running-config"
        ],
        "interface_info": [
            "show ip interface brief",
            "show interfaces",
            "show ip protocols"
        ],
        "routing_info": [
            "show ip route",
            "show ip protocols",
            "show ip ospf neighbor"
        ],
        "system_health": [
            "show processes cpu",
            "show memory statistics",
            "show logging"
        ]
    },
    "nxos": {
        "basic_info": [
            "show version",
            "show inventory",
            "show running-config"
        ],
        "interface_info": [
            "show ip interface brief",
            "show interface status",
            "show interface"
        ],
        "routing_info": [
            "show ip route",
            "show ip ospf neighbors",
            "show ip protocols"
        ],
        "system_health": [
            "show system resources",
            "show processes cpu sort",
            "show logging last 100"
        ]
    },
    "junos": {
        "basic_info": [
            "show version",
            "show chassis hardware",
            "show configuration | display set"
        ],
        "interface_info": [
            "show interfaces terse",
            "show interfaces detail",
            "show protocols"
        ],
        "routing_info": [
            "show route",
            "show ospf neighbor",
            "show protocols"
        ],
        "system_health": [
            "show system processes extensive",
            "show system memory",
            "show log messages | last 100"
        ]
    },
    "eos": {
        "basic_info": [
            "show version",
            "show inventory",
            "show running-config"
        ],
        "interface_info": [
            "show ip interface brief",
            "show interfaces",
            "show ip protocols"
        ],
        "routing_info": [
            "show ip route",
            "show ip ospf neighbor",
            "show ip protocols"
        ],
        "system_health": [
            "show processes top",
            "show memory",
            "show logging last 100"
        ]
    }
}

# List of available tasks
AVAILABLE_TASKS = list(VENDOR_COMMANDS["ios"].keys())  # Using ios as reference since tasks are same

def get_commands_for_task(task_name: str, platform: str) -> list:
    """Get commands for a specific task and platform"""
    platform = platform.lower()
    if platform not in VENDOR_COMMANDS:
        raise ValueError(f"Platform {platform} not supported. Supported platforms: {', '.join(VENDOR_COMMANDS.keys())}")
    
    if task_name not in VENDOR_COMMANDS[platform]:
        raise ValueError(f"Task {task_name} not found. Available tasks: {', '.join(AVAILABLE_TASKS)}")
    
    return VENDOR_COMMANDS[platform][task_name]