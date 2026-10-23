"""add updated_at to knowledge base

Revision ID: 00ab2c5d9f8b
Revises: c8eed632ca74
Create Date: 2026-10-23 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '00ab2c5d9f8b'
down_revision = 'c8eed632ca74'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('knowledgebase', sa.Column('updated_at', sa.DateTime(), nullable=True))
    # Existing knowledge bases were last changed when they were created.
    op.execute('UPDATE knowledgebase SET updated_at = created_at')


def downgrade():
    op.drop_column('knowledgebase', 'updated_at')
