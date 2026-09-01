function setupStudyHub(){
  return lockRun_('setup',()=>{
    sheet_(SH.SHEETS.QUEUE,SH.QUEUE_HEADERS);
    sheet_(SH.SHEETS.RUNLOG,SH.LOG_HEADERS);
    sheet_(SH.SHEETS.SOURCES,SH.SOURCE_HEADERS);
    const p=props_();
    if(!p.getProperty('DISCOVERY_MODE'))p.setProperty('DISCOVERY_MODE','SAMPLE');
    if(!p.getProperty('DISCOVERY_BATCH_SIZE'))p.setProperty('DISCOVERY_BATCH_SIZE','20');
    if(!p.getProperty('DL_BATCH_SIZE'))p.setProperty('DL_BATCH_SIZE','10');
    log_('SETUP','StudyHub','','Sheets ready','OK','');
    return {ok:true,message:'StudyHub sheets ready. Add approved source pages to Sources.'};
  });
}
function installPipelineTriggers(){
  ScriptApp.getProjectTriggers().forEach(t=>{if(['scheduledDiscovery','scheduledDownloads'].includes(t.getHandlerFunction()))ScriptApp.deleteTrigger(t);});
  ScriptApp.newTrigger('scheduledDiscovery').timeBased().everyHours(1).create();
  ScriptApp.newTrigger('scheduledDownloads').timeBased().everyMinutes(15).create();
  return {ok:true};
}
function scheduledDiscovery(){if(String(props_().getProperty('DISCOVERY_RUNNING')).toUpperCase()==='TRUE')runDiscoveryNow();}
function scheduledDownloads(){if(String(props_().getProperty('DL_RUNNING')).toUpperCase()==='TRUE')runDownloadBatch();}
