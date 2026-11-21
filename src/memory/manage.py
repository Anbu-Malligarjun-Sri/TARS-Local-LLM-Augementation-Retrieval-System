"""Operator utilities. Never rewrite or remove source JSON."""
import argparse
import json
from pathlib import Path
from .service import get_repository
from .conversations import import_legacy
from src.utils.config import get_config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=['import','rebuild','status','backup'])
    parser.add_argument('--destination',type=Path)
    args = parser.parse_args()
    repo = get_repository()
    config = get_config()
    if args.operation == 'import':
        if repo.path.exists() and not repo.database_url:
            folder = repo.path.parent/'backups'
            folder.mkdir(exist_ok=True)
            from uuid import uuid4
            repo.backup(folder/(str(uuid4())+'.sqlite3'))
        result = import_legacy(repo,config.project_root/'data'/'conversations',repo.path.parent/'legacy-snapshots')
    elif args.operation == 'rebuild':
        result = repo.project('owner')
    elif args.operation == 'backup':
        if args.destination is None:
            parser.error('--destination is required for backup')
        result = {'backup':str(repo.backup(args.destination))}
    else:
        result = repo.status('owner')
    print(json.dumps(result))

if __name__ == '__main__':
    main()
