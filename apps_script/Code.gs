const SH = Object.freeze({
  SHEETS: { QUEUE:'Queue', RUNLOG:'RunLog', CONFIG:'Config', SOURCES:'Sources' },
  QUEUE_HEADERS:['timestamp','provider','source_url','province','grade','subject','year','language','assessment_type','paper_type','paper_file_type','memo_file_type','paper_url','memo_url','status','source_folder_url','notes'],
  LOG_HEADERS:['timestamp','action','entity','input','output','status','notes'],
  SOURCE_HEADERS:['enabled','provider','province','page_url','notes'],
  SUBJECTS:{
    '8':['Mathematics','Natural Sciences','Social Sciences','Economic and Management Sciences (EMS)','Technology','Creative Arts','English HL','English FAL','Afrikaans HL','Afrikaans FAL'],
    '9':['Mathematics','Natural Sciences','Social Sciences','Economic and Management Sciences (EMS)','Technology','Creative Arts','English HL','English FAL','Afrikaans HL','Afrikaans FAL'],
    '10':['Mathematics','Mathematical Literacy','Physical Sciences','Life Sciences','Accounting','Economics','Business Studies','Geography','History','English HL','English FAL','Afrikaans HL','Afrikaans FAL'],
    '11':['Mathematics','Mathematical Literacy','Physical Sciences','Life Sciences','Accounting','Economics','Business Studies','Geography','History','English HL','English FAL','Afrikaans HL','Afrikaans FAL'],
    '12':['Mathematics','Mathematical Literacy','Physical Sciences','Life Sciences','Accounting','Economics','Business Studies','Geography','History','English HL','English FAL','Afrikaans HL','Afrikaans FAL']
  }
});

function doGet(e){
  const api=String((e&&e.parameter&&e.parameter.api)||'health');
  try{
    if(api==='health') return json_({ok:true,data:health_()});
    if(api==='catalogPublic') return json_({ok:true,data:catalogPublic_()});
    if(api==='runDiscovery') return json_({ok:true,data:runDiscoveryNow()});
    if(api==='runDownloads') return json_({ok:true,data:runDownloadBatch()});
    return json_({ok:false,error:'Unknown API'},404);
  }catch(err){ log_('API_ERROR',api,'',String(err),'ERROR',''); return json_({ok:false,error:String(err)}); }
}
function json_(obj){return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);}
function props_(){return PropertiesService.getScriptProperties();}
function ss_(){const id=props_().getProperty('SHEET_ID'); if(!id) throw new Error('Missing SHEET_ID Script Property'); return SpreadsheetApp.openById(id);}
function sheet_(name,headers){let s=ss_().getSheetByName(name); if(!s)s=ss_().insertSheet(name); if(headers&&s.getLastRow()===0)s.appendRow(headers); return s;}
function rows_(s){if(s.getLastRow()<2)return[];const v=s.getDataRange().getValues(),h=v.shift().map(String);return v.map((r,i)=>{const o={_row:i+2};h.forEach((k,j)=>o[k]=r[j]);return o;});}
function log_(action,entity,input,output,status,notes){try{sheet_(SH.SHEETS.RUNLOG,SH.LOG_HEADERS).appendRow([new Date(),action,entity,asText_(input),asText_(output),status||'OK',notes||'']);}catch(_){}}
function asText_(v){if(v===undefined||v===null)return'';return typeof v==='string'?v:JSON.stringify(v);}
function lockRun_(name,fn){const l=LockService.getScriptLock();if(!l.tryLock(5000))throw new Error(name+' already running');try{return fn();}finally{l.releaseLock();}}
function health_(){return{time:new Date().toISOString(),sheet:true,sourceLibrary:!!props_().getProperty('SOURCE_LIBRARY_ID'),discoveryMode:props_().getProperty('DISCOVERY_MODE')||'SAMPLE'};}
function catalogPublic_(){const s=ss_().getSheetByName('Catalog');if(!s)return[];return rows_(s).filter(x=>String(x.published).toUpperCase()==='TRUE'&&String(x.zip_status).toUpperCase()==='READY'&&x.zip_url);}
