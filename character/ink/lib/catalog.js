/* Shared catalogue timing. One action is one reviewable demonstration. */
(function(g){
 const data=typeof module!=='undefined'&&module.exports?require('./motions.js'):g.InkMotionData;
 const durations={observe:3,walk:4,run:4,pick:6.4,press:4.8,drag:3.8,hang:4.5,recover:5.5,jump:4,frontflip:4,backflip:4,gunAim:1.5};
 const groups={basic:'基础动作',paper:'论文与纸页',gun:'持枪动作',fall:'失衡与倒下',star:'接星与送回',machine:'推动与操控',contact:'抓握与攀爬'};
 let cursor=0;const shots=Object.entries(data.actions).map(([a,v])=>{const start=cursor;cursor=Math.round((cursor+(durations[a]||Math.ceil(v.duration+.6)))*30)/30;return {a,start,end:cursor,lead:a==='gunFire'?.08:.25,category:v.category};});
 const result={shots,duration:cursor,groups};
 if(typeof module!=='undefined'&&module.exports)module.exports=result;else g.InkCatalog=result;
})(globalThis);
