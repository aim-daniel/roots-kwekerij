/* Roots: de plant op de grondlijn en de wortel die tijdens het scrollen door de pagina groeit.
   Werkt op elke pagina met #under en #rootsvg; stappen (#steps), ronde foto, kompas en
   plantencarrousel zijn optioneel. Geen bibliotheken, Safari 16.3-veilig (geen ?. of ??). */
(function(){
  'use strict';
  var NS='http://www.w3.org/2000/svg';
  function el(n,a,p){var e=document.createElementNS(NS,n);for(var k in a)e.setAttribute(k,a[k]);if(p)p.appendChild(e);return e;}
  function rng(s){return function(){s|=0;s=s+0x6D2B79F5|0;var t=Math.imul(s^s>>>15,1|s);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};}
  function clamp(v,a,b){return v<a?a:v>b?b:v;}
  function sstep(a,b,v){var t=clamp((v-a)/(b-a),0,1);return t*t*(3-2*t);}
  var reduce=!!(window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches);

  /* header: licht boven de grond, donker eronder */
  var top=document.getElementById('top'), hero=document.querySelector('.hero');
  function header(){var y=window.pageYOffset||0;top.classList.toggle('scrolled',y>8);top.classList.toggle('dark',y>hero.offsetHeight-72);}

  /* plant: een moederrozet met twee kuikens (hens & chicks) op de grondlijn */
  (function(){
    var s=document.getElementById('plant');if(!s)return;
    var d=el('defs',{},s);
    function g(id,a,b,c){var x=el('linearGradient',{id:id,x1:0,y1:1,x2:0,y2:0},d);el('stop',{offset:0,'stop-color':a},x);el('stop',{offset:.62,'stop-color':b},x);el('stop',{offset:1,'stop-color':c},x);}
    g('lb','#3F6636','#5E7F4C','#7A2630');g('lm','#5C8A4A','#7DA864','#A9363A');g('lf','#7FAE66','#A4CB86','#C64C3D');
    function rosette(cx,cy,sc){
      var rows=[{n:11,sp:176,len:78,w:21,f:'lb'},{n:9,sp:146,len:68,w:22,f:'lm'},{n:7,sp:100,len:56,w:21,f:'lf'},{n:3,sp:34,len:40,w:16,f:'lf'}];
      var grp=el('g',{transform:'translate('+cx+' '+cy+') scale('+sc+')'},s);
      rows.forEach(function(r){for(var i=0;i<r.n;i++){
        var a=-r.sp/2+r.sp*i/(r.n-1),L=r.len*(.55+.45*Math.cos(a*Math.PI/180)),w=r.w;
        el('path',{d:'M0 0C'+w+' '+(-L*.3).toFixed(1)+' '+(w*.72).toFixed(1)+' '+(-L*.8).toFixed(1)+' 0 '+(-L).toFixed(1)+'C'+(-w*.72).toFixed(1)+' '+(-L*.8).toFixed(1)+' '+(-w)+' '+(-L*.3).toFixed(1)+' 0 0Z',fill:'url(#'+r.f+')',stroke:'rgba(40,28,18,.28)','stroke-width':.8,transform:'rotate('+a.toFixed(1)+') scale(1 .9)'},grp);
      }});
    }
    el('path',{d:'M-18 -3C-58 -26 -92 -18 -112 -1',fill:'none',stroke:'#6A9655','stroke-width':3,'stroke-linecap':'round'},s);
    el('path',{d:'M18 -3C54 -24 86 -16 106 -1',fill:'none',stroke:'#6A9655','stroke-width':3,'stroke-linecap':'round'},s);
    rosette(-114,0,.42);rosette(108,0,.36);rosette(0,0,1);
  })();

  /* wortels: één penwortel door de hele site, zijwortels en takken naar de stappen */
  var U=document.getElementById('under'), RS=document.getElementById('rootsvg'), OFF=40, st=null;
  function rel(e){var a=e.getBoundingClientRect(),b=U.getBoundingClientRect();return{top:a.top-b.top,bottom:a.bottom-b.top,left:a.left-b.left,right:a.right-b.left,cy:(a.top+a.bottom)/2-b.top};}
  function catmull(p,step){
    var o=[];
    for(var i=0;i<p.length-1;i++){
      var p0=p[i-1]||p[i],p1=p[i],p2=p[i+1],p3=p[i+2]||p2,n=Math.max(2,Math.ceil(Math.hypot(p2[0]-p1[0],p2[1]-p1[1])/step));
      for(var j=0;j<n;j++){var t=j/n,t2=t*t,t3=t2*t;
        o.push([.5*(2*p1[0]+(-p0[0]+p2[0])*t+(2*p0[0]-5*p1[0]+4*p2[0]-p3[0])*t2+(-p0[0]+3*p1[0]-3*p2[0]+p3[0])*t3),
                .5*(2*p1[1]+(-p0[1]+p2[1])*t+(2*p0[1]-5*p1[1]+4*p2[1]-p3[1])*t2+(-p0[1]+3*p1[1]-3*p2[1]+p3[1])*t3)]);}
    }
    o.push(p[p.length-1]);return o;
  }
  function lens(s){var L=[0];for(var i=1;i<s.length;i++)L.push(L[i-1]+Math.hypot(s[i][0]-s[i-1][0],s[i][1]-s[i-1][1]));return L;}
  function line(s){var o='M';for(var i=0;i<s.length;i++)o+=(i?'L':'')+s[i][0].toFixed(1)+' '+s[i][1].toFixed(1);return o;}
  function bez(a,b,c,d,n){var o=[];for(var i=0;i<=n;i++){var t=i/n,u=1-t;o.push([u*u*u*a[0]+3*u*u*t*b[0]+3*u*t*t*c[0]+t*t*t*d[0],u*u*u*a[1]+3*u*u*t*b[1]+3*u*t*t*c[1]+t*t*t*d[1]]);}return o;}
  function search(arr,v,get){var lo=0,hi=arr.length-1;while(lo<hi){var m=(lo+hi)>>1;if(get(arr[m])<v)lo=m+1;else hi=m;}return lo;}

  function build(){
    var W=U.clientWidth,H=U.clientHeight;if(!W||!H)return;
    var mob=window.matchMedia?matchMedia('(max-width:760px)').matches:W<=760,SEED=20261001,r=rng(SEED),cx=W/2;
    RS.setAttribute('width',W);RS.setAttribute('height',H+OFF);RS.setAttribute('viewBox','0 '+(-OFF)+' '+W+' '+(H+OFF));
    while(RS.firstChild)RS.removeChild(RS.firstChild);
    var stepsBox=document.getElementById('steps'),pr=stepsBox?rel(stepsBox):{top:-1e6,bottom:-1e6},gu=document.querySelector('.group-uit'),gq=gu?rel(gu):null;
    // telefoon: links bij 'de kas in', door het label 'de kas uit' heen naar rechts
    function spineX(y){if(!mob)return cx;var t=gq?sstep(gq.top-60,gq.bottom+50,y):0;return 26+(W-52)*t;}

    // penwortel: route met lichte slingering, in de stappen strak langs de as
    // bij twee kolommen (over ons) loopt de wortel door de tussenruimte, niet door de tekst
    // bij 'over ons' loopt de wortel recht door de ronde foto: erin aan de bovenkant, eruit aan de onderkant
    // ook door het midden van het kompas bij 'inkopen'
    var lanes=[],lel=document.querySelectorAll('.about-photo,.compass .hub i');
    for(var li=0;li<lel.length;li++){var c1=rel(lel[li]);lanes.push({x:(c1.left+c1.right)/2,top:c1.top,bottom:c1.bottom});}
    function nearLane(y){for(var k=0;k<lanes.length;k++)if(y>lanes[k].top-420&&y<lanes[k].bottom+420)return true;return false;}
    var wp=[[cx,-22],[cx,40]],ph=r()*6;
    for(var y=150;y<H-60;y+=((mob&&gq&&y>gq.top-420&&y<gq.bottom+200)||nearLane(y)?55:110)+r()*30){
      var w=sstep(pr.top-460,pr.top-120,y)*(1-sstep(pr.bottom+40,pr.bottom+380,y));
      var base=cx+(spineX(y)-cx)*w,amp=(mob?W*.16:W*.09)*(1-w)+(mob?2:14)*w;
      for(var k=0;k<lanes.length;k++){var ln=lanes[k],lw=sstep(ln.top-360,ln.top+10,y)*(1-sstep(ln.bottom-10,ln.bottom+360,y));base+=(ln.x-base)*lw;amp*=1-lw;}
      wp.push([base+amp*Math.sin(y/520+ph)+(r()-.5)*amp*.35,y]);
    }
    wp.push([wp[wp.length-1][0],H-6]);
    var P=catmull(wp,6),L=lens(P),T=L[L.length-1];
    function nearest(yy){return P[search(P,yy,function(p){return p[1];})];}

    var gLat=el('g',{},RS),gTap=el('g',{},RS),roots=[];
    function addPath(pts,w,cls,s,d,g){
      var l=lens(pts),len=l[l.length-1];if(len<4)return null;
      var e=el('path',{d:line(pts),'class':cls,'stroke-width':w.toFixed(2),'stroke-dasharray':len.toFixed(1)+' '+len.toFixed(1),'stroke-dashoffset':len.toFixed(1)},g||gLat);
      e.style.visibility='hidden';
      var o={e:e,len:len,s:s,d:d,p:-1};roots.push(o);return o;
    }
    function walk(x,y,a,len,depth){
      var pts=[[x,y]],stp=6,n=Math.max(2,Math.round(len/stp));
      for(var i=0;i<n;i++){
        a+=(r()-.5)*.32+(Math.PI/2-a)*.014*depth;
        x+=Math.cos(a)*stp;y+=Math.sin(a)*stp;
        if(x<4||x>W-4){a=Math.PI-a;x=clamp(x,4,W-4);}
        if(y>H-10)break;
        pts.push([x,y]);
      }
      return pts;
    }
    function branch(pts,w,depth,s,d){
      var o=addPath(pts,w,'r r'+depth,s,d);if(!o||depth>=3)return;
      var n=depth===1?2+Math.floor(r()*3):(r()<.65?1+Math.floor(r()*2):0);
      for(var k=0;k<n;k++){
        var f=.18+.72*r(),i=Math.floor(f*(pts.length-2)),p=pts[i],q=pts[i+1],ba=Math.atan2(q[1]-p[1],q[0]-p[0]);
        var a=ba+(r()<.5?-1:1)*(.45+r()*.65),cl=o.len*(.22+r()*.3);
        branch(walk(p[0],p[1],a,cl,depth+1),Math.max(.8,w*.52),depth+1,s+d*f,Math.max(80,cl*1.05));
      }
    }
    // kroon: brede zijwortels vlak onder de plant, zoals in de tekening
    // eigen toevalsreeks per onderdeel: een hogere pagina (vraag opengeklapt) verandert de rest niet
    r=rng(SEED+1);
    var crown=mob?5:7;
    for(var c=0;c<crown;c++){
      var side=c%2?1:-1,y0=-14+c*(mob?16:14),p=nearest(y0),spread=.06+c*.11+r()*.1;
      var a=side>0?spread:Math.PI-spread,len=(mob?W*.6:W*.36)*(1-c*.06)*(.85+r()*.3);
      branch(walk(p[0],p[1],a,len,1),(mob?3.2:4.6)*(1-c*.06),1,y0+16,len*.75);
    }
    // zijwortels verder naar beneden, niet tussen de stappen
    r=rng(SEED+2);
    // geen losse zijwortels rond het kompas: daar lopen alleen de takken naar west en oost
    var cmp=document.querySelector('.compass'),cr=cmp?rel(cmp):null;
    var yy=560;
    while(yy<H-260){
      if(!(yy>pr.top-120&&yy<pr.bottom+60)&&!(cr&&yy>cr.top-260&&yy<cr.bottom+80)){
        var pp=nearest(yy),sd=r()<.5?-1:1,ang=sd>0?.35+r()*.6:Math.PI-(.35+r()*.6),ln=W*(mob?.38:.22)*(.7+r()*.6);
        branch(walk(pp[0],pp[1],ang,ln,1),mob?2.2:3,1,yy,ln*.9);
      }
      yy+=(mob?250:300)+r()*180;
    }
    // zijwortels vanuit het kompas naar Engeland (west) en Duitsland (oost)
    var pls=document.querySelectorAll('.compass .w,.compass .e');
    for(var pk=0;pk<pls.length;pk++){
      r=rng(SEED+400+pk);
      var pc=rel(pls[pk]),py=pc.cy,pb=nearest(py-18),pd=pc.left>pb[0]?1:-1,px=pd>0?pc.left+2:pc.right-2;
      var PB=bez(pb,[pb[0]+pd*24,pb[1]+12],[px-pd*Math.min(50,Math.abs(px-pb[0])*.5),py-8],[px,py],30);
      var po=addPath(PB,mob?2:2.6,'r rt',py-40,mob?110:150);if(po)po.step=pls[pk];
    }
    // takken naar elke stap
    var steps=stepsBox?stepsBox.querySelectorAll('.step'):[];
    for(var n=0;n<steps.length;n++){
      r=rng(SEED+300+n);
      var ic=rel(steps[n].querySelector('.ico')),isL=mob?!!steps[n].closest('.uit'):steps[n].classList.contains('l');
      var tx=isL?ic.right+5:ic.left-5,ty=ic.cy,by=ty-(mob?34:70),bp=nearest(by),dir=tx>bp[0]?1:-1;
      var B=bez(bp,[bp[0]+dir*16,bp[1]+28],[tx-dir*Math.min(70,Math.abs(tx-bp[0])*.5),ty-4],[tx,ty],30);
      var o=addPath(B,mob?2.2:3,'r rt',by,mob?90:150);
      if(o)o.step=steps[n];
      var hp=B[Math.floor(B.length*.55)];
      branch(walk(hp[0],hp[1],Math.PI/2+dir*.3,mob?16:30,3),.9,3,by+(mob?50:80),60);
    }
    // penwortel in stukken zodat hij naar beneden dunner wordt
    var CH=[],chunk=mob?260:340,wTop=mob?7:10,wBot=1.6;
    for(var a0=0;a0<T;a0+=chunk){
      var i0=search(L,a0,function(v){return v;}),i1=search(L,Math.min(T,a0+chunk+6),function(v){return v;});
      var seg=P.slice(i0,i1+1);if(seg.length<2)continue;
      var mid=(a0+chunk/2)/T,wd=wTop-(wTop-wBot)*Math.pow(clamp(mid,0,1),.55),sl=lens(seg),sLen=sl[sl.length-1];
      var e=el('path',{d:line(seg),'class':'r r0','stroke-width':wd.toFixed(2),'stroke-dasharray':sLen.toFixed(1)+' '+sLen.toFixed(1),'stroke-dashoffset':sLen.toFixed(1)},gTap);
      e.style.visibility='hidden';
      CH.push({e:e,a:L[i0],len:sLen,p:-1});
    }
    var defs=el('defs',{},RS),rg=el('radialGradient',{id:'tipglow'},defs);
    el('stop',{offset:0,'stop-color':'#E8C49A','stop-opacity':.55},rg);el('stop',{offset:1,'stop-color':'#E8C49A','stop-opacity':0},rg);
    var tipWrap=el('g',{},RS),tip=el('g',{'class':'tipg'},tipWrap);el('circle',{r:16,fill:'url(#tipglow)'},tip);el('circle',{r:mob?3:4,'class':'tip-dot'},tip);
    // de wortel duikt onder koppen en korte teksten door: per tekstregel een zachte uitsparing in een masker
    var mk=el('mask',{id:'tekstmasker',maskUnits:'userSpaceOnUse',x:0,y:-OFF,width:W,height:H+OFF},defs);
    el('rect',{x:0,y:-OFF,width:W,height:H+OFF,fill:'#fff'},mk);
    var tx=U.querySelectorAll('.sec-title h2,.sec-title .scribble,.sec-title p,.about-txt h2,.about-txt .scribble,.about-txt > p,.contact h2,.contact .lede,.dest .mono');
    var ub0=U.getBoundingClientRect(),feather=[[22,.35],[14,.6],[6,1]];
    for(var ti=0;ti<tx.length;ti++){
      var rg=document.createRange();rg.selectNodeContents(tx[ti]);
      var lr=rg.getClientRects();
      for(var lj=0;lj<lr.length;lj++){
        var q=lr[lj];if(q.width<2||q.height<2)continue;
        for(var fk=0;fk<feather.length;fk++){
          var m=feather[fk][0];
          el('rect',{x:(q.left-ub0.left-m).toFixed(1),y:(q.top-ub0.top-m).toFixed(1),width:(q.width+2*m).toFixed(1),height:(q.height+2*m).toFixed(1),rx:m+6,fill:'#000','fill-opacity':feather[fk][1]},mk);
        }
      }
    }
    gLat.setAttribute('mask','url(#tekstmasker)');gTap.setAttribute('mask','url(#tekstmasker)');tipWrap.setAttribute('mask','url(#tekstmasker)');
    tip.style.opacity=0;
    st={P:P,L:L,T:T,CH:CH,roots:roots,tip:tip};
  }

  function update(){
    raf=0;if(!st)return;
    var ub=U.getBoundingClientRect(),vh=window.innerHeight,left=document.documentElement.scrollHeight-(window.pageYOffset+vh);
    // onderaan de pagina groeit de wortel helemaal uit
    var tipY=reduce?1e9:(vh*.8-ub.top+clamp(1-left/400,0,1)*vh*.5),P=st.P,L=st.L,T=st.T,rev,i;
    if(tipY>=P[P.length-1][1])rev=T;else if(tipY<=P[0][1])rev=0;else{i=search(P,tipY,function(p){return p[1];});rev=L[i];}
    for(var c=0;c<st.CH.length;c++){var ch=st.CH[c],p=clamp((rev-ch.a)/ch.len,0,1);
      if(p!==ch.p){ch.p=p;ch.e.setAttribute('stroke-dashoffset',(ch.len*(1-p)).toFixed(1));ch.e.style.visibility=p>0?'visible':'hidden';}}
    if(rev>0&&rev<T){i=search(L,rev,function(v){return v;});st.tip.setAttribute('transform','translate('+P[i][0].toFixed(1)+' '+P[i][1].toFixed(1)+')');st.tip.style.opacity=1;}
    else st.tip.style.opacity=0;
    for(var k=0;k<st.roots.length;k++){var o=st.roots[k],q=clamp((tipY-o.s)/o.d,0,1);
      if(Math.abs(q-o.p)>.002||(q!==o.p&&(q===0||q===1))){o.p=q;o.e.setAttribute('stroke-dashoffset',(o.len*(1-q)).toFixed(1));o.e.style.visibility=q>0?'visible':'hidden';
        if(o.step)o.step.classList.toggle('on',q>.97);}}
  }

  var raf=0,rt=0;
  function onScroll(){header();if(!raf)raf=requestAnimationFrame(update);}
  function rebuild(){build();update();}
  window.addEventListener('scroll',onScroll,{passive:true});
  if(window.ResizeObserver){new ResizeObserver(function(){clearTimeout(rt);rt=setTimeout(rebuild,120);}).observe(U);}
  else window.addEventListener('resize',function(){clearTimeout(rt);rt=setTimeout(rebuild,120);});
  if(document.fonts&&document.fonts.ready)document.fonts.ready.then(rebuild);
  // een stap of verhaal openklappen verschuift wat eronder staat: takken direct meeschuiven
  var dets=document.querySelectorAll('.st,.more,.faq details');
  for(var di=0;di<dets.length;di++)dets[di].addEventListener('toggle',rebuild);
  header();rebuild();

  /* plantnamenrij: klik, tik of Enter/spatie zet hem stil en weer aan */
  var tick=document.querySelector('.ticker');
  if(tick){
    var tog=function(){tick.classList.toggle('paused');};
    tick.addEventListener('click',tog);
    tick.addEventListener('keydown',function(ev){if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();tog();}});
  }

  /* plantenkaarten: pijlen alleen als niet alles past */
  var cases=document.getElementById('cases'),prev=document.getElementById('prev'),next=document.getElementById('next');
  if(!cases||!prev||!next)return;
  function arrows(){var fits=cases.scrollWidth<=cases.clientWidth+2;prev.hidden=next.hidden=fits;prev.disabled=cases.scrollLeft<4;next.disabled=cases.scrollLeft+cases.clientWidth>=cases.scrollWidth-4;}
  function by(dx){var smooth=!reduce;try{cases.scrollBy({left:dx,behavior:smooth?'smooth':'auto'});}catch(e){cases.scrollLeft+=dx;}}
  prev.addEventListener('click',function(){by(-cases.clientWidth*.8);});
  next.addEventListener('click',function(){by(cases.clientWidth*.8);});
  cases.addEventListener('scroll',arrows,{passive:true});
  window.addEventListener('resize',arrows);
  arrows();
})();
