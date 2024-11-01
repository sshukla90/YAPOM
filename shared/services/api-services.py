from nornir_scrapli.tasks import send_commands
from nornir import InitNornir
from nornir.core.filter import F
from datetime import datetime
from pathlib import Path
import getpass
import argparse
import os
import json
import importlib

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

    def main(self):
        timestamp = "{:%Y-%m-%d_%H-%M}".format(datetime.now())
        nr = InitNornir(
            config_file=((Path(__file__).parent)/"nornir_data/config.yaml").resolve(), core={"raise_on_error": True})
        
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
                nr = nr.filter(site=self.site, role=self.role)

            elif self.site != "ALL":
                nr = nr.filter(site=self.site)

            elif self.role != "ALL":
                nr = nr.filter(role=self.role)

        print(f"Number of Targeted Hosts: {len(nr.inventory.hosts)}.\n")
        
        # Dynamically execute task based on user input
        if self.task:
            self.execute_task(nr, timestamp)

        print(f"The Number of Saved Files: {self.output_counter}\n")

    def mkdir_now(self, timestamp):
        location = f"output/{self.site}/{timestamp}"
        try:
            os.makedirs(location)
            print(f"\nThe Output Will Be Saved in: {location}\n")
        except OSError as err:
            print("Encountered the following error when creating an output directory")
            print(err)

    def save_json(self, task, result, filename, timestamp):
        with open(f"output/{self.site}/{timestamp}/{filename}", "w") as f:
            json.dump(result, f, indent=2)
        self.output_counter += 1

    def execute_task(self, nr, timestamp):
        task_module_name = f"tasks.{self.task.replace('-', '_')}"
        try:
            task_module = importlib.import_module(task_module_name)
            task_function = getattr(task_module, 'run_task', None)
            if task_function:
                print(f"Executing task: {self.task}")
                result = task_function(nr)
                self.save_json(None, result, f"{self.task}.json", timestamp)
            else:
                print(f"Task '{self.task}' does not have a 'run_task' function.")
        except ModuleNotFoundError:
            print(f"Task '{self.task}' not found in the tasks directory.")
        except Exception as e:
            print(f"Error executing task '{self.task}': {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--site', help='Site name', required=False)
    parser.add_argument('-r', '--role', help='Role of the devices', required=False)
    parser.add_argument('-d', '--devices', nargs='+', help='Specific devices', required=False)
    parser.add_argument('-p', '--platform', help='Device platform', required=False)
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
