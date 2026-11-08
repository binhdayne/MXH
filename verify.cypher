MATCH (n:Entity) RETURN labels(n) AS labels, count(*) AS nodes ORDER BY nodes DESC;
MATCH ()-[r]->() RETURN type(r) AS relation, r.sign AS sign, count(*) AS edges ORDER BY edges DESC, relation;
MATCH (n:Entity)-[r]-() WITH n, sum(CASE WHEN r.sign = 1 THEN 1 ELSE 0 END) AS positive, sum(CASE WHEN r.sign = -1 THEN 1 ELSE 0 END) AS negative RETURN n.name AS name, positive, negative ORDER BY positive + negative DESC LIMIT 10;
MATCH (a)-[r]->(b) WHERE r.method = 'nlp' RETURN a.name AS source, type(r) AS relation, b.name AS target, r.date AS date, r.wiki_url AS wiki ORDER BY date, relation;
MATCH (a:Person)-[r:ELECTORAL_RIVAL]-(b:Person) WHERE a.name = 'Rishi Sunak' RETURN a.name AS candidate, b.name AS opponent, r.section AS constituency, r.wiki_url AS wiki;
