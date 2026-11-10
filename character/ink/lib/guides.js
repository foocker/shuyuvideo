/* Preview fixtures only. Exported actors never include a floor or ladder. */
(function(g){g.InkGuides={draw(node,action,rig,visible=true){
 const ns='http://www.w3.org/2000/svg';node.replaceChildren();if(!visible)return;
 const o=rig.options,s=o.scale,x=o.x,y=o.y,flip=o.mirror?-1:1;
 const line=(x1,y1,x2,y2)=>{const n=document.createElementNS(ns,'line');for(const[k,v]of Object.entries({x1:x+flip*x1*s,y1:y+y1*s,x2:x+flip*x2*s,y2:y+y2*s,stroke:'#9aa79e','stroke-width':Math.max(1,s*.45)}))n.setAttribute(k,v);node.append(n);};
 if(action.guide?.kind==='ladder'){
  for(const dx of [-28,26])line(action.guide.x+dx,-149,action.guide.x+dx,2);
  for(const yy of action.guide.rungs||[-132,-113,-105,-68,-46,-24,-3])line(action.guide.x-28,yy,action.guide.x+26,yy);
 }else if(action.guide?.kind==='bar'){
  const [xx,yy]=action.guide.anchor;line(xx-25,yy,xx+25,yy);
 }
}};})(globalThis);
