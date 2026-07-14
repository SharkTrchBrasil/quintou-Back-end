"""add performance indexes

Revision ID: add_performance_indexes
Revises: add_password_reset_tokens
Create Date: 2026-07-13 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_performance_indexes'
down_revision = 'add_password_reset'
branch_labels = None
depends_on = None


def upgrade():
    # Bookings table indexes
    op.create_index('idx_bookings_space_date_status', 'bookings', ['space_id', 'date', 'status'])
    op.create_index('idx_bookings_guest_id', 'bookings', ['guest_id'])
    op.create_index('idx_bookings_status', 'bookings', ['status'])
    op.create_index('idx_bookings_created_at', 'bookings', ['created_at'])
    
    # Conversations table indexes
    op.create_index('idx_conversations_host_id', 'conversations', ['host_id'])
    op.create_index('idx_conversations_guest_id', 'conversations', ['guest_id'])
    op.create_index('idx_conversations_last_message_at', 'conversations', ['last_message_at'])
    
    # Messages table indexes
    op.create_index('idx_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('idx_messages_created_at', 'messages', ['created_at'])
    op.create_index('idx_messages_sender_id', 'messages', ['sender_id'])
    
    # Spaces table indexes for search
    op.create_index('idx_spaces_category_id', 'spaces', ['category_id'])
    op.create_index('idx_spaces_host_id', 'spaces', ['host_id'])
    op.create_index('idx_spaces_is_active_approved', 'spaces', ['is_active', 'is_approved'])
    op.create_index('idx_spaces_city_state', 'spaces', ['city', 'state'])
    
    # Users table indexes
    op.create_index('idx_users_email', 'users', ['email'], unique=True)
    op.create_index('idx_users_phone', 'users', ['phone'], unique=True)
    op.create_index('idx_users_cpf', 'users', ['cpf'], unique=True)
    op.create_index('idx_users_is_host', 'users', ['is_host'])
    
    # Reviews table indexes
    op.create_index('idx_reviews_booking_id', 'reviews', ['booking_id'])
    op.create_index('idx_reviews_reviewer_id', 'reviews', ['reviewer_id'])
    op.create_index('idx_reviews_reviewee_id', 'reviews', ['reviewee_id'])
    
    # Notifications table indexes
    op.create_index('idx_notifications_user_id_read', 'notifications', ['user_id', 'is_read'])
    op.create_index('idx_notifications_created_at', 'notifications', ['created_at'])
    
    # Favorites table indexes
    op.create_index('idx_favorites_user_space', 'favorites', ['user_id', 'space_id'], unique=True)
    
    # Password reset tokens index
    op.create_index('idx_password_reset_token', 'password_reset_tokens', ['token'], unique=True)
    op.create_index('idx_password_reset_user_expires', 'password_reset_tokens', ['user_id', 'expires_at'])


def downgrade():
    # Drop all indexes
    op.drop_index('idx_bookings_space_date_status', 'bookings')
    op.drop_index('idx_bookings_guest_id', 'bookings')
    op.drop_index('idx_bookings_status', 'bookings')
    op.drop_index('idx_bookings_created_at', 'bookings')
    
    op.drop_index('idx_conversations_host_id', 'conversations')
    op.drop_index('idx_conversations_guest_id', 'conversations')
    op.drop_index('idx_conversations_last_message_at', 'conversations')
    
    op.drop_index('idx_messages_conversation_id', 'messages')
    op.drop_index('idx_messages_created_at', 'messages')
    op.drop_index('idx_messages_sender_id', 'messages')
    
    op.drop_index('idx_spaces_category_id', 'spaces')
    op.drop_index('idx_spaces_host_id', 'spaces')
    op.drop_index('idx_spaces_is_active_approved', 'spaces')
    op.drop_index('idx_spaces_city_state', 'spaces')
    
    op.drop_index('idx_users_email', 'users')
    op.drop_index('idx_users_phone', 'users')
    op.drop_index('idx_users_cpf', 'users')
    op.drop_index('idx_users_is_host', 'users')
    
    op.drop_index('idx_reviews_booking_id', 'reviews')
    op.drop_index('idx_reviews_reviewer_id', 'reviews')
    op.drop_index('idx_reviews_reviewee_id', 'reviews')
    
    op.drop_index('idx_notifications_user_id_read', 'notifications')
    op.drop_index('idx_notifications_created_at', 'notifications')
    
    op.drop_index('idx_favorites_user_space', 'favorites')
    
    op.drop_index('idx_password_reset_token', 'password_reset_tokens')
    op.drop_index('idx_password_reset_user_expires', 'password_reset_tokens')
