"""Optional read-model mirrors. Canonical repository always enforces disclosure.

These are explicit operator exports; external services are not queried by the
runtime. Use dedicated databases; don't point at unrelated application graphs.
"""
import json


def sync_neo4j(repository, owner, driver):
    claims = repository.claims(owner)
    # Atomic owner-scoped replace: removes corrected/forgotten graph content.
    def write(tx):
        tx.run('MATCH (n:TarsMemory {owner: $owner}) DETACH DELETE n', owner=owner).consume()
        for c in claims:
            tx.run('''MERGE (a:TarsMemory {owner: $owner, name: $subject})
                      MERGE (b:TarsMemory {owner: $owner, name: $value})
                      CREATE (a)-[:FACT {claim_id: $id, predicate: $predicate, source_id: $source}]->(b)''',
                   owner=owner,subject=c['subject'],value=c['value'],id=c['id'],predicate=c['predicate'],source=c['source_id']).consume()
    with driver.session() as session:
        session.execute_write(write)
    return {'claims':len(claims)}


def sync_pgvector(repository, owner, connection):
    dimension = int(repository.dimension)
    if not 1 <= dimension <= 16000:
        raise ValueError('Invalid vector dimension')
    claims = repository.claims(owner)
    with repository.transaction() as db:
        rows = {r['claim_id']:dict(r) for r in db.execute('SELECT * FROM vectors WHERE owner=? AND model=? AND dimension=?', (owner,repository.embedding_model,dimension)).fetchall()}
    # Unbounded vector column keeps versions/dimensions separate. Runtime queries
    # must filter owner/model/dimension and canonical claim permissions first.
    with connection.transaction():
        connection.execute('CREATE EXTENSION IF NOT EXISTS vector')
        connection.execute('CREATE TABLE IF NOT EXISTS tars_memory_vectors (owner TEXT, claim_id TEXT, model TEXT, dimension INTEGER, embedding vector, PRIMARY KEY(owner,claim_id))')
        connection.execute('DELETE FROM tars_memory_vectors WHERE owner=%s', (owner,))
        for claim in claims:
            if claim['id'] in rows:
                row = rows[claim['id']]
                connection.execute('INSERT INTO tars_memory_vectors VALUES (%s,%s,%s,%s,%s::vector)', (owner,claim['id'],row['model'],dimension,row['vector']))
    return {'vectors':len(rows)}
