# workers/ospf_analysis.py

from nornir_scrapli.tasks import send_command
import re
import json
import os
from datetime import datetime

def analyze_ospf_neighbors(task):
    """Analyze OSPF neighbor states"""
    result = task.run(
        task=send_command,
        command="show ip ospf neighbor"
    )
    
    if result.failed:
        return {"error": str(result.exception)}
        
    output = result.result
    neighbors = {}
    
    # Parse OSPF neighbors
    for line in output.splitlines():
        match = re.search(r'(\d+\.\d+\.\d+\.\d+)\s+\d+\s+(\w+/\w+)\s+(\w+)', line)
        if match:
            neighbor_ip = match.group(1)
            state = match.group(3)
            interface = match.group(2)
            
            neighbors[neighbor_ip] = {
                "state": state,
                "interface": interface,
                "needs_investigation": state != "FULL"
            }
    
    return neighbors

def check_ospf_interface(task, interface):
    """Check OSPF interface details"""
    commands = [
        f"show ip ospf interface {interface}",
        f"show interface {interface}",
        f"show ip route ospf"
    ]
    
    interface_details = {}
    for command in commands:
        result = task.run(
            task=send_command,
            command=command
        )
        if not result.failed:
            interface_details[command] = result.result
    
    return interface_details

def run_task(nr, timestamp=None):
    """Main worker function for OSPF analysis"""
    analysis_results = {}
    
    for host in nr.inventory.hosts.values():
        print(f"\nAnalyzing OSPF on {host.name}...")
        host_results = {
            "neighbors": None,
            "problem_interfaces": {},
            "routes": None
        }
        
        # Step 1: Get OSPF neighbors
        neighbor_result = nr.filter(name=host.name).run(
            task=analyze_ospf_neighbors
        )
        
        if not neighbor_result[host.name].failed:
            ospf_neighbors = neighbor_result[host.name][0]
            host_results["neighbors"] = ospf_neighbors
            
            # Step 2: Check problematic interfaces
            checked_interfaces = set()
            for neighbor_ip, info in ospf_neighbors.items():
                interface = info["interface"]
                if info.get("needs_investigation") and interface not in checked_interfaces:
                    print(f"  Investigating interface {interface}...")
                    details = nr.filter(name=host.name).run(
                        task=check_ospf_interface,
                        interface=interface
                    )
                    if not details[host.name].failed:
                        host_results["problem_interfaces"][interface] = {
                            "neighbor_ips": [n for n, i in ospf_neighbors.items() if i["interface"] == interface],
                            "details": details[host.name][0]
                        }
                    checked_interfaces.add(interface)
        
        analysis_results[host.name] = host_results
    
    # Save results
    if timestamp:
        save_path = f"output/ALL/{timestamp}/worker_ospf_analysis"
        os.makedirs(save_path, exist_ok=True)
        
        with open(f"{save_path}/analysis_results.json", 'w') as f:
            json.dump(analysis_results, f, indent=2)
        
        # Create a readable summary
        with open(f"{save_path}/analysis_summary.txt", 'w') as f:
            f.write("OSPF Analysis Summary\n")
            f.write("=" * 50 + "\n\n")
            
            for host, results in analysis_results.items():
                f.write(f"Device: {host}\n")
                f.write("-" * 30 + "\n")
                
                if results["neighbors"]:
                    f.write("OSPF Neighbors:\n")
                    for neighbor, info in results["neighbors"].items():
                        status = "✓" if not info.get("needs_investigation") else "✗"
                        f.write(f"{status} {neighbor} ({info['interface']}): {info['state']}\n")
                
                if results["problem_interfaces"]:
                    f.write("\nProblem Interfaces:\n")
                    for interface, info in results["problem_interfaces"].items():
                        f.write(f"- {interface}: {', '.join(info['neighbor_ips'])}\n")
                
                f.write("\n")
    
    return analysis_results