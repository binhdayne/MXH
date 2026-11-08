MATCH (n:WWII) RETURN labels(n) AS labels, count(*) AS nodes ORDER BY nodes DESC;
MATCH (:WWII)-[r]->(:WWII) RETURN type(r) AS relation, r.sign AS sign, count(*) AS edges ORDER BY edges DESC;
MATCH (a:WWII)-[r]->(b:WWII) WHERE r.method IN ['nlp','manual'] RETURN a, r, b;
