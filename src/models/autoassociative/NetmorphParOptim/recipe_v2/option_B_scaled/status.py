import sys,glob,re; sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe')
import recipelib as L
ids=sorted({int(m) for f in glob.glob('log_*.txt') for m in re.findall(r'^sim (\d+)',open(f).read(),re.M)})
NES,c=L.connect(); alive=[]
for i in list(ids)+list(range(max(ids)+1,max(ids)+15)):
    r=c.RequestHandler.BuildPostQuery([{"Simulation/GetStatus": {"SimulationID": i}}], "/NES")[0]
    if r.get('StatusCode')!=2: alive.append((i,r))
print(len(ids),min(ids),max(ids),'not-deleted/alive:',alive)
