MATCH (h:WWII:WartimePolitician {name:'Adolf Hitler'}), (g:WWII:WartimeGovernment {name:'United States'})
MERGE (h)-[r:DECLARED_WAR_ON {atlas_key:'atlas-hitler-DECLARED_WAR_ON'}]->(g)
SET r.year=1941, r.sign=-1, r.method='reviewed_text', r.category='opposition',
 r.evidence='After ordering an invasion of the Soviet Union in June 1941, he declared war on the United States in December of the same year.', r.wiki_url='https://en.wikipedia.org/wiki/Special:PermanentLink/1386057491',
 r.reviewer='Codex source check: independent student review pending',
 r.human_review_pending=true, r.review_status='corrected_after_assistant_source_check';

MATCH (h:WWII:WartimePolitician {name:'Adolf Hitler'}), (g:WWII:WartimeGovernment {name:'Soviet Union'})
MERGE (h)-[r:ORDERED_INVASION_OF {atlas_key:'atlas-hitler-ORDERED_INVASION_OF'}]->(g)
SET r.year=1941, r.sign=-1, r.method='reviewed_text', r.category='opposition',
 r.evidence='After ordering an invasion of the Soviet Union in June 1941, he declared war on the United States in December of the same year.', r.wiki_url='https://en.wikipedia.org/wiki/Special:PermanentLink/1386057491',
 r.reviewer='Codex source check: independent student review pending',
 r.human_review_pending=true, r.review_status='corrected_after_assistant_source_check';

