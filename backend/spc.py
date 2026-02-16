import numpy as np
from typing import List, Dict, Any

def calculate_cpk(data: List[float], usl: float, lsl: float) -> float:
    """
    Calculate Cpk (Process Capability Index).
    """
    if not data or len(data) < 2:
        return 0.0

    arr = np.array(data)
    mean = np.mean(arr)
    std = np.std(arr, ddof=1) # Sample standard deviation

    if std == 0:
        return 0.0

    cpu = (usl - mean) / (3 * std)
    cpl = (mean - lsl) / (3 * std)

    return float(min(cpu, cpl))

def generate_control_chart_data(parameter_id: str, points: int = 20) -> Dict[str, Any]:
    """
    Generates simulated Xbar-R chart data.
    """
    # Simulate data based on parameter type
    if parameter_id == "temp":
        mean_val = 100.0
        std_val = 2.0
        usl, lsl = 106.0, 94.0
    elif parameter_id == "pressure":
        mean_val = 50.0
        std_val = 1.5
        usl, lsl = 55.0, 45.0
    else:
        mean_val = 10.0
        std_val = 1.0
        usl, lsl = 13.0, 7.0

    # Generate 'points' subgroups of size 5
    subgroup_size = 5
    raw_data = np.random.normal(mean_val, std_val, (points, subgroup_size))

    chart_data = []
    all_values = []

    for i in range(points):
        subgroup = raw_data[i]
        xbar = float(np.mean(subgroup))
        r_val = float(np.max(subgroup) - np.min(subgroup))

        chart_data.append({
            "id": i + 1,
            "xbar": round(xbar, 2),
            "r": round(r_val, 2),
            "ucl_x": round(mean_val + (3 * std_val / np.sqrt(subgroup_size)), 2), # Simplified UCL
            "lcl_x": round(mean_val - (3 * std_val / np.sqrt(subgroup_size)), 2)  # Simplified LCL
        })
        all_values.extend(subgroup)

    cpk = calculate_cpk(all_values, usl, lsl)

    return {
        "parameter": parameter_id,
        "cpk": round(cpk, 3),
        "usl": usl,
        "lsl": lsl,
        "data": chart_data
    }
