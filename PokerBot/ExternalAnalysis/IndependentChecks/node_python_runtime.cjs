// Map the unavailable Windows python3 app alias to the bundled interpreter.
const cp=require('node:child_process');
const original=cp.spawnSync;
cp.spawnSync=function(command,args,options){
  if(command==='python3') command='C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1112-737-0_26.1112.737.0_x64__3k8sg7r9htsxt/dependencies/python/python.exe';
  return original.call(this,command,args,options);
};
require('node:module').syncBuiltinESMExports();
