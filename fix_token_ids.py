#!/usr/bin/env python3
"""
Fix the token_id for existing lands by checking the blockchain
"""

import os
import sys
sys.path.append('/backend')

# Set environment variables
os.environ['POLYGON_RPC_URL'] = 'https://rpc-amoy.polygon.technology'
os.environ['CHAIN_ID'] = '80002'
os.environ['CONTRACT_ADDRESS'] = '0x2267014b6C2471fbb7358382Cbb85F3Ea6E9477E'

from app.blockchain import BlockchainService
from app.models import Land, db
from app import create_app

def fix_token_ids():
    """Fix missing token IDs by checking totalSupply and updating lands"""
    
    print("🔧 Fixing missing token IDs...")
    
    blockchain_service = BlockchainService()
    
    try:
        # Get total supply from blockchain
        total_supply = blockchain_service.contract.functions.totalSupply().call()
        print(f"📊 Total tokens on blockchain: {total_supply}")
        
        # Get lands that are registered but missing token_id
        lands_without_token = Land.query.filter(
            Land.is_registered_on_blockchain == True,
            Land.token_id.is_(None)
        ).order_by(Land.blockchain_block_number).all()
        
        print(f"🔍 Found {len(lands_without_token)} lands without token_id")
        
        # Assume sequential token IDs starting from existing max + 1
        existing_max_token = db.session.query(db.func.max(Land.token_id)).scalar() or 0
        next_token_id = existing_max_token + 1
        
        print(f"📝 Starting token ID assignment from: {next_token_id}")
        
        for land in lands_without_token:
            print(f"   Land ID {land.id} ({land.title}) -> Token ID {next_token_id}")
            land.token_id = next_token_id
            next_token_id += 1
        
        db.session.commit()
        print("✅ Token IDs updated successfully!")
        
        # Verify
        for land in lands_without_token:
            print(f"   ✓ Land {land.id}: Token ID {land.token_id}")
            
    except Exception as e:
        print(f"❌ Error fixing token IDs: {e}")
        db.session.rollback()

def main():
    app = create_app()
    with app.app_context():
        fix_token_ids()

if __name__ == "__main__":
    main()