import sys; sys.path.insert(0,'/home/johnjose/cos/netmorph_work/recipe')
import recipelib as L
NES,c=L.connect()
ids=[int(x) for x in sys.argv[1:]]
for i in ids:
    s=NES.Simulation.Simulation(NES.Simulation.Configuration(),c.RequestHandler,_Create=False); s.ID=i
    print(i,s.DeleteResidentByID(Pause_s=0.1))
