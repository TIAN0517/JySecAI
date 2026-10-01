#!/usr/bin/env python3
import nessus_integration

print("nessus_servers_config:")
if hasattr(nessus_integration, 'nessus_servers_config'):
    print(nessus_integration.nessus_servers_config)
else:
    print("nessus_servers_config not found")

print("\nNessusManager class:")
if hasattr(nessus_integration, 'NessusManager'):
    print("Found NessusManager class")
else:
    print("NessusManager class not found")