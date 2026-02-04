"""seed blocked_email_domains from domains.txt"""

from alembic import op
from sqlalchemy.sql import table, column
from sqlalchemy import String
import os

# revision identifiers
revision = '0002_seed_blocked_email_domains'
down_revision = '0001_initial_schema'
branch_labels = None
depends_on = None

FILE = "domains.txt"

def upgrade():
    blocked_table = table('blocked_email_domains',
                          column('domain', String))

    if os.path.exists(FILE):
        with open(FILE) as f:
            domains = [d.strip() for d in f if d.strip()]
        if domains:
            op.bulk_insert(blocked_table, [{"domain": d} for d in domains])

def downgrade():
    op.execute("DELETE FROM blocked_email_domains")
