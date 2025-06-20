from datetime import datetime, timedelta
import json
from copy import copy

class InstanceData:
    def __init__(self, file_path=None, data=None):
        """
        Initializes an instance by loading data from a JSON file or using a provided dictionary.

        :param file_path: Path to the JSON file (optional).
        :param data: Dictionary with instance data (optional).
        :raises ValueError: If neither file_path nor data is provided.
        """
        if file_path:
            with open(file_path, "r", encoding="utf-8") as file:
                self.data = json.load(file)
        elif data:
            self.data = data
        else:
            raise ValueError("Either a file path or a dictionary must be provided.")

    @classmethod
    def from_json(cls, file_path):
        """
        Creates an instance from a JSON file.

        :param file_path: Path to the JSON file.
        :return: An instance of the class with loaded data.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data):
        """
        Creates an instance from a dictionary, converting the list of dams into a dictionary indexed by ID.

        :param data: Dictionary containing instance data.
        :return: An instance of the class with transformed data.
        """
        data_p = dict(data)
        data_p["dams"] = {el["id"]: el for el in data_p.get("dams", [])}
        return cls(data=data_p)
    
    def get_ids_of_dams(self) -> list[str]:
        """
        :return: The IDs of all dams in the river basin
        """
        return list(self.data["dams"].keys())
    
    def get_start_decisions_datetime(self) -> datetime:
        """

        :return: Starting datetime for the decisions, after the starting information offset
        """
        start = datetime.strptime(self.data["datetime"]["start"], "%Y-%m-%d %H:%M")
        return start

    def get_end_decisions_datetime(self) -> datetime:
        """

        :return: Final datetime for the decisions, before the impact buffer and final information offset
        """
        end = datetime.strptime(self.data["datetime"]["end_decisions"], "%Y-%m-%d %H:%M")
        return end

    def get_end_impact_datetime(self) -> datetime:

        """
       Get the datetime of the largest impact horizon
       (the datetime up to which the chosen flows have an impact in the income obtained).

       For example, if the instance spans one day, we consider steps of 1/4 hour, and
       the longest channel has a maximum delay of 3/4 hour, this will be (24 + 3/4) * 4 = 99 time steps
       after the beginning of the decisions.

       :return: Datetime of the largest impact horizon
       """

        end_decisions = self.get_end_decisions_datetime()
        impact_buffer = max([self.get_relevant_lags_of_dam(dam_id)[0] for dam_id in self.get_ids_of_dams()])
        end_impact = end_decisions + timedelta(seconds=self.get_time_step_seconds()) * impact_buffer

        return end_impact

    def get_time_step_seconds(self) -> float:

        """

        :return: The time between updates in seconds (s)
        """

        time_step_seconds = self.data["time_step_minutes"] * 60
        return time_step_seconds
    
    def get_decision_horizon(self) -> int:

        """
        Get the number of time steps up to the decision horizon
        (number of time steps in which we have to choose the flows).

        For example, if the instance spans one day, and we consider steps of 1/4 hour,
        this will be 24*4 = 96.

        :return: Number of time steps up to the decision horizon
        """

        start_decisions = self.get_start_decisions_datetime()
        end_decisions = self.get_end_decisions_datetime()
        difference = end_decisions - start_decisions
        num_time_steps_decisions = difference.total_seconds() // self.get_time_step_seconds() + 1

        return int(num_time_steps_decisions)
    

    def get_largest_impact_horizon(self) -> int:

        """
        Get the number of time steps up to the largest impact horizon
        (maximum number of time steps in which the chosen flows have an impact in the income obtained).
        This should be equal to the total number of time steps of the instance
        (that is, the number of time steps for which we have data on the energy price, the unregulated flows, etc.).

        For example, if the instance spans one day, we consider steps of 1/4 hour, and
        the longest channel has a maximum delay of 3/4 hour, this will be (24 + 3/4) * 4 = 99.

        :return: Number of time steps up to the largest impact horizon
        """

        start_decisions = self.get_start_decisions_datetime()
        end_impact = self.get_end_impact_datetime()
        difference = end_impact - start_decisions

        return int(difference.total_seconds() // self.get_time_step_seconds() + 1)
    
    def get_all_unregulated_flows_of_dam(self, idx: str) -> list[float]:
        
        """
        
        :return: All unregulated flow that enters the dam (flow that comes from the river)
        within the decision horizon (m3/s)
        """
        
        unreg_flows = self.data["dams"][idx]["unregulated_flows"]
        return copy(unreg_flows)

    def get_relevant_lags_of_dam(self, idx: str) -> list[int]:

        """

        :param idx: ID of the dam in the river basin
        :return: List of the relevant lags of the dam (1 lag = 15 minutes of time delay)
        """

        relevant_lags = self.data["dams"][idx]["relevant_lags"]
        return copy(relevant_lags)

    def get_verification_lags_of_dam(self, idx: str) -> list[int]:

        """

        :param idx: ID of the dam in the river basin
        :return: List of the verification lags of the dam (1 lag = 15 minutes of time delay)
        This must be a subset of the relevant lags, containing only the most important lags
        At each time step, the turbined flow should be roughly equal to the average of the verification lags
        """

        verification_lags = self.data["dams"][idx]["verification_lags"]
        return copy(verification_lags)
    
    def get_turbined_flow_obs_for_power_group(self, idx: str) -> dict[str, list[float]]:

        """

        :param idx: ID of the dam in the river basin
        :return: Dictionary with a list of turbined flows and the corresponding power observed (m3/s and MW)
        """

        points = {
            "observed_flows": copy(self.data["dams"][idx]["turbined_flow"]["observed_flows"]),
            "observed_powers": copy(self.data["dams"][idx]["turbined_flow"]["observed_powers"]),
        }

        return points

    def get_max_flow_of_channel(self, idx: str) -> float:

        """

        :param idx: ID of the dam in the river basin
        :return: Maximum flow the channel can carry (m3/s)
        """

        flow_max = self.data["dams"][idx]["flow_max"]
        return copy(flow_max)

    def get_flow_limit_obs_for_channel(self, idx: str) -> dict[str, list[float]] | None:

        """

        :param idx: ID of the dam in the river basin
        :return: Dictionary with a list of volumes and the corresponding maximum flow limits observed (m3 and m3/s)
        """

        if self.data["dams"][idx]["flow_limit"]["exists"]:
            points = {
                "observed_vols": copy(self.data["dams"][idx]["flow_limit"]["observed_vols"]),
                "observed_flows": copy(self.data["dams"][idx]["flow_limit"]["observed_flows"]),
            }
        else:
            points = None

        return points
    
    def get_initial_vol_of_dam(self, idx: str) -> float:

        """

        :param idx: ID of the dam in the river basin
        :return: The volume of the dam in the beginning (m3)
        """

        min_vol = self.get_min_vol_of_dam(idx)
        max_vol = self.get_max_vol_of_dam(idx)
        initial_vol = self.data["dams"][idx]["initial_vol"]

        return max(min_vol, min(initial_vol, max_vol))

    def get_max_vol_of_dam(self, idx: str) -> float:

        """

        :param idx: ID of the dam in the river basin
        :return: Maximum volume of the dam (m3)
        """

        vol_max = self.data["dams"][idx]["vol_max"]
        return copy(vol_max)

    def get_min_vol_of_dam(self, idx: str) -> float:

        """

        :param idx: ID of the dam in the river basin
        :return: Minimum volume of the dam (m3)
        """

        vol_min = self.data["dams"][idx]["vol_min"]
        return copy(vol_min)

    def get_all_prices(self) -> list[float]:
        
        """
        
        :return: All the prices of energy (EUR/MWh) in the time bands within the decision horizon
        """
        
        prices = self.data["energy_prices"]
        return copy(prices)
    
    def get_initial_lags_of_channel(self, idx: str) -> list[float]:

        """

        :param idx: ID of the dam in the river basin
        :return:
            Flow that went through the channel in the previous time steps,
            in decreasing order (i.e., flow in time steps -1, ..., -last_lag) (m3/s)
        """

        initial_lags = self.data["dams"][idx]["initial_lags"]
        return copy(initial_lags)

    def get_all_incoming_flows(self) -> list[float]:
        
        """
        
        :return: All the flows (m3/s) entering the first dam in the time bands within the decision horizon
        """
        
        incoming_flows = self.data["incoming_flows"]
        return copy(incoming_flows)

    def get_shutdown_flows_of_power_group(self, idx: str) -> list[float]:

        """

        :param idx: ID of the dam in the river basin
        :return: List with the shutdown flows of the power group (m3/s)
        When the turbined flow falls behind one of these flows,one of the power group units is deactivated
        """

        shutdown_flows = self.data["dams"][idx]["shutdown_flows"]
        return copy(shutdown_flows)

    def get_startup_flows_of_power_group(self, idx: str) -> list[float]:

        """

        :param idx: ID of the dam in the river basin
        :return: List with the startup flows of the power group (m3/s)
        When the turbined flow exceeds one of these flows, an additional power group unit is activated
        """

        startup_flows = self.data["dams"][idx]["startup_flows"]
        return copy(startup_flows)

    def get_total_avg_inflow(self) -> float:

        """
        Calculate the total average inflow of the day.
        The total average inflow is calculated by adding the average incoming and unregulated flows
        up to the decision horizon.
        """

        incoming_flows = self.get_all_incoming_flows()[:self.get_decision_horizon()]
        # print("Incoming flows:", incoming_flows)
        # print("Incoming flow mean:", sum(incoming_flows)/len(incoming_flows))
        total_avg_inflow = sum(incoming_flows) / len(incoming_flows)
        for dam_id in self.get_ids_of_dams():
            unreg_flows = self.get_all_unregulated_flows_of_dam(dam_id)[:self.get_decision_horizon()]
            # print(dam_id, "unregulated flows:", unreg_flows)
            # print(dam_id, "unregulated flow mean:", sum(unreg_flows) / len(unreg_flows))
            total_avg_inflow += sum(unreg_flows) / len(unreg_flows)
        # print("Total avg inflow:", total_avg_inflow)

        return total_avg_inflow
    
    def get_avg_price(self) -> float:

        """
        Get the largest average price value for the instance.

        :return: Average price of the information interval
        """

        avg_price = sum(self.data["energy_prices"]) / len(self.data["energy_prices"])
        return avg_price