# The majority of this code was genereated by ChatGPT. Then debuged by me (it did a quite good job!).
# I also added:
# * degradation cost
# * soc min/max
#  
# The prompt I used was:
# I have a year of time series data from a household (in a pandas dataframe):
# * ac power from solar panels (pv_ac_power)
# * household consumption (consumption)
# * hourly prices for importing energy from the grid (grid_import_unitPrice)
# * hourly prices for exporting energy from the grid (grid_export_unitPrice)
# 
# I want to simulate the effect of introducing a battery in the system. The battery have these known variables:
# * battery storage capacity (b_capacity)
# * battery max discharge rate (b_d_rate)
# * battery max charge rate (b_c_rate)
# * battery discharge efficiency (b_d_eff)
# * battery charge efficiency (b_c_eff)
# 
# I want the simulation to minimize the cost of energy from the grid.
# I want you to help me write a python script using the pulp library to accomplish this.


import numpy as np
import pandas as pd
import pulp


import logging
logger = logging.getLogger(__name__)


def optimize_battery(
    df,
    b_capacity,        # kWh
    b_c_rate,          # kW
    b_d_rate,          # kW
    g_cap = None,      # kW. Grid capacity VAC*fuse size. None = disable
    b_c_eff=0.95,      # charging efficiency (0..1)
    b_d_eff=0.95,      # discharging efficiency (0..1)
    b_soc_max=1,
    b_soc_min=0,
    c_deg=0,           # currency unit/kWh cycled  5/6
    initial_soc=None,  # kWh, if None -> 50% of capacity
    forbid_simultaneous=False,  # enforce no charge+discharge same hour (MILP)
    verbose=False
):

    logger.info('Running battery optimizer...')
    
    df.index.name = 'time_utc'
    df = df.copy().reset_index() #(drop=True)
    #print(df)
    n = len(df)
    required = ["source", "load", "grid_import_price", "grid_export_price"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))

    if initial_soc is None:
        initial_soc = 0.5 * b_capacity

    prob = pulp.LpProblem("battery_schedule", pulp.LpMinimize)

    # variables
    charge = pulp.LpVariable.dicts("charge_kW", range(n), lowBound=0, upBound=b_c_rate, cat="Continuous")
    discharge = pulp.LpVariable.dicts("discharge_kW", range(n), lowBound=0, upBound=b_d_rate, cat="Continuous")
    grid_import = pulp.LpVariable.dicts("grid_import_kW", range(n), lowBound=0, cat="Continuous")
    grid_export = pulp.LpVariable.dicts("grid_export_kW", range(n), lowBound=0, cat="Continuous")
    soc = pulp.LpVariable.dicts("soc_kWh", range(n), lowBound=b_capacity*b_soc_min, upBound=b_capacity*b_soc_max, cat="Continuous")

    if forbid_simultaneous:
        use_charge = pulp.LpVariable.dicts("use_charge", range(n), lowBound=0, upBound=1, cat="Binary")
        use_discharge = pulp.LpVariable.dicts("use_discharge", range(n), lowBound=0, upBound=1, cat="Binary")
        for t in range(n):
            prob += use_charge[t] + use_discharge[t] <= 1, f"no_simul_{t}"
            prob += charge[t] <= b_c_rate * use_charge[t], f"link_charge_bin_{t}"
            prob += discharge[t] <= b_d_rate * use_discharge[t], f"link_discharge_bin_{t}"

    # constraints
    for t in range(n):

        source = float(df.loc[t, "source"])
        load = float(df.loc[t, "load"])
        # energy balance
        prob += (
            (
                source + grid_import[t] + discharge[t] 
                == 
                load + grid_export[t] + charge[t] 
            ), f"energy_balance_{t}"
        )

        # soc update
        if t == 0:
            prob += soc[t] == initial_soc + (b_c_eff * charge[t]) - (discharge[t] / b_d_eff), f"soc_update_{t}"
        else:
            prob += soc[t] == soc[t-1] + (b_c_eff * charge[t]) - (discharge[t] / b_d_eff), f"soc_update_{t}"

    if not g_cap == None:
        for t in range(n):
            prob += grid_import[t] <= g_cap, f"link_charge_bin_{t}"
            prob += grid_export[t] <= g_cap, f"link_discharge_bin_{t}"


    # keep final soc approximately equal to initial to avoid end-game exploitation
    prob += soc[n-1] >= initial_soc * 0.99, "end_soc_min"
    prob += soc[n-1] <= initial_soc * 1.01, "end_soc_max"

    # objective (imports cost money; exports earn revenue)
    cost_terms = []
    for t in range(n):
        price_imp = float(df.loc[t, "grid_import_price"])
        price_exp = float(df.loc[t, "grid_export_price"])
        #cost_terms.append(grid_import[t] * price_imp + grid_export[t] * price_exp)
        cost_terms.append(
            (grid_import[t] * price_imp) 
            - (grid_export[t] * price_exp) 
            + (c_deg * (charge[t] + discharge[t]) / 2)
        )
    prob += pulp.lpSum(cost_terms)

    solver = pulp.PULP_CBC_CMD(msg=verbose)
    prob.solve(solver)

    status = pulp.LpStatus[prob.status]
    results = pd.DataFrame()
    results.index = df.index
    results['time_utc'] = df['time_utc']
    #results = df.copy()
    results["battery_charge_energy"] = [pulp.value(charge[t]) for t in range(n)]
    results["battery_discharge_energy"] = [pulp.value(discharge[t]) for t in range(n)]
    results["grid_import_energy"] = [pulp.value(grid_import[t]) for t in range(n)]
    results["grid_export_energy"] = [pulp.value(grid_export[t]) for t in range(n)]
    results["battery_soc_energy"] = [pulp.value(soc[t]) for t in range(n)]
    #results["grid_cost"] = [pulp.value(grid_import[t]) * float(df.loc[t,"grid_import_price"]) + pulp.value(grid_export[t]) * float(df.loc[t,"grid_export_price"]) for t in range(n)]
    #results["cumulative_cost"] = results["timestep_cost"].cumsum()
    #meta = {"status": status, "objective_value": pulp.value(prob.objective)} #, "total_cost": results["grid_cost"].sum()}

    logger.info('Battery optimizer done with status: ' + status)

    # reset index to time_utc
    results.set_index('time_utc', inplace=True, drop=True)
    
    return results #, meta



if __name__ == "__main__":
    print("cant run like this")

