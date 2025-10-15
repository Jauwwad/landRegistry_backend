from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User, Land, LandTransfer, UserRole
from app.blockchain import blockchain_service

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to require admin access"""
    def decorated_function(*args, **kwargs):
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user or user.role != UserRole.ADMIN:
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@admin_required
def get_dashboard():
    """Get admin dashboard data"""
    try:
        # Get statistics
        total_users = User.query.count()
        total_lands = Land.query.count()
        pending_lands = Land.query.filter_by(status='pending').count()
        verified_lands = Land.query.filter_by(status='verified').count()
        rejected_lands = Land.query.filter_by(status='rejected').count()
        blockchain_lands = Land.query.filter_by(is_registered_on_blockchain=True).count()
        total_transfers = LandTransfer.query.count()
        
        # Get recent activities
        recent_lands = Land.query.order_by(Land.created_at.desc()).limit(5).all()
        recent_transfers = LandTransfer.query.order_by(LandTransfer.initiated_at.desc()).limit(5).all()
        
        # Get blockchain statistics
        blockchain_connected = blockchain_service.is_connected()
        blockchain_total_supply = 0
        if blockchain_connected:
            blockchain_total_supply = blockchain_service.get_total_supply()
        
        return jsonify({
            'statistics': {
                'total_users': total_users,
                'total_lands': total_lands,
                'pending_lands': pending_lands,
                'verified_lands': verified_lands,
                'rejected_lands': rejected_lands,
                'blockchain_lands': blockchain_lands,
                'total_transfers': total_transfers,
                'blockchain_connected': blockchain_connected,
                'blockchain_total_supply': blockchain_total_supply
            },
            'recent_lands': [land.to_dict() for land in recent_lands],
            'recent_transfers': [transfer.to_dict() for transfer in recent_transfers]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
def get_users():
    """Get all users with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        
        query = User.query
        
        if search:
            query = query.filter(
                (User.username.contains(search)) |
                (User.email.contains(search)) |
                (User.first_name.contains(search)) |
                (User.last_name.contains(search))
            )
        
        users = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'users': [user.to_dict() for user in users.items],
            'total': users.total,
            'pages': users.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_user(user_id):
    """Get specific user details"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get user's lands
        lands = Land.query.filter_by(owner_id=user_id).all()
        
        # Get user's transfers
        transfers = LandTransfer.query.filter(
            (LandTransfer.from_user_id == user_id) | (LandTransfer.to_user_id == user_id)
        ).all()
        
        user_data = user.to_dict()
        user_data['lands'] = [land.to_dict() for land in lands]
        user_data['transfers'] = [transfer.to_dict() for transfer in transfers]
        
        return jsonify({'user': user_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@jwt_required()
@admin_required
def toggle_user_status(user_id):
    """Activate/deactivate user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user.is_active = not user.is_active
        db.session.commit()
        
        return jsonify({
            'message': f'User {"activated" if user.is_active else "deactivated"} successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/lands/pending', methods=['GET'])
@jwt_required()
@admin_required
def get_pending_lands():
    """Get all pending lands for review"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        lands = Land.query.filter_by(status='pending').paginate(
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

@admin_bp.route('/lands/<int:land_id>/review', methods=['POST'])
@jwt_required()
@admin_required
def review_land(land_id):
    """Review land application (approve/reject) with automatic blockchain registration"""
    try:
        land = Land.query.get(land_id)
        if not land:
            return jsonify({'error': 'Land not found'}), 404
        
        data = request.get_json()
        action = data.get('action')  # 'approve' or 'reject'
        comments = data.get('comments', '')
        auto_register_blockchain = data.get('auto_register_blockchain', True)  # Default to True
        
        if action not in ['approve', 'reject']:
            return jsonify({'error': 'Invalid action. Use "approve" or "reject"'}), 400
        
        blockchain_result = None
        
        if action == 'approve':
            land.status = 'verified'
            land.is_verified = True
            
            # Automatically register on blockchain if conditions are met
            if auto_register_blockchain and not land.is_registered_on_blockchain:
                # Get owner for wallet address
                owner = User.query.get(land.owner_id)
                if owner and owner.wallet_address:
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
                        # Continue with approval even if blockchain registration fails
                        blockchain_result = {'error': str(e)}
                else:
                    print(f"Cannot register on blockchain: Owner wallet address missing")
        else:
            land.status = 'rejected'
            land.is_verified = False
        
        db.session.commit()
        
        response_data = {
            'message': f'Land {action}d successfully',
            'land': land.to_dict()
        }
        
        # Include blockchain registration result if attempted
        if blockchain_result:
            if 'error' in blockchain_result:
                response_data['blockchain_warning'] = f"Land approved but blockchain registration failed: {blockchain_result['error']}"
            else:
                response_data['blockchain_success'] = f"Land approved and registered on blockchain with token ID: {blockchain_result.get('token_id')}"
                response_data['blockchain_data'] = blockchain_result
        
        return jsonify(response_data), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/transfers', methods=['GET'])
@jwt_required()
@admin_required
def get_transfers():
    """Get all land transfers"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        
        query = LandTransfer.query
        
        if status:
            query = query.filter_by(status=status)
        
        transfers = query.order_by(LandTransfer.initiated_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'transfers': [transfer.to_dict() for transfer in transfers.items],
            'total': transfers.total,
            'pages': transfers.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/blockchain/status', methods=['GET'])
@jwt_required()
@admin_required
def get_blockchain_status():
    """Get blockchain connection status and statistics"""
    try:
        # Test blockchain connection
        connected = blockchain_service.is_connected()
        
        status_data = {
            'connected': connected,
            'network': 'Polygon Amoy Testnet',
            'chain_id': blockchain_service.chain_id,
            'rpc_url': blockchain_service.rpc_url,
            'contract_address': blockchain_service.contract_address,
            'balance': '0',
            'account_address': None,
            'total_supply': 0,
            'error': None
        }
        
        if connected:
            try:
                # Get account address
                account_address = blockchain_service.get_account_from_private_key()
                if account_address:
                    status_data['account_address'] = account_address
                    
                    # Get balance
                    balance_wei = blockchain_service.w3.eth.get_balance(account_address)
                    balance_matic = blockchain_service.w3.from_wei(balance_wei, 'ether')
                    status_data['balance'] = f"{balance_matic:.4f}"
                
                # Get total supply from contract
                total_supply = blockchain_service.get_total_supply()
                status_data['total_supply'] = total_supply
                
            except Exception as e:
                status_data['error'] = f"Connected but contract interaction failed: {str(e)}"
        else:
            status_data['error'] = "Not connected to blockchain network"
        
        return jsonify(status_data), 200
        
    except Exception as e:
        return jsonify({
            'connected': False,
            'error': str(e)
        }), 500

@admin_bp.route('/reports/land-distribution', methods=['GET'])
@jwt_required()
@admin_required
def get_land_distribution_report():
    """Get land distribution report by property type and status"""
    try:
        # Group by property type
        property_type_query = db.session.query(
            Land.property_type,
            db.func.count(Land.id).label('count')
        ).group_by(Land.property_type).all()
        
        # Group by status
        status_query = db.session.query(
            Land.status,
            db.func.count(Land.id).label('count')
        ).group_by(Land.status).all()
        
        # Group by area ranges
        area_ranges = [
            ('Small (< 1000 sqm)', Land.area < 1000),
            ('Medium (1000-5000 sqm)', (Land.area >= 1000) & (Land.area < 5000)),
            ('Large (>= 5000 sqm)', Land.area >= 5000)
        ]
        
        area_distribution = []
        for label, condition in area_ranges:
            count = Land.query.filter(condition).count()
            area_distribution.append({'label': label, 'count': count})
        
        return jsonify({
            'property_type_distribution': [
                {'type': row.property_type, 'count': row.count}
                for row in property_type_query
            ],
            'status_distribution': [
                {'status': row.status, 'count': row.count}
                for row in status_query
            ],
            'area_distribution': area_distribution
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/system/info', methods=['GET'])
@jwt_required()
@admin_required
def get_system_info():
    """Get system information"""
    try:
        import os
        from datetime import datetime
        
        return jsonify({
            'system': {
                'environment': os.getenv('FLASK_ENV', 'development'),
                'database_connected': True,  # If we reach here, DB is connected
                'blockchain_connected': blockchain_service.is_connected(),
                'current_time': datetime.utcnow().isoformat(),
                'contract_address': blockchain_service.contract_address,
                'chain_id': blockchain_service.chain_id
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/lands/<int:land_id>/register-blockchain', methods=['POST'])
@jwt_required()
@admin_required
def register_land_on_blockchain(land_id):
    """Register a verified land on blockchain"""
    try:
        # Get the land record
        land = Land.query.get_or_404(land_id)
        
        # Check if land is verified
        if land.status != 'verified':
            return jsonify({'error': 'Land must be verified before blockchain registration'}), 400
        
        # Check if already registered on blockchain
        if land.is_registered_on_blockchain:
            return jsonify({'error': 'Land is already registered on blockchain'}), 400
        
        # Check if owner has wallet address
        if not land.wallet_address:
            return jsonify({'error': 'Owner must have a wallet address'}), 400
        
        # Prepare land data for blockchain
        land_data = {
            'property_id': land.property_id,
            'owner_wallet': land.wallet_address,
            'location': land.location,
            'area': land.area,
            'property_type': land.property_type,
            'latitude': land.latitude,
            'longitude': land.longitude,
            'ipfs_hash': ''  # You can add IPFS hash for document storage
        }
        
        # Register on blockchain
        result = blockchain_service.register_land_on_blockchain(land_data)
        
        if result:
            # Update land record with blockchain information
            land.blockchain_token_id = result['token_id']
            land.blockchain_tx_hash = result['tx_hash']
            land.is_registered_on_blockchain = True
            land.blockchain_block_number = result['block_number']
            
            db.session.commit()
            
            return jsonify({
                'message': 'Land registered on blockchain successfully',
                'blockchain_data': result
            }), 200
        else:
            return jsonify({'error': 'Failed to register land on blockchain'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500