#!/usr/bin/env python3
"""
Blockchain Sync Utility
This script syncs the database with the blockchain to ensure data consistency.
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

def register_verified_lands_on_blockchain():
    """Register all verified lands that aren't yet on blockchain"""
    
    app = create_app()
    with app.app_context():
        print("=== Register Verified Lands on Blockchain ===")
        
        # Check blockchain connection
        if not blockchain_service.is_connected():
            print("❌ Error: Cannot connect to blockchain")
            return False
        
        # Get verified lands that aren't on blockchain
        unregistered_lands = Land.query.filter_by(
            status='verified',
            is_registered_on_blockchain=False
        ).all()
        
        print(f"📊 Found {len(unregistered_lands)} verified lands not on blockchain")
        
        if not unregistered_lands:
            print("✅ All verified lands are already registered on blockchain!")
            return True
        
        registered_count = 0
        failed_count = 0
        
        for land in unregistered_lands:
            print(f"\n🔄 Processing land: {land.title} (ID: {land.id})")
            
            # Get owner
            owner = User.query.get(land.owner_id)
            if not owner:
                print(f"  ❌ Error: Owner not found for land {land.id}")
                failed_count += 1
                continue
            
            if not owner.wallet_address:
                print(f"  ⚠️  Warning: Owner {owner.username} has no wallet address")
                failed_count += 1
                continue
            
            try:
                # Prepare land data for blockchain registration
                land_data = {
                    'property_id': land.property_id,
                    'owner_wallet': owner.wallet_address,
                    'location': land.location,
                    'area': land.area,
                    'property_type': land.property_type,
                    'latitude': land.latitude or 0.0,
                    'longitude': land.longitude or 0.0,
                    'ipfs_hash': ''  # Add IPFS hash if available
                }
                
                print(f"  📋 Registering: {land.property_id} for {owner.wallet_address}")
                
                # Register on blockchain
                result = blockchain_service.register_land_on_blockchain(land_data)
                
                if result:
                    # Update land with blockchain information
                    land.token_id = result.get('token_id')
                    land.blockchain_tx_hash = result.get('tx_hash')
                    land.is_registered_on_blockchain = True
                    land.blockchain_block_number = result.get('block_number')
                    
                    db.session.commit()
                    registered_count += 1
                    
                    print(f"  ✅ Success! Token ID: {result.get('token_id')}")
                    print(f"     TX Hash: {result.get('tx_hash')}")
                else:
                    print(f"  ❌ Failed to register on blockchain")
                    failed_count += 1
                    
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                failed_count += 1
        
        print(f"\n📊 Registration Summary:")
        print(f"  - Successfully registered: {registered_count}")
        print(f"  - Failed registrations: {failed_count}")
        print(f"  - Total processed: {len(unregistered_lands)}")
        
        if registered_count > 0:
            print("\n✅ Blockchain registration completed!")
        else:
            print("\n⚠️  No lands were successfully registered on blockchain")
        
        return registered_count > 0

