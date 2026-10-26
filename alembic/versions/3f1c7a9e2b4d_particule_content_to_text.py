"""particule content to text

Revision ID: 3f1c7a9e2b4d
Revises: 00ab2c5d9f8b
Create Date: 2026-10-26 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3f1c7a9e2b4d'
down_revision = '00ab2c5d9f8b'
branch_labels = None
depends_on = None


def upgrade():
    # The initial schema created it as AutoString, i.e. VARCHAR(255) on MySQL.
    op.alter_column('particule', 'content',
                    existing_type=sa.String(length=255),
                    type_=sa.Text(),
                    existing_nullable=False)


def downgrade():
    # Fails if a row holds more than 255 characters.
    op.alter_column('particule', 'content',
                    existing_type=sa.Text(),
                    type_=sa.String(length=255),
                    existing_nullable=False)
