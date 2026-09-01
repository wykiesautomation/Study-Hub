function runDiscoveryNow(){return lockRun_('discovery',()=>{
  const mode=(props_().getProperty('DISCOVERY_MODE')||'SAMPLE').toUpperCase();
  if(mode!=='LIVE'){log_('DISCOVERY_TICK','scanner',mode,'No synthetic rows created','OK','Use LIVE for approved sources');return {mode,inserted:0,message:'SAMPLE mode does not create fake products.'};}
  const sources=rows_(sheet_(SH.SHEETS.SOURCES,SH.SOURCE_HEADERS)).filter(x=>String(x.enabled).toUpperCase()==='TRUE'&&x.page_url);
  const limit=Math.max(1,Math.min(100,Number(props_().getProperty('DISCOVERY_BATCH_SIZE')||20)));
  let inserted=0,rejected=0,duplicates=0,pairs=0;
  for(const src of sources.slice(0,limit)){
    try{
      const html=fetchText_(src.page_url);
      const links=extractFileLinks_(html,src.page_url);
      const found=pairLinks_(links,src);
      pairs+=found.length;
      found.forEach(c=>{const v=validateCandidate_(c);if(!v.ok){rejected++;log_('DISCOVERY_REJECT',c.source_url,c,'', 'REJECTED',v.reason);return;}if(isDuplicate_(c)){duplicates++;return;}appendCandidate_(c);inserted++;});
    }catch(err){rejected++;log_('DISCOVERY_SOURCE_ERROR',src.page_url,src,'','ERROR',String(err));}
  }
  props_().setProperty('DISCOVERY_LAST_RUN',new Date().toISOString());
  log_('DISCOVERY_FINISH','scanner',{sources:sources.length},{pairs,inserted,rejected,duplicates},'OK','');
  return {sources:sources.length,pairs,inserted,rejected,duplicates};
});}
function fetchText_(url){const r=UrlFetchApp.fetch(String(url),{muteHttpExceptions:true,followRedirects:true,headers:{'User-Agent':'StudyHub/1.0'}});if(r.getResponseCode()<200||r.getResponseCode()>299)throw new Error('HTTP '+r.getResponseCode());return r.getContentText();}
function extractFileLinks_(html,base){const out=[],seen={};const re=/href\s*=\s*["']([^"'#]+)["']/gi;let m;while((m=re.exec(html))){try{const u=absoluteUrl_(m[1],base);if(!/\.(pdf|zip)(\?|$)/i.test(u)||seen[u])continue;seen[u]=1;out.push({url:u,name:decodeURIComponent(u.split('/').pop().split('?')[0])});}catch(_){}}return out;}
function absoluteUrl_(href,base){if(/^https?:\/\//i.test(href))return href;if(href.startsWith('//'))return 'https:'+href;const b=String(base).match(/^(https?:\/\/[^/]+)(\/.*)?$/);if(!b)throw new Error('Bad base URL');if(href.startsWith('/'))return b[1]+href;const dir=String(base).replace(/[?#].*$/,'').replace(/\/[^/]*$/,'/');return dir+href;}
function keyName_(name){return String(name).toLowerCase().replace(/memorandum|memo|marking[ _-]?guidelines?/g,'').replace(/question[ _-]?paper|paper|qp/g,'').replace(/[^a-z0-9]+/g,' ').trim();}
function isMemoName_(n){return /memo|memorandum|marking[ _-]?guideline/i.test(n);}
function pairLinks_(links,src){const papers=links.filter(x=>!isMemoName_(x.name)),memos=links.filter(x=>isMemoName_(x.name)),out=[];papers.forEach(p=>{let best=null,score=-1;const pk=keyName_(p.name);memos.forEach(m=>{const mk=keyName_(m.name);let s=0;if(pk===mk)s=100;else{pk.split(' ').forEach(t=>{if(t.length>2&&mk.includes(t))s++;});}if(s>score){score=s;best=m;}});if(best&&score>0)out.push(candidateFromNames_(p,best,src));});return out;}
function candidateFromNames_(p,m,src){const text=(p.name+' '+m.name).replace(/%20/g,' ');const year=(text.match(/20(2[2-9]|[3-9]\d)/)||[])[0]||'';const grade=(text.match(/(?:grade|gr)[ _-]?(8|9|10|11|12)\b/i)||[])[1]||'';let subject='';Object.keys(SH.SUBJECTS).forEach(g=>SH.SUBJECTS[g].forEach(s=>{if(!subject&&text.toLowerCase().includes(s.toLowerCase()))subject=s;}));return{provider:src.provider||'ApprovedSource',source_url:src.page_url,province:src.province||'National',grade,subject,year,language:/afrikaans|\bafr\b/i.test(text)?'Afrikaans':'English',assessment_type:/trial|prelim/i.test(text)?'Trial Exam':(/test/i.test(text)?'Test':'Exam'),paper_type:(text.match(/\bP([123])\b/i)||[])[0]||'Other',paper_file_type:fileType_(p.url),memo_file_type:fileType_(m.url),paper_url:p.url,memo_url:m.url,status:'DISCOVERED',source_folder_url:'',notes:'Auto-paired from approved source page'};}
function fileType_(u){return /\.zip(\?|$)/i.test(u)?'ZIP':'PDF';}
function validateCandidate_(c){if(!c.paper_url||!c.memo_url)return{ok:false,reason:'Paper and memo are mandatory'};if(!['8','9','10','11','12'].includes(String(c.grade)))return{ok:false,reason:'Grade missing or unsupported'};if(Number(c.year)<2022)return{ok:false,reason:'Year missing or before 2022'};if(!SH.SUBJECTS[String(c.grade)].includes(c.subject))return{ok:false,reason:'Subject missing or unsupported'};if(!['English','Afrikaans'].includes(c.language))return{ok:false,reason:'Unsupported language'};return{ok:true};}
function isDuplicate_(c){return rows_(sheet_(SH.SHEETS.QUEUE,SH.QUEUE_HEADERS)).some(x=>String(x.paper_url)===String(c.paper_url)&&String(x.memo_url)===String(c.memo_url));}
function appendCandidate_(c){sheet_(SH.SHEETS.QUEUE,SH.QUEUE_HEADERS).appendRow(SH.QUEUE_HEADERS.map(h=>h==='timestamp'?new Date():(c[h]||'')));}