def sync_database_with_blockchain():
    """Sync database lands with blockchain registrations"""
    
    app = create_app()
    with app.app_context():
        print("=== Blockchain Database Sync ===")
        
        # Check blockchain connection
        if not blockchain_service.is_connected():
            print("❌ Error: Cannot connect to blockchain")
            return False
        
        # Get total supply from blockchain
        total_supply = blockchain_service.get_total_supply()
        print(f"📊 Total lands on blockchain: {total_supply}")
        
        # Get all lands from database
        db_lands = Land.query.all()
        print(f"📊 Total lands in database: {len(db_lands)}")
        
        updated_count = 0
        
        # Check each blockchain token
        for token_id in range(1, total_supply + 1):
            print(f"\n🔍 Checking token ID {token_id}...")
            
            # Get land details from blockchain
            blockchain_land = blockchain_service.get_land_details_from_blockchain(token_id)
            
            if blockchain_land:
                property_id = blockchain_land['property_id']
                owner_address = blockchain_land['owner']
                
                print(f"  📋 Property ID: {property_id}")
                print(f"  👤 Owner: {owner_address}")
                
                # Try to find matching land in database by property_id
                db_land = Land.query.filter_by(property_id=property_id).first()
                
                if db_land:
                    # Update database land with blockchain info
                    if not db_land.is_registered_on_blockchain:
                        db_land.is_registered_on_blockchain = True
                        db_land.token_id = token_id
                        db_land.blockchain_tx_hash = "synced_manually"  # You can update this with actual tx hash if available
                        
                        db.session.commit()
                        updated_count += 1
                        print(f"  ✅ Updated land '{db_land.title}' - marked as registered on blockchain")
                    else:
                        print(f"  ℹ️  Land '{db_land.title}' already marked as registered")
                else:
                    print(f"  ⚠️  No matching land found in database for property ID: {property_id}")
                    print(f"      Consider creating a new database entry or checking property ID mapping")
            else:
                print(f"  ❌ Could not retrieve details for token ID {token_id}")
        
        print(f"\n📊 Sync Summary:")
        print(f"  - Blockchain lands: {total_supply}")
        print(f"  - Database lands: {len(db_lands)}")
        print(f"  - Updated records: {updated_count}")
        
        # Show final status
        blockchain_marked = Land.query.filter_by(is_registered_on_blockchain=True).count()
        print(f"  - Database lands marked as blockchain-registered: {blockchain_marked}")
        
        if blockchain_marked == total_supply:
            print("\n✅ Database and blockchain are now in sync!")
        else:
            print(f"\n⚠️  Sync incomplete. {total_supply - blockchain_marked} lands still need attention.")
        
        return True
    """Sync database lands with blockchain registrations"""
    
    app = create_app()
    with app.app_context():
        print("=== Blockchain Database Sync ===")
        
        # Check blockchain connection
        if not blockchain_service.is_connected():
            print("❌ Error: Cannot connect to blockchain")
            return False
        
        # Get total supply from blockchain
        total_supply = blockchain_service.get_total_supply()
        print(f"📊 Total lands on blockchain: {total_supply}")
        
        # Get all lands from database
        db_lands = Land.query.all()
        print(f"📊 Total lands in database: {len(db_lands)}")
        
        updated_count = 0
        
        # Check each blockchain token
        for token_id in range(1, total_supply + 1):
            print(f"\n🔍 Checking token ID {token_id}...")
            
            # Get land details from blockchain
            blockchain_land = blockchain_service.get_land_details_from_blockchain(token_id)
            
            if blockchain_land:
                property_id = blockchain_land['property_id']
                owner_address = blockchain_land['owner']
                
                print(f"  📋 Property ID: {property_id}")
                print(f"  👤 Owner: {owner_address}")
                
                # Try to find matching land in database by property_id
                db_land = Land.query.filter_by(property_id=property_id).first()
                
                if db_land:
                    # Update database land with blockchain info
                    if not db_land.is_registered_on_blockchain:
                        db_land.is_registered_on_blockchain = True
                        db_land.token_id = token_id
                        db_land.blockchain_tx_hash = "synced_manually"  # You can update this with actual tx hash if available
                        
                        db.session.commit()
                        updated_count += 1
                        print(f"  ✅ Updated land '{db_land.title}' - marked as registered on blockchain")
                    else:
                        print(f"  ℹ️  Land '{db_land.title}' already marked as registered")
                else:
                    print(f"  ⚠️  No matching land found in database for property ID: {property_id}")
                    print(f"      Consider creating a new database entry or checking property ID mapping")
            else:
                print(f"  ❌ Could not retrieve details for token ID {token_id}")
        
        print(f"\n📊 Sync Summary:")
        print(f"  - Blockchain lands: {total_supply}")
        print(f"  - Database lands: {len(db_lands)}")
        print(f"  - Updated records: {updated_count}")
        
        # Show final status
        blockchain_marked = Land.query.filter_by(is_registered_on_blockchain=True).count()
        print(f"  - Database lands marked as blockchain-registered: {blockchain_marked}")
        
        if blockchain_marked == total_supply:
            print("\n✅ Database and blockchain are now in sync!")
        else:
            print(f"\n⚠️  Sync incomplete. {total_supply - blockchain_marked} lands still need attention.")
        
        return True

def show_blockchain_vs_database():
    """Show comparison between blockchain and database"""
    
    app = create_app()
    with app.app_context():
        print("=== Blockchain vs Database Comparison ===")
        
        # Blockchain data
        if blockchain_service.is_connected():
            total_supply = blockchain_service.get_total_supply()
            print(f"\n🔗 Blockchain Status:")
            print(f"  - Total lands: {total_supply}")
            
            for token_id in range(1, total_supply + 1):
                land = blockchain_service.get_land_details_from_blockchain(token_id)
                if land:
                    print(f"  - Token {token_id}: {land['property_id']} - {land['location']}")
        
        # Database data
        db_lands = Land.query.all()
        blockchain_lands = Land.query.filter_by(is_registered_on_blockchain=True).count()
        
        print(f"\n💾 Database Status:")
        print(f"  - Total lands: {len(db_lands)}")
        print(f"  - Marked as blockchain-registered: {blockchain_lands}")
        
        for land in db_lands:
            status = "✅ On blockchain" if land.is_registered_on_blockchain else "❌ Not on blockchain"
            token_info = f"(Token: {land.token_id})" if land.token_id else "(No token)"
            print(f"  - {land.property_id}: {land.title} - {status} {token_info}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Blockchain Database Sync Utility")
    parser.add_argument("--sync", action="store_true", help="Sync database with blockchain")
    parser.add_argument("--compare", action="store_true", help="Compare blockchain and database")
    parser.add_argument("--register-verified", action="store_true", help="Register all verified lands on blockchain")
    
    args = parser.parse_args()
    
    if args.sync:
        sync_database_with_blockchain()
    elif args.compare:
        show_blockchain_vs_database()
    elif args.register_verified:
        register_verified_lands_on_blockchain()
    else:
        print("Usage:")
        print("  python sync_blockchain.py --compare          # Show comparison")
        print("  python sync_blockchain.py --sync             # Sync database with blockchain")
        print("  python sync_blockchain.py --register-verified # Register verified lands on blockchain")