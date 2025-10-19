import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url

DB = os.environ.get('DATABASE_URL') or os.environ.get('DATABASE_URL'.upper())
if not DB:
    print('NO_DATABASE_URL')
    sys.exit(2)

# mask details for logs (do not print password)
try:
    url = make_url(DB)
    print('Found DATABASE_URL:')
    print('  driver:', url.drivername)
    print('  host:', url.host)
    print('  port:', url.port)
    print('  database:', url.database)
    print('  username:', url.username)
except Exception as e:
    print('WARNING: Failed to parse DATABASE_URL:', e)

# attempt connection
try:
    engine = create_engine(DB, connect_args={})
    with engine.connect() as conn:
        # run a simple test query
        res = conn.execute('SELECT 1')
        print('CONNECTED: test query returned', res.scalar())
        sys.exit(0)
except Exception as e:
    print('ERROR: Could not connect to DATABASE_URL')
    print('  Exception:', str(e))
    sys.exit(3)
