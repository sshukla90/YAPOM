from nornir_scrapli.tasks import send_commands, send_command
from nornir import InitNornir
from nornir.core.filter import F
from datetime import datetime
from pathlib import Path
import getpass
import argparse
import os
import importlib
from shared.services.mod import get_commands_for_task, AVAILABLE_TASKS, VENDOR_COMMANDS

class Yapom:
    def __init__(
        self, 
        site=None, 
        role=None, 
        devices=None, 
        platform=None,
        login_user=None,
        task=None
    ):
        self.site = site
        self.role = role
        self.devices = devices
        self.platform = platform
        self.login_user = login_user
        self.task = task
        self.output_counter = 0

    def verify_connectivity(self, nr):
        """Verify connectivity to all devices using platform-agnostic approach"""
        print("\nVerifying device connectivity...")
        print("=" * 50)
        
        # Single command execution for all devices
        results = nr.run(
            task=send_command,
            command="show version"
        )
        
        accessible = []
        inaccessible = []
        
        for hostname, result in results.items():
            device = nr.inventory.hosts[hostname]
            if result.failed:
                print(f"✗ {hostname} ({device.hostname})")
                print(f"  Error: {str(result.exception)}")
                inaccessible.append(hostname)
            else:
                # Extract version info based on platform
                version_info = result.result.splitlines()[0] if result.result else "Version info not found"
                print(f"✓ {hostname} ({device.hostname})")
                print(f"  {version_info.strip()}")
                accessible.append(hostname)
        
        print("\nConnectivity Summary")
        print("=" * 50)        
        print(f"Total Devices: {len(nr.inventory.hosts)}")
        print(f"Accessible: {len(accessible)}")
        print(f"Inaccessible: {len(inaccessible)}")
        print("=" * 50 + "\n")
        
        if inaccessible:
            print("Inaccessible Devices:")
            for host in inaccessible:
                print(f"- {host} ({nr.inventory.hosts[host].hostname})")
            print()
        
        return nr.filter(filter_func=lambda h: h.name in accessible)

    def save_output(self, hostname: str, command: str, output: str, timestamp: str) -> None:
        """Save command output to file"""
        try:
            device_dir = f"output/{self.site}/{timestamp}/{hostname}"
            os.makedirs(device_dir, exist_ok=True)
            
            filename = f"{command}.txt"
            
            with open(f"{device_dir}/{filename}", "w") as f:
                f.write(f"Command: {command}\n")
                f.write("=" * 80 + "\n")
                f.write(output)
                f.write("\n" + "=" * 80 + "\n")
            
            self.output_counter += 1
            
        except Exception as e:
            print(f"Error saving output for {hostname}: {e}")

    def execute_commands(self, nr, commands: list, timestamp: str):
        """Execute a list of commands on devices"""
        for command in commands:
            print(f"Running command: {command}")
            result = nr.run(task=send_commands, commands=[command])
            
            for hostname, host_data in result.items():
                try:
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
                    print(f"Error processing result for {hostname}: {str(e)}")

    def execute_task(self, nr, timestamp):
        """Execute tasks based on platform and task type"""
        try:
            if self.task.lower() == 'all':
                tasks_to_run = AVAILABLE_TASKS
            else:
                if self.task not in AVAILABLE_TASKS:
                    print(f"Task '{self.task}' not found. Available tasks: {', '.join(AVAILABLE_TASKS)}")
                    return
                tasks_to_run = [self.task]

            # Group hosts by platform for efficient command execution
            platforms = set(host.platform for host in nr.inventory.hosts.values())
            
            for platform in platforms:
                platform_hosts = nr.filter(platform=platform)
                print(f"\nExecuting commands for {platform} devices:")
                
                for task_name in tasks_to_run:
                    try:
                        commands = get_commands_for_task(task_name, platform)
                        print(f"\nExecuting task: {task_name}")
                        self.execute_commands(platform_hosts, commands, timestamp)
                    except ValueError as e:
                        print(f"Skipping task {task_name} for platform {platform}: {str(e)}")
                    except Exception as e:
                        print(f"Error executing task {task_name} for platform {platform}: {str(e)}")

        except Exception as e:
            print(f"Error executing tasks: {str(e)}")

    def main(self):
        timestamp = "{:%Y-%m-%d_%H-%M}".format(datetime.now())
        nr = InitNornir(
            config_file=((Path(__file__).parent)/"shared/nornir_data/config.yaml").resolve(), 
            core={"raise_on_error": False}
        )
        
        if self.login_user:
            self.login_password = getpass.getpass(prompt="Login Password: ")
            nr.inventory.defaults.username = self.login_user
            nr.inventory.defaults.password = self.login_password

        # Set site and create output directory
        if self.devices:
            self.site = "ALL"
        elif not self.site:
            print("Error: Site parameter is required when not specifying devices")
            exit(1)
        
        self.mkdir_now(timestamp=timestamp)

        # Apply filters
        if self.devices:
            self.devices = [device.upper() for device in self.devices]
            nr = nr.filter(F(hostname__any=self.devices))
        else:  # Using site/role filtering
            if self.platform:
                nr = nr.filter(platform=self.platform.lower())
            
            # Apply site filter
            if self.site != "ALL":
                nr = nr.filter(data__site=self.site)
            
            # Apply role filter if specified
            if self.role and self.role != "ALL":
                nr = nr.filter(data__role=self.role)

        # Show selected devices
        print(f"\nSelected Devices:")
        print("=" * 50)
        for host in nr.inventory.hosts.values():
            print(f"- {host.name} ({host.hostname})")
        print(f"\nNumber of Targeted Hosts: {len(nr.inventory.hosts)}.\n")
        
        if len(nr.inventory.hosts) == 0:
            print("No devices matched the specified criteria. Exiting.")
            exit(1)

        # Verify connectivity
        nr = self.verify_connectivity(nr)
        if len(nr.inventory.hosts) == 0:
            print("No devices are accessible. Exiting.")
            exit(1)

        # Execute tasks
        if self.task:
            self.execute_task(nr, timestamp)

        print(f"\nThe Number of Saved Files: {self.output_counter}")

    def mkdir_now(self, timestamp):
        """Create output directory"""
        location = f"output/{self.site}/{timestamp}"
        try:
            os.makedirs(location)
            print(f"\nThe Output Will Be Saved in: {location}\n")
        except OSError as err:
            print("Encountered the following error when creating an output directory")
            print(err)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='YAPOM - Yet Another Python Output Manager',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  1. Run all tasks for all devices:
     %(prog)s -t all -s ALL -pu admin

  2. Run specific task for all devices:
     %(prog)s -t basic_info -s ALL -pu admin

  3. Run task for specific devices:
     %(prog)s -t basic_info -d device1 device2 -pu admin

  4. Run task for specific site (all roles):
     %(prog)s -t basic_info -s NYC -pu admin

  5. Run task for specific site and role:
     %(prog)s -t basic_info -s NYC -r edge -pu admin

