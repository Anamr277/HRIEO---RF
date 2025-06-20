from datetime import datetime
import matplotlib.pyplot as plt
from instance_ana import InstanceData
from lp_ana import LPConfiguration, LPModel
import time 
import orloge as ol 

start_time = time.time()

EXAMPLE = 1
NUM_DAMS = 2
NUM_DAYS = 1
DATE = 20200908
TIME_LIMIT_MINUTES = 15
SAVE_SOLUTION = False
SAVE_GRAPH = False

config = LPConfiguration(
    volume_shortage_penalty=3,
    volume_exceedance_bonus=0,
    startups_penalty=50,
    limit_zones_penalty=1000,
    volume_objectives={
        "dam1": 59627.42324,
        "dam2": 31010.43613642857,
        "dam3": 59627.42324,
        "dam4": 31010.43613642857,
        "dam5": 59627.42324,
        "dam6": 31010.43613642857,
        "dam7": 59627.42324,
        "dam8": 31010.43613642857,
    },
    MIPGap=0.0,
    time_limit_seconds=TIME_LIMIT_MINUTES*60,
    flow_smoothing=2
)

instance = InstanceData.from_json(f"/home/admin/tfm_ana/new/percentiles/00/instance_{NUM_DAMS}dams_{DATE}.json")
lp = LPModel(config=config, instance=instance)
lp.LPModel_print()

lp.solve()
path_sol = f"/home/admin/tfm_ana/new/test/MILPsol_instance{EXAMPLE}_LPmodel_{NUM_DAMS}dams_{DATE}" \
           f"_time{datetime.now().strftime('%Y-%m-%d_%H-%M')}.json"
if SAVE_SOLUTION == True: lp.solution.to_json(path_sol)

end_time = time.time()
execution_time = end_time - start_time
print(f"Tiempo de ejecución: {execution_time:.2f} segundos")

if SAVE_GRAPH == True:
# Plot simple solution graph for each dam
    for dam_id in instance.get_ids_of_dams():

        assigned_flows = lp.solution.get_exiting_flows_of_dam(dam_id)
        predicted_volumes = lp.solution.get_volumes_of_dam(dam_id)

        fig, ax = plt.subplots(1, 1)
        twinax = ax.twinx()
        ax.plot(predicted_volumes, color='b', label="Predicted volume")
        ax.set_xlabel("Time (15min)")
        ax.set_ylabel("Volume (m3)")
        ax.legend()
        twinax.plot(instance.get_all_prices(), color='r', label="Price")
        twinax.plot(assigned_flows, color='g', label="Flow")
        twinax.set_ylabel("Flow (m3/s), Price (€)")
        twinax.legend()
        plot_filename = f"/home/admin/tfm_ana/new/test/MILPdam_{dam_id}_plot.png"  
        plt.savefig(plot_filename)
        plt.close()  

# Info from the solver using the library orloge
info=ol.get_info_solver('/home/admin/tfm_ana/new/output.log', 'GUROBI')
print("INFO DEL SOLVER:", info, flush=True)
progress_df = info['progress']
print(progress_df.to_string(index=False), flush=True)