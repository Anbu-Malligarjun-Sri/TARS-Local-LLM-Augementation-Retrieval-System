"""Explicit optional external projection export. Not an automatic sync daemon."""
import argparse
import json
import os
from .service import get_repository
from .external_projections import sync_neo4j, sync_pgvector

def main():
    parser = argparse.ArgumentParser(description='Export private owner memory to a configured dedicated local service')
    parser.add_argument('target',choices=['neo4j','pgvector'])
    args = parser.parse_args()
    repository = get_repository()
    if args.target == 'neo4j':
        from neo4j import GraphDatabase
        uri = os.environ['MEMORY_NEO4J_URI']
        with GraphDatabase.driver(uri, auth=(os.environ.get('MEMORY_NEO4J_USER','neo4j'),os.environ['MEMORY_NEO4J_PASSWORD'])) as driver:
            driver.verify_connectivity()
            result = sync_neo4j(repository,'owner',driver)
    else:
        import psycopg
        repository.project('owner')
        with psycopg.connect(os.environ['MEMORY_PGVECTOR_URL'],connect_timeout=5) as connection:
            result = sync_pgvector(repository,'owner',connection)
    print(json.dumps(result))

if __name__ == '__main__':
    main()
