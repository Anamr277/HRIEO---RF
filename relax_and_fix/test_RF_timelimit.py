from datetime import datetime
import matplotlib.pyplot as plt
from instance_ana import InstanceData
from lp_RF import LPConfiguration, LPModel_RF
import time 

start_time = time.time()

EXAMPLE = 1
NUM_DAMS = 12
NUM_DAYS = 1
DATE = 20200618
TIME_LIMIT_MINUTES = 2
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
        "dam3": 31010.43613642857,
        "dam4": 31010.43613642857,
        "dam5": 59627.42324,
        "dam6": 59627.42324,
        "dam7": 31010.43613642857,
        "dam8": 59627.42324,
        "dam9": 59627.42324,
        "dam10": 31010.43613642857,
        "dam11": 59627.42324,
        "dam12": 31010.43613642857,
    },
    MIPGap=0.0,
    time_limit_seconds=TIME_LIMIT_MINUTES*60,
    flow_smoothing=2
)

instance = InstanceData.from_json(f"/home/admin/tfm_ana/new/percentiles/20/instance_{NUM_DAMS}dams_{DATE}.json")
lp = LPModel_RF(config=config, instance=instance)


# Definir el tamaño de bloque y los rangos de tiempo para los subproblemas
block_size = 4
num_ts = instance.get_largest_impact_horizon()
num_blocks = (num_ts + block_size - 1) // block_size

# Se definen dos time limits distintos para que RF no sobrepase los 900 segundos en instancias largas
first_half_limit = (900/24)*2
second_half_limit = (900/24)*0.5

# Resolver iterativamente el modelo para cada bloque de franjas de tiempo
for current_block in range(num_blocks):
    if current_block < num_blocks // 2:
        lp.config.time_limit_seconds = first_half_limit
    else:
        lp.config.time_limit_seconds = second_half_limit
    
    start_t = current_block * block_size
    end_t = min((current_block + 1) * block_size, num_ts)
    current_binary_t_range = list(range(start_t, end_t))
    lp.current_binary_t_range = current_binary_t_range
    # Llamar a solve con el nuevo rango
    print(f"--------Resolviendo subproblema {current_block}--------")
    print(f"Franjas de tiempo binarias: {current_binary_t_range}")
    lp.solve()

lp.validate_solution()


path_sol = f"/home/admin/tfm_ana/new/relax_and_fix/RFsol_instance{EXAMPLE}_LPmodel_{NUM_DAMS}dams_{DATE}" \
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

        plot_filename = f"/home/admin/tfm_ana/new/relax_and_fix/RFdam_{dam_id}_plot.png"  
        plt.savefig(plot_filename)
        plt.close()  
