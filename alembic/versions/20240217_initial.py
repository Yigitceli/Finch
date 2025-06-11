"""create_bitcoin_prices_table

Revision ID: 20240217_initial
Revises: 
Create Date: 2024-02-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '20240217_initial'
down_revision = None
branch_labels = ('bitcoin_prices',)  # Branch label for feature tracking
depends_on = None


def upgrade() -> None:
    # Create bitcoin_prices table with proper constraints and defaults
    op.create_table(
        'bitcoin_prices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('price_usd', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('source', sa.String(length=50), nullable=False, server_default='coingecko'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id', name='pk_bitcoin_prices'),
        sa.CheckConstraint('price_usd > 0', name='check_price_positive')
    )
    
    # Create indexes with proper names
    op.create_index(
        'ix_bitcoin_prices_id',
        'bitcoin_prices',
        ['id'],
        unique=False,
        postgresql_ops={'id': 'btree'}
    )
    op.create_index(
        'ix_bitcoin_prices_timestamp',
        'bitcoin_prices',
        ['timestamp'],
        unique=False,
        postgresql_ops={'timestamp': 'btree'}
    )

    # Add comment to table
    op.execute("COMMENT ON TABLE bitcoin_prices IS 'Stores historical Bitcoin prices from various sources'")


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('ix_bitcoin_prices_timestamp', table_name='bitcoin_prices')
    op.drop_index('ix_bitcoin_prices_id', table_name='bitcoin_prices')
    
    # Drop table
    op.drop_table('bitcoin_prices') 