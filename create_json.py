import pandas as pd
import json
import os
from datetime import datetime, timedelta

# Se crea una función para poder crear instancias con un número de dams distinto de 2
def generate_adjusted_dataframe(data_path, total_dams):
    """
    Esta función genera un DataFrame ajustado a partir de los datos históricos con datos duplicados para el número de dams especificado.
    Los datos se copian segun el criterio apuntado en dam_source_map
    """
    df = pd.read_pickle(data_path)
    #Como se copian los datos
    dam_source_map = {
        3: 'dam2',
        4: 'dam2',
        5: 'dam1',
        6: 'dam1',
        7: 'dam2',
        8: 'dam1',
        9: 'dam1',
        10: 'dam2',
        11: 'dam1',
        12: 'dam2',
    }
    new_columns = df.columns.tolist()
    for dam_id in range(3, total_dams + 1):
        new_columns.append(f"dam{dam_id}_flow")
        new_columns.append(f"dam{dam_id}_vol")
        new_columns.append(f"dam{dam_id}_turbined_flow")
        new_columns.append(f"dam{dam_id}_power")
        new_columns.append(f"dam{dam_id}_unreg_flow")

    adjusted_df = pd.DataFrame(columns=new_columns)
    adjusted_df['datetime'] = df['datetime']

    for dam_id in range(1, total_dams + 1):
        if dam_id == 1:
            source = 'dam1'
        elif dam_id == 2:
            source = 'dam2'
        else:
            source = dam_source_map[dam_id]

        adjusted_df[f"dam{dam_id}_flow"] = df[f"{source}_flow"]
        adjusted_df[f"dam{dam_id}_vol"] = df[f"{source}_vol"]
        adjusted_df[f"dam{dam_id}_turbined_flow"] = df[f"{source}_turbined_flow"]
        adjusted_df[f"dam{dam_id}_power"] = df[f"{source}_power"]
        adjusted_df[f"dam{dam_id}_unreg_flow"] = df[f"{source}_unreg_flow"]

    adjusted_df['incoming_flow'] = df['incoming_flow']
    adjusted_df['price'] = df['price']

    return adjusted_df

# Se crea una función para obtener y ajustar los datos del dataframe dadas las fechas de inicio y fin
def get_data_by_dates(data_path, total_dams, start_date, end_date):
    """
    Esta función filtra los datos por las fechas de inicio y fin y devuelve los datos de cada columna en una lista.
    """
    if total_dams<=2:
        df = pd.read_pickle(data_path)
    else: df = generate_adjusted_dataframe(data_path, total_dams)

    df['datetime'] = pd.to_datetime(df['datetime'])
    filtered_df = df[(df['datetime'] >= start_date) & (df['datetime'] <= end_date)]
    data_dict = {col: filtered_df[col].tolist() for col in filtered_df.columns}
    
    return data_dict

# Se crea una función para acceder al archivo JSON con las constantes
def load_constants_json(total_dams, file_path):
    """
    Función para obtener el archivo json con los datos constantes, dependiendo del numero de dams.
    """
    filename = f'constants_{total_dams}dams.json'
    full_path = os.path.join(file_path, filename)
    
    try:
        with open(full_path, 'r') as file:
            json_data = json.load(file)
        print(f"Archivo '{full_path}' cargado exitosamente.")
        return json_data
    except FileNotFoundError:
        print(f"Error: El archivo '{full_path}' no existe.")
        return None
    except json.JSONDecodeError:
        print(f"Error: El archivo '{full_path}' no es un JSON válido.")
        return None

# Se crea una función para acceder a los datos del día anterior 
def get_previous_day_data(data_path,total_dams, json_data, start_date):
    """
    Función para obtener initial_vol e initial_lags.

    """
    if total_dams<=2:
        df = pd.read_pickle(data_path)
    else: df = generate_adjusted_dataframe(data_path, total_dams)

    start_datetime = datetime.strptime(start_date, '%Y-%m-%d %H:%M')
    previous_day = start_datetime - timedelta(days=1)
    previous_day_start = previous_day.replace(hour=0, minute=0)
    previous_day_end = previous_day.replace(hour=23, minute=45)

    previous_day_data = df[(df['datetime'] >= previous_day_start) & (df['datetime'] <= previous_day_end)]
    previous_data_dict = {}
    
    for dam in json_data.get("dams", []):
        dam_id = dam["id"]

        if not previous_day_data.empty:
            initial_vol_series = df.loc[df['datetime'] == start_datetime, f"{dam_id}_vol"]
            if not initial_vol_series.empty:
                initial_vol = initial_vol_series.iloc[0]  
            else:
                initial_vol = None
        else:
            initial_vol = None
        
        verification_lags = dam.get("verification_lags", [])
        if verification_lags:
            max_lag = max(verification_lags)
            initial_lags = [
                previous_day_data[f"{dam_id}_flow"].iloc[-lag]
                for lag in range(1, max_lag + 1)
                if lag <= len(previous_day_data)
            ]
        else:
            initial_lags = []
        previous_data_dict[dam_id] = {
            "initial_vol": initial_vol,
            "initial_lags": initial_lags
        }

    return previous_data_dict

