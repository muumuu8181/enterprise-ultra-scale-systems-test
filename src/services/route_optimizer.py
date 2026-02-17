import math
from typing import List, Dict, Any
from geoalchemy2.shape import to_shape
from src.models.waste_models import WasteBin

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    2点間の距離を計算 (Haversine formula)
    """
    R = 6371  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_path_distance(route: List[int], dist_matrix: List[List[float]]) -> float:
    dist = 0.0
    for i in range(len(route) - 1):
        dist += dist_matrix[route[i]][route[i+1]]
    return dist

def optimize_collection_route(bins: List[WasteBin]) -> Dict[str, Any]:
    """
    2-opt法を用いたTSP近似アルゴリズムによる収集ルート最適化
    """
    if not bins:
        return {
            "waypoints": [],
            "total_distance_km": 0.0,
            "estimated_duration_min": 0.0
        }

    points = []
    for b in bins:
        # GeoAlchemy2の要素をShapelyオブジェクトに変換
        shape = to_shape(b.location)
        points.append({"id": b.id, "lat": shape.y, "lon": shape.x})

    n = len(points)
    # 距離行列の計算
    dist_matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                dist_matrix[i][j] = haversine_distance(
                    points[i]["lat"], points[i]["lon"],
                    points[j]["lat"], points[j]["lon"]
                )

    # 初期ルート: 単純な順序
    route = list(range(n))

    # 2-opt アルゴリズム
    improved = True
    max_iterations = 100 # 無限ループ防止
    iteration = 0

    while improved and iteration < max_iterations:
        improved = False
        iteration += 1
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                if j - i == 1: continue

                # 現在のコスト: A->B + C->D
                # A = route[i-1], B = route[i]
                # C = route[j], D = route[j+1] (存在する場合)

                idx_A = route[i-1]
                idx_B = route[i]
                idx_C = route[j]

                d_old = dist_matrix[idx_A][idx_B]
                d_new = dist_matrix[idx_A][idx_C]

                if j + 1 < n:
                    idx_D = route[j+1]
                    d_old += dist_matrix[idx_C][idx_D]
                    d_new += dist_matrix[idx_B][idx_D]

                # 改善する場合のみスワップ
                if d_new < d_old:
                    route[i:j+1] = route[i:j+1][::-1]
                    improved = True

    total_dist = calculate_path_distance(route, dist_matrix)

    # 所要時間の見積もり
    # 平均速度 30km/h + 各ポイントでの作業時間 5分
    avg_speed_kmh = 30.0
    collection_time_min_per_bin = 5.0

    travel_time_min = (total_dist / avg_speed_kmh) * 60 if avg_speed_kmh > 0 else 0
    total_time_min = travel_time_min + (n * collection_time_min_per_bin)

    result_waypoints = [points[i] for i in route]

    return {
        "waypoints": result_waypoints,
        "total_distance_km": round(total_dist, 2),
        "estimated_duration_min": round(total_time_min, 1)
    }
