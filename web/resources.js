/* Pacotes por contexto: transferência cooperativa sem cópia persistente na RAM JS. */
(() => {
  let sequence=0;
  const jobs=new Map();
  window.scapeResources={
    begin(url) {
      const id=++sequence,job={pending:true,received:0,total:0};jobs.set(id,job);
      (async()=>{
        const response=await fetch(url,{cache:"force-cache"});
        if(!response.ok){
          const error=response.headers.get("X-Scape-Offline") ? (await response.json()).message : "Falha HTTP "+response.status;
          throw new Error(error);
        }
        job.total=Number(response.headers.get("content-length")||0);
        const reader=response.body.getReader(),chunks=[];
        while(true){const {done,value}=await reader.read();if(done)break;
          chunks.push(value);job.received+=value.length;}
        const bytes=new Uint8Array(job.received);let offset=0;
        for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}
        job.bytes=bytes;job.pending=false;
      })().catch(error=>{job.error=error.message;job.pending=false;});
      return id;
    },
    poll(id){const j=jobs.get(id);return JSON.stringify({pending:j.pending,error:j.error,
      received:j.received,total:j.total});},
    chunk(id,offset){const bytes=jobs.get(id).bytes.subarray(offset,offset+262144);
      const pieces=[];for(let i=0;i<bytes.length;i+=8192)
        pieces.push(String.fromCharCode(...bytes.subarray(i,i+8192)));
      return btoa(pieces.join(""));},
    release(id){jobs.delete(id);}
  };
})();

