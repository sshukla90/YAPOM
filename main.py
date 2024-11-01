# main.py
from nornir_scrapli.tasks import send_commands
from nornir import InitNornir
from nornir.core.filter import F
from datetime import datetime
from pathlib import Path
import os
import importlib
from dotenv import load_dotenv
from typing import Any, Dict, List, Optional
import argparse
import sys

class Yapom:
    def __init__(
        self, 
        site=None, 
        role=None, 
        devices=None, 
        platform=None,
        task=None
    ):
        self.site = site
        self.role = role
        self.devices = devices
        self.platform = platform
        self.task = task
        self.output_counter = 0
        
        # Load environment variables
        load_dotenv()
        self.login_user = os.getenv('NETWORK_USER')
        self.login_password = os.getenv('NETWORK_PASSWORD')

    def main(self):
        timestamp = "{:%Y-%m-%d_%H-%M}".format(datetime.now())
        nr = InitNornir(
            config_file=((Path(__file__).parent)/"shared/nornir_data/config.yaml").resolve(), 
            core={"raise_on_error": True}
        )
        
        # Set credentials from environment variables
        if self.login_user and self.login_password:
            nr.inventory.defaults.username = self.login_user
            nr.inventory.defaults.password = self.login_password
        else:
            print("Error: Network credentials not found in environment variables")
            exit(1)

        if self.devices:
            self.site = "ALL"
            self.mkdir_now(timestamp=timestamp)
            self.devices = [device.upper() for device in self.devices]
            nr = nr.filter(F(hostname__any=self.devices))
        else:
            self.site = "ALL"
            self.mkdir_now(timestamp=timestamp)

        print(f"Number of Targeted Hosts: {len(nr.inventory.hosts)}.\n")
        
        if self.task:
            self.execute_task(nr, timestamp)

        print(f"The Number of Saved Files: {self.output_counter}\n")

    def mkdir_now(self, timestamp: str) -> None:
        location = f"output/{self.site}/{timestamp}"
        try:
            os.makedirs(location)
            print(f"\nThe Output Will Be Saved in: {location}\n")
        except OSError as err:
            print("Encountered the following error when creating an output directory")
            print(err)

    def save_output(self, hostname: str, command: str, output: str, timestamp: str) -> None:
        try:
            device_dir = f"output/{self.site}/{timestamp}/{hostname}"
            os.makedirs(device_dir, exist_ok=True)
            
            # Use exact command for filename
            filename = f"{command}.txt"
            
            with open(f"{device_dir}/{filename}", "w") as f:
                f.write(f"Command: {command}\n")
                f.write("=" * 80 + "\n")
                f.write(output)
                f.write("\n" + "=" * 80 + "\n")
            
            self.output_counter += 1
            
        except Exception as e:
            print(f"Error saving output for {hostname}: {e}")
            raise

    def execute_task(self, nr, timestamp: str) -> None:
        try:
            mod = importlib.import_module('shared.services.mod')
            available_tasks = getattr(mod, 'AVAILABLE_TASKS', {})
            
            if not available_tasks:
                print("No tasks defined in mod.py")
                return

            if self.task.lower() == 'all':
                tasks_to_run = available_tasks
            else:
                tasks_to_run = {self.task: available_tasks.get(self.task)}
                if not tasks_to_run[self.task]:
                    print(f"Task '{self.task}' not found in mod.py")
                    return

            for task_name, commands in tasks_to_run.items():
                if commands:
                    print(f"Executing task: {task_name}")
                    try:
                        for command in commands:
                            print(f"Running command: {command}")
                            result = nr.run(
                                task=send_commands,
                                commands=[command]
                            )
                            
                            for hostname, host_data in result.items():
                                if host_data.failed:
                                    error_msg = f"Error executing command:\n{str(host_data.exception)}"
                                    self.save_output(
                                        hostname=str(hostname),
                                        command=command,
                                        output=error_msg,
                                        timestamp=timestamp
                                    )
                                else:
                                    command_output = host_data.result
                                    if isinstance(command_output, dict):
                                        command_output = command_output.get(command, "No output")
                                    elif isinstance(command_output, list):
                                        command_output = command_output[0] if command_output else "No output"
                                    
                                    self.save_output(
                                        hostname=str(hostname),
                                        command=command,
                                        output=str(command_output),
                                        timestamp=timestamp
                                    )

                    except Exception as e:
                        print(f"Error executing command '{command}': {str(e)}")
                else:
                    print(f"No commands defined for task: {task_name}")

        except ModuleNotFoundError:
            print("Error: mod.py not found in the shared/services directory")
        except Exception as e:
            print(f"Error executing tasks: {str(e)}")