Available Tasks:
  {', '.join(AVAILABLE_TASKS)}
  all - Run all tasks

Supported Platforms:
  {', '.join(VENDOR_COMMANDS.keys())}
        """
    )
    
    # Required arguments
    parser.add_argument('-t', '--task', 
                       help='Task to execute', 
                       required=True,
                       choices=list(AVAILABLE_TASKS) + ['all'])
    
    parser.add_argument('-pu', '--login_user', 
                       help='Login username', 
                       required=True)

    # Device targeting group (mutually exclusive)
    device_group = parser.add_mutually_exclusive_group()
    
    device_group.add_argument('-d', '--devices', 
                            nargs='+', 
                            help='Specific devices')
    
    device_group.add_argument('-s', '--site', 
                            help='Site name (use ALL for all sites)')
    
    # Optional arguments
    parser.add_argument('-r', '--role', 
                       help='Role filter (only used with -s)')
    
    parser.add_argument('-p', '--platform', 
                       choices=list(VENDOR_COMMANDS.keys()), 
                       help='Device platform filter')
    
    args = parser.parse_args()

    # Validate argument combinations
    if not args.devices and not args.site:
        parser.error("Either -d (devices) or -s (site) must be specified")

    if args.devices and (args.site or args.role):
        parser.error("Cannot combine -d with -s or -r")

    if args.role and not args.site:
        parser.error("-r (role) requires -s (site)")

    # Convert to upper case where needed
    if args.site:
        args.site = args.site.upper()
    if args.role:
        args.role = args.role.upper()

    yapom_tasks = Yapom(
        site=args.site,
        role=args.role,
        devices=args.devices,
        platform=args.platform,
        login_user=args.login_user,
        task=args.task
    )
    yapom_tasks.main()