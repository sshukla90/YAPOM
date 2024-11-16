# workers/bgp_analysis.py

from nornir_scrapli.tasks import send_command
import re
import json
from datetime import datetime
import os

def analyze_bgp_summary(task):
    """Analyze BGP summary output"""
    result = task.run(
        task=send_command,
        command="show ip bgp summary"
    )
    
    if result.failed:
        return {"error": str(result.exception)}
        
    output = result.result
    neighbors = {}
    
    # Parse BGP summary
    for line in output.splitlines():
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', line):
            fields = line.split()
            neighbor_ip = fields[0]
            state = fields[-1]
            prefixes = fields[-2] if len(fields) > 2 else "N/A"
            
            neighbors[neighbor_ip] = {
                "state": state,
                "prefixes": prefixes,
                "needs_investigation": not state.isdigit()
            }
    
    return neighbors

def check_bgp_neighbor(task, neighbor_ip):
    """Detailed check of a specific BGP neighbor"""
    commands = [
        f"show ip bgp neighbor {neighbor_ip}",
        f"show ip bgp neighbor {neighbor_ip} advertised-routes",
        f"show ip bgp neighbor {neighbor_ip} received-routes",
        "show ip route bgp"
    ]
    
    neighbor_details = {}
    for command in commands:
        result = task.run(
            task=send_command,
            command=command
        )
        if not result.failed:
            neighbor_details[command] = result.result
    
    return neighbor_details

def run_task(nr, timestamp=None):
    """Main worker function for BGP analysis"""
    analysis_results = {}
    
    for host in nr.inventory.hosts.values():
        print(f"\nAnalyzing BGP on {host.name}...")
        host_results = {
            "summary": None,
            "problem_neighbors": {},
            "routes": None
        }
        
        # Step 1: Get BGP summary
        summary_result = nr.filter(name=host.name).run(
            task=analyze_bgp_summary
        )
        
        if not summary_result[host.name].failed:
            bgp_summary = summary_result[host.name][0]
            host_results["summary"] = bgp_summary
            
            # Step 2: Check problematic neighbors
            for neighbor_ip, info in bgp_summary.items():
                if info.get("needs_investigation"):
                    print(f"  Investigating neighbor {neighbor_ip}...")
                    details = nr.filter(name=host.name).run(
                        task=check_bgp_neighbor,
                        neighbor_ip=neighbor_ip
                    )
                    if not details[host.name].failed:
                        host_results["problem_neighbors"][neighbor_ip] = {
                            "state": info["state"],
                            "details": details[host.name][0]
                        }
        
        analysis_results[host.name] = host_results
    
    # Save results
    if timestamp:
        save_path = f"output/ALL/{timestamp}/worker_bgp_analysis"
        os.makedirs(save_path, exist_ok=True)
        
        with open(f"{save_path}/analysis_results.json", 'w') as f:
            json.dump(analysis_results, f, indent=2)
        
        # Create a readable summary
        with open(f"{save_path}/analysis_summary.txt", 'w') as f:
            f.write("BGP Analysis Summary\n")
            f.write("=" * 50 + "\n\n")
            
            for host, results in analysis_results.items():
                f.write(f"Device: {host}\n")
                f.write("-" * 30 + "\n")
                
                if results["summary"]:
                    f.write("BGP Neighbors:\n")
                    for neighbor, info in results["summary"].items():
                        status = "✓" if not info.get("needs_investigation") else "✗"
                        f.write(f"{status} {neighbor}: {info['state']}\n")
                
                if results["problem_neighbors"]:
                    f.write("\nProblem Neighbors:\n")
                    for neighbor, info in results["problem_neighbors"].items():
                        f.write(f"- {neighbor}: {info['state']}\n")
                
                f.write("\n")
    
    return analysis_results