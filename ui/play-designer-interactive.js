(function(){
  const host=document.getElementById('play-designer');
  const section=document.getElementById('play-designer-section');
  const api=window.NFLFIDOSPlayDesigner;
  if(!host||!section||!api)return;

  const NS='http://www.w3.org/2000/svg';
  const FIELD_LENGTH=100;
  const FIELD_WIDTH=53.33;
  const TOOLS=[
    ['select','Select / move'],['route','Route'],['motion','Motion'],['run','Run'],
    ['block','Block'],['coverage','Coverage'],['rush','Rush'],['stunt','Stunt'],['landmark','Landmark']
  ];
  const state={
    tool:'route',snap:true,selection:new Set(),pointer:null,preview:null,copyBuffer:[],
    layerState:{offense:true,defense:true,annotation:true},observer:null
  };
  const get=()=>api.getDesign();
  const clone=value=>JSON.parse(JSON.stringify(value));
  const id=prefix=>prefix+'-'+Date.now().toString(36)+'-'+Math.random().toString(36).slice(2,8);
  const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const clamp=(value,min,max)=>Math.max(min,Math.min(max,value));
  const snapPoint=(x,y)=>({x:clamp(Math.round(x*4)/4,0,FIELD_LENGTH),y:clamp(Math.round(y*4)/4,0,FIELD_WIDTH)});
  const fieldPoint=(x,y)=>state.snap?snapPoint(x,y):{x:clamp(x,0,FIELD_LENGTH),y:clamp(y,0,FIELD_WIDTH)};

  function canvas(){return host.querySelector('.pd-canvas');}
  function svgPoint(event){
    const svg=canvas();
    if(!svg)return {x:0,y:0};
    const box=svg.getBoundingClientRect();
    return fieldPoint((event.clientX-box.left)/box.width*FIELD_LENGTH,(event.clientY-box.top)/box.height*FIELD_WIDTH);
  }
  function currentElement(elementId){return get().elements?.find(element=>element.id===elementId);}
  function currentPlayer(playerId){return get().players?.find(player=>player.id===playerId);}
  function lastSelection(){const values=[...state.selection];return values[values.length-1]||null;}
  function selectedPlayerId(){
    const design=get();
    const values=[...state.selection].filter(value=>design.players?.some(player=>player.id===value));
    return values[values.length-1]||null;
  }

  function status(message){
    const element=document.getElementById('pd-interactive-status');
    if(element)element.textContent=message;
  }

  function ensureControls(){
    let box=document.getElementById('pd-interactive-controls');
    if(box)return box;
    box=document.createElement('div');
    box.id='pd-interactive-controls';
    box.className='pd-interactive-controls';
    section.appendChild(box);
    box.innerHTML='<h4>Authoring controls</h4>'+
      '<div><div class="label">Tool</div><div class="pd-tool-grid">'+TOOLS.map(tool=>'<button type="button" data-tool="'+tool[0]+'" title="'+tool[1]+'">'+tool[1]+'</button>').join('')+'</div></div>'+ 
      '<div><div class="label">Selection and geometry</div><div class="pd-control-group">'+
        '<button type="button" id="pd-duplicate">Duplicate</button><button type="button" id="pd-copy">Copy</button><button type="button" id="pd-paste">Paste</button><button type="button" id="pd-mirror">Mirror</button><button type="button" id="pd-group">Group</button><button type="button" id="pd-ungroup">Ungroup</button></div>'+ 
        '<label><input id="pd-snap" type="checkbox" checked> Snap to field grid</label></div>'+ 
      '<div><div class="label">Layers</div><div class="pd-control-group">'+
        '<label><input class="pd-layer" data-layer="offense" type="checkbox" checked> Offense</label><label><input class="pd-layer" data-layer="defense" type="checkbox" checked> Defense</label><label><input class="pd-layer" data-layer="annotation" type="checkbox" checked> Notes</label>'+ 
        '<button type="button" id="pd-lock">Lock selected</button><button type="button" id="pd-unlock">Unlock selected</button></div></div>'+ 
      '<div><div class="label">Selected objects</div><div id="pd-selection-list" class="pd-selection-list"></div></div>'+ 
      '<div class="pd-interactive-status" id="pd-interactive-status" role="status" aria-live="polite"></div>'+ 
      '<div class="pd-defensive-inspector"><h5>Defensive assignment inspector</h5>'+ 
        '<label>Responsibility<input id="pd-defense-responsibility" placeholder="force, spill, curl-flat, man X"></label>'+ 
        '<label>Gap / landmark<input id="pd-defense-gap" placeholder="A, B, C, curl-flat"></label>'+ 
        '<label>Leverage<select id="pd-defense-leverage"><option value="">Not set</option><option value="inside">Inside</option><option value="outside">Outside</option><option value="top-down">Top-down</option><option value="trail">Trail</option></select></label>'+ 
        '<label>Read key<input id="pd-defense-key" placeholder="near back, QB, #2"></label>'+ 
        '<button type="button" id="pd-apply-defense-assignment">Apply selected assignment</button></div>';

    box.querySelectorAll('[data-tool]').forEach(button=>button.onclick=()=>{
      state.tool=button.dataset.tool;
      box.querySelectorAll('[data-tool]').forEach(other=>other.classList.toggle('active',other===button));
      status(state.tool==='select'?'Select / move: click an object, or drag a player to realign.':'Tool: '+state.tool+' - click-drag from a player to draw.');
    });
    box.querySelector('[data-tool="route"]').classList.add('active');
    box.querySelector('#pd-snap').onchange=event=>{state.snap=event.target.checked;status('Grid snapping '+(state.snap?'enabled':'disabled'));};
    box.querySelectorAll('.pd-layer').forEach(control=>control.onchange=()=>{state.layerState[control.dataset.layer]=control.checked;applyLayers();});
    box.querySelector('#pd-duplicate').onclick=duplicate;
    box.querySelector('#pd-copy').onclick=copySelection;
    box.querySelector('#pd-paste').onclick=pasteSelection;
    box.querySelector('#pd-mirror').onclick=mirror;
    box.querySelector('#pd-group').onclick=group;
    box.querySelector('#pd-ungroup').onclick=ungroup;
    box.querySelector('#pd-lock').onclick=()=>setLock(true);
    box.querySelector('#pd-unlock').onclick=()=>setLock(false);
    box.querySelector('#pd-apply-defense-assignment').onclick=applyDefense;
    return box;
  }

  function layerFor(element){
    if(element?.layer&&state.layerState[element.layer]!==undefined)return element.layer;
    if(['annotation','landmark','read'].includes(element?.kind))return 'annotation';
    if(['coverage','rush','stunt','rotation','front'].includes(element?.kind))return 'defense';
    return 'offense';
  }
  function applyLayers(){
    host.querySelectorAll('.pd-path').forEach(path=>{
      const element=currentElement(path.dataset.id);
      if(!element)return;
      path.style.display=state.layerState[layerFor(element)]?'':'none';
      path.classList.toggle('pd-locked',Boolean(element.locked));
    });
    host.querySelectorAll('.pd-player').forEach(group=>{
      const player=currentPlayer(group.dataset.id);
      const layer=player?.unit==='defense'?'defense':'offense';
      group.style.display=state.layerState[layer]?'':'none';
      group.classList.toggle('pd-locked',Boolean(player?.locked));
    });
    host.querySelectorAll('.pd-handle').forEach(handle=>{
      const element=currentElement(handle.dataset.element);
      handle.style.display=element&&state.layerState[layerFor(element)]?'':'none';
    });
  }
  function syncCoreSelection(){
    const selected=lastSelection();
    if(api.syncSelection)api.syncSelection(selected);
    host.querySelectorAll('.pd-path,.pd-player').forEach(node=>{
      node.classList.toggle('selected',node.dataset.id===selected);
      node.classList.toggle('pd-multi-selected',state.selection.has(node.dataset.id));
    });
  }
  function updateSelection(){
    const list=document.getElementById('pd-selection-list');
    if(list)list.innerHTML=[...state.selection].map(value=>'<div class="selected">'+esc(value)+'</div>').join('')||'<span>None - Ctrl/Cmd-click to multi-select.</span>';
    syncCoreSelection();
    renderHandles();
    applyLayers();
  }
  function select(value,additive=false){
    if(!additive)state.selection.clear();
    if(value){
      if(additive&&state.selection.has(value))state.selection.delete(value);
      else state.selection.add(value);
    }
    updateSelection();
    status(state.selection.size+' object'+(state.selection.size===1?'':'s')+' selected');
  }

  function simplify(points){
    const result=[];
    points.forEach(point=>{
      const previous=result[result.length-1];
      if(!previous||Math.hypot(point.x-previous.x,point.y-previous.y)>=.35)result.push(point);
    });
    if(result.length>80){
      const stride=Math.ceil(result.length/80);
      return result.filter((point,index)=>index===0||index===result.length-1||index%stride===0);
    }
    return result;
  }
  function makeElement(design,playerId,points){
    const isLandmark=state.tool==='landmark';
    const layer=isLandmark?'annotation':['coverage','rush','stunt'].includes(state.tool)?'defense':'offense';
    return {
      id:id('E-EDITOR'),kind:isLandmark?'annotation':state.tool,type:isLandmark?'landmark':state.tool,
      asset_id:'EDITOR-'+state.tool.toUpperCase(),player_id:playerId,points:simplify(points),
      arrow_style:isLandmark?'read':state.tool,note:isLandmark?'Teaching landmark':'',layer,locked:false,
      start_ms:0,end_ms:1200,timing:{start_ms:0,end_ms:1200,phases:[{id:'release',label:'Release',start_ms:0,end_ms:250},{id:'develop',label:'Develop',start_ms:250,end_ms:800},{id:'finish',label:'Finish',start_ms:800,end_ms:1200}]}
    };
  }
  function startDraw(player,event,captureTarget){
    state.pointer={mode:'draw',playerId:player.id,pointerId:event.pointerId,startClientX:event.clientX,startClientY:event.clientY,active:false,points:[{...player.start}]};
    captureTarget?.setPointerCapture?.(event.pointerId);
    event.preventDefault();
  }
  function startMove(player,event,captureTarget){
    state.pointer={mode:'move',playerId:player.id,pointerId:event.pointerId,startClientX:event.clientX,startClientY:event.clientY,active:false,base:clone(get()),baseStart:{...player.start},draft:null};
    captureTarget?.setPointerCapture?.(event.pointerId);
    event.preventDefault();
  }
  function pointerDistance(event){return Math.hypot(event.clientX-state.pointer.startClientX,event.clientY-state.pointer.startClientY);}
  function pathData(points){return (points||[]).map((point,index)=>(index?'L':'M')+' '+point.x+' '+point.y).join(' ');}
  function updateMove(event){
    const pointer=state.pointer;
    const field=canvas();
    if(!field)return;
    const box=field.getBoundingClientRect();
    const dx=(event.clientX-pointer.startClientX)/box.width*FIELD_LENGTH;
    const dy=(event.clientY-pointer.startClientY)/box.height*FIELD_WIDTH;
    const draft=clone(pointer.base);
    const player=draft.players.find(value=>value.id===pointer.playerId);
    if(!player)return;
    const next=fieldPoint(pointer.baseStart.x+dx,pointer.baseStart.y+dy);
    const shift={x:next.x-pointer.baseStart.x,y:next.y-pointer.baseStart.y};
    player.start=next;
    draft.elements?.forEach(element=>{
      if(element.player_id!==pointer.playerId||element.follow_player===false||!element.points)return;
      element.points=element.points.map(point=>({x:clamp(point.x+shift.x,0,FIELD_LENGTH),y:clamp(point.y+shift.y,0,FIELD_WIDTH)}));
    });
    pointer.draft=draft;
    const group=Array.from(host.querySelectorAll('.pd-player')).find(value=>value.dataset.id===pointer.playerId);
    if(group)group.setAttribute('transform','translate('+next.x+' '+next.y+')');
    draft.elements?.forEach(element=>{
      const path=Array.from(host.querySelectorAll('.pd-path')).find(value=>value.dataset.id===element.id);
      if(path)path.setAttribute('d',pathData(element.points));
    });
  }
  function drawPreview(points){
    const field=canvas();
    if(!field)return;
    if(!state.preview){state.preview=document.createElementNS(NS,'path');state.preview.classList.add('pd-draw-preview');field.appendChild(state.preview);}
    state.preview.setAttribute('d',pathData(points));
  }
  function pointerMove(event){
    const pointer=state.pointer;
    if(!pointer||event.pointerId!==pointer.pointerId)return;
    if(!pointer.active){
      if(pointerDistance(event)<4)return;
      pointer.active=true;
    }
    if(pointer.mode==='move'){updateMove(event);return;}
    const next=svgPoint(event);
    const previous=pointer.points[pointer.points.length-1];
    if(!previous||Math.hypot(next.x-previous.x,next.y-previous.y)>=.35)pointer.points.push(next);
    drawPreview(pointer.points);
  }
  function finishPointer(event){
    const pointer=state.pointer;
    if(!pointer||event&&event.pointerId!==pointer.pointerId)return;
    state.pointer=null;
    if(state.preview){state.preview.remove();state.preview=null;}
    if(!pointer.active){status(state.selection.size+' object'+(state.selection.size===1?'':'s')+' selected');return;}
    if(pointer.mode==='move'){
      if(pointer.draft){set(pointer.draft);status('Realigned '+pointer.playerId+' and carried its assignments with the player.');}
      return;
    }
    const points=simplify(pointer.points);
    if(points.length<2)points.push(fieldPoint(points[0].x+8,points[0].y+6));
    const design=get();
    design.elements=design.elements||[];
    const element=makeElement(design,pointer.playerId,points);
    design.elements.push(element);
    state.selection.clear();state.selection.add(element.id);
    set(design);
    status('Created '+element.kind+' with '+element.points.length+' editable points.');
  }
  function emptyPointerDown(event){
    if(event.target.closest?.('.pd-player,.pd-path,.pd-handle'))return;
    const playerId=selectedPlayerId();
    const player=playerId&&currentPlayer(playerId);
    if(player&&state.tool!=='select'&&!player.locked){startDraw(player,event,event.currentTarget);return;}
    select(null);
  }
  function targetPointerDown(event){
    const target=event.currentTarget;
    const additive=event.ctrlKey||event.metaKey;
    select(target.dataset.id,additive);
    if(additive)return;
    if(!target.classList.contains('pd-player'))return;
    const player=currentPlayer(target.dataset.id);
    if(!player||player.locked)return;
    if(state.tool==='select'||event.altKey)startMove(player,event,target);
    else startDraw(player,event,target);
    event.stopPropagation();
  }
  function targetKeyDown(event){
    const target=event.currentTarget;
    if(event.key==='Enter'||event.key===' '){select(target.dataset.id,event.ctrlKey||event.metaKey);event.preventDefault();return;}
    if(event.key==='Delete'&&target.classList.contains('pd-path')){deleteSelection();event.preventDefault();}
  }

  function handlePointerDown(event,elementId,index){
    const target=event.currentTarget;
    const draft=get();
    const element=draft.elements?.find(value=>value.id===elementId);
    if(!element||element.locked)return;
    event.stopPropagation();event.preventDefault();
    let active=false;
    const move=moveEvent=>{
      if(moveEvent.pointerId!==event.pointerId)return;
      if(!active){if(Math.hypot(moveEvent.clientX-event.clientX,moveEvent.clientY-event.clientY)<3)return;active=true;}
      const next=svgPoint(moveEvent);
      const current=draft.elements?.find(value=>value.id===elementId);
      if(!current)return;
      current.points[index]=next;
      target.setAttribute('cx',next.x);target.setAttribute('cy',next.y);target.setAttribute('aria-valuetext',next.x+', '+next.y);
      const path=Array.from(host.querySelectorAll('.pd-path')).find(value=>value.dataset.id===elementId);
      if(path)path.setAttribute('d',pathData(current.points));
    };
    const up=upEvent=>{
      if(upEvent.pointerId!==event.pointerId)return;
      window.removeEventListener('pointermove',move);window.removeEventListener('pointerup',up);window.removeEventListener('pointercancel',up);
      if(active){set(draft);select(elementId);status('Updated '+(element.type||element.kind)+' point '+(index+1)+'.');}
    };
    target.setPointerCapture?.(event.pointerId);
    window.addEventListener('pointermove',move);window.addEventListener('pointerup',up);window.addEventListener('pointercancel',up);
  }
  function handleKeyDown(event,elementId,index){
    const deltas={ArrowLeft:{x:-.25,y:0},ArrowRight:{x:.25,y:0},ArrowUp:{x:0,y:-.25},ArrowDown:{x:0,y:.25}};
    const delta=deltas[event.key];
    if(!delta)return;
    const design=get();const element=design.elements?.find(value=>value.id===elementId);
    if(!element||element.locked)return;
    const step=event.shiftKey?4:1;
    element.points[index]=fieldPoint(element.points[index].x+delta.x*step,element.points[index].y+delta.y*step);
    set(design);select(elementId);status('Moved handle '+(index+1)+' with the keyboard.');event.preventDefault();
  }
  function renderHandles(){
    host.querySelectorAll('.pd-handle').forEach(handle=>handle.remove());
    const field=canvas();
    if(!field)return;
    state.selection.forEach(elementId=>{
      const element=currentElement(elementId);
      if(!element||element.locked||!element.points)return;
      element.points.forEach((point,index)=>{
        const handle=document.createElementNS(NS,'circle');
        handle.classList.add('pd-handle');handle.setAttribute('r','1.2');handle.setAttribute('cx',point.x);handle.setAttribute('cy',point.y);
        handle.dataset.element=elementId;handle.dataset.index=index;handle.setAttribute('tabindex','0');handle.setAttribute('role','slider');
        handle.setAttribute('aria-label','Edit '+(element.type||element.kind)+' point '+(index+1));handle.setAttribute('aria-valuetext',point.x+', '+point.y);
        handle.onpointerdown=event=>handlePointerDown(event,elementId,index);
        handle.onkeydown=event=>handleKeyDown(event,elementId,index);
        field.appendChild(handle);
      });
    });
  }
  function bind(){
    ensureControls();
    const field=canvas();
    if(!field)return;
    field.onpointerdown=emptyPointerDown;
    field.onpointermove=pointerMove;
    field.onpointerup=finishPointer;
    field.onpointercancel=finishPointer;
    host.querySelectorAll('.pd-player,.pd-path').forEach(target=>{
      target.onpointerdown=targetPointerDown;
      target.onkeydown=targetKeyDown;
    });
    updateSelection();
  }
  function selectedElements(){
    const design=get();
    return (design.elements||[]).filter(element=>state.selection.has(element.id));
  }
  function duplicate(){
    const design=get();const items=selectedElements();
    if(!items.length){status('Select one or more paths first.');return;}
    items.forEach((element,index)=>{const copy=clone(element);copy.id=id('E-COPY');copy.points=copy.points.map(point=>fieldPoint(point.x+2+(index%3),point.y+1));copy.locked=false;design.elements.push(copy);state.selection.add(copy.id);});
    set(design);status('Duplicated '+items.length+' element'+(items.length===1?'':'s')+'.');
  }
  function copySelection(){
    state.copyBuffer=clone(selectedElements());
    status(state.copyBuffer.length+' element'+(state.copyBuffer.length===1?'':'s')+' copied.');
  }
  function pasteSelection(){
    if(!state.copyBuffer.length){status('Copy an element before pasting.');return;}
    const design=get();state.selection.clear();
    state.copyBuffer.forEach((element,index)=>{const copy=clone(element);copy.id=id('E-PASTE');copy.points=copy.points.map(point=>fieldPoint(point.x+3+(index%2),point.y+2));copy.locked=false;design.elements.push(copy);state.selection.add(copy.id);});
    set(design);status('Pasted '+state.copyBuffer.length+' element'+(state.copyBuffer.length===1?'':'s')+'.');
  }
  function mirror(){
    const design=get();
    selectedElements().forEach(element=>{element.points=(element.points||[]).map(point=>({...point,x:FIELD_LENGTH-point.x}));});
    design.players?.forEach(player=>{if(state.selection.has(player.id))player.start.x=FIELD_LENGTH-player.start.x;});
    set(design);status('Mirrored selected geometry across the field center.');
  }
  function group(){
    const items=selectedElements();
    if(!items.length){status('Select one or more elements to group.');return;}
    const design=get();const groupId=id('GROUP');design.elements.forEach(element=>{if(state.selection.has(element.id))element.group_id=groupId;});set(design);status('Grouped '+items.length+' element'+(items.length===1?'':'s')+'.');
  }
  function ungroup(){
    const design=get();const items=selectedElements();items.forEach(element=>delete element.group_id);set(design);status('Ungrouped '+items.length+' selected element'+(items.length===1?'':'s')+'.');
  }
  function setLock(locked){
    const design=get();let count=0;
    design.elements?.forEach(element=>{if(state.selection.has(element.id)){element.locked=locked;count++;}});
    design.players?.forEach(player=>{if(state.selection.has(player.id)){player.locked=locked;count++;}});
    if(!count){status('Select an object before changing its lock state.');return;}
    set(design);status((locked?'Locked ':'Unlocked ')+count+' selected object'+(count===1?'':'s')+'.');
  }
  function deleteSelection(){
    const design=get();const before=design.elements?.length||0;
    design.elements=(design.elements||[]).filter(element=>!state.selection.has(element.id));
    if(design.elements.length===before){status('Select one or more assignments to delete.');return;}
    state.selection.clear();set(design);status('Deleted selected assignments.');
  }
  function applyDefense(){
    const design=get();
    const assignment={
      responsibility:document.getElementById('pd-defense-responsibility')?.value.trim()||'',
      gap_or_landmark:document.getElementById('pd-defense-gap')?.value.trim()||'',
      leverage:document.getElementById('pd-defense-leverage')?.value||'',
      read_key:document.getElementById('pd-defense-key')?.value.trim()||''
    };
    let count=0;
    design.players?.forEach(player=>{if(state.selection.has(player.id)){Object.assign(player,assignment,{unit:'defense',assignment:clone(assignment)});count++;}});
    design.elements?.forEach(element=>{if(state.selection.has(element.id)){Object.assign(element,assignment,{layer:'defense'});count++;}});
    if(!count){status('Select a defender or defensive assignment first.');return;}
    set(design);status('Applied defensive responsibilities to '+count+' selected object'+(count===1?'':'s')+'.');
  }

  const originalSet=api.setDesign;
  api.setDesign=design=>{originalSet(design);requestAnimationFrame(()=>{window.NFLFIDOSPlayDesignerAssets?.refresh?.();bind();});};
  if(window.MutationObserver){
    state.observer=new MutationObserver(mutations=>{
      if(mutations.some(mutation=>[...mutation.addedNodes,...mutation.removedNodes].some(node=>node.nodeType===1&&node.classList?.contains('pd-dynamic'))))requestAnimationFrame(bind);
    });
    const field=canvas();
    if(field)state.observer.observe(field,{childList:true});
  }
  window.NFLFIDOSPlayDesignerInteractive={getSelectedPlayerId:selectedPlayerId,getSelection:()=>[...state.selection],refresh:bind};
  bind();
}());
