import json,os,urllib.request
op=urllib.request.build_opener();op.addheaders=[('User-Agent','Mozilla/5.0 cortes/1.0')];urllib.request.install_opener(op),urllib.parse
K=os.environ['PIXABAY_KEY'];q=json.load(open('queries.json'));out={}
os.makedirs('thumbs',exist_ok=True)
for k,v in q.items():
    u='https://pixabay.com/api/videos/?'+urllib.parse.urlencode({'key':K,'q':v,'per_page':8,'safesearch':'true'})
    hits=json.load(urllib.request.urlopen(u))['hits'];out[k]=[]
    for h in hits:
        r=h['videos'];out[k].append({'id':h['id'],'dur':h['duration'],'tags':h['tags'],'w':r['large']['width'] or r['medium']['width'],'h':r['large']['height'] or r['medium']['height'],'urls':{s:r[s]['url'] for s in r if r[s]['url']}})
        t=r['medium'].get('thumbnail') or r['small'].get('thumbnail')
        if t:
            try: urllib.request.urlretrieve(t,f"thumbs/{k}_{h['id']}.jpg")
            except Exception as e: print(e)
json.dump(out,open('resultados.json','w'),indent=1)
