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
        """Verify connectivity to all devices"""
        print("\nVerifying device connectivity...")
        print("=" * 50)
        
        # Use appropriate command based on platform
        results = {}
        for hostname, host in nr.inventory.hosts.items():
            platform = host.platform.lower()
            if platform in ['ios', 'nxos', 'eos']:
                command = "show version | include Version"
            elif platform == 'junos':
                command = "show version | match Junos:"
            else:
                print(f"Warning: Unknown platform {platform} for host {hostname}")
                command = "show version"
                
            result = nr.filter(name=hostname).run(task=send_command, command=command)
            results.update(result)
        
        accessible = []
        inaccessible = []
        
        for hostname, result in results.items():
            device = nr.inventory.hosts[hostname]
            if result.failed:
                print(f"✗ {hostname} ({device.hostname})")
                print(f"  Error: {str(result.exception)}")
                inaccessible.append(hostname)
            else:
                print(f"✓ {hostname} ({device.hostname})")
                print(f"  {result.result.strip()}")
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

        if self.devices is None and (self.site is None or self.role is None):
            print("Please specify the targeted devices or filter groups of devices by site and role")
            exit()

        elif self.devices:
            self.site = "ALL"
            self.mkdir_now(timestamp=timestamp)
            self.devices = [device.upper() for device in self.devices]
            nr = nr.filter(F(hostname__any=self.devices))

        elif self.site and self.role:
            self.site = self.site.upper()
            self.role = self.role.upper()
            self.mkdir_now(timestamp=timestamp)

            if self.platform:
                nr = nr.filter(platform=self.platform.lower())

            if self.site != "ALL" and self.role != "ALL":
                nr = nr.filter(F(data__site=self.site) & F(data__role=self.role))
            elif self.site != "ALL":
                nr = nr.filter(data__site=self.site)
            elif self.role != "ALL":
                nr = nr.filter(data__role=self.role)

        print(f"Number of Targeted Hosts: {len(nr.inventory.hosts)}.\n")
        
        # Verify connectivity first
        nr = self.verify_connectivity(nr)
        if len(nr.inventory.hosts) == 0:
            print("No devices are accessible. Exiting.")
            exit()

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
Available Tasks:
  {', '.join(AVAILABLE_TASKS)}
  all - Run all tasks

Supported Platforms:
  {', '.join(VENDOR_COMMANDS.keys())}

Examples:
  Run all tasks:
    %(prog)s -t all -pu admin
  
  Run specific task for specific devices:
    %(prog)s -t basic_info -d device1 device2 -pu admin
  
  Run task for a specific site and role:
    %(prog)s -t interface_info -s AUS -r edge -pu admin
        """
    )
    
    parser.add_argument('-s', '--site', help='Site name', required=False)
    parser.add_argument('-r', '--role', help='Role of the devices', required=False)
    parser.add_argument('-d', '--devices', nargs='+', help='Specific devices', required=False)
    parser.add_argument('-p', '--platform', choices=list(VENDOR_COMMANDS.keys()), help='Device platform', required=False)
    parser.add_argument('-pu', '--login_user', help='Login username', required=True)
    parser.add_argument('-t', '--task', help='Task to execute', required=True)
    
    args = parser.parse_args()

    yapom_tasks = Yapom(
        site=args.site,
        role=args.role,
        devices=args.devices,
        platform=args.platform,
        login_user=args.login_user,
        task=args.task
    )
    yapom_tasks.main()