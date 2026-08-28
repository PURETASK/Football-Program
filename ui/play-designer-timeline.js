(function(){
  const host=document.getElementById('play-designer');
  const api=window.NFLFIDOSPlayDesigner;
  const root=document.getElementById('pd-enhancements');
  let card=root?.querySelector('.pd-enhance-card');
  if(!host||!api||!root||!card)return;

  const NS='http://www.w3.org/2000/svg';
  const FIELD_WIDTH=53.33;
  const MIN_DURATION=3000;
  const PHASES={
    route:[['release','Release',0,.18],['stem','Stem',.18,.48],['break','Break',.48,.72],['finish','Finish',.72,1]],
    motion:[['align','Align',0,.2],['travel','Travel',.2,.78],['settle','Settle',.78,1]],
    run:[['mesh','Mesh',0,.25],['track','Track',.25,.72],['finish','Finish',.72,1]],
    block:[['strike','Strike',0,.22],['fit','Fit',.22,.58],['sustain','Sustain',.58,1]],
    coverage:[['pedal','Pedal',0,.25],['match','Match',.25,.72],['close','Close',.72,1]],
    rush:[['getoff','Get off',0,.22],['attack','Attack',.22,.62],['finish','Finish',.62,1]],
    stunt:[['penetrate','Penetrate',0,.32],['exchange','Exchange',.32,.68],['finish','Finish',.68,1]],
    rotation:[['key','Key',0,.25],['rotate','Rotate',.25,.72],['fit','Fit',.72,1]],
    read:[['identify','Identify',0,.3],['confirm','Confirm',.3,.72],['decide','Decide',.72,1]],
    annotation:[['teach','Teach',0,1]]
  };
  const state={design:null,ms:0,playing:false,raf:0,lastFrame:0,speed:1,voice:false,markerKind:'cue',selectedElement:'',lastCaption:'',pauseMarkerId:null,keyboardBound:false,visibleElementIds:null};
  const clone=value=>JSON.parse(JSON.stringify(value));
  const number=(value,fallback)=>Number.isFinite(Number(value))?Number(value):fallback;
  const clamp=(value,min,max)=>Math.max(min,Math.min(max,value));
  const id=prefix=>prefix+'-'+Date.now().toString(36)+'-'+Math.random().toString(36).slice(2,8);
  const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  function pathData(points){return (points||[]).map((point,index)=>(index?'L':'M')+' '+point.x+' '+point.y).join(' ');}
  function phaseTemplate(kind,start,end){
    const catalog=PHASES[kind]||PHASES.annotation;
    const span=Math.max(1,end-start);
    return catalog.map(item=>({id:item[0],label:item[1],start_ms:Math.round(start+span*item[2]),end_ms:Math.round(start+span*item[3])}));
  }
  function normalizeDesign(input){
    const design=clone(input||{});
    design.timeline=design.timeline&&typeof design.timeline==='object'?design.timeline:{};
    design.timeline.snap_ms=Math.max(1,Math.round(number(design.timeline.snap_ms,50)));
    design.timeline.markers=Array.isArray(design.timeline.markers)?design.timeline.markers:[];
    design.timeline.narration=Array.isArray(design.timeline.narration)?design.timeline.narration:[];
    design.timeline.events=Array.isArray(design.timeline.events)?design.timeline.events:[];
    design.elements=Array.isArray(design.elements)?design.elements:[];
    let maximum=MIN_DURATION;
    design.elements.forEach(element=>{
      const timing=element.timing&&typeof element.timing==='object'?element.timing:{};
      const start=Math.max(0,Math.round(number(timing.start_ms,number(element.start_ms,0))));
      const fallbackEnd=Math.max(start+100,number(element.end_ms,start+1200));
      const end=Math.max(start+1,Math.round(number(timing.end_ms,fallbackEnd)));
      element.start_ms=start;element.end_ms=end;
      const phases=Array.isArray(timing.phases)&&timing.phases.length?timing.phases:phaseTemplate(element.kind,start,end);
      element.timing={...timing,start_ms:start,end_ms:end,phases:phases.map((phase,index)=>({id:phase.id||'phase-'+(index+1),label:phase.label||phase.id||'Phase '+(index+1),start_ms:Math.round(number(phase.start_ms,start)),end_ms:Math.max(Math.round(number(phase.end_ms,end)),Math.round(number(phase.start_ms,start))+1)}))};
      maximum=Math.max(maximum,end);
    });
    design.timeline.duration_ms=Math.max(MIN_DURATION,Math.round(number(design.timeline.duration_ms,maximum)));
    design.timeline.markers=design.timeline.markers.map((marker,index)=>({...marker,id:marker.id||id('MARK'),label:marker.label||'Cue '+(index+1),ms:clamp(Math.round(number(marker.ms,0)),0,design.timeline.duration_ms),kind:marker.kind||'cue'}));
    design.timeline.narration=design.timeline.narration.map((cue,index)=>{const start=clamp(Math.round(number(cue.start_ms,0)),0,design.timeline.duration_ms);return {...cue,id:cue.id||id('NARRATION'),start_ms:start,end_ms:clamp(Math.max(start+1,Math.round(number(cue.end_ms,start+700))),0,design.timeline.duration_ms),text:String(cue.text||''),role:cue.role||'coach'};});
    return design;
  }
  function design(){state.design=normalizeDesign(api.getDesign());return state.design;}
  function timing(element){return element?.timing||{start_ms:number(element?.start_ms,0),end_ms:number(element?.end_ms,1200),phases:[]};}
  function progress(element,ms){const range=timing(element);return clamp((ms-range.start_ms)/Math.max(1,range.end_ms-range.start_ms),0,1);}
  function pointAt(points,ratio){
    if(!points?.length)return {x:50,y:26.66};
    if(points.length===1)return {...points[0]};
    const lengths=[];let total=0;
    for(let index=1;index<points.length;index++){const length=Math.hypot(points[index].x-points[index-1].x,points[index].y-points[index-1].y);lengths.push(length);total+=length;}
    if(!total)return {...points[0]};
    let distance=clamp(ratio,0,1)*total;
    for(let index=0;index<lengths.length;index++){
      if(distance<=lengths[index]){const p1=points[index],p2=points[index+1],part=distance/Math.max(lengths[index],.001);return {x:p1.x+(p2.x-p1.x)*part,y:p1.y+(p2.y-p1.y)*part};}
      distance-=lengths[index];
    }
    return {...points[points.length-1]};
  }
  function polylineLength(points){
    let length=0;
    for(let index=1;index<(points||[]).length;index++)length+=Math.hypot(points[index].x-points[index-1].x,points[index].y-points[index-1].y);
    return Math.max(1,length);
  }
  function phaseAt(element,ms){
    const phases=timing(element).phases||[];
    return phases.find(phase=>ms>=phase.start_ms&&ms<=phase.end_ms)?.label||((ms<timing(element).start_ms)?'Pre-snap':'Complete');
  }
  function selectedElement(){return state.design?.elements?.find(element=>element.id===state.selectedElement)||state.design?.elements?.[0];}
  function markerPosition(marker){return marker.position&&Number.isFinite(Number(marker.position.x))?{x:Number(marker.position.x),y:Number(marker.position.y)}:{x:50,y:5};}

  function buildCard(){
    card.classList.add('pd-timeline-card');
    card.innerHTML='<h4>Timeline & animation</h4>'+ 
      '<div class="pd-timeline-toolbar"><button type="button" id="pd-play-animation">Play</button><button type="button" id="pd-timeline-step-back">Step back</button><button type="button" id="pd-timeline-step-forward">Step forward</button><button type="button" id="pd-timeline-stop">Stop</button><label>Speed<select id="pd-timeline-speed"><option value="0.5">0.5x</option><option value="1" selected>1x</option><option value="1.5">1.5x</option><option value="2">2x</option></select></label><label><input id="pd-timeline-voice" type="checkbox"> Read teaching cues aloud</label></div>'+ 
      '<div class="pd-timeline-scrubber"><span class="pd-timeline-readout" id="pd-time-label">0 ms</span><input id="pd-time" type="range" min="0" max="3000" step="50" value="0" aria-label="Animation time in milliseconds"><span class="pd-timeline-readout" id="pd-duration-label">3000 ms</span></div>'+ 
      '<div id="pd-timeline-ruler" class="pd-timeline-ruler" aria-label="Timeline markers"></div><div id="pd-timeline-caption" class="pd-timeline-caption" role="status" aria-live="polite"></div>'+ 
      '<div class="pd-timeline-subgrid"><div class="pd-timeline-subcard"><h5>Timeline cue</h5><div class="pd-timeline-event-row"><label>Kind<select id="pd-marker-kind"><option value="cue">Cue</option><option value="pause">Pause</option><option value="read">QB read</option><option value="rotation">Coverage rotation</option><option value="exchange">Block / rush exchange</option></select></label><label>Label<input id="pd-marker-label" value="Teaching cue" autocomplete="off"></label><button type="button" id="pd-add-marker">Add cue at playhead</button></div></div>'+ 
      '<div class="pd-timeline-subcard"><h5>Teaching narration</h5><div class="pd-timeline-narration-row"><label>Role<input id="pd-narration-role" value="coach" autocomplete="off"></label><label>Narration<textarea id="pd-narration-text" rows="2" placeholder="Explain the read, leverage, or adjustment."></textarea></label><button type="button" id="pd-add-narration">Add narration</button></div></div></div>'+ 
      '<div class="pd-timeline-subcard" style="margin-top:.65rem"><h5>Selected element timing and relationships</h5><div class="pd-timeline-selected-row"><label>Element<select id="pd-timeline-element"></select></label><label>Start ms<input id="pd-timing-start" type="number" min="0" step="50"></label><label>End ms<input id="pd-timing-end" type="number" min="1" step="50"></label><button type="button" id="pd-apply-timing">Apply timing</button></div><div class="pd-timeline-selected-row" style="margin-top:.45rem"><label>New phase label<input id="pd-phase-label" placeholder="Late break" autocomplete="off"></label><button type="button" id="pd-add-phase">Add phase at playhead</button><label>Exchange target<select id="pd-exchange-target"></select></label><button type="button" id="pd-link-exchange">Link exchange</button><label>Read key<input id="pd-timeline-read-key" placeholder="Sam / safety / #2" autocomplete="off"></label><button type="button" id="pd-save-read-key">Save read key</button></div><p class="pd-timeline-help">Timing is stored on each element. Link block/rush exchanges, name QB read keys, and use pause cues to synchronize teaching.</p><div id="pd-timeline-elements" class="pd-timeline-elements"></div></div>'+ 
      '<div id="pd-markers" class="label" style="margin-top:.5rem"></div>';
  }

  function commit(next){
    state.design=normalizeDesign(next);
    api.setDesign(state.design);
    requestAnimationFrame(renderStatic);
  }
  function setTime(value){
    const maximum=state.design?.timeline?.duration_ms||MIN_DURATION;
    state.ms=clamp(Math.round(number(value,0)),0,maximum);
    if(state.pauseMarkerId&&state.ms>=(state.design.timeline.markers.find(marker=>marker.id===state.pauseMarkerId)?.ms||-1)+1)state.pauseMarkerId=null;
    renderTime();
  }
  function addMarker(){
    const next=clone(state.design);const label=document.getElementById('pd-marker-label').value.trim()||'Teaching cue';const kind=document.getElementById('pd-marker-kind').value;
    next.timeline.markers.push({id:id('MARK'),label,kind,ms:state.ms,position:{x:50,y:5}});commit(next);
  }
  function addNarration(){
    const text=document.getElementById('pd-narration-text').value.trim();
    if(!text){document.getElementById('pd-timeline-caption').textContent='Enter narration before adding a cue.';return;}
    const next=clone(state.design);const role=document.getElementById('pd-narration-role').value.trim()||'coach';
    next.timeline.narration.push({id:id('NARRATION'),start_ms:state.ms,end_ms:Math.min(next.timeline.duration_ms,state.ms+800),role,text});commit(next);document.getElementById('pd-narration-text').value='';
  }
  function currentElementFromControl(){return state.design?.elements?.find(element=>element.id===document.getElementById('pd-timeline-element')?.value);}
  function applyTiming(){
    const selected=currentElementFromControl();if(!selected)return;
    const next=clone(state.design);const element=next.elements.find(item=>item.id===selected.id);const start=Math.max(0,Math.round(number(document.getElementById('pd-timing-start').value,0)));const end=Math.max(start+1,Math.round(number(document.getElementById('pd-timing-end').value,start+1200)));element.start_ms=start;element.end_ms=end;element.timing={...element.timing,start_ms:start,end_ms:end,phases:(element.timing?.phases?.length?element.timing.phases:phaseTemplate(element.kind,start,end)).map(phase=>({...phase,start_ms:clamp(phase.start_ms,start,end-1),end_ms:clamp(Math.max(phase.end_ms,phase.start_ms+1),start+1,end)}))};next.timeline.duration_ms=Math.max(next.timeline.duration_ms,end);commit(next);
  }
  function addPhase(){
    const selected=currentElementFromControl();const label=document.getElementById('pd-phase-label').value.trim()||'Teaching phase';if(!selected)return;
    const next=clone(state.design);const element=next.elements.find(item=>item.id===selected.id);const range=element.timing||{start_ms:element.start_ms||0,end_ms:element.end_ms||1200,phases:[]};const start=clamp(state.ms,range.start_ms,Math.max(range.start_ms,range.end_ms-1));range.phases=range.phases||[];range.phases.push({id:id('PHASE'),label,start_ms:start,end_ms:Math.min(range.end_ms,start+Math.max(50,next.timeline.snap_ms*4))});element.timing=range;commit(next);document.getElementById('pd-phase-label').value='';
  }
  function linkExchange(){
    const selected=currentElementFromControl();const target=document.getElementById('pd-exchange-target').value;if(!selected)return;
    const next=clone(state.design);const element=next.elements.find(item=>item.id===selected.id);if(target)element.exchange_with=target;else delete element.exchange_with;commit(next);
  }
  function saveReadKey(){
    const selected=currentElementFromControl();if(!selected)return;
    const next=clone(state.design);const element=next.elements.find(item=>item.id===selected.id);element.read_key=document.getElementById('pd-timeline-read-key').value.trim();element.kind=element.kind||'read';commit(next);
  }
  function markerCaption(){
    const cue=state.design.timeline.narration.find(item=>state.ms>=item.start_ms&&state.ms<=item.end_ms&&item.text);
    if(cue)return (cue.role?cue.role.toUpperCase()+': ':'')+cue.text;
    const marker=state.design.timeline.markers.find(item=>Math.abs(item.ms-state.ms)<=Math.max(25,state.design.timeline.snap_ms/2));
    if(marker)return marker.label+' ('+marker.kind+')';
    const selected=selectedElement();
    return selected?((selected.type||selected.kind)+' - '+phaseAt(selected,state.ms)+' - '+Math.round(state.ms)+' ms'):'';
  }
  function narrateCaption(caption){
    if(caption===state.lastCaption)return;
    state.lastCaption=caption;
    const target=document.getElementById('pd-timeline-caption');if(target)target.textContent=caption;
    if(state.voice&&caption&&'speechSynthesis' in window&&'SpeechSynthesisUtterance' in window){window.speechSynthesis.cancel();const utterance=new SpeechSynthesisUtterance(caption);utterance.rate=.95;window.speechSynthesis.speak(utterance);}
  }
  function renderTime(){
    if(!state.design)return;
    const time=document.getElementById('pd-time');if(time){time.max=state.design.timeline.duration_ms;time.value=state.ms;}
    const label=document.getElementById('pd-time-label');if(label)label.textContent=Math.round(state.ms)+' ms';
    const caption=markerCaption();narrateCaption(caption);renderAnimation();
    document.querySelectorAll('.pd-timeline-marker').forEach(marker=>marker.classList.toggle('active',Math.abs(Number(marker.dataset.ms)-state.ms)<=Math.max(25,state.design.timeline.snap_ms/2)));
  }
  function renderRuler(){
    const ruler=document.getElementById('pd-timeline-ruler');if(!ruler)return;ruler.innerHTML='';const duration=state.design.timeline.duration_ms;
    state.design.timeline.markers.slice().sort((a,b)=>a.ms-b.ms).forEach(marker=>{const button=document.createElement('button');button.type='button';button.className='pd-timeline-marker '+(marker.kind||'cue');button.dataset.ms=marker.ms;button.title=marker.label+' at '+marker.ms+' ms';button.textContent=marker.label;button.style.left=(marker.ms/duration*100)+'%';button.onclick=()=>setTime(marker.ms);ruler.appendChild(button);});
  }
  function renderSelectedControls(){
    const select=document.getElementById('pd-timeline-element');const target=document.getElementById('pd-exchange-target');if(!select||!target)return;
    const elements=state.design.elements||[];const previous=state.selectedElement||select.value;select.innerHTML='<option value="">Select element</option>'+elements.map(element=>'<option value="'+esc(element.id)+'">'+esc((element.type||element.kind)+' - '+element.id)+'</option>').join('');select.value=elements.some(element=>element.id===previous)?previous:'';state.selectedElement=select.value;
    target.innerHTML='<option value="">No exchange link</option>'+elements.filter(element=>element.id!==state.selectedElement).map(element=>'<option value="'+esc(element.id)+'">'+esc((element.type||element.kind)+' - '+element.id)+'</option>').join('');
    const selected=currentElementFromControl();const range=selected?timing(selected):{start_ms:0,end_ms:1200};document.getElementById('pd-timing-start').value=range.start_ms;document.getElementById('pd-timing-end').value=range.end_ms;document.getElementById('pd-timeline-read-key').value=selected?.read_key||'';if(selected?.exchange_with)target.value=selected.exchange_with;
    const rows=document.getElementById('pd-timeline-elements');rows.innerHTML='';elements.forEach(element=>{const row=document.createElement('div');row.className='pd-timeline-element-row';const label=document.createElement('span');label.className='pd-timeline-element-label';label.textContent=(element.type||element.kind)+' / '+element.id;label.title=label.textContent;const start=document.createElement('input');start.type='number';start.min='0';start.step='50';start.value=timing(element).start_ms;start.setAttribute('aria-label','Start time for '+element.id);const end=document.createElement('input');end.type='number';end.min='1';end.step='50';end.value=timing(element).end_ms;end.setAttribute('aria-label','End time for '+element.id);const apply=document.createElement('button');apply.type='button';apply.textContent='Apply';apply.onclick=()=>{const next=clone(state.design);const item=next.elements.find(value=>value.id===element.id);const startMs=Math.max(0,Math.round(number(start.value,0)));const endMs=Math.max(startMs+1,Math.round(number(end.value,startMs+1200)));item.start_ms=startMs;item.end_ms=endMs;item.timing={...item.timing,start_ms:startMs,end_ms:endMs,phases:item.timing?.phases||phaseTemplate(item.kind,startMs,endMs)};next.timeline.duration_ms=Math.max(next.timeline.duration_ms,endMs);commit(next);};row.append(label,start,end,apply);const phases=document.createElement('div');phases.style.gridColumn='1/-1';(timing(element).phases||[]).forEach(phase=>{const chip=document.createElement('span');chip.className='pd-timeline-phase '+(state.ms>=phase.start_ms&&state.ms<=phase.end_ms?'current':'');chip.textContent=phase.label+' '+phase.start_ms+'-'+phase.end_ms+'ms';phases.appendChild(chip);});row.appendChild(phases);rows.appendChild(row);});
  }
  function renderStatic(){
    state.design=normalizeDesign(api.getDesign());
    const duration=document.getElementById('pd-duration-label');if(duration)duration.textContent=state.design.timeline.duration_ms+' ms';
    const speed=document.getElementById('pd-timeline-speed');if(speed)speed.value=String(state.speed);
    const voice=document.getElementById('pd-timeline-voice');if(voice)voice.checked=state.voice;
    renderRuler();renderSelectedControls();setTime(state.ms);const oldMarkers=document.getElementById('pd-markers');if(oldMarkers)oldMarkers.textContent=state.design.timeline.markers.map(marker=>marker.label+' @ '+marker.ms+'ms').join(' · ')||'No timeline markers.';
  }
  function renderAnimation(){
    const field=host.querySelector('.pd-canvas');if(!field||!state.design)return;
    host.querySelectorAll('.pd-animation-layer').forEach(layer=>layer.remove());
    const layer=document.createElementNS(NS,'g');layer.classList.add('pd-animation-layer');const elements=state.design.elements||[];
    host.querySelectorAll('.pd-path').forEach(path=>{const element=elements.find(item=>item.id===path.dataset.id);if(element){const hidden=state.visibleElementIds&&!state.visibleElementIds.has(element.id);path.style.display=hidden?'none':'';const p=progress(element,state.ms);path.style.opacity=p<=0 ? '.18' : '.38';}});
    const positions=new Map();
    elements.filter(element=>!state.visibleElementIds||state.visibleElementIds.has(element.id)).forEach(element=>{
      if(!element.points||element.points.length<2)return;
      const p=progress(element,state.ms);const point=pointAt(element.points,p);positions.set(element.id,point);
      if(p<=0)return;
      const animated=document.createElementNS(NS,'path');animated.classList.add('pd-animation-path',element.arrow_style||element.kind);animated.setAttribute('d',pathData(element.points));layer.appendChild(animated);
      let length=0;try{length=animated.getTotalLength();}catch(error){length=0;}if(!length)length=polylineLength(element.points);
      animated.style.strokeDasharray=String(length);animated.style.strokeDashoffset=String(length*(1-p));
      const token=document.createElementNS(NS,'circle');token.classList.add('pd-animation-token');token.setAttribute('cx',point.x);token.setAttribute('cy',point.y);token.setAttribute('r','1.25');layer.appendChild(token);
      const label=document.createElementNS(NS,'text');label.classList.add('pd-animation-label');label.setAttribute('x',point.x+1.6);label.setAttribute('y',point.y-.8);label.textContent=phaseAt(element,state.ms);layer.appendChild(label);
      if(element.kind==='read'||element.read_key){const badge=document.createElementNS(NS,'circle');badge.classList.add('pd-read-badge');badge.setAttribute('cx',point.x);badge.setAttribute('cy',point.y-3);badge.setAttribute('r','1.8');layer.appendChild(badge);const read=document.createElementNS(NS,'text');read.classList.add('pd-read-text');read.setAttribute('x',point.x-1.2);read.setAttribute('y',point.y-2.45);read.textContent='R';layer.appendChild(read);}
      if(element.kind==='rotation'){const rotation=document.createElementNS(NS,'text');rotation.classList.add('pd-event-text');rotation.setAttribute('x',point.x+1.6);rotation.setAttribute('y',point.y+2);rotation.textContent='ROT';layer.appendChild(rotation);}
    });
    elements.forEach(element=>{if(!element.exchange_with||!positions.has(element.id)||!positions.has(element.exchange_with))return;const other=positions.get(element.exchange_with);const point=positions.get(element.id);const line=document.createElementNS(NS,'line');line.classList.add('pd-exchange-line');line.setAttribute('x1',point.x);line.setAttribute('y1',point.y);line.setAttribute('x2',other.x);line.setAttribute('y2',other.y);layer.appendChild(line);});
    state.design.timeline.markers.filter(marker=>['read','rotation','exchange'].includes(marker.kind)&&marker.ms<=state.ms).forEach(marker=>{const point=markerPosition(marker);const line=document.createElementNS(NS,'line');line.classList.add('pd-event-marker');line.setAttribute('x1',point.x);line.setAttribute('x2',point.x);line.setAttribute('y1',0);line.setAttribute('y2',FIELD_WIDTH);layer.appendChild(line);const text=document.createElementNS(NS,'text');text.classList.add('pd-event-text');text.setAttribute('x',point.x+1);text.setAttribute('y',point.y);text.textContent=marker.label;layer.appendChild(text);});
    field.appendChild(layer);
  }
  function stop(){state.playing=false;cancelAnimationFrame(state.raf);state.raf=0;state.lastFrame=0;const button=document.getElementById('pd-play-animation');if(button)button.textContent='Play';}
  function tick(now){
    if(!state.playing)return;
    const delta=state.lastFrame?now-state.lastFrame:0;state.lastFrame=now;const previous=state.ms;let next=state.ms+delta*state.speed;
    const pause=state.design.timeline.markers.filter(marker=>marker.kind==='pause'&&marker.id!==state.pauseMarkerId&&marker.ms>previous&&marker.ms<=next).sort((a,b)=>a.ms-b.ms)[0];
    if(pause){state.ms=pause.ms;state.pauseMarkerId=pause.id;stop();renderTime();return;}
    if(next>=state.design.timeline.duration_ms){state.ms=state.design.timeline.duration_ms;stop();renderTime();return;}
    state.ms=next;renderTime();state.raf=requestAnimationFrame(tick);
  }
  function play(){
    if(state.playing){stop();return;}
    if(state.ms>=state.design.timeline.duration_ms){state.ms=0;state.pauseMarkerId=null;}
    state.playing=true;state.lastFrame=0;const button=document.getElementById('pd-play-animation');if(button)button.textContent='Pause';state.raf=requestAnimationFrame(tick);
  }
  function step(direction){stop();setTime(state.ms+direction*Math.max(25,state.design.timeline.snap_ms));}
  function bind(){
    document.getElementById('pd-time').oninput=event=>setTime(Number(event.target.value));
    document.getElementById('pd-play-animation').onclick=play;
    document.getElementById('pd-timeline-step-back').onclick=()=>step(-1);
    document.getElementById('pd-timeline-step-forward').onclick=()=>step(1);
    document.getElementById('pd-timeline-stop').onclick=()=>{stop();setTime(0);};
    document.getElementById('pd-timeline-speed').onchange=event=>{state.speed=Number(event.target.value)||1;};
    document.getElementById('pd-timeline-voice').onchange=event=>{state.voice=event.target.checked;};
    document.getElementById('pd-add-marker').onclick=addMarker;
    document.getElementById('pd-add-narration').onclick=addNarration;
    document.getElementById('pd-apply-timing').onclick=applyTiming;
    document.getElementById('pd-add-phase').onclick=addPhase;
    document.getElementById('pd-link-exchange').onclick=linkExchange;
    document.getElementById('pd-save-read-key').onclick=saveReadKey;
    document.getElementById('pd-timeline-element').onchange=event=>{state.selectedElement=event.target.value;renderSelectedControls();};
    if(!state.keyboardBound){state.keyboardBound=true;document.addEventListener('keydown',event=>{if(!host.contains(document.activeElement)||['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName))return;if(event.code==='Space'){event.preventDefault();play();}if(event.key==='ArrowLeft'){event.preventDefault();step(-1);}if(event.key==='ArrowRight'){event.preventDefault();step(1);}});}
  }

  function refresh(){
    card=root.querySelector('.pd-enhance-card');
    if(!card)return;
    if(!card.querySelector('#pd-timeline-ruler')){buildCard();bind();}
    renderStatic();
  }
  function setVisibilityFilter(ids){state.visibleElementIds=ids?new Set(ids):null;renderAnimation();}
  window.NFLFIDOSPlayDesignerTimeline={refresh,setVisibilityFilter};
  refresh();
  const originalSet=api.setDesign;
  api.setDesign=next=>{originalSet(next);requestAnimationFrame(renderStatic);};
  state.design=normalizeDesign(api.getDesign());
  renderStatic();
}());
