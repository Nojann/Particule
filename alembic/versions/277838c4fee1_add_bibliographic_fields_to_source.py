"""add bibliographic fields to source

Revision ID: 277838c4fee1
Revises: 3f1c7a9e2b4d
Create Date: 2026-10-26 19:40:36.167717

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '277838c4fee1'
down_revision = '3f1c7a9e2b4d'
branch_labels = None
depends_on = None


def upgrade():
    # type and title are required: add them nullable, backfill existing rows, then tighten.
    source_type = sa.Enum('book', 'journal_article', 'book_chapter', 'web_page', name='sourcetype')
    op.add_column('source', sa.Column('type', source_type, nullable=True))
    op.add_column('source', sa.Column('title', sqlmodel.sql.sqltypes.AutoString(length=1024), nullable=True))
    op.execute("UPDATE source SET type = 'book', title = 'Untitled'")
    op.alter_column('source', 'type', existing_type=source_type, nullable=False)
    op.alter_column('source', 'title',
               existing_type=sqlmodel.sql.sqltypes.AutoString(length=1024),
               nullable=False)
    op.add_column('source', sa.Column('editors', sqlmodel.sql.sqltypes.AutoString(length=1024), nullable=True))
    op.add_column('source', sa.Column('container_title', sqlmodel.sql.sqltypes.AutoString(length=1024), nullable=True))
    op.add_column('source', sa.Column('volume', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=True))
    op.add_column('source', sa.Column('issue', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=True))
    op.add_column('source', sa.Column('pages', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=True))
    op.add_column('source', sa.Column('doi', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True))
    op.add_column('source', sa.Column('url', sqlmodel.sql.sqltypes.AutoString(length=2048), nullable=True))
    op.add_column('source', sa.Column('published_date', sa.Date(), nullable=True))
    op.add_column('source', sa.Column('accessed_date', sa.Date(), nullable=True))
    op.alter_column('source', 'authors',
               existing_type=mysql.VARCHAR(length=255),
               type_=sqlmodel.sql.sqltypes.AutoString(length=1024),
               existing_nullable=False)
    op.alter_column('source', 'year',
               existing_type=mysql.INTEGER(display_width=11),
               nullable=True)
    op.alter_column('source', 'edition',
               existing_type=mysql.VARCHAR(length=255),
               nullable=True)
    op.alter_column('source', 'publisher',
               existing_type=mysql.VARCHAR(length=255),
               nullable=True)


def downgrade():
    # Lossy: the new fields are dropped, a null year becomes 0 and a null edition/publisher ''.
    # Fails if a row holds authors longer than 255 characters.
    op.execute("UPDATE source SET year = 0 WHERE year IS NULL")
    op.execute("UPDATE source SET edition = '' WHERE edition IS NULL")
    op.execute("UPDATE source SET publisher = '' WHERE publisher IS NULL")
    op.alter_column('source', 'publisher',
               existing_type=mysql.VARCHAR(length=255),
               nullable=False)
    op.alter_column('source', 'edition',
               existing_type=mysql.VARCHAR(length=255),
               nullable=False)
    op.alter_column('source', 'year',
               existing_type=mysql.INTEGER(display_width=11),
               nullable=False)
    op.alter_column('source', 'authors',
               existing_type=sqlmodel.sql.sqltypes.AutoString(length=1024),
               type_=mysql.VARCHAR(length=255),
               existing_nullable=False)
    op.drop_column('source', 'accessed_date')
    op.drop_column('source', 'published_date')
    op.drop_column('source', 'url')
    op.drop_column('source', 'doi')
    op.drop_column('source', 'pages')
    op.drop_column('source', 'issue')
    op.drop_column('source', 'volume')
    op.drop_column('source', 'container_title')
    op.drop_column('source', 'editors')
    op.drop_column('source', 'title')
    op.drop_column('source', 'type')
