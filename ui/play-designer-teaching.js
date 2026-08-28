(function(){
  const section=document.getElementById('play-designer-section');
  const host=document.getElementById('play-designer');
  const api=window.NFLFIDOSPlayDesigner;
  if(!section||!host||!api)return;

  const state={view:null,role:'',mode:'player',step:-1};
  const PLAYER_QUIZ_FIELD='answer_required';
  const clone=value=>JSON.parse(JSON.stringify(value));
  const design=()=>clone(api.getDesign());
  const credentials=()=>({organization:document.getElementById('film-org')?.value.trim()||'',token:document.getElementById('film-token')?.value.trim()||''});
  const card=()=>document.getElementById('pd-teaching-card');
  const status=(message,tone='')=>{const node=document.getElementById('pd-teaching-status');if(node){node.textContent=message;node.className='pd-teaching-status '+tone;}};
  const json=value=>{try{return JSON.stringify(value,null,2);}catch(error){return String(value??'');}};

  async function fetchJson(url,options){
    const response=await fetch(url,options);let payload=null;
    try{payload=await response.json();}catch(error){payload={error:'Server returned a non-JSON response.'};}
    if(!response.ok){const failure=new Error(payload?.error||('Request failed ('+response.status+')'));failure.status=response.status;failure.payload=payload;throw failure;}
    return payload;
  }

  function roles(){
    const players=design().players||[];const values=[];players.forEach(player=>{if(player.position&&!values.includes(player.position))values.push(player.position);});return values.length?values:['QB'];
  }

  function buildCard(){
    let box=card();if(box)return box;
    box=document.createElement('article');box.id='pd-teaching-card';box.className='pd-teaching-card';section.appendChild(box);
    box.innerHTML='<h4>Teaching & player views</h4><p class="pd-teaching-help">Load an organization-scoped view to reveal only the assigned path, animate the selected player or position group, present readable step instructions, grade quizzes server-side, and link the rep to practice.</p><div class="pd-teaching-toolbar"><label>Role<select id="pd-teaching-role"></select></label><label>View mode<select id="pd-teaching-mode"><option value="player">Player-only</option><option value="position_group">Position group</option><option value="coach">Full coach</option></select></label><label>Reveal step<input id="pd-teaching-step" type="range" min="-1" max="0" step="1" value="-1" aria-label="Teaching reveal step"><span id="pd-teaching-step-label">All steps</span></label><button type="button" id="pd-teaching-load">Load teaching view</button><button type="button" id="pd-teaching-full">Show full diagram</button></div><p id="pd-teaching-status" class="pd-teaching-status" role="status" aria-live="polite">Enter organization and token, then load a teaching view.</p><div class="pd-teaching-grid"><div class="pd-teaching-panel"><h5>Step-by-step read reveal</h5><div id="pd-teaching-steps" class="pd-teaching-steps"></div></div><div class="pd-teaching-panel"><h5>Accessible text view</h5><pre id="pd-teaching-accessible" class="pd-teaching-accessible">No teaching view loaded.</pre></div><div class="pd-teaching-panel"><h5>Quiz and mastery</h5><div id="pd-teaching-quizzes" class="pd-teaching-quizzes"></div><label>Practice linkage<input id="pd-teaching-practice" placeholder="DRILL- or PRACTICE- reference" autocomplete="off"></label><button type="button" id="pd-teaching-master-current">Mark current step mastered</button><div id="pd-teaching-mastery" class="pd-teaching-mastery"></div></div><div class="pd-teaching-panel"><h5>Practice linkage</h5><pre id="pd-teaching-practice-output" class="pd-teaching-accessible">No practice linkage loaded.</pre><h5>Read reveal keys</h5><div id="pd-teaching-reads" class="pd-teaching-reads"></div></div></div>';
    const roleSelect=box.querySelector('#pd-teaching-role');roleSelect.replaceChildren();roles().forEach(role=>{const option=document.createElement('option');option.value=role;option.textContent=role+' position group';roleSelect.appendChild(option);});state.role=roleSelect.value||'QB';
    roleSelect.onchange=()=>{state.role=roleSelect.value;};
    box.querySelector('#pd-teaching-mode').onchange=event=>{state.mode=event.target.value;};
    box.querySelector('#pd-teaching-load').onclick=loadView;
    box.querySelector('#pd-teaching-full').onclick=()=>{state.mode='coach';box.querySelector('#pd-teaching-mode').value='coach';state.step=-1;loadView();};
    box.querySelector('#pd-teaching-step').oninput=event=>{state.step=Number(event.target.value);renderView();};
    box.querySelector('#pd-teaching-master-current').onclick=recordCurrentStep;
    return box;
  }

  function applyCanvasFilter(){
    const view=state.view;const visibleIds=new Set(view?.visible_element_ids||[]);const playerIds=new Set((view?.filtered_diagram?.players||[]).map(player=>player.id));
    host.querySelectorAll('.pd-path').forEach(path=>{path.style.display=!view||view.mode==='coach'||visibleIds.has(path.dataset.id)?'':'none';});
    host.querySelectorAll('.pd-player').forEach(player=>{player.style.display=!view||view.mode==='coach'||playerIds.has(player.dataset.id)?'':'none';});
    if(window.NFLFIDOSPlayDesignerTimeline?.setVisibilityFilter)window.NFLFIDOSPlayDesignerTimeline.setVisibilityFilter(!view||view.mode==='coach'?null:[...visibleIds]);
  }

  function renderSteps(){
    const list=document.getElementById('pd-teaching-steps');if(!list)return;list.replaceChildren();
    if(!state.view){const empty=document.createElement('p');empty.className='pd-teaching-help';empty.textContent='Load a teaching view to reveal the progression.';list.appendChild(empty);return;}
    const activeStep=state.step;
    state.view.steps.forEach(step=>{const row=document.createElement('article');row.className='pd-teaching-step '+(step.revealed&&activeStep>=0&&step.step_index===activeStep?'current':'')+(step.revealed?' revealed':' hidden');const title=document.createElement('strong');title.textContent='Step '+(step.step_index+1)+' · '+step.label;const body=document.createElement('span');body.textContent=step.revealed?step.instruction:'Locked until the prior read is revealed.';const timing=document.createElement('small');timing.textContent=step.start_ms+'–'+step.end_ms+' ms';row.append(title,body,timing);list.appendChild(row);});
  }

  async function submitQuiz(quiz,answer,resultNode){
    try{const credentialsValue=credentials();const current=design();if(!credentialsValue.organization||!credentialsValue.token)throw new Error('Enter organization and Bearer token first.');const response=await fetchJson('/v1/playbook/designs/quiz',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+credentialsValue.token},body:JSON.stringify({organization_id:credentialsValue.organization,design_id:current.id,role:state.role,quiz_id:quiz.id,answer,practice_ref:document.getElementById('pd-teaching-practice').value.trim()||undefined})});resultNode.textContent=response.data?.correct?'Correct. Mastery attempt recorded.':'Not yet. Review the step and try again.';resultNode.className='pd-teaching-quiz-result '+(response.data?.correct?'good':'warn');await loadMastery();}catch(error){resultNode.textContent='Quiz submission failed: '+error.message;resultNode.className='pd-teaching-quiz-result bad';}
  }

  function renderQuizzes(){
    const box=document.getElementById('pd-teaching-quizzes');if(!box)return;box.replaceChildren();
    if(!state.view?.quizzes?.length){const empty=document.createElement('p');empty.className='pd-teaching-help';empty.textContent='No quiz items are attached to this play version.';box.appendChild(empty);return;}
    state.view.quizzes.forEach(quiz=>{const article=document.createElement('article');article.className='pd-teaching-quiz';const question=document.createElement('strong');question.textContent=quiz.question;article.appendChild(question);const result=document.createElement('span');result.className='pd-teaching-quiz-result';quiz.options.forEach(optionValue=>{const button=document.createElement('button');button.type='button';button.className='pd-teaching-option';button.textContent=optionValue;button.onclick=()=>submitQuiz(quiz,optionValue,result);article.appendChild(button);});article.appendChild(result);box.appendChild(article);});
  }

  function renderView(){
    const label=document.getElementById('pd-teaching-step-label');const slider=document.getElementById('pd-teaching-step');
    if(!state.view){if(label)label.textContent='All steps';if(slider)slider.max='0';renderSteps();applyCanvasFilter();return;}
    const max=Math.max(0,state.view.steps.length-1);if(slider){slider.max=String(max);slider.value=String(state.step<0?max:Math.min(state.step,max));}if(label)label.textContent=state.step<0?'All steps':'Step '+(state.step+1)+' of '+state.view.steps.length;
    const steps=state.view.steps.map(step=>({...step,revealed:state.step<0||step.step_index<=state.step}));state.view={...state.view,steps};
    const accessible=document.getElementById('pd-teaching-accessible');if(accessible)accessible.textContent=state.view.accessible_text+(state.step<0?'':'\n\nReveal focus: Step '+(state.step+1)+' of '+state.view.steps.length+'.');
    const practice=document.getElementById('pd-teaching-practice-output');if(practice)practice.textContent=json(state.view.practice_linkage||{});
    const reads=document.getElementById('pd-teaching-reads');if(reads){reads.replaceChildren();(state.view.read_reveal||[]).forEach(read=>{const node=document.createElement('div');node.className='pd-teaching-read';node.textContent=(read.key||'Read key')+' · '+read.prompt;reads.appendChild(node);});if(!state.view.read_reveal?.length){const empty=document.createElement('span');empty.className='pd-teaching-help';empty.textContent='No explicit read keys on the current view.';reads.appendChild(empty);}}
    renderSteps();renderQuizzes();renderMastery();applyCanvasFilter();
  }

  async function loadMastery(){
    if(!state.view)return;try{const credentialsValue=credentials();const current=design();const payload=await fetchJson('/v1/playbook/designs/'+encodeURIComponent(current.id)+'/mastery?organization_id='+encodeURIComponent(credentialsValue.organization)+'&role='+encodeURIComponent(state.role),{headers:{Authorization:'Bearer '+credentialsValue.token}});state.view={...state.view,mastery:payload.data};renderMastery();}catch(error){status('Mastery refresh failed: '+error.message,'warn');}}

  function renderMastery(){const box=document.getElementById('pd-teaching-mastery');if(!box)return;box.textContent=state.view?.mastery?json(state.view.mastery.summary):'No mastery attempts loaded.';}

  async function recordCurrentStep(){
    try{if(!state.view?.steps?.length)throw new Error('Load a teaching view first.');const credentialsValue=credentials();const current=design();const index=state.step<0?0:Math.min(state.step,state.view.steps.length-1);await fetchJson('/v1/playbook/designs/mastery',{method:'POST',headers:{'Content-Type':'application/json',Authorization:'Bearer '+credentialsValue.token},body:JSON.stringify({organization_id:credentialsValue.organization,design_id:current.id,role:state.role,step_id:state.view.steps[index].id,score:1,result:'mastered',practice_ref:document.getElementById('pd-teaching-practice').value.trim()||undefined})});status('Mastery recorded for '+state.view.steps[index].label+'.','good');await loadMastery();}catch(error){status('Mastery recording failed: '+error.message,'bad');}
  }

  async function loadView(){
    try{const credentialsValue=credentials();const current=design();if(!credentialsValue.organization||!credentialsValue.token)throw new Error('Enter organization and Bearer token in Film Room first.');if(!state.role)state.role=roles()[0];let url='/v1/playbook/designs/'+encodeURIComponent(current.id)+'/teaching-view?organization_id='+encodeURIComponent(credentialsValue.organization)+'&role='+encodeURIComponent(state.role)+'&mode='+encodeURIComponent(state.mode);if(state.step>=0)url+='&step='+encodeURIComponent(state.step);const payload=await fetchJson(url,{headers:{Authorization:'Bearer '+credentialsValue.token}});state.view=payload.data;status('Loaded '+state.mode+' teaching view for '+state.role+'.','good');renderView();}catch(error){status('Teaching view failed: '+error.message,'bad');}
  }

  buildCard();renderView();
  window.NFLFIDOSPlayDesignerTeaching={load:loadView,refresh:renderView,clear:()=>{state.view=null;state.step=-1;renderView();}};
  api.setDesign&&(()=>{const originalSet=api.setDesign;api.setDesign=next=>{originalSet(next);const roleSelect=document.getElementById('pd-teaching-role');if(roleSelect){const currentRole=state.role;roleSelect.replaceChildren();roles().forEach(role=>{const option=document.createElement('option');option.value=role;option.textContent=role+' position group';roleSelect.appendChild(option);});roleSelect.value=roles().includes(currentRole)?currentRole:roleSelect.value;state.role=roleSelect.value;}state.view=null;state.step=-1;renderView();};})();
}());
