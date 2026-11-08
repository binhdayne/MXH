UNWIND [
  {name:'Cairo Conference', year:1943, page:'Cairo_Conference', people:['Winston Churchill','Franklin D. Roosevelt','Chiang Kai-shek']},
  {name:'Tehran Conference', year:1943, page:'Tehran_Conference', people:['Winston Churchill','Franklin D. Roosevelt','Joseph Stalin']},
  {name:'Yalta Conference', year:1945, page:'Yalta_Conference', people:['Winston Churchill','Franklin D. Roosevelt','Joseph Stalin']},
  {name:'Potsdam Conference', year:1945, page:'Potsdam_Conference', people:['Winston Churchill','Clement Attlee','Harry S. Truman','Joseph Stalin']},
  {name:'Greater East Asia Conference', year:1943, page:'Greater_East_Asia_Conference', people:['Hideki Tōjō','Ba Maw','Zhang Jinghui','Wang Jingwei','Wan Waithayakon','Jose P. Laurel','Subhas Chandra Bose']}
] AS row
MERGE (e:WWII:WartimeEvent {name:row.name})
SET e.year = row.year, e.wiki_url = 'https://en.wikipedia.org/wiki/' + row.page
WITH e, row UNWIND row.people AS name
MERGE (p:WWII:WartimePolitician {name:name})
MERGE (p)-[r:ATTENDED]->(e)
SET r.year = row.year, r.wiki_url = e.wiki_url;

UNWIND [
  {name:'Tripartite Pact', year:1940, page:'Tripartite_Pact', people:['Joachim von Ribbentrop','Galeazzo Ciano','Saburō Kurusu']},
  {name:'Molotov–Ribbentrop Pact', year:1939, page:'Molotov%E2%80%93Ribbentrop_Pact', people:['Vyacheslav Molotov','Joachim von Ribbentrop']},
  {name:'Soviet–Japanese Neutrality Pact', year:1941, page:'Soviet%E2%80%93Japanese_Neutrality_Pact', people:['Vyacheslav Molotov','Yōsuke Matsuoka','Yoshitsugu Tatekawa']}
] AS row
MERGE (e:WWII:WartimeEvent {name:row.name})
SET e.year = row.year, e.wiki_url = 'https://en.wikipedia.org/wiki/' + row.page
WITH e, row UNWIND row.people AS name
MERGE (p:WWII:WartimePolitician {name:name})
MERGE (p)-[r:SIGNED]->(e)
SET r.year = row.year, r.wiki_url = e.wiki_url;

MATCH (e:WWII:WartimeEvent {name:'Tripartite Pact'})
MERGE (p:WWII:WartimePolitician {name:'Adolf Hitler'})
MERGE (p)-[r:ATTENDED]->(e)
SET r.year = e.year, r.wiki_url = e.wiki_url;

UNWIND [
  {p:'Winston Churchill', g:'United Kingdom', page:'Tehran_Conference', event:'Tehran Conference'},
  {p:'Franklin D. Roosevelt', g:'United States', page:'Tehran_Conference', event:'Tehran Conference'},
  {p:'Joseph Stalin', g:'Soviet Union', page:'Tehran_Conference', event:'Tehran Conference'},
  {p:'Chiang Kai-shek', g:'Republic of China (Nationalist government)', page:'Cairo_Conference', event:'Cairo Conference'},
  {p:'Joachim von Ribbentrop', g:'Nazi Germany', page:'Tripartite_Pact', event:'Tripartite Pact'},
  {p:'Galeazzo Ciano', g:'Kingdom of Italy', page:'Tripartite_Pact', event:'Tripartite Pact'},
  {p:'Saburō Kurusu', g:'Empire of Japan', page:'Tripartite_Pact', event:'Tripartite Pact'},
  {p:'Hideki Tōjō', g:'Empire of Japan', page:'Greater_East_Asia_Conference', event:'Greater East Asia Conference'}
] AS row
MATCH (p:WWII:WartimePolitician {name:row.p}), (e:WWII:WartimeEvent {name:row.event})
MERGE (g:WWII:WartimeGovernment {name:row.g})
MERGE (p)-[r:REPRESENTED {event:row.event}]->(g)
SET r.year = e.year, r.wiki_url = 'https://en.wikipedia.org/wiki/' + row.page;

UNWIND [
  ['Nazi Germany','Kingdom of Italy'], ['Nazi Germany','Empire of Japan'], ['Kingdom of Italy','Empire of Japan']
] AS pair
MATCH (a:WWII:WartimeGovernment {name:pair[0]}), (b:WWII:WartimeGovernment {name:pair[1]})
MERGE (a)-[r:MILITARY_PACT {event:'Tripartite Pact'}]->(b)
SET r.sign = 1, r.symmetric = true, r.year = 1940, r.wiki_url = 'https://en.wikipedia.org/wiki/Tripartite_Pact';

UNWIND [
  {a:'Nazi Germany', b:'Soviet Union', event:'Molotov–Ribbentrop Pact', year:1939, page:'Molotov%E2%80%93Ribbentrop_Pact'},
  {a:'Soviet Union', b:'Empire of Japan', event:'Soviet–Japanese Neutrality Pact', year:1941, page:'Soviet%E2%80%93Japanese_Neutrality_Pact'}
] AS row
MATCH (a:WWII:WartimeGovernment {name:row.a}), (b:WWII:WartimeGovernment {name:row.b})
MERGE (a)-[r:NON_AGGRESSION_PACT {event:row.event}]->(b)
SET r.sign = 1, r.symmetric = true, r.year = row.year, r.wiki_url = 'https://en.wikipedia.org/wiki/' + row.page;

MATCH (a:WWII:WartimeGovernment {name:'Nazi Germany'}), (b:WWII:WartimeGovernment {name:'Soviet Union'})
MERGE (a)-[r:INVADED {event:'Operation Barbarossa'}]->(b)
SET r.sign = -1, r.year = 1941, r.date = date('1941-06-22'), r.wiki_url = 'https://en.wikipedia.org/wiki/Operation_Barbarossa';

UNWIND [
  {a:'Nazi Germany', b:'United States', date:'1941-12-11', page:'German_declaration_of_war_on_the_United_States'},
  {a:'United States', b:'Empire of Japan', date:'1941-12-08', page:'German_declaration_of_war_on_the_United_States'},
  {a:'Soviet Union', b:'Empire of Japan', date:'1945-08-08', page:'Soviet%E2%80%93Japanese_Neutrality_Pact'}
] AS row
MATCH (a:WWII:WartimeGovernment {name:row.a}), (b:WWII:WartimeGovernment {name:row.b})
MERGE (a)-[r:DECLARED_WAR_ON {date:date(row.date)}]->(b)
SET r.sign = -1, r.year = r.date.year, r.wiki_url = 'https://en.wikipedia.org/wiki/' + row.page;

MATCH (n:WWII) RETURN labels(n) AS labels, count(*) AS nodes ORDER BY labels;
MATCH (:WWII)-[r]->(:WWII) RETURN type(r) AS type, count(*) AS edges ORDER BY type;
