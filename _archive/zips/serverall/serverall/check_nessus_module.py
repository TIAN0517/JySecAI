#!/usr/bin/env python3
import nessus_integration

print("Available attributes in nessus_integration:")
for attr in dir(nessus_integration):
    if not attr.startswith('_'):
        print(f"  {attr}")

# Check if nessus_integrations exists
if hasattr(nessus_integration, 'nessus_integrations'):
    print("\nnessus_integrations exists:")
    print(nessus_integration.nessus_integrations)
else:
    print("\nnessus_integrations does not exist")