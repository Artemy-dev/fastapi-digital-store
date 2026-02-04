"""initial schema: all tables including blocked_email_domains"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '0001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('is_admin', sa.Boolean, default=False)
    )

    # Products
    op.create_table(
        'products',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('price', sa.Float, nullable=False),
        sa.Column('file_url', sa.String(1024), nullable=False)
    )

    # Cart
    op.create_table(
        'cart',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column('product_id', sa.Integer, sa.ForeignKey("products.id"), nullable=False),
        sa.Column('quantity', sa.Integer, default=1)
    )

    # Orders
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column('total_amount', sa.Float, nullable=False),
        sa.Column('status', sa.String(50), default="pending")
    )

    # Blocked Email Domains
    op.create_table(
        'blocked_email_domains',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('domain', sa.String(255), unique=True, nullable=False, index=True)
    )

def downgrade():
    op.drop_table('blocked_email_domains')
    op.drop_table('orders')
    op.drop_table('cart')
    op.drop_table('products')
    op.drop_table('users')
