#!/usr/bin/env python3
"""
Test the approval checking functionality directly
"""

import os
import sys
sys.path.append('/backend')

# Set environment variables for testing
os.environ['POLYGON_RPC_URL'] = 'https://rpc-amoy.polygon.technology'
os.environ['CHAIN_ID'] = '80002'
os.environ['CONTRACT_ADDRESS'] = '0x2267014b6C2471fbb7358382Cbb85F3Ea6E9477E'

from app.blockchain import BlockchainService

def test_approval_checking():
    print("🔧 Testing approval checking functionality...")
    
    blockchain_service = BlockchainService()
    
    # Test token 2 (should be owned by demo_user)
    token_id = 2
    owner_address = "0x8ba1f109551bD432803012645aac136c73c0d1b1"
    
    print(f"Checking approval for token {token_id}")
    print(f"Owner address: {owner_address}")
    
    result = blockchain_service.check_transfer_approval(token_id, owner_address)
    
    print(f"Result: {result}")
    
    if result.get('can_transfer'):
        print(f"✅ Can transfer! Reason: {result.get('reason')}")
    else:
        print(f"❌ Cannot transfer. Reason: {result.get('reason')}")
        if result.get('needs_approval'):
            backend_addr = result.get('backend_address')
            print(f"💡 Solution: Owner needs to approve {backend_addr}")

if __name__ == "__main__":
    test_approval_checking()