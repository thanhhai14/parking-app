"""initial migration

Revision ID: 001
Revises: 
Create Date: 2026-06-17 16:50:00.000000

"""
from typing import Sequence, Union
import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
import bcrypt

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Create roles table
    op.create_table(
        'roles',
        sa.Column('id', sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column('code', sa.String(length=100), nullable=False, unique=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('permissions', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), primary_key=True, default=uuid.uuid4),
        sa.Column('username', sa.String(length=100), nullable=False, unique=True),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('role_id', sa.UUID(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='RESTRICT')
    )
    
    # Seed default roles
    admin_role_id = str(uuid.uuid4())
    guard_role_id = str(uuid.uuid4())
    
    op.execute(
        f"INSERT INTO roles (id, code, name, description, permissions) VALUES "
        f"('{admin_role_id}', 'admin', 'Administrator', 'System Administrator', '{{\"all\": true}}'), "
        f"('{guard_role_id}', 'guard', 'Security Guard', 'Parking Lot Guard', '{{\"parking_session.create\": true, \"parking_session.checkout\": true}}')"
    )
    
    # Seed default admin user (password: admin123)
    password_bytes = "admin123".encode('utf-8')
    salt = bcrypt.gensalt()
    admin_password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    admin_user_id = str(uuid.uuid4())
    
    op.execute(
        f"INSERT INTO users (id, username, password_hash, full_name, role_id, is_active) VALUES "
        f"('{admin_user_id}', 'admin', '{admin_password_hash}', 'System Administrator', '{admin_role_id}', true)"
    )


def downgrade() -> None:
    op.drop_table('users')
    op.drop_table('roles')