def get_next_day_data(data_path, total_dams, end_date):
    """
    Función para coger los tres datos siguientes fuera del horizonte de decisión.
    """
    if total_dams<=2:
        data = pd.read_pickle(data_path)
    else: data = generate_adjusted_dataframe(data_path, total_dams)

    end_datetime = datetime.strptime(end_date, '%Y-%m-%d %H:%M')
    next_day = end_datetime + timedelta(days=1)
    next_day_start = next_day.replace(hour=0, minute=0)
    next_day_end = next_day.replace(hour=23, minute=45)
    next_day_data = data[
        (data['datetime'] >= next_day_start) & 
        (data['datetime'] <= next_day_end)
    ]
    dams_data = {}
    for dam_id in range(1, total_dams + 1):
        dam_name = f"dam{dam_id}"
        unregulated_flows = next_day_data[f"{dam_name}_unreg_flow"].head(3).tolist()
        dams_data[dam_name] = {
            "unregulated_flows": unregulated_flows
        }
    incoming_flows = next_day_data['incoming_flow'].head(3).tolist()
    energy_prices = next_day_data['price'].head(3).tolist()

    next_day_dict = {
        "dams": dams_data,
        "incoming_flows": incoming_flows,
        "energy_prices": energy_prices
    }
    
    return next_day_dict


def fill_json_with_data(json_data, data_dict, previous_day_data, next_day_data, start_date, end_date):
    """
    Rellena el JSON con los datos obtenidos del DataFrame.
    
    """
 
    if json_data["datetime"]["start"] is None:
        json_data["datetime"]["start"] = start_date
    
    if json_data["datetime"]["end_decisions"] is None:
        json_data["datetime"]["end_decisions"] = end_date

    if json_data["incoming_flows"] is None:
        json_data["incoming_flows"] = data_dict.get("incoming_flow", None)
        json_data["incoming_flows"] += next_day_data["incoming_flows"]
    
    if json_data["energy_prices"] is None:
        json_data["energy_prices"] = data_dict.get("price", None)
        json_data["energy_prices"] += next_day_data["energy_prices"]
    
    for dam in json_data.get("dams", []):
        dam_id = dam["id"]
        unregulated_flow_key = f"{dam_id}_unreg_flow"
        if dam["unregulated_flows"] is None:
            dam["unregulated_flows"] = data_dict.get(unregulated_flow_key, None)
            dam["unregulated_flows"] += next_day_data["dams"].get(dam_id, {}).get("unregulated_flows", [])
        
        if dam_id in previous_day_data:
            dam_data = previous_day_data[dam_id]

            if dam["initial_vol"] is None:
                dam["initial_vol"] = dam_data["initial_vol"]
            
            if dam["initial_lags"] is None:
                dam["initial_lags"] = dam_data["initial_lags"]
             
    return json_data

def save_json(json_data, repo_path):
    """
    Función para guardar la nueva instacia como un json en la carpeta seleccionada.
    """
    for key, value in json_data.items():
        if isinstance(value, pd.Series):
            json_data[key] = value.tolist()
        elif isinstance(value, dict):
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, pd.Series):
                    json_data[key][sub_key] = sub_value.tolist()

    selected_date = json_data.get("datetime", {}).get("start", None) 
    if selected_date is None:
        print("Advertencia: No se encontró la fecha en el JSON")
        return
    selected_date = datetime.strptime(selected_date, "%Y-%m-%d %H:%M").strftime("%Y%m%d")
    total_dams = len(json_data.get("dams", []))
    file_name = f"instance_{total_dams}dams_{selected_date}.json"
    full_path = os.path.join(repo_path, file_name)
    os.makedirs(repo_path, exist_ok=True)
    try:
        with open(full_path, 'w') as archivo_json:
            json.dump(json_data, archivo_json, indent=4)
        print(f"Archivo guardado exitosamente en: {full_path}")
    except IOError as e:
        print(f"Error al guardar el archivo JSON: {e}")



historical_data_path = "data/historical_data.pickle" 
selected_start_date = "2021-05-21 00:00"
selected_end_date = "2021-05-21 23:45"
for i in range(1,13):
    data = generate_adjusted_dataframe(historical_data_path,i)
    data_selected = get_data_by_dates(historical_data_path,i,selected_start_date,selected_end_date)
    constant_data = load_constants_json(i,"new/constants_edited")
    previous_day_data = get_previous_day_data(historical_data_path, i,constant_data,selected_start_date)
    next_day_data = get_next_day_data(historical_data_path, i, selected_end_date)
    new_instance_data = fill_json_with_data(constant_data,data_selected,previous_day_data,next_day_data,selected_start_date,selected_end_date)
    save_json(new_instance_data, "new/percentiles/90")
