from enum import Enum
class TaskType(Enum):
    COMMAND = "command"    # Simple command execution
    WORKER = "worker"      # Complex analysis/troubleshooting

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

# Define both command-based and worker-based tasks
TASK_DEFINITIONS = {
    # Command-based tasks
    "basic_info": {
        "type": TaskType.COMMAND,
        "description": "Basic device information"
    },
    "interface_info": {
        "type": TaskType.COMMAND,
        "description": "Interface status and configuration"
    },
    "routing_info": {
        "type": TaskType.COMMAND,
        "description": "Routing protocol information"
    },
    "system_health": {
        "type": TaskType.COMMAND,
        "description": "System health and resources"
    },
    # Worker-based tasks
    "tshoot_bgp": {
        "type": TaskType.WORKER,
        "description": "BGP troubleshooting workflow",
        "worker": "bgp_analysis"
    },
    "analyze_ospf": {
        "type": TaskType.WORKER,
        "description": "OSPF analysis and verification",
        "worker": "ospf_analysis"
    }
}

# List of available tasks
AVAILABLE_TASKS = list(TASK_DEFINITIONS.keys())

def get_task_type(task_name: str) -> TaskType:
    """Get the type of task (command or worker)"""
    if task_name not in TASK_DEFINITIONS:
        raise ValueError(f"Task {task_name} not found")
    return TASK_DEFINITIONS[task_name]["type"]

def get_worker_module(task_name: str) -> str:
    """Get the worker module name for worker-based tasks"""
    if (task_name not in TASK_DEFINITIONS or 
        TASK_DEFINITIONS[task_name]["type"] != TaskType.WORKER):
        raise ValueError(f"No worker defined for task {task_name}")
    return TASK_DEFINITIONS[task_name]["worker"]

def get_commands_for_task(task_name: str, platform: str) -> list:
    """Get commands for a command-based task and platform"""
    if get_task_type(task_name) != TaskType.COMMAND:
        raise ValueError(f"Task {task_name} is not a command-based task")
        
    platform = platform.lower()
    if platform not in VENDOR_COMMANDS:
        raise ValueError(f"Platform {platform} not supported")
    
    if task_name not in VENDOR_COMMANDS[platform]:
        raise ValueError(f"Task {task_name} not found for platform {platform}")
    
    return VENDOR_COMMANDS[platform][task_name]