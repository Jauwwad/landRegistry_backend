from web3 import Web3
from web3.middleware import geth_poa_middleware
import json
import os
from typing import Dict, Any, Optional

class BlockchainService:
    def __init__(self):
        self.rpc_url = os.getenv('POLYGON_RPC_URL')
        self.chain_id = int(os.getenv('CHAIN_ID', 80002))
        self.private_key = os.getenv('PRIVATE_KEY')
        self.contract_address = os.getenv('CONTRACT_ADDRESS')
        
        print(f"Initializing blockchain service with RPC: {self.rpc_url}")
        print(f"Contract address: {self.contract_address}")
        print(f"Chain ID: {self.chain_id}")
        
        # Initialize Web3
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            
            # Add POA middleware for Polygon Amoy (POA chain)
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            print(f"Web3 provider initialized successfully with POA middleware")
        except Exception as e:
            print(f"Failed to initialize Web3: {e}")
            self.w3 = None
        
        # Load contract ABI from compiled artifact
        try:
            contract_artifact_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                'contracts', 
                'artifacts', 
                'contracts', 
                'LandRegistry.sol', 
                'LandRegistry.json'
            )
            
            if os.path.exists(contract_artifact_path):
                with open(contract_artifact_path, 'r') as f:
                    artifact = json.load(f)
                    self.contract_abi = artifact['abi']
                    print(f"✅ Loaded contract ABI from artifact ({len(self.contract_abi)} functions)")
            else:
                print(f"⚠️ Contract artifact not found at {contract_artifact_path}, using fallback ABI")
                raise FileNotFoundError("Artifact not found")
                
        except Exception as e:
            print(f"⚠️ Failed to load contract artifact: {e}")
            print("Using fallback minimal ABI...")
            # Fallback minimal ABI with essential ERC721 and custom functions
            self.contract_abi = [
                # Events
                {
                    "anonymous": False,
                    "inputs": [
                        {"indexed": True, "internalType": "uint256", "name": "tokenId", "type": "uint256"},
                        {"indexed": False, "internalType": "string", "name": "propertyId", "type": "string"},
                        {"indexed": True, "internalType": "address", "name": "owner", "type": "address"},
                        {"indexed": False, "internalType": "string", "name": "location", "type": "string"},
                        {"indexed": False, "internalType": "uint256", "name": "area", "type": "uint256"}
                    ],
                    "name": "LandRegistered",
                    "type": "event"
                },
                {
                    "anonymous": False,
                    "inputs": [
                        {"indexed": True, "internalType": "uint256", "name": "tokenId", "type": "uint256"},
                        {"indexed": True, "internalType": "address", "name": "from", "type": "address"},
                        {"indexed": True, "internalType": "address", "name": "to", "type": "address"},
                        {"indexed": False, "internalType": "uint256", "name": "price", "type": "uint256"},
                        {"indexed": False, "internalType": "uint256", "name": "transferDate", "type": "uint256"}
                    ],
                    "name": "LandTransferred",
                    "type": "event"
                },
                # ERC721 Standard Functions
                {
                    "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
                    "name": "ownerOf",
                    "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [{"internalType": "uint256", "name": "tokenId", "type": "uint256"}],
                    "name": "getApproved",
                    "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [
                        {"internalType": "address", "name": "owner", "type": "address"},
                        {"internalType": "address", "name": "operator", "type": "address"}
                    ],
                    "name": "isApprovedForAll",
                    "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [
                        {"internalType": "address", "name": "from", "type": "address"},
                        {"internalType": "address", "name": "to", "type": "address"},
                        {"internalType": "uint256", "name": "tokenId", "type": "uint256"}
                    ],
                    "name": "transferFrom",
                    "outputs": [],
                    "stateMutability": "nonpayable",
                    "type": "function"
                },
                # Custom Land Registry Functions
                {
                    "inputs": [
                        {"internalType": "string", "name": "_propertyId", "type": "string"},
                        {"internalType": "address", "name": "_owner", "type": "address"},
                        {"internalType": "string", "name": "_location", "type": "string"},
                        {"internalType": "uint256", "name": "_area", "type": "uint256"},
                        {"internalType": "string", "name": "_propertyType", "type": "string"},
                        {"internalType": "string", "name": "_ipfsHash", "type": "string"},
                        {"internalType": "uint256", "name": "_latitude", "type": "uint256"},
                        {"internalType": "uint256", "name": "_longitude", "type": "uint256"}
                    ],
                    "name": "registerLand",
                    "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                    "stateMutability": "nonpayable",
                    "type": "function"
                },
                {
                    "inputs": [
                        {"internalType": "uint256", "name": "_tokenId", "type": "uint256"},
                        {"internalType": "address", "name": "_to", "type": "address"},
                        {"internalType": "uint256", "name": "_price", "type": "uint256"}
                    ],
                    "name": "transferLand",
                    "outputs": [],
                    "stateMutability": "nonpayable",
                    "type": "function"
                },
                {
                    "inputs": [{"internalType": "uint256", "name": "_tokenId", "type": "uint256"}],
                    "name": "getLandDetails",
                    "outputs": [
                        {
                            "components": [
                                {"internalType": "uint256", "name": "id", "type": "uint256"},
                                {"internalType": "string", "name": "propertyId", "type": "string"},
                                {"internalType": "address", "name": "owner", "type": "address"},
                                {"internalType": "string", "name": "location", "type": "string"},
                                {"internalType": "uint256", "name": "area", "type": "uint256"},
                                {"internalType": "string", "name": "propertyType", "type": "string"},
                                {"internalType": "uint256", "name": "registrationDate", "type": "uint256"},
                                {"internalType": "bool", "name": "isVerified", "type": "bool"},
                                {"internalType": "string", "name": "ipfsHash", "type": "string"},
                                {"internalType": "uint256", "name": "latitude", "type": "uint256"},
                                {"internalType": "uint256", "name": "longitude", "type": "uint256"}
                            ],
                            "internalType": "struct LandRegistry.Land",
                            "name": "",
                            "type": "tuple"
                        }
                    ],
                    "stateMutability": "view",
                    "type": "function"
                },
                {
                    "inputs": [],
                    "name": "totalSupply",
                    "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
        
        # Initialize contract
        if self.contract_address and self.w3:
            try:
                self.contract = self.w3.eth.contract(
                    address=Web3.to_checksum_address(self.contract_address),
                    abi=self.contract_abi
                )
                print(f"Contract initialized successfully")
            except Exception as e:
                print(f"Failed to initialize contract: {e}")
                self.contract = None
        else:
            self.contract = None
            print("Contract not initialized - missing address or Web3 instance")
    
    def is_connected(self) -> bool:
        """Check if connected to blockchain"""
        try:
            if not self.w3:
                print("Web3 instance not initialized")
                return False
            
            # Use a more reliable connection test
            latest_block = self.w3.eth.get_block('latest')
            print(f"Successfully retrieved latest block: {latest_block.number}")
            return latest_block is not None
        except Exception as e:
            print(f"Blockchain connection error: {e}")
            return False
    
    def diagnose_connection(self):
        """Diagnose blockchain connection issues"""
        print("=== Blockchain Connection Diagnosis ===")
        print(f"RPC URL: {self.rpc_url}")
        print(f"Chain ID: {self.chain_id}")
        print(f"Contract Address: {self.contract_address}")
        print(f"Private Key Present: {'Yes' if self.private_key else 'No'}")
        print(f"Web3 Instance: {'Initialized' if self.w3 else 'Not Initialized'}")
        print(f"Contract Instance: {'Initialized' if self.contract else 'Not Initialized'}")
        
        if self.w3:
            try:
                # Test basic connectivity
                latest_block = self.w3.eth.get_block('latest')
                print(f"Latest Block: {latest_block.number}")
                print(f"Connection Status: Connected")
                
                # Test account
                if self.private_key:
                    account = self.w3.eth.account.from_key(self.private_key)
                    balance = self.w3.eth.get_balance(account.address)
                    print(f"Account Address: {account.address}")
                    print(f"Account Balance: {self.w3.from_wei(balance, 'ether')} MATIC")
                
            except Exception as e:
                print(f"Connection Test Failed: {e}")
        
        print("=== End Diagnosis ===")
        
    def get_account_from_private_key(self) -> str:
        """Get account address from private key"""
        try:
            account = self.w3.eth.account.from_key(self.private_key)
            return account.address
        except:
            return None
    
    def register_land_on_blockchain(self, land_data: Dict[str, Any]) -> Optional[str]:
        """Register land on blockchain"""
        try:
            if not self.contract:
                raise Exception("Contract not initialized")
            
            print(f"Registering land on blockchain: {land_data}")
            
            account = self.w3.eth.account.from_key(self.private_key)
            
            # Ensure all required fields are present and valid
            property_id = str(land_data['property_id'])
            # Use backend account as blockchain owner for easier transfers
            backend_account = self.w3.eth.account.from_key(self.private_key)
            owner_wallet = backend_account.address  # Backend owns on blockchain
            user_wallet = str(land_data['owner_wallet'])  # Original user wallet for reference
            
            print(f"🔄 Registering with backend ownership model:")
            print(f"   Blockchain owner: {owner_wallet} (backend)")
            print(f"   Logical owner: {user_wallet} (user - tracked in database)")
            
            location = str(land_data['location'])
            area = int(float(land_data['area']))
            property_type = str(land_data['property_type'])
            ipfs_hash = str(land_data.get('ipfs_hash', ''))
            
            # Handle coordinates - use default values if None or invalid
            try:
                latitude = int(float(land_data.get('latitude', 40.7128)) * 1000000)
            except (ValueError, TypeError):
                latitude = int(40.7128 * 1000000)  # Default to NYC coordinates
                
            try:
                longitude = int(float(land_data.get('longitude', -74.0060)) * 1000000)
            except (ValueError, TypeError):
                longitude = int(-74.0060 * 1000000)  # Default to NYC coordinates
            
            print(f"Prepared data - Property ID: {property_id}, Backend Owner: {owner_wallet}, Area: {area}")
            print(f"   User wallet for reference: {user_wallet}")
            print(f"Coordinates: lat={latitude}, lng={longitude}")
            
            # Validate user wallet address format (for reference)
            if not user_wallet.startswith('0x') or len(user_wallet) != 42:
                print(f"⚠️ Warning: Invalid user wallet format: {user_wallet}")
            
            # Backend wallet is always valid since we generated it
            print(f"✅ Using backend wallet as blockchain owner: {owner_wallet}")
            
            # Convert integers to proper uint256 format by ensuring they're positive
            area_uint = max(0, area)
            latitude_uint = max(0, latitude + 180000000)  # Shift to make positive
            longitude_uint = max(0, longitude + 180000000)  # Shift to make positive
            
            print(f"Converted to uint256 - Area: {area_uint}, Lat: {latitude_uint}, Lng: {longitude_uint}")
            
            # Build transaction
            transaction = self.contract.functions.registerLand(
                property_id,
                Web3.to_checksum_address(owner_wallet),
                location,
                area_uint,  # Converted to uint256
                property_type,
                ipfs_hash,
                latitude_uint,  # Converted to uint256
                longitude_uint  # Converted to uint256
            ).build_transaction({
                'chainId': self.chain_id,
                'gas': 2000000,
                'gasPrice': self.w3.to_wei('30', 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(account.address),
            })
            
            print(f"Transaction prepared, signing...")
            
            # Sign transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
            
            print(f"Transaction signed, sending...")
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            print(f"Transaction sent: {tx_hash.hex()}")
            
            # Wait for transaction receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            print(f"Transaction mined in block: {receipt.blockNumber}")
            
            if receipt.status == 1:
                # Parse events to get token ID
                try:
                    logs = self.contract.events.LandRegistered().process_receipt(receipt)
                    if logs:
                        token_id = logs[0]['args']['tokenId']
                        print(f"Land registered with token ID: {token_id}")
                        return {
                            'tx_hash': receipt.transactionHash.hex(),
                            'token_id': token_id,
                            'block_number': receipt.blockNumber
                        }
                except Exception as e:
                    print(f"Could not parse event logs: {e}")
                    # Return basic success info even if event parsing fails
                    return {
                        'tx_hash': receipt.transactionHash.hex(),
                        'token_id': None,
                        'block_number': receipt.blockNumber
                    }
            else:
                print(f"Transaction failed with status: {receipt.status}")
                return None
            
            return None
            
        except Exception as e:
            print(f"Error registering land on blockchain: {str(e)}")
            return None
    
    def transfer_land_on_blockchain(self, token_id: int, to_address: str, price: float, from_address: str = None) -> Optional[str]:
        """Transfer land on blockchain with proper ownership verification"""
        try:
            if not self.contract:
                raise Exception("Contract not initialized")
            
            print(f"Initiating blockchain transfer for token {token_id} to {to_address}")
            
            account = self.w3.eth.account.from_key(self.private_key)
            backend_address = account.address
            
            # Get current owner of the token
            try:
                current_owner = self.contract.functions.ownerOf(token_id).call()
                print(f"Current token owner: {current_owner}")
                print(f"Backend account: {backend_address}")
            except Exception as e:
                print(f"Error getting token owner: {e}")
                return None
            
            # Validate addresses
            to_address_checksum = Web3.to_checksum_address(to_address)
            current_owner_checksum = Web3.to_checksum_address(current_owner)
            
            # Convert price to wei (assuming price is in MATIC)
            price_wei = self.w3.to_wei(price, 'ether')
            
            print(f"Transfer details: Token {token_id}, From: {current_owner_checksum}, To: {to_address_checksum}, Price: {price} MATIC ({price_wei} wei)")
            
            # Check if backend account is the owner or has approval
            if current_owner_checksum.lower() == backend_address.lower():
                print("✅ Backend account owns the token, proceeding with direct transfer")
                calling_account = backend_address
            else:
                # Check if backend account is approved to transfer this token
                try:
                    approved_address = self.contract.functions.getApproved(token_id).call()
                    is_approved_for_all = self.contract.functions.isApprovedForAll(current_owner, backend_address).call()
                    
                    print(f"Approved address for token: {approved_address}")
                    print(f"Is approved for all: {is_approved_for_all}")
                    
                    if (approved_address and approved_address.lower() == backend_address.lower()) or is_approved_for_all:
                        print("✅ Backend account is approved to transfer this token")
                        calling_account = backend_address
                    else:
                        print("❌ Backend account is not authorized to transfer this token")
                        print("💡 The land owner needs to approve the backend account first")
                        return None
                        
                except Exception as e:
                    print(f"Error checking approvals: {e}")
                    return None
            
            # Build transaction - use transferFrom since we might not be the owner
            try:
                if current_owner_checksum.lower() == backend_address.lower():
                    # We own the token, use transferLand
                    transaction = self.contract.functions.transferLand(
                        token_id,
                        to_address_checksum,
                        price_wei
                    ).build_transaction({
                        'chainId': self.chain_id,
                        'gas': 2000000,
                        'gasPrice': self.w3.to_wei('30', 'gwei'),
                        'nonce': self.w3.eth.get_transaction_count(backend_address),
                    })
                else:
                    # We're approved, use transferFrom (standard ERC721)
                    transaction = self.contract.functions.transferFrom(
                        current_owner_checksum,
                        to_address_checksum,
                        token_id
                    ).build_transaction({
                        'chainId': self.chain_id,
                        'gas': 2000000,
                        'gasPrice': self.w3.to_wei('30', 'gwei'),
                        'nonce': self.w3.eth.get_transaction_count(backend_address),
                    })
                    
                    print("⚠️ Using transferFrom instead of transferLand (no price/history recording)")
                    
            except Exception as e:
                print(f"Error building transaction: {e}")
                return None
            
            print(f"Transaction built, signing...")
            
            # Sign transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
            
            print(f"Transaction signed, sending...")
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            print(f"Transaction sent: {tx_hash.hex()}")
            
            # Wait for transaction receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            print(f"Transaction mined in block: {receipt.blockNumber}")
            
            if receipt.status == 1:
                print(f"✅ Land transfer successful! TX: {receipt.transactionHash.hex()}")
                return receipt.transactionHash.hex()
            else:
                print(f"❌ Transaction failed with status: {receipt.status}")
                # Try to get the revert reason
                try:
                    self.w3.eth.call({
                        'to': receipt.to,
                        'data': receipt.input
                    }, receipt.blockNumber)
                except Exception as revert_error:
                    print(f"Revert reason: {revert_error}")
                return None
            
        except Exception as e:
            print(f"Error transferring land on blockchain: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_backend_address(self) -> str:
        """Get the backend account address"""
        try:
            account = self.w3.eth.account.from_key(self.private_key)
            return account.address
        except Exception as e:
            print(f"Error getting backend address: {e}")
            return None
    
    def check_transfer_approval(self, token_id: int, owner_address: str) -> Dict[str, Any]:
        """Check if backend account can transfer the token"""
        try:
            if not self.contract:
                return {"error": "Contract not initialized"}
            
            backend_address = self.get_backend_address()
            if not backend_address:
                return {"error": "Backend account not available"}
            
            # Get current owner
            current_owner = self.contract.functions.ownerOf(token_id).call()
            
            # Check if backend is the owner
            if current_owner.lower() == backend_address.lower():
                return {
                    "can_transfer": True,
                    "reason": "backend_owns_token",
                    "backend_address": backend_address,
                    "current_owner": current_owner
                }
            
            # Check specific approval for this token
            approved_address = self.contract.functions.getApproved(token_id).call()
            if approved_address and approved_address.lower() == backend_address.lower():
                return {
                    "can_transfer": True,
                    "reason": "token_approved",
                    "backend_address": backend_address,
                    "current_owner": current_owner,
                    "approved_address": approved_address
                }
            
            # Check approval for all tokens
            is_approved_for_all = self.contract.functions.isApprovedForAll(current_owner, backend_address).call()
            if is_approved_for_all:
                return {
                    "can_transfer": True,
                    "reason": "approved_for_all",
                    "backend_address": backend_address,
                    "current_owner": current_owner
                }
            
            # No approval found
            return {
                "can_transfer": False,
                "reason": "not_approved",
                "backend_address": backend_address,
                "current_owner": current_owner,
                "needs_approval": True
            }
            
        except Exception as e:
            return {"error": f"Error checking approval: {str(e)}"}

    def get_land_details_from_blockchain(self, token_id: int) -> Optional[Dict[str, Any]]:
        """Get land details from blockchain"""
        try:
            if not self.contract:
                return None
            
            land_data = self.contract.functions.getLandDetails(token_id).call()
            
            return {
                'id': land_data[0],
                'property_id': land_data[1],
                'owner': land_data[2],
                'location': land_data[3],
                'area': land_data[4],
                'property_type': land_data[5],
                'registration_date': land_data[6],
                'is_verified': land_data[7],
                'ipfs_hash': land_data[8],
                'latitude': land_data[9] / 1000000,  # Convert back to decimal
                'longitude': land_data[10] / 1000000  # Convert back to decimal
            }
            
        except Exception as e:
            print(f"Error getting land details from blockchain: {str(e)}")
            return None
    
    def get_lands_by_owner(self, owner_address: str) -> list:
        """Get all lands owned by an address"""
        try:
            if not self.contract:
                return []
            
            token_ids = self.contract.functions.getLandsByOwner(
                Web3.to_checksum_address(owner_address)
            ).call()
            
            return token_ids
            
        except Exception as e:
            print(f"Error getting lands by owner: {str(e)}")
            return []
    
    def get_land_transfer_history(self, token_id: int) -> list:
        """Get transfer history for a specific land token"""
        try:
            if not self.contract:
                return []
            
            # Get transfer history from blockchain events
            transfer_history = self.contract.functions.getLandTransferHistory(token_id).call()
            
            # Format the transfer history
            formatted_history = []
            for transfer in transfer_history:
                formatted_history.append({
                    'land_id': transfer[0],
                    'from': transfer[1],
                    'to': transfer[2],
                    'transfer_date': transfer[3],
                    'price': transfer[4],
                    'is_completed': transfer[5]
                })
            
            return formatted_history
            
        except Exception as e:
            print(f"Error getting land transfer history: {str(e)}")
            return []
    
    def get_total_supply(self) -> int:
        """Get total number of registered lands"""
        try:
            if not self.contract:
                return 0
            
            return self.contract.functions.totalSupply().call()
            
        except Exception as e:
            print(f"Error getting total supply: {str(e)}")
            return 0

# Global instance
blockchain_service = BlockchainService()