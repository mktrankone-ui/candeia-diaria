import json,os,subprocess,urllib.request
op=urllib.request.build_opener();op.addheaders=[('User-Agent','Mozilla/5.0 cortes/1.0')];urllib.request.install_opener(op)
res=json.load(open('resultados.json'));idx={h['id']:h for v in res.values() for h in v}
os.makedirs('cenas',exist_ok=True);os.makedirs('tmp',exist_ok=True)
for n,(i,ss,d) in enumerate(json.load(open('cenas.json'))):
    u=idx[i]['urls'];w=idx[i]['w']
    url=u['large'] if w<=1920 and 'large' in u else u.get('medium')
    src=f'tmp/{i}.mp4'
    if not os.path.exists(src): urllib.request.urlretrieve(url,src)
    vf="scale='if(gt(a,9/16),-2,1188)':'if(gt(a,9/16),2112,-2)',crop=1188:2112,fps=30,setsar=1"
    subprocess.run(['ffmpeg','-loglevel','error','-y','-ss',str(ss),'-t',str(d+0.2),'-i',src,'-vf',vf,'-an','-c:v','libx264','-crf','17','-preset','medium',f'cenas/{n:02d}_{i}.mp4'],check=True)
    print(n,i,os.path.getsize(f'cenas/{n:02d}_{i}.mp4'))
