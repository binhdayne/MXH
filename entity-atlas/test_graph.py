import json,tempfile,unittest
from pathlib import Path
from graph_core import GraphStore,validate_proposal,check_generation

class RetrievalTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory()
  path=Path(self.temp.name)/'graph.json'
  path.write_text(json.dumps({'nodes':[{'id':str(i),'name':str(i)} for i in range(7)],
   'edges':[{'id':str(i),'source':str(i+1),'target':str(i),'relation':'ATTENDED'} for i in range(5)]}))
  self.graph=GraphStore(path)
 def tearDown(self):self.temp.cleanup()
 def test_reverse_traversal_keeps_original_direction(self):
  context=self.graph.context('0','2')
  self.assertEqual([(x['source'],x['target']) for x in context],[('1','0'),('2','1')])
 def test_four_hop_limit_and_disconnected(self):
  self.assertIsNone(self.graph.path('0','5'))
  self.assertIsNone(self.graph.path('0','6'))
  self.assertEqual(len(self.graph.path('0','4')),4)
 def test_same_entity_and_missing(self):
  self.assertEqual(self.graph.path('0','0'),[])
  with self.assertRaises(ValueError):self.graph.context('0','missing')
 def test_evidence_and_sign_validation(self):
  text='Hitler declared war against the United States.'
  relation={'source':'Hitler','target':'United States','type':'DECLARED_WAR_ON','sign':-1,'year':1941,'evidence':text}
  proposal={'entities':[{'name':'Hitler','type':'Person'},{'name':'United States','type':'Government'}],'relations':[relation]}
  self.assertEqual(len(validate_proposal(proposal,text)['validated_proposals']),1)
  relation['evidence']='Invented quotation'
  self.assertEqual(validate_proposal(proposal,text)['rejected'][0]['reason'],'evidence_not_verbatim')
  relation['evidence']=text;relation['sign']=1
  self.assertEqual(validate_proposal(proposal,text)['rejected'][0]['reason'],'sign_mismatch')
 def test_wrong_entity_type_cannot_pass_quote_check(self):
  text='Hitler declared war against the United States.'
  proposal={'entities':[{'name':'Hitler','type':'Person'},{'name':'United States','type':'Event'}],
   'relations':[{'source':'Hitler','target':'United States','type':'DECLARED_WAR_ON','sign':-1,'year':1941,'evidence':text}]}
  result=validate_proposal(proposal,text)
  self.assertEqual(result['validated_proposals'],[])
  self.assertEqual(result['rejected'][0]['reason'],'domain_range_mismatch')
 def test_citation_ids_alone_do_not_accept_bad_generation(self):
  context=[{'citation':1},{'citation':2}]
  result=check_generation('A dẫn đến B 宣战 [1] [2]',context)
  self.assertTrue(result['citation_ids_valid'])
  self.assertFalse(result['generation_accepted'])
  self.assertIn('causal_language_without_causal_relation',result['verification_flags'])

if __name__=='__main__':unittest.main()