def validate_task(task: str) -> str:
    """Validate if the task exists in mod.py"""
    try:
        mod = importlib.import_module('shared.services.mod')
        available_tasks = getattr(mod, 'AVAILABLE_TASKS', {})
        
        if task.lower() == 'all':
            return task
        
        if task not in available_tasks:
            tasks_list = list(available_tasks.keys())
            raise argparse.ArgumentTypeError(
                f"Invalid task: {task}\nAvailable tasks: {', '.join(tasks_list)} or 'all'"
            )
        return task
    except ModuleNotFoundError:
        raise argparse.ArgumentTypeError("Could not load tasks from mod.py")

def validate_site(site: str) -> str:
    """Validate site name"""
    valid_sites = {'AUS', 'IND', 'ALL'}  # Add your valid sites here
    if site and site.upper() not in valid_sites:
        raise argparse.ArgumentTypeError(
            f"Invalid site. Available sites: {', '.join(valid_sites)}"
        )
    return site.upper() if site else site

def validate_role(role: str) -> str:
    """Validate role name"""
    valid_roles = {'edge', 'ISP', 'ALL'}  # Add your valid roles here
    if role and role.upper() not in valid_roles:
        raise argparse.ArgumentTypeError(
            f"Invalid role. Available roles: {', '.join(valid_roles)}"
        )
    return role.upper() if role else role

def setup_argparse() -> argparse.ArgumentParser:
    """Setup argument parser with improved help and validation"""
    parser = argparse.ArgumentParser(
        description='YAPOM - Network Device Command Management Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Run all tasks:
    %(prog)s -t all
  
  Run specific task for specific devices:
    %(prog)s -t basic_info -d device1 device2
  
  Run task for a specific site and role:
    %(prog)s -t interface_info -s AUS -r edge
    
Available Tasks:
  basic_info     - Basic device information
  interface_info - Interface status and configuration
  routing_info   - Routing protocols and tables
  system_health  - System resource utilization
  all            - Run all available tasks
        """
    )

    parser.add_argument(
        '-s', '--site',
        help='Site name (e.g., AUS, IND, ALL)',
        type=validate_site
    )
    
    parser.add_argument(
        '-r', '--role',
        help='Role of the devices (e.g., edge, ISP, ALL)',
        type=validate_role
    )
    
    parser.add_argument(
        '-d', '--devices',
        nargs='+',
        help='One or more device hostnames'
    )
    
    parser.add_argument(
        '-p', '--platform',
        choices=['ios', 'nxos', 'iosxr'],
        help='Device platform type'
    )
    
    parser.add_argument(
        '-t', '--task',
        help='Task to execute (use "all" for all tasks)',
        required=True,
        type=validate_task
    )

    return parser

def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse and validate command line arguments"""
    parser = setup_argparse()
    parsed_args = parser.parse_args(args)
    
    if parsed_args.devices and (parsed_args.site or parsed_args.role):
        parser.error("Cannot combine --devices with --site or --role")
    
    if bool(parsed_args.site) != bool(parsed_args.role):
        parser.error("--site and --role must be used together")
        
    return parsed_args

if __name__ == "__main__":
    try:
        args = parse_args()
        
        yapom_tasks = Yapom(
            site=args.site,
            role=args.role,
            devices=args.devices,
            platform=args.platform,
            task=args.task
        )
        yapom_tasks.main()
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)