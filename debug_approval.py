#!/usr/bin/env python3
"""
Debug script to test the land approval and blockchain registration process
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

# Add current directory to path
sys.path.append('.')

from app import create_app
from app.models import Land, User, db
from app.blockchain import blockchain_service

def debug_land_approval():
    """Debug the land approval process"""
    
    app = create_app()
    with app.app_context():
        print("=== Debug Land Approval Process ===")
        
        # Get all lands
        all_lands = Land.query.all()
        verified_lands = Land.query.filter_by(status='verified').all()
        blockchain_lands = Land.query.filter_by(is_registered_on_blockchain=True).all()
        
        print(f"📊 Current Status:")
        print(f"  - Total lands: {len(all_lands)}")
        print(f"  - Verified lands: {len(verified_lands)}")
        print(f"  - Blockchain registered: {len(blockchain_lands)}")
        
        print(f"\n📋 Land Details:")
        for land in all_lands:
            owner = User.query.get(land.owner_id)
            blockchain_status = "✅ On blockchain" if land.is_registered_on_blockchain else "❌ Not on blockchain"
            wallet_status = f"Wallet: {owner.wallet_address}" if owner and owner.wallet_address else "❌ No wallet"
            
            print(f"  Land {land.id}: {land.title}")
            print(f"    - Property ID: {land.property_id}")
            print(f"    - Status: {land.status}")
            print(f"    - Owner: {owner.username if owner else 'Unknown'}")
            print(f"    - {wallet_status}")
            print(f"    - {blockchain_status}")
            if land.token_id:
                print(f"    - Token ID: {land.token_id}")
            print()
        
        # Check blockchain connection
        print(f"🔗 Blockchain Status:")
        if blockchain_service.is_connected():
            print(f"  ✅ Connected to blockchain")
            total_supply = blockchain_service.get_total_supply()
            print(f"  📊 Total blockchain lands: {total_supply}")
        else:
            print(f"  ❌ Not connected to blockchain")
            return
        
        # Find unregistered verified lands
        unregistered_verified = Land.query.filter_by(
            status='verified',
            is_registered_on_blockchain=False
        ).all()
        
        if unregistered_verified:
            print(f"\n⚠️  Found {len(unregistered_verified)} verified lands NOT on blockchain:")
            
            for land in unregistered_verified:
                owner = User.query.get(land.owner_id)
                print(f"\n🔍 Analyzing Land {land.id}: {land.title}")
                print(f"  - Property ID: {land.property_id}")
                print(f"  - Owner: {owner.username if owner else 'Unknown'}")
                
                if not owner:
                    print(f"  ❌ ISSUE: No owner found!")
                    continue
                
                if not owner.wallet_address:
                    print(f"  ❌ ISSUE: Owner has no wallet address!")
                    continue
                
                print(f"  - Wallet: {owner.wallet_address}")
                print(f"  ✅ Ready for blockchain registration")
                
                # Test blockchain registration
                print(f"  🧪 Testing blockchain registration...")
                
                try:
                    land_data = {
                        'property_id': land.property_id,
                        'owner_wallet': owner.wallet_address,
                        'location': land.location,
                        'area': land.area,
                        'property_type': land.property_type,
                        'latitude': land.latitude or 0.0,
                        'longitude': land.longitude or 0.0,
                        'ipfs_hash': ''
                    }
                    
                    print(f"  📋 Land data prepared:")
                    for key, value in land_data.items():
                        print(f"    - {key}: {value}")
                    
                    # Simulate registration (uncomment next lines to actually register)
                    # result = blockchain_service.register_land_on_blockchain(land_data)
                    # if result:
                    #     print(f"  ✅ Would register with token ID: {result.get('token_id')}")
                    # else:
                    #     print(f"  ❌ Registration would fail")
                    
                except Exception as e:
                    print(f"  ❌ ERROR: {str(e)}")
        else:
            print(f"\n✅ All verified lands are registered on blockchain!")

def test_approval_function():
    """Test the approval function directly"""
    
    app = create_app()
    with app.app_context():
        print("\n=== Test Approval Function ===")
        
        # Find a verified land that's not on blockchain
        unregistered_land = Land.query.filter_by(
            status='verified',
            is_registered_on_blockchain=False
        ).first()
        
        if not unregistered_land:
            print("No unregistered verified lands found to test")
            return
        
        print(f"Testing with land: {unregistered_land.title}")
        
        # Import the admin functions
        from app.admin import review_land
        from flask import request
        import json
        
        # This would simulate the approval process
        # Note: This is a simplified test - actual Flask request context needed
        print("Note: Full testing requires Flask request context")
        print("The approval function should automatically register on blockchain")

if __name__ == "__main__":
    debug_land_approval()
    test_approval_function()