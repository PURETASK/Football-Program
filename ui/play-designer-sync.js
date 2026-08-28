(function(){
  const host=document.getElementById('play-designer');
  const section=document.getElementById('play-designer-section');
  const api=window.NFLFIDOSPlayDesigner;
  if(!host||!section||!api)return;

  const QUEUE_KEY='nfl-fidos-play-designer-sync-queue-v1';
  const DRAFT_KEY='nfl-fidos-play-designer-drafts-v1';
  const DB_NAME='nfl-fidos-play-designer-sync-v1';
  const DB_STORE='queue';
  const DRAFT_STORE='drafts';
  const KEY_STORE='keys';
  const state={
    queue:[],queueLoaded:false,remoteDesigns:[],organization:'',token:'',activeRevision:null,
    autosave:true,autosaveTimer:0,retryTimer:0,flushing:false,remoteApplying:false,conflict:null,dbPromise:null,cryptoKeyPromise:null
  };
  const clone=value=>JSON.parse(JSON.stringify(value));
  const id=prefix=>prefix+'-'+Date.now().toString(36)+'-'+Math.random().toString(36).slice(2,8);
  const now=()=>Date.now();
  const panel=()=>document.getElementById('pd-sync-card');

  function credentials(){
    const organizationInput=document.getElementById('film-org');
    const tokenInput=document.getElementById('film-token');
    const organization=organizationInput?organizationInput.value.trim():state.organization;
    const token=tokenInput?tokenInput.value.trim():state.token;
    return {organization,token};
  }
  function online(){return !('onLine' in navigator)||navigator.onLine!==false;}
  function localQueue(){try{const parsed=JSON.parse(localStorage.getItem(QUEUE_KEY)||'[]');return Array.isArray(parsed)?parsed:[];}catch(error){return [];}}
  function saveLocalQueue(items){try{localStorage.setItem(QUEUE_KEY,JSON.stringify(items));setStatus('Encrypted IndexedDB is unavailable; compatibility queue storage is active. Keep this tab open until sync completes.','warn');}catch(error){setStatus('Local queue storage is unavailable; keep this tab open until sync completes.','bad');}}
  function localDrafts(){try{const parsed=JSON.parse(localStorage.getItem(DRAFT_KEY)||'[]');return Array.isArray(parsed)?parsed:[];}catch(error){return [];}}
  function saveLegacyDraft(design){try{const list=localDrafts().filter(item=>item.id!==design.id);list.unshift(clone(design));localStorage.setItem(DRAFT_KEY,JSON.stringify(list.slice(0,25)));}catch(error){setStatus('Local draft recovery storage is unavailable.','bad');}}

  function openDb(){
    if(state.dbPromise)return state.dbPromise;
    if(!window.indexedDB){state.dbPromise=Promise.resolve(null);return state.dbPromise;}
    state.dbPromise=new Promise((resolve,reject)=>{const request=window.indexedDB.open(DB_NAME,2);request.onupgradeneeded=()=>{const database=request.result;if(!database.objectStoreNames.contains(DB_STORE))database.createObjectStore(DB_STORE,{keyPath:'id'});if(!database.objectStoreNames.contains(DRAFT_STORE))database.createObjectStore(DRAFT_STORE,{keyPath:'id'});if(!database.objectStoreNames.contains(KEY_STORE))database.createObjectStore(KEY_STORE);};request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(request.error||new Error('IndexedDB unavailable'));});
    return state.dbPromise;
  }
  function bytesToBase64(bytes){let binary='';bytes.forEach(byte=>{binary+=String.fromCharCode(byte);});return btoa(binary);}
  function base64ToBytes(value){const binary=atob(value);const bytes=new Uint8Array(binary.length);for(let index=0;index<binary.length;index++)bytes[index]=binary.charCodeAt(index);return bytes;}
  async function offlineKey(){
    if(!window.crypto?.subtle||!window.indexedDB)return null;
    if(state.cryptoKeyPromise)return state.cryptoKeyPromise;
    state.cryptoKeyPromise=(async()=>{const db=await openDb();if(!db)return null;const existing=await new Promise((resolve,reject)=>{const request=db.transaction(KEY_STORE,'readonly').objectStore(KEY_STORE).get('offline-aes-gcm');request.onsuccess=()=>resolve(request.result||null);request.onerror=()=>reject(request.error);});if(existing)return existing;const key=await window.crypto.subtle.generateKey({name:'AES-GCM',length:256},true,['encrypt','decrypt']);await new Promise((resolve,reject)=>{const transaction=db.transaction(KEY_STORE,'readwrite');transaction.objectStore(KEY_STORE).put(key,'offline-aes-gcm');transaction.oncomplete=resolve;transaction.onerror=()=>reject(transaction.error);});return key;})().catch(()=>null);
    return state.cryptoKeyPromise;
  }
  async function encryptRecord(value){const key=await offlineKey();if(!key)return value;const iv=window.crypto.getRandomValues(new Uint8Array(12));const encoded=new TextEncoder().encode(JSON.stringify(value));const ciphertext=await window.crypto.subtle.encrypt({name:'AES-GCM',iv},key,encoded);return {id:value.id,encrypted:true,algorithm:'AES-GCM-256',iv:bytesToBase64(iv),ciphertext:bytesToBase64(new Uint8Array(ciphertext))};}
  async function decryptRecord(value){if(!value?.encrypted)return value;const key=await offlineKey();if(!key)throw new Error('Encrypted offline key is unavailable');const plaintext=await window.crypto.subtle.decrypt({name:'AES-GCM',iv:base64ToBytes(value.iv)},key,base64ToBytes(value.ciphertext));return JSON.parse(new TextDecoder().decode(plaintext));}
  async function readDrafts(){try{const db=await openDb();if(!db)return localDrafts();const records=await new Promise((resolve,reject)=>{const request=db.transaction(DRAFT_STORE,'readonly').objectStore(DRAFT_STORE).getAll();request.onsuccess=()=>resolve(Array.isArray(request.result)?request.result:[]);request.onerror=()=>reject(request.error);});const drafts=await Promise.all(records.map(decryptRecord));return drafts.filter(Boolean).sort((first,second)=>(second.saved_at||0)-(first.saved_at||0));}catch(error){return localDrafts();}}
  async function saveLocalDraft(design){try{const db=await openDb();if(!db){saveLegacyDraft(design);return;}const persisted=await encryptRecord({...clone(design),saved_at:now()});await new Promise((resolve,reject)=>{const transaction=db.transaction(DRAFT_STORE,'readwrite');transaction.objectStore(DRAFT_STORE).put(persisted);transaction.oncomplete=resolve;transaction.onerror=()=>reject(transaction.error);});}catch(error){saveLegacyDraft(design);}}
  async function readQueue(){
    try{const db=await openDb();if(!db)return localQueue();const records=await new Promise((resolve,reject)=>{const request=db.transaction(DB_STORE,'readonly').objectStore(DB_STORE).getAll();request.onsuccess=()=>resolve(Array.isArray(request.result)?request.result:[]);request.onerror=()=>reject(request.error);});return (await Promise.all(records.map(decryptRecord))).filter(Boolean);}catch(error){return localQueue();}
  }
  async function replaceQueue(items){
    state.queue=items;
    try{const db=await openDb();if(!db){saveLocalQueue(items);return;}const persisted=await Promise.all(items.map(encryptRecord));await new Promise((resolve,reject)=>{const transaction=db.transaction(DB_STORE,'readwrite');const store=transaction.objectStore(DB_STORE);store.clear();persisted.forEach(item=>store.put(item));transaction.oncomplete=resolve;transaction.onerror=()=>reject(transaction.error);});}catch(error){saveLocalQueue(items);}
  }
  async function ensureQueue(){if(!state.queueLoaded){state.queue=await readQueue();state.queueLoaded=true;}return state.queue;}
  async function fetchJson(url,options){
    const response=await fetch(url,options);let payload=null;try{payload=await response.json();}catch(error){payload={error:'Server returned a non-JSON response.'};}
    if(!response.ok){const failure=new Error(payload?.error||('Request failed ('+response.status+')'));failure.status=response.status;failure.payload=payload;throw failure;}
    return payload;
  }
  function setStatus(message,tone=''){const element=document.getElementById('pd-sync-status');if(!element)return;element.textContent=message;element.className='pd-sync-status '+tone;}
  function designLabel(design){return (design?.concept||design?.id||'Unnamed play')+' / '+(design?.unit||'unit')+(design?(' / rev '+(design._revision??'local')):'');}
  function currentDesign(){return clone(api.getDesign());}
  function findQueueEntry(organization,designId){return state.queue.find(entry=>entry.organization_id===organization&&entry.design_id===designId);}

  function renderQueue(){
    const list=document.getElementById('pd-sync-queue-list');if(!list)return;list.innerHTML='';
    if(!state.queue.length){list.innerHTML='<span class="pd-sync-help">No pending offline or retry work.</span>';return;}
    state.queue.slice().sort((a,b)=>(a.next_attempt_at||0)-(b.next_attempt_at||0)).forEach(entry=>{const row=document.createElement('div');row.className='pd-sync-queue-item';const meta=document.createElement('span');meta.className='meta';meta.textContent=designLabel(entry.design)+' / '+entry.organization_id;const status=document.createElement('span');status.textContent=(entry.status||'queued')+(entry.last_error?' - '+entry.last_error:'');row.append(meta,status);list.appendChild(row);});
  }
  function diffSummary(local,server){
    const changes=[];const keys=[...new Set([...Object.keys(local||{}),...Object.keys(server||{})])].filter(key=>!['_revision','validation','updated_at','organization_id'].includes(key));
    keys.forEach(key=>{if(JSON.stringify(local?.[key])!==JSON.stringify(server?.[key]))changes.push(key);});
    const localElements=new Map((local?.elements||[]).map(element=>[element.id,element]));const serverElements=new Map((server?.elements||[]).map(element=>[element.id,element]));
    const added=[...serverElements.keys()].filter(key=>!localElements.has(key));const removed=[...localElements.keys()].filter(key=>!serverElements.has(key));const changed=[...localElements.keys()].filter(key=>serverElements.has(key)&&JSON.stringify(localElements.get(key))!==JSON.stringify(serverElements.get(key)));
    return 'Changed top-level fields: '+(changes.join(', ')||'none')+'\nAssignments added on server: '+(added.length||0)+'; removed on server: '+(removed.length||0)+'; changed in both: '+(changed.length||0);
  }
  function renderConflict(){
    const box=document.getElementById('pd-sync-conflict');if(!box)return;const conflict=state.conflict;box.hidden=!conflict;if(!conflict)return;
    const server=conflict.details?.server_design||{};document.getElementById('pd-sync-conflict-title').textContent='Conflict: '+designLabel(conflict.entry.design);document.getElementById('pd-sync-conflict-diff').textContent=diffSummary(conflict.entry.design,server)+'\nServer revision: '+(server._revision??'unknown')+' | Local expected: '+(conflict.entry.expected_revision??'local');
  }
  function renderRemote(){
    const select=document.getElementById('pd-sync-remote-design');if(!select)return;select.innerHTML='';const empty=document.createElement('option');empty.value='';empty.textContent='Select a server design';select.appendChild(empty);state.remoteDesigns.forEach(design=>{const option=document.createElement('option');option.value=design.id;option.textContent=designLabel(design);select.appendChild(option);});
  }
  function renderPanel(){
    const badge=document.getElementById('pd-sync-online');if(badge){badge.textContent=online()?'Online':'Offline / queued';badge.classList.toggle('offline',!online());}
    const count=document.getElementById('pd-sync-queue-count');if(count)count.textContent=state.queue.length+' pending item'+(state.queue.length===1?'':'s');
    const checkbox=document.getElementById('pd-sync-autosave');if(checkbox)checkbox.checked=state.autosave;
    renderQueue();renderRemote();renderConflict();
  }
  function buildPanel(){
    let box=panel();if(box)return box;box=document.createElement('article');box.id='pd-sync-card';box.className='pd-sync-card';section.appendChild(box);
    box.innerHTML='<h4>Organization sync & recovery</h4><p class="pd-sync-help">Uses the organization and Bearer token entered in Film Room. Tokens stay in memory; IndexedDB queue and draft records use AES-GCM encryption at rest when Web Crypto is available, with an explicit compatibility warning if it is not.</p><div class="pd-sync-toolbar"><span id="pd-sync-online" class="pd-sync-online">Online</span><label><input id="pd-sync-autosave" type="checkbox" checked> Autosave organization draft changes</label></div><div class="pd-sync-actions" style="margin-top:.5rem"><button type="button" id="pd-sync-load">Load organization plays</button><button type="button" id="pd-sync-save">Save current play now</button><button type="button" id="pd-sync-recover">Recover latest local draft</button><button type="button" id="pd-sync-retry">Retry queued work</button></div><p id="pd-sync-status" class="pd-sync-status" role="status" aria-live="polite">Local draft mode until an organization and token are provided.</p><div class="pd-sync-remote"><label>Server play to open<select id="pd-sync-remote-design"><option value="">Load the organization first</option></select></label><button type="button" id="pd-sync-open">Open selected server play</button></div><div class="pd-sync-queue"><strong id="pd-sync-queue-count">0 pending items</strong><div id="pd-sync-queue-list" class="pd-sync-queue-list"></div></div><div id="pd-sync-conflict" class="pd-sync-conflict" hidden><h5 id="pd-sync-conflict-title">Conflict</h5><div id="pd-sync-conflict-diff" class="pd-sync-conflict-diff"></div><div class="pd-sync-conflict-actions"><button type="button" id="pd-sync-use-server">Use server version</button><button type="button" id="pd-sync-retry-local">Retry local over server revision</button><button type="button" id="pd-sync-save-branch" class="primary">Save local as branch</button><button type="button" id="pd-sync-dismiss">Keep conflict visible</button></div></div>';
    box.querySelector('#pd-sync-load').onclick=loadOrganization;
    box.querySelector('#pd-sync-save').onclick=()=>enqueueCurrent('manual',true);
    box.querySelector('#pd-sync-recover').onclick=recoverLocal;
    box.querySelector('#pd-sync-retry').onclick=()=>flushQueue(true);
    box.querySelector('#pd-sync-autosave').onchange=event=>{state.autosave=event.target.checked;setStatus(state.autosave?'Autosave enabled.':'Autosave disabled; use Save current play now.','good');};
    box.querySelector('#pd-sync-open').onclick=openRemote;
    box.querySelector('#pd-sync-use-server').onclick=useServer;
    box.querySelector('#pd-sync-retry-local').onclick=retryLocal;
    box.querySelector('#pd-sync-save-branch').onclick=saveAsBranch;
    box.querySelector('#pd-sync-dismiss').onclick=()=>setStatus('Conflict remains visible until a resolution is selected.','warn');
    return box;
  }
  async function loadOrganization(){
    const {organization,token}=credentials();if(!organization||!token){setStatus('Enter organization and Bearer token in Film Room before loading server plays.','warn');return;}
    state.organization=organization;state.token=token;setStatus('Loading organization-scoped play designs...');
    try{const payload=await fetchJson('/v1/playbook/designs?organization_id='+encodeURIComponent(organization),{headers:{Authorization:'Bearer '+token}});state.remoteDesigns=payload.data?.designs||[];renderPanel();setStatus('Loaded '+state.remoteDesigns.length+' server play'+(state.remoteDesigns.length===1?'':'s')+' for '+organization+'.','good');}catch(error){setStatus('Server load failed: '+error.message,'bad');}
  }
  function applyRemote(design){state.remoteApplying=true;try{api.setDesign(clone(design));saveLocalDraft(design);}finally{state.remoteApplying=false;}}
  async function openRemote(){
    const selected=document.getElementById('pd-sync-remote-design').value;const remote=state.remoteDesigns.find(design=>design.id===selected);if(!remote){setStatus('Select a server play before opening it.','warn');return;}
    const local=currentDesign();if(local.id===remote.id&&JSON.stringify(local)!==JSON.stringify(remote)&&!window.confirm('Opening the server play will replace the current local draft. Continue?'))return;
    state.conflict=null;applyRemote(remote);state.activeRevision=remote._revision??null;setStatus('Opened '+designLabel(remote)+' from the organization server.','good');renderPanel();
  }
  async function recoverLocal(){
    const drafts=await readDrafts();if(!drafts.length){setStatus('No recoverable local drafts were found.','warn');return;}
    const draft=drafts[0];if(!window.confirm('Recover the latest local draft '+designLabel(draft)+' into the editor?'))return;applyRemote(draft);setStatus('Recovered '+designLabel(draft)+' from local draft storage.','good');
  }
  async function upsertQueue(entry){
    await ensureQueue();const existing=findQueueEntry(entry.organization_id,entry.design_id);const merged={...(existing||{}),...entry,id:existing?.id||entry.id||id('SYNC'),status:entry.status||existing?.status||'queued'};state.queue=state.queue.filter(item=>item.id!==merged.id&&!(item.organization_id===merged.organization_id&&item.design_id===merged.design_id));state.queue.push(merged);await replaceQueue(state.queue);renderPanel();return merged;
  }
  async function removeQueue(entryId){await ensureQueue();await replaceQueue(state.queue.filter(entry=>entry.id!==entryId));renderPanel();}
  async function enqueueCurrent(reason='autosave',force=false){
    const {organization,token}=credentials();if(!organization||!token){if(force)setStatus('Enter organization and Bearer token in Film Room before saving to the server.','warn');return;}
    state.organization=organization;state.token=token;const design=currentDesign();const entry=await upsertQueue({organization_id:organization,design_id:design.id,design,expected_revision:design._revision??state.activeRevision??null,attempt:0,next_attempt_at:0,last_error:'',status:'queued',reason,created_at:now()});setStatus((reason==='manual'?'Save requested. ':'Autosave queued. ')+designLabel(entry.design),'warn');await flushQueue(false);
  }
  function scheduleRetry(){clearTimeout(state.retryTimer);const next=state.queue.filter(entry=>entry.status==='retry_wait'&&entry.next_attempt_at).sort((a,b)=>a.next_attempt_at-b.next_attempt_at)[0];if(next)state.retryTimer=setTimeout(()=>flushQueue(false),Math.max(250,next.next_attempt_at-now()));}
  async function handleConflict(entry,payload){
    const details=payload?.data||{};entry.status='conflict';entry.last_error='Server revision conflict';await upsertQueue(entry);state.conflict={entry,details};renderPanel();setStatus('Server revision conflict requires a deliberate resolution.','bad');
  }
  async function flushQueue(force=false){
    await ensureQueue();if(state.flushing)return;const {organization,token}=credentials();if(!organization||!token){setStatus('Queue is ready; enter organization and token to sync.','warn');return;}if(!online()){setStatus('Offline: changes are safely queued for retry when connection returns.','warn');renderPanel();return;}
    state.organization=organization;state.token=token;state.flushing=true;
    try{
      for(const entry of state.queue.slice().filter(item=>item.organization_id===organization)){
        if(entry.status==='conflict'&&!force)continue;if(!force&&entry.next_attempt_at&&entry.next_attempt_at>now())continue;
        entry.status='syncing';await replaceQueue(state.queue);renderPanel();
        try{
          const payload=await fetchJson('/v1/playbook/designs',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+token},body:JSON.stringify({organization_id:organization,design:entry.design,expected_revision:entry.expected_revision})});
          const saved=payload.data;await removeQueue(entry.id);state.remoteDesigns=[saved,...state.remoteDesigns.filter(item=>item.id!==saved.id)];if(currentDesign().id===saved.id&&!state.conflict){state.activeRevision=saved._revision??null;applyRemote(saved);}setStatus('Server synchronized '+designLabel(saved)+'.','good');
        }catch(error){
          if(error.status===409){await handleConflict(entry,error.payload);continue;}
          if(error.status===401||error.status===403){entry.status='auth_error';entry.last_error='Authorization rejected; refresh the Film Room token.';await replaceQueue(state.queue);setStatus(entry.last_error,'bad');continue;}
          if(error.status===422){entry.status='invalid';entry.last_error=error.message;await replaceQueue(state.queue);setStatus('Server rejected the play: '+error.message,'bad');continue;}
          entry.attempt=(entry.attempt||0)+1;entry.status='retry_wait';entry.last_error=error.message;entry.next_attempt_at=now()+Math.min(30000,1000*Math.pow(2,Math.min(5,entry.attempt)));await replaceQueue(state.queue);setStatus('Sync failed; retry scheduled in '+Math.round((entry.next_attempt_at-now())/1000)+' seconds.','warn');
        }
      }
    }finally{state.flushing=false;renderPanel();scheduleRetry();}
  }
  function useServer(){const conflict=state.conflict;const server=conflict?.details?.server_design;if(!conflict||!server){setStatus('No active conflict to resolve.','warn');return;}state.conflict=null;removeQueue(conflict.entry.id);applyRemote(server);state.activeRevision=server._revision??null;setStatus('Server version applied; local conflicting draft was discarded from the sync queue.','good');}
  async function retryLocal(){const conflict=state.conflict;const server=conflict?.details?.server_design;if(!conflict||!server){setStatus('No active conflict to resolve.','warn');return;}const entry=conflict.entry;entry.expected_revision=server._revision??null;entry.status='queued';entry.attempt=0;entry.next_attempt_at=0;entry.last_error='';state.conflict=null;await upsertQueue(entry);setStatus('Local draft queued against server revision '+(entry.expected_revision??'unknown')+'.','warn');await flushQueue(true);}
  async function saveAsBranch(){const conflict=state.conflict;const server=conflict?.details?.server_design;if(!conflict||!server){setStatus('No active conflict to resolve.','warn');return;}const branch=clone(conflict.entry.design);branch.id=branch.id+'-BRANCH-'+Date.now().toString(36);branch.parent_design_id=server.id;branch.version=String(server.version||branch.version||'0.1.0')+'.branch';branch.status='draft';delete branch._revision;delete branch.validation;state.conflict=null;await removeQueue(conflict.entry.id);applyRemote(branch);await upsertQueue({organization_id:conflict.entry.organization_id,design_id:branch.id,design:branch,expected_revision:null,attempt:0,next_attempt_at:0,last_error:'',status:'queued',reason:'conflict_branch',created_at:now()});setStatus('Local work was preserved as '+branch.id+' and queued as a new branch.','warn');await flushQueue(true);}
  function onDesignChanged(design){if(state.remoteApplying)return;saveLocalDraft(design);if(!state.autosave)return;clearTimeout(state.autosaveTimer);state.autosaveTimer=setTimeout(()=>enqueueCurrent('autosave'),1200);}

  buildPanel();
  const originalSet=api.setDesign;
  api.setDesign=design=>{originalSet(design);onDesignChanged(design);renderPanel();};
  window.NFLFIDOSPlayDesignerSync={refresh:renderPanel,flush:()=>flushQueue(true),load:loadOrganization,recover:recoverLocal};
  window.addEventListener('online',()=>{setStatus('Connection restored; flushing queued play changes.','good');flushQueue(false);});
  window.addEventListener('offline',()=>{setStatus('Offline: editor changes remain available and will queue for retry.','warn');renderPanel();});
  document.getElementById('film-org')?.addEventListener('change',()=>{state.organization=document.getElementById('film-org').value.trim();});
  document.getElementById('film-token')?.addEventListener('change',()=>{state.token=document.getElementById('film-token').value.trim();});
  ensureQueue().then(()=>{renderPanel();scheduleRetry();});
}());
