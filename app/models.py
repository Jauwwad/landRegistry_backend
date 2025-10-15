from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from enum import Enum

class UserRole(Enum):
    USER = "user"
    ADMIN = "admin"

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    wallet_address = db.Column(db.String(42), unique=True, nullable=True)
    role = db.Column(db.Enum(UserRole), default=UserRole.USER, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lands = db.relationship('Land', backref='owner_user', lazy=True, foreign_keys='Land.owner_id')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'wallet_address': self.wallet_address,
            'role': self.role.value,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'address': self.address,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Land(db.Model):
    __tablename__ = 'lands'
    
    id = db.Column(db.Integer, primary_key=True)
    token_id = db.Column(db.Integer, unique=True, nullable=True)  # Blockchain token ID
    property_id = db.Column(db.String(50), unique=True, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    wallet_address = db.Column(db.String(42), nullable=True)  # Current owner's wallet
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(255), nullable=False)
    area = db.Column(db.Float, nullable=False)  # in square meters
    property_type = db.Column(db.String(50), nullable=False)  # residential, commercial, agricultural
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=True)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_registered_on_blockchain = db.Column(db.Boolean, default=False, nullable=False)
    blockchain_tx_hash = db.Column(db.String(66), nullable=True)
    blockchain_token_id = db.Column(db.Integer, nullable=True)  # Token ID from smart contract
    blockchain_block_number = db.Column(db.Integer, nullable=True)  # Block number of registration
    ipfs_hash = db.Column(db.String(100), nullable=True)  # For documents
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, verified, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transfers = db.relationship('LandTransfer', backref='land', lazy=True)
    documents = db.relationship('LandDocument', backref='land', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'token_id': self.token_id,
            'property_id': self.property_id,
            'owner_id': self.owner_id,
            'wallet_address': self.wallet_address,
            'title': self.title,
            'description': self.description,
            'location': self.location,
            'area': self.area,
            'property_type': self.property_type,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'price': self.price,
            'is_verified': self.is_verified,
            'is_registered_on_blockchain': self.is_registered_on_blockchain,
            'blockchain_tx_hash': self.blockchain_tx_hash,
            'blockchain_token_id': self.blockchain_token_id,
            'blockchain_block_number': self.blockchain_block_number,
            'ipfs_hash': self.ipfs_hash,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'owner': self.owner_user.to_dict() if self.owner_user else None
        }

class LandTransfer(db.Model):
    __tablename__ = 'land_transfers'
    
    id = db.Column(db.Integer, primary_key=True)
    land_id = db.Column(db.Integer, db.ForeignKey('lands.id'), nullable=False)
    from_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    from_wallet = db.Column(db.String(42), nullable=True)
    to_wallet = db.Column(db.String(42), nullable=True)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, completed, failed
    blockchain_tx_hash = db.Column(db.String(66), nullable=True)
    initiated_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    from_user = db.relationship('User', foreign_keys=[from_user_id], backref='transfers_from')
    to_user = db.relationship('User', foreign_keys=[to_user_id], backref='transfers_to')
    
    def to_dict(self):
        return {
            'id': self.id,
            'land_id': self.land_id,
            'from_user_id': self.from_user_id,
            'to_user_id': self.to_user_id,
            'from_wallet': self.from_wallet,
            'to_wallet': self.to_wallet,
            'price': self.price,
            'status': self.status,
            'blockchain_tx_hash': self.blockchain_tx_hash,
            'initiated_at': self.initiated_at.isoformat() if self.initiated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'from_user': self.from_user.to_dict() if self.from_user else None,
            'to_user': self.to_user.to_dict() if self.to_user else None
        }

class LandDocument(db.Model):
    __tablename__ = 'land_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    land_id = db.Column(db.Integer, db.ForeignKey('lands.id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # deed, survey, tax_record, etc.
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    ipfs_hash = db.Column(db.String(100), nullable=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    uploader = db.relationship('User', backref='uploaded_documents')
    
    def to_dict(self):
        return {
            'id': self.id,
            'land_id': self.land_id,
            'document_type': self.document_type,
            'file_name': self.file_name,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'ipfs_hash': self.ipfs_hash,
            'uploaded_by': self.uploaded_by,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'uploader': self.uploader.to_dict() if self.uploader else None
        }