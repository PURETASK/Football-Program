(function(){
  const section=document.getElementById('usability-feedback');
  if(!section)return;
  const credentials=()=>({organization:document.getElementById('film-org')?.value.trim()||'',token:document.getElementById('film-token')?.value.trim()||''});
  const status=(message,tone='')=>{const node=document.getElementById('pd-pilot-metrics-status');if(node){node.textContent=message;node.className='pd-pilot-metrics-status '+tone;}};
  async function load(){
    try{const value=credentials();if(!value.organization||!value.token)throw new Error('Enter organization and Bearer token in Film Room first.');const response=await fetch('/v1/ux/usability-feedback/summary?organization_id='+encodeURIComponent(value.organization),{headers:{Authorization:'Bearer '+value.token}});const payload=await response.json();if(!response.ok)throw new Error(payload.error||'Pilot summary failed');const data=payload.data;const output=document.getElementById('pd-pilot-metrics-output');output.textContent=JSON.stringify(data,null,2);status('Moderated evidence summary loaded. Human pilot validation remains '+(data.pilot_validation_complete?'complete.':'open.'),data.pilot_validation_complete?'good':'warn');}catch(error){status('Pilot summary unavailable: '+error.message,'bad');}}
  const box=document.createElement('article');box.id='pd-pilot-metrics-card';box.className='pd-pilot-metrics-card';box.innerHTML='<h3>Moderated pilot metrics</h3><p class="label">Aggregates role coverage, completion, timing, satisfaction, accessibility findings, and severity for human review. This never declares a pilot complete automatically.</p><button type="button" id="pd-pilot-metrics-load">Load organization pilot summary</button><p id="pd-pilot-metrics-status" class="pd-pilot-metrics-status" role="status" aria-live="polite">No pilot summary loaded.</p><pre id="pd-pilot-metrics-output" class="pd-pilot-metrics-output">No evidence loaded.</pre>';
  box.querySelector('#pd-pilot-metrics-load').onclick=load;section.querySelector('.card')?.appendChild(box);
  window.NFLFIDOSPilotVerification={load};
}());
