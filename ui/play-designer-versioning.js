(function(){
  const section=document.getElementById('play-designer-section');
  const api=window.NFLFIDOSPlayDesigner;
  if(!section||!api)return;

  const state={snapshots:[],releases:[],base:'',compare:'',busy:false};
  const clone=value=>JSON.parse(JSON.stringify(value));
  const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const design=()=>clone(api.getDesign());
  const credentials=()=>({organization:document.getElementById('film-org')?.value.trim()||'',token:document.getElementById('film-token')?.value.trim()||''});
  const card=()=>document.getElementById('pd-versioning-card');
  const status=(message,tone='')=>{const node=document.getElementById('pd-versioning-status');if(node){node.textContent=message;node.className='pd-versioning-status '+tone;}};
  const id=prefix=>prefix+'-'+Date.now().toString(36)+'-'+Math.random().toString(36).slice(2,8);

  async function fetchJson(url,options){
    const response=await fetch(url,options);
    let payload=null;
    try{payload=await response.json();}catch(error){payload={error:'Server returned a non-JSON response.'};}
    if(!response.ok){const failure=new Error(payload?.error||('Request failed ('+response.status+')'));failure.status=response.status;failure.payload=payload;throw failure;}
    return payload;
  }

  function requireCredentials(){
    const credentialsValue=credentials();
    if(!credentialsValue.organization||!credentialsValue.token)throw new Error('Enter organization and Bearer token in Film Room first.');
    if(!design().id)throw new Error('The current play has no design id.');
    return credentialsValue;
  }

  function buildCard(){
    let box=card();
    if(box)return box;
    box=document.createElement('article');
    box.id='pd-versioning-card';
    box.className='pd-versioning-card';
    section.appendChild(box);
    box.innerHTML='<h4>Version history & release control</h4><p class="pd-versioning-help">Every server save creates an immutable snapshot with a content checksum and renderer checksum. Published bundles are locked; rollback always creates a new draft for review.</p>'+
      '<div class="pd-versioning-toolbar"><button type="button" id="pd-versioning-load">Load version history</button><button type="button" id="pd-versioning-save">Save server snapshot</button><button type="button" id="pd-versioning-review">Request review</button><span id="pd-versioning-current" class="pd-versioning-badge">Local draft</span></div>'+
      '<p id="pd-versioning-status" class="pd-versioning-status" role="status" aria-live="polite">Version history is organization-scoped and requires an approved token.</p>'+
      '<div class="pd-versioning-grid"><div class="pd-versioning-panel"><h5>Compare snapshots</h5><label>Base snapshot<select id="pd-versioning-base"><option value="">Load history first</option></select></label><label>Compare snapshot<select id="pd-versioning-compare"><option value="">Load history first</option></select></label><button type="button" id="pd-versioning-diff">Compare element changes</button><div id="pd-versioning-diff-output" class="pd-versioning-diff" aria-live="polite"></div></div>'+ 
      '<div class="pd-versioning-panel"><h5>Publish immutable release</h5><label>Owner decision reference<input id="pd-versioning-decision" placeholder="DEC-PLAY-..." autocomplete="off"></label><label>Game-plan snapshot lock (optional)<input id="pd-versioning-game-plan" placeholder="GAMEPLAN-SNAPSHOT-..." autocomplete="off"></label><button type="button" id="pd-versioning-publish">Publish release</button><div id="pd-versioning-releases" class="pd-versioning-releases"></div></div>'+ 
      '<div class="pd-versioning-panel"><h5>Branch and merge</h5><label>Branch id<input id="pd-versioning-branch-id" autocomplete="off"></label><button type="button" id="pd-versioning-branch">Create immutable-base branch</button><label>Branch to merge<input id="pd-versioning-merge-id" placeholder="DESIGN-...-BRANCH-..." autocomplete="off"></label><button type="button" id="pd-versioning-merge">Three-way merge branch</button></div>'+ 
      '<div class="pd-versioning-panel"><h5>Owner rollback</h5><label>Snapshot to restore<select id="pd-versioning-rollback"><option value="">Load history first</option></select></label><label>Rollback decision reference<input id="pd-versioning-rollback-decision" placeholder="DEC-ROLLBACK-..." autocomplete="off"></label><button type="button" id="pd-versioning-rollback-action">Create rollback draft</button><p class="pd-versioning-help">Rollback never rewrites history and is restricted to the program owner.</p></div></div>'+ 
      '<div class="pd-versioning-panel pd-versioning-snapshot-list"><h5>Immutable snapshots</h5><div id="pd-versioning-snapshots"></div></div>';
    box.querySelector('#pd-versioning-load').onclick=loadVersions;
    box.querySelector('#pd-versioning-save').onclick=saveServer;
    box.querySelector('#pd-versioning-review').onclick=requestReview;
    box.querySelector('#pd-versioning-diff').onclick=compareSnapshots;
    box.querySelector('#pd-versioning-publish').onclick=publish;
    box.querySelector('#pd-versioning-branch').onclick=createBranch;
    box.querySelector('#pd-versioning-merge').onclick=mergeBranch;
    box.querySelector('#pd-versioning-rollback-action').onclick=rollback;
    box.querySelector('#pd-versioning-base').onchange=event=>{state.base=event.target.value;};
    box.querySelector('#pd-versioning-compare').onchange=event=>{state.compare=event.target.value;};
    return box;
  }

  function snapshotLabel(snapshot){
    return (snapshot.version||'0.1.0')+' · '+(snapshot.source||'save')+' · '+String(snapshot.checksum||'').slice(0,12);
  }

  function setOptions(selectId,items,selected){
    const select=document.getElementById(selectId);if(!select)return;
    select.replaceChildren();
    if(!items.length){const option=document.createElement('option');option.value='';option.textContent='No snapshots';select.appendChild(option);return;}
    items.forEach(item=>{const option=document.createElement('option');option.value=item.id;option.textContent=snapshotLabel(item);select.appendChild(option);});
    select.value=items.some(item=>item.id===selected)?selected:items[0].id;
  }

  function renderHistory(){
    const current=design();
    const badge=document.getElementById('pd-versioning-current');
    if(badge)badge.textContent=(current.status||'draft')+' · v'+(current.version||'local')+' · '+String(current.checksum||'local').slice(0,12);
    setOptions('pd-versioning-base',state.snapshots,state.base);
    setOptions('pd-versioning-compare',state.snapshots,state.compare||state.snapshots[1]?.id||state.snapshots[0]?.id||'');
    setOptions('pd-versioning-rollback',state.snapshots,state.snapshots[0]?.id||'');
    state.base=document.getElementById('pd-versioning-base')?.value||'';
    state.compare=document.getElementById('pd-versioning-compare')?.value||'';
    const list=document.getElementById('pd-versioning-snapshots');
    if(list){list.replaceChildren();if(!state.snapshots.length){const empty=document.createElement('p');empty.className='pd-versioning-help';empty.textContent='No server snapshots loaded.';list.appendChild(empty);}state.snapshots.slice().reverse().forEach(snapshot=>{const row=document.createElement('div');row.className='pd-versioning-snapshot';const title=document.createElement('strong');title.textContent=snapshotLabel(snapshot);const meta=document.createElement('span');meta.textContent=(snapshot.created_by||'staff')+' · '+(snapshot.created_at||'')+' · '+(snapshot.id||'');row.append(title,meta);list.appendChild(row);});}
    const releases=document.getElementById('pd-versioning-releases');
    if(releases){releases.replaceChildren();if(!state.releases.length){const empty=document.createElement('p');empty.className='pd-versioning-help';empty.textContent='No immutable releases yet.';releases.appendChild(empty);}state.releases.slice().reverse().forEach(release=>{const row=document.createElement('div');row.className='pd-versioning-release';const title=document.createElement('strong');title.textContent=release.id+' · v'+release.version;const meta=document.createElement('span');meta.textContent='Snapshot '+release.snapshot_id+' · '+(release.game_plan_snapshot_locked?'game-plan locked':'no game-plan lock');row.append(title,meta);releases.appendChild(row);});}
  }

  function textRow(label,value){const row=document.createElement('div');row.className='pd-diff-row';const key=document.createElement('strong');key.textContent=label;const valueNode=document.createElement('span');valueNode.textContent=value;row.append(key,valueNode);return row;}
  function renderDiff(payload){
    const output=document.getElementById('pd-versioning-diff-output');if(!output)return;output.replaceChildren();
    const diff=payload?.diff||{};output.appendChild(textRow('Snapshot',String(payload?.base_version||'')+' → '+String(payload?.compare_version||'')));
    output.appendChild(textRow('Changed fields',diff.changed_fields?.join(', ')||'None'));
    output.appendChild(textRow('Timeline',diff.timeline_changed?'Changed':'Unchanged'));
    ['players','elements'].forEach(collection=>{
      const data=diff[collection]||{};const block=document.createElement('div');block.className='pd-diff-block';const heading=document.createElement('strong');heading.textContent=collection[0].toUpperCase()+collection.slice(1);block.appendChild(heading);block.appendChild(textRow('Added',data.added?.join(', ')||'None'));block.appendChild(textRow('Removed',data.removed?.join(', ')||'None'));(data.changed||[]).forEach(item=>block.appendChild(textRow('Changed '+item.id,(item.fields||[]).join(', ')||'details')));output.appendChild(block);
    });
    output.appendChild(textRow('Checksums',String(diff.base_checksum||'').slice(0,16)+' → '+String(diff.candidate_checksum||'').slice(0,16)));
  }

  function applyServerDesign(saved){
    if(!saved)return;
    api.setDesign(clone(saved));
    window.NFLFIDOSPlayDesignerSync?.refresh?.();
    renderHistory();
  }

  async function loadVersions(){
    try{
      const credentialsValue=requireCredentials();const current=design();
      const payload=await fetchJson('/v1/playbook/designs/'+encodeURIComponent(current.id)+'/versions?organization_id='+encodeURIComponent(credentialsValue.organization),{headers:{Authorization:'Bearer '+credentialsValue.token}});
      state.snapshots=payload.data?.snapshots||[];state.releases=payload.data?.releases||[];renderHistory();status('Loaded '+state.snapshots.length+' immutable snapshot'+(state.snapshots.length===1?'':'s')+' and '+state.releases.length+' release'+(state.releases.length===1?'':'s')+'.','good');
    }catch(error){status('Version history unavailable: '+error.message,'bad');}
  }

  async function saveServer(){
    try{
      const credentialsValue=requireCredentials();const current=design();
      const payload=await fetchJson('/v1/playbook/designs',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+credentialsValue.token},body:JSON.stringify({organization_id:credentialsValue.organization,design:current,expected_revision:current._revision??null})});
      applyServerDesign(payload.data);status('Server snapshot saved at revision '+payload.data._revision+'.','good');await loadVersions();
    }catch(error){status('Server snapshot failed: '+error.message,'bad');}
  }

  async function requestReview(){
    try{const credentialsValue=requireCredentials();const current=design();const payload=await fetchJson('/v1/playbook/designs/request-review',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+credentialsValue.token},body:JSON.stringify({organization_id:credentialsValue.organization,design_id:current.id,decision_ref:'DEC-REVIEW-'+Date.now().toString(36)})});applyServerDesign(payload.data);status('Review requested. Publication remains owner-controlled.','warn');}catch(error){status('Review request failed: '+error.message,'bad');}
  }

  async function compareSnapshots(){
    try{const credentialsValue=requireCredentials();const current=design();if(!state.base||!state.compare){throw new Error('Load history and choose two snapshots first.');}const payload=await fetchJson('/v1/playbook/designs/'+encodeURIComponent(current.id)+'/diff?organization_id='+encodeURIComponent(credentialsValue.organization)+'&base_snapshot_id='+encodeURIComponent(state.base)+'&compare_snapshot_id='+encodeURIComponent(state.compare),{headers:{Authorization:'Bearer '+credentialsValue.token}});renderDiff(payload.data);status('Element-level comparison complete.','good');}catch(error){status('Comparison failed: '+error.message,'bad');}
  }

  async function publish(){
    try{const credentialsValue=requireCredentials();const current=design();const decision=document.getElementById('pd-versioning-decision').value.trim();if(!decision)throw new Error('Owner decision reference is required.');const gamePlan=document.getElementById('pd-versioning-game-plan').value.trim();const body={organization_id:credentialsValue.organization,design_id:current.id,decision_ref:decision};if(gamePlan)body.game_plan_snapshot_id=gamePlan;const payload=await fetchJson('/v1/playbook/designs/publish',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+credentialsValue.token},body:JSON.stringify(body)});applyServerDesign(payload.data);status('Immutable release '+(payload.data.release_id||'created')+' published.','good');await loadVersions();}catch(error){status('Publish failed: '+error.message,'bad');}
  }

  async function createBranch(){
    try{const credentialsValue=requireCredentials();const current=design();const input=document.getElementById('pd-versioning-branch-id');const branchId=input.value.trim()||current.id+'-BRANCH-'+Date.now().toString(36);const payload=await fetchJson('/v1/playbook/designs/branch',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+credentialsValue.token},body:JSON.stringify({organization_id:credentialsValue.organization,design_id:current.id,branch_id:branchId})});input.value=branchId;document.getElementById('pd-versioning-merge-id').value=branchId;status('Branch '+branchId+' created from immutable base snapshot.','good');}catch(error){status('Branch creation failed: '+error.message,'bad');}
  }

  async function mergeBranch(){
    try{const credentialsValue=requireCredentials();const current=design();const branchId=document.getElementById('pd-versioning-merge-id').value.trim();if(!branchId)throw new Error('Enter a branch id to merge.');const payload=await fetchJson('/v1/playbook/designs/versioning/merge',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+credentialsValue.token},body:JSON.stringify({organization_id:credentialsValue.organization,design_id:current.id,branch_id:branchId,expected_revision:current._revision??null})});if(payload.status==='conflict'||payload.data?.status==='conflict'){status('Merge conflict: review the element-level paths returned by the server.','bad');renderDiff(payload.data?.diff||{});return;}applyServerDesign(payload.data?.design);status('Branch merged into a new draft revision.','good');await loadVersions();}catch(error){const details=error.payload?.data;if(details?.conflicts)status('Merge conflict: '+details.conflicts.join('; '),'bad');else status('Merge failed: '+error.message,'bad');}
  }

  async function rollback(){
    try{const credentialsValue=requireCredentials();const current=design();const snapshotId=document.getElementById('pd-versioning-rollback').value;const decision=document.getElementById('pd-versioning-rollback-decision').value.trim();if(!snapshotId||!decision)throw new Error('Choose a snapshot and enter the owner rollback decision reference.');const payload=await fetchJson('/v1/playbook/designs/versioning/rollback',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+credentialsValue.token},body:JSON.stringify({organization_id:credentialsValue.organization,design_id:current.id,snapshot_id:snapshotId,decision_ref:decision,expected_revision:current._revision??null})});applyServerDesign(payload.data?.design);status('Rollback created a new draft from '+snapshotId+'.','warn');await loadVersions();}catch(error){status('Rollback failed: '+error.message,'bad');}
  }

  buildCard();
  renderHistory();
  window.NFLFIDOSPlayDesignerVersioning={refresh:renderHistory,load:loadVersions,compare:compareSnapshots};
}());
