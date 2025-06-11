"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    """
    Upgrade database schema.
    
    This function is called when upgrading the database to this version.
    It should contain all the necessary changes to upgrade the schema.
    
    Note: Always test migrations in a development environment before applying to production.
    """
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """
    Downgrade database schema.
    
    This function is called when downgrading the database from this version.
    It should contain all the necessary changes to revert the schema to its previous state.
    
    Warning: Downgrading may result in data loss. Always backup your database before downgrading.
    """
    ${downgrades if downgrades else "pass"} 