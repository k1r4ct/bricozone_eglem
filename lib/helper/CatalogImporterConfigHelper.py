import os
from decouple import Config, RepositoryEnv

# Load configurations from .env.attributes if exists, otherwise use default .env
if os.path.exists('import-catalog.env'):
    config = Config(RepositoryEnv('import-catalog.env'))
    print("Configurations loaded from: import-catalog.env")
else:
    from decouple import config
    print("Configurations loaded from default .env")