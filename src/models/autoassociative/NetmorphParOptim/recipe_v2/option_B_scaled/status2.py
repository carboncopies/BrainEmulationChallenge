import sys; sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe')
import recipelib as L
NES,c=L.connect(); alive=[]
for i in range(0,130):
    r=c.RequestHandler.BuildPostQuery([{"Simulation/GetStatus": {"SimulationID": i}}], "/NES")[0]
    if r.get('StatusCode')!=2: alive.append(i)
print('ALIVE',alive)
