import json,os,urllib.request
res=json.load(open('resultados.json'));sel=json.load(open('selecao.json'));os.makedirs('clips',exist_ok=True)
idx={h['id']:h for v in res.values() for h in v}
for i in sel:
    u=idx[i]['urls'];url=u.get('medium') or u.get('large') or u.get('small')
    urllib.request.urlretrieve(url,f'clips/{i}.mp4');print(i,os.path.getsize(f'clips/{i}.mp4'))
