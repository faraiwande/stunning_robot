from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import JSON
from uuid import uuid4
import re

db = SQLAlchemy()

def utc_now():
    return datetime.now(timezone.utc)

class Seller(db.Model):
    __tablename__ = 'sellers'

    phone = db.Column(db.String(20), primary_key=True, unique=True, nullable=False)
    business_name = db.Column(db.String(100))
    location = db.Column(db.String(100))
    payment_method = db.Column(db.String(50))
    is_verified = db.Column(db.Boolean, default=False)
    is_paid = db.Column(db.Boolean, default=False)
    subscription_type = db.Column(db.String(20), default='free')
    last_payment_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=utc_now)
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime)

    listings = db.relationship('Listing', backref='seller', lazy=True)
    payments = db.relationship('Payment', backref='seller', lazy=True)

    def get_active_listings(self):
        return [listing for listing in self.listings if listing.is_active and not listing.is_deleted]

    def verify_seller(self):
        self.is_verified = True
        return self

class Listing(db.Model):
    __tablename__ = 'listings'
    __table_args__ = (
        db.Index('idx_listing_product', 'product_name'),
        db.Index('idx_listing_location', 'location'),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    seller_phone = db.Column(db.String(20), db.ForeignKey('sellers.phone'), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.String(50))
    price = db.Column(db.Numeric(10, 2))
    location = db.Column(db.String(100))
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    views = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime)

    images = db.relationship('ListingImage', backref='listing', lazy=True)

    def deactivate(self):
        self.is_active = False
        return self

    def increment_views(self):
        self.views += 1
        return self

class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    seller_phone = db.Column(db.String(20), db.ForeignKey('sellers.phone'), nullable=False)
    amount = db.Column(db.Numeric(10, 2))
    method = db.Column(db.String(50))
    reference = db.Column(db.String(100))
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=utc_now)
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime)

    def mark_paid(self, reference):
        self.status = 'confirmed'
        self.reference = reference
        return self

    def mark_failed(self):
        self.status = 'failed'
        return self

class ListingImage(db.Model):
    __tablename__ = 'listing_images'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    listing_id = db.Column(db.String(36), db.ForeignKey('listings.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    uploaded_at = db.Column(db.DateTime, default=utc_now)
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime)

class BuyerAlert(db.Model):
    __tablename__ = 'buyer_alerts'
    __table_args__ = (
        db.Index('idx_buyer_alert_product', 'product_name'),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    phone = db.Column(db.String(20), nullable=False)
    product_name = db.Column(db.String(100))
    location = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime)

class BuyRequest(db.Model):
    __tablename__ = 'buy_requests'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    phone = db.Column(db.String(20), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100))
    quantity = db.Column(db.String(50))
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=utc_now)
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime)

class SellerReview(db.Model):
    __tablename__ = 'seller_reviews'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    seller_phone = db.Column(db.String(20), db.ForeignKey('sellers.phone'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utc_now)

    seller = db.relationship('Seller', backref=db.backref('reviews', lazy=True))
