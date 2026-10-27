"""add other source type and note

Revision ID: 22bea583b66a
Revises: 277838c4fee1
Create Date: 2026-10-27 15:29:19.240267

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '22bea583b66a'
down_revision = '277838c4fee1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('source', sa.Column('note', sa.Text(), nullable=True))
    op.alter_column('source', 'type',
               existing_type=mysql.ENUM('book', 'journal_article', 'book_chapter', 'web_page'),
               type_=sa.Enum('book', 'journal_article', 'book_chapter', 'web_page', 'other', name='sourcetype'),
               existing_nullable=False)
    # Optional for the other type only; the rule is checked by the API, not the database.
    op.alter_column('source', 'authors',
               existing_type=mysql.VARCHAR(length=1024),
               nullable=True)


def downgrade():
    # Lossy: notes are dropped, other sources become books and a null authors becomes ''.
    op.execute("UPDATE source SET type = 'book' WHERE type = 'other'")
    op.execute("UPDATE source SET authors = '' WHERE authors IS NULL")
    op.alter_column('source', 'authors',
               existing_type=mysql.VARCHAR(length=1024),
               nullable=False)
    op.alter_column('source', 'type',
               existing_type=sa.Enum('book', 'journal_article', 'book_chapter', 'web_page', 'other', name='sourcetype'),
               type_=mysql.ENUM('book', 'journal_article', 'book_chapter', 'web_page'),
               existing_nullable=False)
    op.drop_column('source', 'note')
