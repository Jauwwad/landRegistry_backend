from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Land, User, UserRole, LandTransfer
from app.blockchain import blockchain_service
from app.email_service import email_service
from datetime import datetime
from sqlalchemy import or_

lands_bp = Blueprint('lands', __name__)

@lands_bp.route('/', methods=['GET'])
@jwt_required()
def get_lands():
    """Get all lands with optional filtering"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Parse query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        property_type = request.args.get('property_type')
        owner_only = request.args.get('owner_only', 'false').lower() == 'true'
        
        # Build query
        query = Land.query
        
        # Filter by owner if requested or if user is not admin
        if owner_only or user.role != UserRole.ADMIN:
            query = query.filter(Land.owner_id == user_id)
        
        # Apply filters
        if status:
            query = query.filter(Land.status == status)
        if property_type:
            query = query.filter(Land.property_type == property_type)
        
        # Paginate
        lands = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'lands': [land.to_dict() for land in lands.items],
            'total': lands.total,
            'pages': lands.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lands_bp.route('/<int:land_id>', methods=['GET'])
@jwt_required()
def get_land(land_id):
    """Get specific land details"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        land = Land.query.get(land_id)
        if not land:
            return jsonify({'error': 'Land not found'}), 404
        
        # Check permissions
        if user.role != UserRole.ADMIN and land.owner_id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Get blockchain data if available
        blockchain_data = None
        if land.token_id:
            blockchain_data = blockchain_service.get_land_details_from_blockchain(land.token_id)
        
        land_dict = land.to_dict()
        if blockchain_data:
            land_dict['blockchain_data'] = blockchain_data
        
        return jsonify({'land': land_dict}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lands_bp.route('/', methods=['POST'])
@jwt_required()
def register_land():
    """Register a new land"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['property_id', 'title', 'location', 'area', 'property_type', 'latitude', 'longitude']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if property ID already exists
        if Land.query.filter_by(property_id=data['property_id']).first():
            return jsonify({'error': 'Property ID already exists'}), 400
        
        # Create land record
        land = Land(
            property_id=data['property_id'],
            owner_id=user_id,
            wallet_address=user.wallet_address,
            title=data['title'],
            description=data.get('description'),
            location=data['location'],
            area=float(data['area']),
            property_type=data['property_type'],
            latitude=float(data['latitude']),
            longitude=float(data['longitude']),
            price=float(data['price']) if data.get('price') else None,
            status='pending'
        )
        
        db.session.add(land)
        db.session.commit()
        
        return jsonify({
            'message': 'Land registered successfully',
            'land': land.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@lands_bp.route('/<int:land_id>/register-blockchain', methods=['POST'])
@jwt_required()
def register_land_on_blockchain(land_id):
    """Register land on blockchain (admin only)"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user or user.role != UserRole.ADMIN:
            return jsonify({'error': 'Admin access required'}), 403
        
        land = Land.query.get(land_id)
        if not land:
            return jsonify({'error': 'Land not found'}), 404
        
        if land.is_registered_on_blockchain:
            return jsonify({'error': 'Land already registered on blockchain'}), 400
        
        # Prepare land data for blockchain
        land_data = {
            'property_id': land.property_id,
            'owner_wallet': land.wallet_address or user.wallet_address,
            'location': land.location,
            'area': land.area,
            'property_type': land.property_type,
            'latitude': land.latitude,
            'longitude': land.longitude,
            'ipfs_hash': land.ipfs_hash or ''
        }
        
        # Register on blockchain
        result = blockchain_service.register_land_on_blockchain(land_data)
        
        if result:
            # Update land record
            land.token_id = result['token_id']
            land.blockchain_tx_hash = result['tx_hash']
            land.is_registered_on_blockchain = True
            land.status = 'verified'
            
            db.session.commit()
            
            return jsonify({
                'message': 'Land registered on blockchain successfully',
                'tx_hash': result['tx_hash'],
                'token_id': result['token_id'],
                'land': land.to_dict()
            }), 200
        else:
            return jsonify({'error': 'Failed to register land on blockchain'}), 500
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@lands_bp.route('/<int:land_id>/transfer', methods=['POST'])
@jwt_required()
def transfer_land(land_id):
    """Transfer land to another user"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        land = Land.query.get(land_id)
        if not land:
            return jsonify({'error': 'Land not found'}), 404
        
        # Check if user owns the land
        if land.owner_id != user_id:
            return jsonify({'error': 'You do not own this land'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('to_user_id') or not data.get('price'):
            return jsonify({'error': 'to_user_id and price are required'}), 400
        
        to_user = User.query.get(data['to_user_id'])
        if not to_user:
            return jsonify({'error': 'Recipient user not found'}), 404
        
        # Create transfer record
        transfer = LandTransfer(
            land_id=land.id,
            from_user_id=user_id,
            to_user_id=data['to_user_id'],
            from_wallet=user.wallet_address,
            to_wallet=to_user.wallet_address,
            price=float(data['price']),
            status='pending'
        )
        
        db.session.add(transfer)
        
        # If land is on blockchain, transfer there too
        if land.is_registered_on_blockchain and land.token_id:
            tx_hash = blockchain_service.transfer_land_on_blockchain(
                land.token_id,
                to_user.wallet_address,
                float(data['price'])
            )
            
            if tx_hash:
                transfer.blockchain_tx_hash = tx_hash
                transfer.status = 'completed'
                transfer.completed_at = datetime.utcnow()
                
                # Update land ownership
                land.owner_id = data['to_user_id']
                land.wallet_address = to_user.wallet_address
            else:
                transfer.status = 'failed'
        else:
            # For non-blockchain lands, complete transfer immediately
            transfer.status = 'completed'
            transfer.completed_at = datetime.utcnow()
            land.owner_id = data['to_user_id']
            land.wallet_address = to_user.wallet_address
        
        db.session.commit()
        
        return jsonify({
            'message': 'Land transfer initiated successfully',
            'transfer': transfer.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@lands_bp.route('/<int:land_id>/verify', methods=['POST'])
@jwt_required()
def verify_land(land_id):
    """Verify land (admin only) with automatic blockchain registration"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user or user.role != UserRole.ADMIN:
            return jsonify({'error': 'Admin access required'}), 403
        
        land = Land.query.get(land_id)
        if not land:
            return jsonify({'error': 'Land not found'}), 404
        
        data = request.get_json()
        verified = data.get('verified', True)
        auto_register_blockchain = data.get('auto_register_blockchain', True)  # Default to True
        
        blockchain_result = None
        
        if verified:
            land.is_verified = True
            land.status = 'verified'
            
            # Automatically register on blockchain if conditions are met
            if auto_register_blockchain and not land.is_registered_on_blockchain:
                # Get owner for wallet address
                owner = User.query.get(land.owner_id)
                if owner and owner.wallet_address:
                    try:
                        # Import blockchain service
                        from app.blockchain import blockchain_service
                        
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
                        
                        # Register on blockchain
                        blockchain_result = blockchain_service.register_land_on_blockchain(land_data)
                        
                        if blockchain_result:
                            # Update land with blockchain information
                            land.token_id = blockchain_result.get('token_id')
                            land.blockchain_tx_hash = blockchain_result.get('tx_hash')
                            land.is_registered_on_blockchain = True
                            land.blockchain_block_number = blockchain_result.get('block_number')
                            
                    except Exception as e:
                        print(f"Blockchain registration failed: {str(e)}")
                        # Continue with verification even if blockchain registration fails
                        blockchain_result = {'error': str(e)}
                else:
                    print(f"Cannot register on blockchain: Owner wallet address missing")
        else:
            land.is_verified = False
            land.status = 'rejected'
        
        db.session.commit()
        
        response_data = {
            'message': f'Land {"verified" if verified else "rejected"} successfully',
            'land': land.to_dict()
        }
        
        # Include blockchain registration result if attempted
        if blockchain_result:
            if 'error' in blockchain_result:
                response_data['blockchain_warning'] = f"Land verified but blockchain registration failed: {blockchain_result['error']}"
            else:
                response_data['blockchain_success'] = f"Land verified and registered on blockchain with token ID: {blockchain_result.get('token_id')}"
                response_data['blockchain_data'] = blockchain_result
        
        return jsonify(response_data), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@lands_bp.route('/map-data', methods=['GET'])
@jwt_required()
def get_map_data():
    """Get land data for map visualization"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        # Get query parameters
        bounds = request.args.get('bounds')  # Format: "lat1,lng1,lat2,lng2"
        
        query = Land.query.filter(Land.status == 'verified')
        
        # Apply bounds filter if provided
        if bounds:
            try:
                lat1, lng1, lat2, lng2 = map(float, bounds.split(','))
                query = query.filter(
                    Land.latitude.between(min(lat1, lat2), max(lat1, lat2)),
                    Land.longitude.between(min(lng1, lng2), max(lng1, lng2))
                )
            except:
                pass  # Ignore invalid bounds
        
        lands = query.all()
        
        # Format data for map
        map_data = []
        for land in lands:
            land_info = {
                'id': land.id,
                'property_id': land.property_id,
                'title': land.title,
                'location': land.location,
                'area': land.area,
                'property_type': land.property_type,
                'latitude': land.latitude,
                'longitude': land.longitude,
                'price': land.price,
                'is_verified': land.is_verified,
                'is_registered_on_blockchain': land.is_registered_on_blockchain,
                'owner_name': f"{land.owner_user.first_name} {land.owner_user.last_name}" if land.owner_user else "Unknown"
            }
            
            # Only show owner details if user owns the land or is admin
            if user.role == UserRole.ADMIN or land.owner_id == user_id:
                land_info['owner_details'] = land.owner_user.to_dict() if land.owner_user else None
            
            map_data.append(land_info)
        
        return jsonify({'lands': map_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lands_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_statistics():
    """Get land statistics"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if user.role == UserRole.ADMIN:
            # Admin can see all statistics
            total_lands = Land.query.count()
            verified_lands = Land.query.filter_by(status='verified').count()
            pending_lands = Land.query.filter_by(status='pending').count()
            blockchain_lands = Land.query.filter_by(is_registered_on_blockchain=True).count()
            total_transfers = LandTransfer.query.count()
        else:
            # Users can only see their own statistics
            total_lands = Land.query.filter_by(owner_id=user_id).count()
            verified_lands = Land.query.filter_by(owner_id=user_id, status='verified').count()
            pending_lands = Land.query.filter_by(owner_id=user_id, status='pending').count()
            blockchain_lands = Land.query.filter_by(owner_id=user_id, is_registered_on_blockchain=True).count()
            total_transfers = LandTransfer.query.filter(
                (LandTransfer.from_user_id == user_id) | (LandTransfer.to_user_id == user_id)
            ).count()
        
        return jsonify({
            'total_lands': total_lands,
            'verified_lands': verified_lands,
            'pending_lands': pending_lands,
            'blockchain_lands': blockchain_lands,
            'total_transfers': total_transfers
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==========================================
# LAND TRANSFER ENDPOINTS
# ==========================================

@lands_bp.route('/<int:land_id>/transfer/initiate', methods=['POST'])
@jwt_required()
def initiate_land_transfer(land_id):
    """Initiate a land transfer for blockchain-registered lands"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get the land
        land = Land.query.get(land_id)
        if not land:
            return jsonify({'error': 'Land not found'}), 404
        
        # Verify ownership
        if land.owner_id != user_id:
            return jsonify({'error': 'You are not the owner of this land'}), 403
        
        # Check if land is registered on blockchain
        if not land.is_registered_on_blockchain:
            return jsonify({'error': 'Land must be registered on blockchain before transfer'}), 400
        
        # Check if there's already a pending transfer
        existing_transfer = LandTransfer.query.filter_by(
            land_id=land_id,
            status='pending'
        ).first()
        
        if existing_transfer:
            return jsonify({'error': 'There is already a pending transfer for this land'}), 400
        
        data = request.get_json()
        to_user_identifier = data.get('to_user')  # Can be username, email, or wallet address
        price = data.get('price', 0)
        transfer_type = data.get('transfer_type', 'sale')  # sale, gift, inheritance
        
        if not to_user_identifier:
            return jsonify({'error': 'Recipient user identifier is required'}), 400
        
        # Find the recipient user
        to_user = (User.query.filter_by(username=to_user_identifier).first() or
                  User.query.filter_by(email=to_user_identifier).first() or
                  User.query.filter_by(wallet_address=to_user_identifier).first())
        
        if not to_user:
            return jsonify({'error': 'Recipient user not found'}), 404
        
        if to_user.id == user_id:
            return jsonify({'error': 'Cannot transfer to yourself'}), 400
        
        if not to_user.wallet_address:
            return jsonify({'error': 'Recipient must have a wallet address to receive blockchain assets'}), 400
        
        # Create transfer record
        transfer = LandTransfer(
            land_id=land_id,
            from_user_id=user_id,
            to_user_id=to_user.id,
            from_wallet=user.wallet_address,
            to_wallet=to_user.wallet_address,
            price=float(price),
            status='pending'
        )
        
        db.session.add(transfer)
        db.session.commit()
        
        # Send email notifications
        try:
            email_service.send_transfer_initiated_email(transfer, land, user, to_user)
        except Exception as email_error:
            print(f"Email notification failed: {email_error}")
        
        return jsonify({
            'message': 'Land transfer initiated successfully',
            'transfer': transfer.to_dict(),
            'transfer_type': transfer_type
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@lands_bp.route('/<int:land_id>/transfer/<int:transfer_id>/execute', methods=['POST'])
@jwt_required()
def execute_land_transfer(land_id, transfer_id):
    """Execute the land transfer on blockchain"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get the transfer
        transfer = LandTransfer.query.get(transfer_id)
        if not transfer:
            return jsonify({'error': 'Transfer not found'}), 404
        
        if transfer.land_id != land_id:
            return jsonify({'error': 'Transfer does not match the land'}), 400
        
        # Verify ownership (only land owner can execute)
        if transfer.from_user_id != user_id:
            return jsonify({'error': 'Only the land owner can execute the transfer'}), 403
        
        if transfer.status != 'pending':
            return jsonify({'error': f'Transfer is not pending (current status: {transfer.status})'}), 400
        
        # Get the land
        land = Land.query.get(land_id)
        if not land:
            return jsonify({'error': 'Land not found'}), 404
        
        if not land.is_registered_on_blockchain or not land.token_id:
            return jsonify({'error': 'Land is not properly registered on blockchain'}), 400
        
        # Check if backend can transfer this token
        approval_status = blockchain_service.check_transfer_approval(land.token_id, land.wallet_address)
        
        if 'error' in approval_status:
            return jsonify({'error': f'Blockchain error: {approval_status["error"]}'}), 500
        
        if not approval_status.get('can_transfer', False):
            backend_address = approval_status.get('backend_address', 'Unknown')
            return jsonify({
                'error': 'Cannot transfer land on blockchain',
                'reason': 'Backend account is not authorized to transfer this land',
                'details': {
                    'backend_address': backend_address,
                    'current_owner': approval_status.get('current_owner'),
                    'token_id': land.token_id,
                    'approval_needed': True
                },
                'solution': f'The land owner needs to approve the backend address {backend_address} for transfers'
            }), 400
        
        # Execute transfer on blockchain
        try:
            transfer.status = 'processing'
            db.session.commit()
            
            print(f"✅ Transfer approved, proceeding with blockchain transfer. Reason: {approval_status.get('reason')}")
            
            # Call blockchain transfer function
            tx_hash = blockchain_service.transfer_land_on_blockchain(
                token_id=land.token_id,
                to_address=transfer.to_wallet,
                price=transfer.price,
                from_address=land.wallet_address
            )
            
            if tx_hash:
                # Update transfer and land records
                transfer.status = 'completed'
                transfer.blockchain_tx_hash = tx_hash
                transfer.completed_at = datetime.utcnow()
                
                # Update land ownership
                land.owner_id = transfer.to_user_id
                land.wallet_address = transfer.to_wallet
                
                db.session.commit()
                
                # Send success email notifications
                try:
                    from_user = User.query.get(transfer.from_user_id)
                    to_user = User.query.get(transfer.to_user_id)
                    email_service.send_transfer_completed_email(transfer, land, from_user, to_user)
                except Exception as email_error:
                    print(f"Email notification failed: {email_error}")
                
                return jsonify({
                    'message': 'Land transfer executed successfully on blockchain',
                    'transfer': transfer.to_dict(),
                    'transaction_hash': tx_hash
                }), 200
            else:
                transfer.status = 'failed'
                db.session.commit()
                return jsonify({'error': 'Blockchain transfer failed'}), 500
                
        except Exception as blockchain_error:
            transfer.status = 'failed'
            db.session.commit()
            return jsonify({'error': f'Blockchain transfer failed: {str(blockchain_error)}'}), 500
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@lands_bp.route('/<int:land_id>/transfer/<int:transfer_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_land_transfer(land_id, transfer_id):
    """Cancel a pending land transfer"""
    try:
        user_id = int(get_jwt_identity())
        
        # Get the transfer
        transfer = LandTransfer.query.get(transfer_id)
        if not transfer:
            return jsonify({'error': 'Transfer not found'}), 404
        
        if transfer.land_id != land_id:
            return jsonify({'error': 'Transfer does not match the land'}), 400
        
        # Only the land owner or recipient can cancel
        if transfer.from_user_id != user_id and transfer.to_user_id != user_id:
            return jsonify({'error': 'You are not authorized to cancel this transfer'}), 403
        
        if transfer.status != 'pending':
            return jsonify({'error': f'Cannot cancel transfer with status: {transfer.status}'}), 400
        
        transfer.status = 'cancelled'
        transfer.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        # Send cancellation email notifications
        try:
            from_user = User.query.get(transfer.from_user_id)
            to_user = User.query.get(transfer.to_user_id)
            land = Land.query.get(land_id)
            email_service.send_transfer_cancelled_email(transfer, land, from_user, to_user)
        except Exception as email_error:
            print(f"Email notification failed: {email_error}")
        
        return jsonify({
            'message': 'Transfer cancelled successfully',
            'transfer': transfer.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@lands_bp.route('/transfers', methods=['GET'])
@jwt_required()
def get_user_transfers():
    """Get all transfers for the current user"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Parse query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        transfer_type = request.args.get('type')  # 'sent', 'received', 'all'
        
        # Build query
        if user.role == UserRole.ADMIN and transfer_type == 'all':
            # Admin can see all transfers
            query = LandTransfer.query
        else:
            # Regular users see only their transfers
            if transfer_type == 'sent':
                query = LandTransfer.query.filter_by(from_user_id=user_id)
            elif transfer_type == 'received':
                query = LandTransfer.query.filter_by(to_user_id=user_id)
            else:
                # Default: both sent and received
                query = LandTransfer.query.filter(
                    or_(LandTransfer.from_user_id == user_id, LandTransfer.to_user_id == user_id)
                )
        
        # Filter by status if provided
        if status:
            query = query.filter_by(status=status)
        
        # Order by most recent first
        query = query.order_by(LandTransfer.initiated_at.desc())
        
        # Paginate
        transfers = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Include land details in response
        transfer_data = []
        for transfer in transfers.items:
            transfer_dict = transfer.to_dict()
            
            # Add land details
            land = Land.query.get(transfer.land_id)
            if land:
                transfer_dict['land'] = {
                    'id': land.id,
                    'title': land.title,
                    'property_id': land.property_id,
                    'location': land.location,
                    'area': land.area,
                    'property_type': land.property_type,
                    'token_id': land.token_id
                }
            
            transfer_data.append(transfer_dict)
        
        return jsonify({
            'transfers': transfer_data,
            'total': transfers.total,
            'pages': transfers.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lands_bp.route('/transfers/<int:transfer_id>', methods=['GET'])
@jwt_required()
def get_transfer_details(transfer_id):
    """Get detailed information about a specific transfer"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        transfer = LandTransfer.query.get(transfer_id)
        if not transfer:
            return jsonify({'error': 'Transfer not found'}), 404
        
        # Check authorization
        if (user.role != UserRole.ADMIN and 
            transfer.from_user_id != user_id and 
            transfer.to_user_id != user_id):
            return jsonify({'error': 'You are not authorized to view this transfer'}), 403
        
        # Get detailed transfer information
        transfer_dict = transfer.to_dict()
        
        # Add land details
        land = Land.query.get(transfer.land_id)
        if land:
            transfer_dict['land'] = land.to_dict()
        
        # Add blockchain verification if completed
        if transfer.status == 'completed' and transfer.blockchain_tx_hash:
            # You could add blockchain transaction verification here
            transfer_dict['blockchain_verified'] = True
        
        return jsonify({'transfer': transfer_dict}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lands_bp.route('/<int:land_id>/transfer-history', methods=['GET'])
@jwt_required()
def get_land_transfer_history(land_id):
    """Get complete transfer history for a land"""
    try:
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        land = Land.query.get(land_id)
        if not land:
            return jsonify({'error': 'Land not found'}), 404
        
        # Check authorization (land owner or admin can view history)
        if user.role != UserRole.ADMIN and land.owner_id != user_id:
            return jsonify({'error': 'You are not authorized to view this land\'s transfer history'}), 403
        
        # Get all transfers for this land
        transfers = LandTransfer.query.filter_by(land_id=land_id).order_by(
            LandTransfer.initiated_at.desc()
        ).all()
        
        transfer_history = []
        for transfer in transfers:
            transfer_dict = transfer.to_dict()
            transfer_history.append(transfer_dict)
        
        # Also get blockchain transfer history if available
        blockchain_history = []
        if land.is_registered_on_blockchain and land.token_id:
            try:
                blockchain_transfers = blockchain_service.get_land_transfer_history(land.token_id)
                if blockchain_transfers:
                    blockchain_history = blockchain_transfers
            except Exception as e:
                print(f"Error fetching blockchain history: {e}")
        
        return jsonify({
            'land': land.to_dict(),
            'database_transfers': transfer_history,
            'blockchain_transfers': blockchain_history
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500