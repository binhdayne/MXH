// Deterministic cached overview layout; node/edge identities and metrics stay intact.
const fs=require('node:fs'),crypto=require('node:crypto'),model=require('./dist/graph-model.js');
const bytes=fs.readFileSync(__dirname+'/dist/graph.json'),data=JSON.parse(bytes);
const layout=model.prepare(data.nodes,data.edges,{overview:true});
layout.simulation.tick(300);layout.simulation.force('link',null).force('charge',null).alpha(.08).tick(60);layout.simulation.stop();
const result={version:1,graph_sha256:crypto.createHash('sha256').update(bytes).digest('hex'),nodes:layout.nodes.map(n=>({id:n.id,x:+n.x.toFixed(3),y:+n.y.toFixed(3)})),groups:layout.groups};
if(result.nodes.length!==data.nodes.length||result.nodes.some(n=>!Number.isFinite(n.x)||!Number.isFinite(n.y)))throw Error('Invalid layout');
fs.writeFileSync(__dirname+'/dist/layout.json',JSON.stringify(result));console.log('Cached positions for',result.nodes.length,'nodes and',result.groups.length,'communities.');
