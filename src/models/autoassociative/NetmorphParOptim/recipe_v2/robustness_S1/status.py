import sys, json; sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe'); import recipelib as L
S=json.load(open('summary.json')); ids=sorted(v['sim_id'] for v in S.values()); print(len(ids),ids)
NES,c=L.connect()
for i in ids:
    try: r=c.RequestHandler.BuildPostQuery([{"Simulation/GetStatus": {"SimulationID": i}}], "/NES")[0]
    except Exception as e: r=repr(e)
    print(i,r)
print([m for m in dir(c) if 'tatus' in m or 'List' in m or 'Sim' in m])
