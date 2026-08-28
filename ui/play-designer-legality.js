(function(){
  const section=document.getElementById('play-designer-section');
  const api=window.NFLFIDOSPlayDesigner;
  if(!section||!api)return;

  const state={profiles:[],report:null,selectedIssue:''};
  const fallbackProfiles=[
    {id:'nfl',label:'NFL tackle football'},
    {id:'ncaa',label:'NCAA college football'},
    {id:'high_school',label:'NFHS high-school tackle football'},
    {id:'youth',label:'Youth tackle football (local rules required)'},
    {id:'flag',label:'NFL FLAG 5-on-5 baseline'}
  ];
  const clone=value=>JSON.parse(JSON.stringify(value));
  const design=()=>clone(api.getDesign());
  const credentials=()=>({organization:document.getElementById('film-org')?.value.trim()||'',token:document.getElementById('film-token')?.value.trim()||''});
  const card=()=>document.getElementById('pd-legality-card');
  const status=(message,tone='')=>{const node=document.getElementById('pd-legality-status');if(node){node.textContent=message;node.className='pd-legality-status '+tone;}};
  const json=value=>{try{return JSON.stringify(value,null,2);}catch(error){return String(value??'');}};

  async function fetchJson(url,options){
    const response=await fetch(url,options);let payload=null;
    try{payload=await response.json();}catch(error){payload={error:'Server returned a non-JSON response.'};}
    if(!response.ok){const failure=new Error(payload?.error||('Request failed ('+response.status+')'));failure.status=response.status;failure.payload=payload;throw failure;}
    return payload;
  }

  function activeProfiles(){return state.profiles.length?state.profiles:fallbackProfiles;}

  function syncControls(){
    const current=design();
    const profile=document.getElementById('pd-legality-profile');
    const count=document.getElementById('pd-legality-field-count');
    const routePolicy=document.getElementById('pd-legality-route-policy');
    const zones=document.getElementById('pd-legality-coverage-zones');
    if(profile){profile.value=current.rule_profile||'nfl';if(!profile.value)profile.value='nfl';}
    if(count)count.value=current.players_on_field??'';
    if(routePolicy)routePolicy.value=current.route_collision_policy||'warn';
    if(zones)zones.value=Array.isArray(current.coverage_zones)?current.coverage_zones.join(', '):'';
  }

  function renderProfileOptions(){
    const select=document.getElementById('pd-legality-profile');if(!select)return;
    const selected=design().rule_profile||'nfl';select.replaceChildren();
    activeProfiles().forEach(profile=>{const option=document.createElement('option');option.value=profile.id;option.textContent=profile.label||profile.id;option.selected=profile.id===selected;select.appendChild(option);});
  }

  function buildCard(){
    let box=card();if(box)return box;
    box=document.createElement('article');box.id='pd-legality-card';box.className='pd-legality-card';section.appendChild(box);
    box.innerHTML='<h4>Advanced legality & release linting</h4><p class="pd-legality-help">Choose the governing rule profile, run explainable formation and assignment checks, and preserve every coach exception with evidence and program-owner approval. A finding is never silently bypassed.</p><div class="pd-legality-grid"><label>Rule profile<select id="pd-legality-profile"></select></label><label>Players on field (optional)<input id="pd-legality-field-count" type="number" min="1" max="22" placeholder="Profile default"></label><label>Route collision policy<select id="pd-legality-route-policy"><option value="warn">Warn and confirm</option><option value="error">Block until approved</option></select></label><label>Coverage zones (optional)<input id="pd-legality-coverage-zones" placeholder="deep_left, deep_middle, flat"></label><button type="button" id="pd-legality-apply-profile">Apply profile to draft</button><button type="button" id="pd-legality-load">Run server legality report</button></div><p id="pd-legality-status" class="pd-legality-status" role="status" aria-live="polite">Select a profile and run the organization-scoped report.</p><div id="pd-legality-summary" class="pd-legality-summary"></div><div id="pd-legality-findings" class="pd-legality-findings"></div><div class="pd-legality-override"><h5>Request coach override</h5><p class="pd-legality-help">Overrides are finding-specific, expire, retain evidence, and require a separate program-owner approval before they affect validation.</p><div class="pd-legality-grid"><label>Overrideable finding<select id="pd-legality-issue"><option value="">Run a report first</option></select></label><label>Decision reference<input id="pd-legality-decision-ref" placeholder="DEC-LEGALITY-..." autocomplete="off"></label><label>Evidence references<input id="pd-legality-evidence" placeholder="film://clip, install://note" autocomplete="off"></label><label>Expires at<input id="pd-legality-expires" type="datetime-local"></label><label class="pd-legality-wide">Rationale<textarea id="pd-legality-rationale" rows="3" placeholder="Explain why the exception is intentional and what evidence supports it."></textarea></label><button type="button" id="pd-legality-request">Request owner approval</button></div></div><div class="pd-legality-approval"><h5>Approve pending override (<span data-required-role="program_owner">program owner only</span>)</h5><div class="pd-legality-grid"><label>Pending override<select id="pd-legality-override"><option value="">No pending override</option></select></label><label>Approval decision reference<input id="pd-legality-approval-ref" placeholder="DEC-OWNER-..." autocomplete="off"></label><button type="button" id="pd-legality-approve">Approve override</button></div></div><details class="pd-legality-details"><summary>Raw report and source basis</summary><pre id="pd-legality-raw">No report loaded.</pre></details>';
    box.querySelector('#pd-legality-apply-profile').onclick=applyProfile;
    box.querySelector('#pd-legality-load').onclick=loadReport;
    box.querySelector('#pd-legality-request').onclick=requestOverride;
    box.querySelector('#pd-legality-approve').onclick=approveOverride;
    renderProfileOptions();syncControls();renderReport();
    return box;
  }

  function applyProfile(){
    const next=design();next.rule_profile=document.getElementById('pd-legality-profile').value||'nfl';
    const rawCount=document.getElementById('pd-legality-field-count').value.trim();
    if(rawCount)next.players_on_field=Number(rawCount);else delete next.players_on_field;
    next.route_collision_policy=document.getElementById('pd-legality-route-policy').value||'warn';
    const zones=document.getElementById('pd-legality-coverage-zones').value.split(',').map(value=>value.trim()).filter(Boolean);
    if(zones.length)next.coverage_zones=zones;else delete next.coverage_zones;
    api.setDesign(next);state.report=null;renderReport();status('Rule profile applied to the local draft. Save or sync the draft to run the server report.','warn');
  }

  async function loadProfiles(){
    const credentialsValue=credentials();if(!credentialsValue.organization||!credentialsValue.token)return;
    try{const payload=await fetchJson('/v1/playbook/designs/rule-profiles?organization_id='+encodeURIComponent(credentialsValue.organization),{headers:{Authorization:'Bearer '+credentialsValue.token}});state.profiles=payload.data?.profiles||[];renderProfileOptions();syncControls();}catch(error){/* fallback catalog remains available until credentials are corrected */}
  }

  function renderFinding(finding){
    const article=document.createElement('article');article.className='pd-legality-finding '+(finding.severity||'warning');
    const heading=document.createElement('div');heading.className='pd-legality-finding-heading';const code=document.createElement('strong');code.textContent=finding.code||'FINDING';const severity=document.createElement('span');severity.textContent=(finding.severity||'warning').toUpperCase()+(finding.status==='overridden'?' · OVERRIDDEN':'')+(finding.override_expired?' · OVERRIDE EXPIRED':'');heading.append(code,severity);
    const message=document.createElement('p');message.textContent=finding.message||'No message provided.';
    const detail=document.createElement('p');detail.className='pd-legality-detail';detail.textContent='Path: '+(finding.path||'n/a')+' · '+(finding.explanation||'');
    article.append(heading,message,detail);
    if(finding.source?.uri){const source=document.createElement('a');source.href=finding.source.uri;source.target='_blank';source.rel='noreferrer';source.textContent='Source: '+(finding.source.title||finding.source.uri);article.appendChild(source);}
    return article;
  }

  function renderReport(){
    const summary=document.getElementById('pd-legality-summary');const findings=document.getElementById('pd-legality-findings');const issueSelect=document.getElementById('pd-legality-issue');const overrideSelect=document.getElementById('pd-legality-override');const raw=document.getElementById('pd-legality-raw');
    if(!summary||!findings||!issueSelect||!overrideSelect||!raw)return;
    summary.replaceChildren();findings.replaceChildren();issueSelect.replaceChildren();overrideSelect.replaceChildren();raw.textContent=state.report?json(state.report):'No report loaded.';
    if(!state.report){summary.textContent='No server report loaded.';const empty=document.createElement('p');empty.className='pd-legality-help';empty.textContent='The server evaluates the canonical organization-scoped design, not an unsaved browser-only copy.';findings.appendChild(empty);const issue=document.createElement('option');issue.value='';issue.textContent='Run a report first';issueSelect.appendChild(issue);const pending=document.createElement('option');pending.value='';pending.textContent='No pending override';overrideSelect.appendChild(pending);return;}
    const total=state.report.issues?.length||0;const errors=(state.report.issues||[]).filter(item=>item.severity==='error').length;const profile=state.report.profile?.label||state.report.rule_profile;summary.textContent='Status: '+state.report.status.toUpperCase()+' · '+errors+' blocking finding'+(errors===1?'':'s')+' · '+total+' total · '+profile;
    (state.report.issues||[]).forEach(finding=>findings.appendChild(renderFinding(finding)));
    const overrideable=(state.report.issues||[]).filter(item=>item.overrideable===true);if(!overrideable.length){const empty=document.createElement('option');empty.value='';empty.textContent='No overrideable finding';issueSelect.appendChild(empty);}else{overrideable.forEach(finding=>{const option=document.createElement('option');option.value=finding.code;option.textContent=finding.code+' · '+finding.severity;issueSelect.appendChild(option);});issueSelect.value=state.selectedIssue&&overrideable.some(item=>item.code===state.selectedIssue)?state.selectedIssue:overrideable[0].code;state.selectedIssue=issueSelect.value;}
    const pendingOverrides=(state.report.overrides||[]).filter(item=>item.status==='pending_owner_approval');if(!pendingOverrides.length){const empty=document.createElement('option');empty.value='';empty.textContent='No pending override';overrideSelect.appendChild(empty);}else{pendingOverrides.forEach(item=>{const option=document.createElement('option');option.value=item.id;option.textContent=item.id+' · '+item.issue_code;overrideSelect.appendChild(option);});}
  }

  async function loadReport(){
    try{const credentialsValue=credentials();const current=design();if(!credentialsValue.organization||!credentialsValue.token)throw new Error('Enter organization and Bearer token in Film Room first.');await loadProfiles();const payload=await fetchJson('/v1/playbook/designs/'+encodeURIComponent(current.id)+'/legality?organization_id='+encodeURIComponent(credentialsValue.organization),{headers:{Authorization:'Bearer '+credentialsValue.token}});state.report=payload.data;renderReport();status('Legality report loaded for '+current.id+'. '+(state.report.status==='valid'?'No blocking findings.':'Resolve blocking findings or obtain documented owner approval.'),state.report.status==='valid'?'good':'warn');}catch(error){status('Legality report failed: '+error.message,'bad');}
  }

  async function requestOverride(){
    try{const credentialsValue=credentials();const current=design();const issueCode=document.getElementById('pd-legality-issue').value;const expiryValue=document.getElementById('pd-legality-expires').value;if(!credentialsValue.organization||!credentialsValue.token)throw new Error('Enter organization and Bearer token first.');if(!issueCode)throw new Error('Select an overrideable finding first.');if(!expiryValue)throw new Error('Choose an expiration time.');const evidence=document.getElementById('pd-legality-evidence').value.split(',').map(value=>value.trim()).filter(Boolean);const payload=await fetchJson('/v1/playbook/designs/legality/override',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+credentialsValue.token},body:JSON.stringify({organization_id:credentialsValue.organization,design_id:current.id,issue_code:issueCode,rationale:document.getElementById('pd-legality-rationale').value.trim(),decision_ref:document.getElementById('pd-legality-decision-ref').value.trim(),evidence_refs:evidence,expires_at:new Date(expiryValue).toISOString()})});status('Override request '+payload.data.id+' is pending program-owner approval.','warn');await loadReport();}catch(error){status('Override request failed: '+error.message,'bad');}
  }

  async function approveOverride(){
    try{const credentialsValue=credentials();const current=design();const overrideId=document.getElementById('pd-legality-override').value;if(!credentialsValue.organization||!credentialsValue.token)throw new Error('Enter organization and Bearer token first.');if(!overrideId)throw new Error('Select a pending override first.');const payload=await fetchJson('/v1/playbook/designs/legality/override/approve',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+credentialsValue.token},body:JSON.stringify({organization_id:credentialsValue.organization,design_id:current.id,override_id:overrideId,decision_ref:document.getElementById('pd-legality-approval-ref').value.trim()})});status('Override '+payload.data.id+' approved by the program owner; resave the draft to persist downgraded validation.','good');await loadReport();}catch(error){status('Override approval failed: '+error.message,'bad');}
  }

  buildCard();
  const originalSet=api.setDesign;
  api.setDesign=next=>{originalSet(next);state.report=null;renderProfileOptions();syncControls();renderReport();};
  document.getElementById('film-org')?.addEventListener('change',loadProfiles);
  window.NFLFIDOSPlayDesignerLegality={load:loadReport,refresh:renderReport,applyProfile};
  loadProfiles();
}());
