from __future__ import annotations

import json
import os
import sys
import time
from typing import Any

import requests

SUPERSET_URL = os.environ.get("SUPERSET_URL", "http://localhost:8088")
USERNAME     = os.environ.get("SUPERSET_USER", "admin")
PASSWORD     = os.environ.get("SUPERSET_PASSWORD", "admin")

DB_NAME = "Oilfield Postgres"
DB_URI  = "postgresql://oilfield:oilfield_pass@postgres:5432/oilfield"
SCHEMA  = "marts"


class Superset:
    def __init__(self, url: str, user: str, pwd: str):
        self.url = url.rstrip("/")
        self.s = requests.Session()
        login = self.s.post(
            f"{self.url}/api/v1/security/login",
            json={"username": user, "password": pwd, "provider": "db", "refresh": True},
            timeout=10,
        )
        login.raise_for_status()
        self.token = login.json()["access_token"]
        self.s.headers.update({"Authorization": f"Bearer {self.token}"})
        csrf = self.s.get(f"{self.url}/api/v1/security/csrf_token/", timeout=10)
        csrf.raise_for_status()
        self.csrf = csrf.json()["result"]
        self.s.headers.update({
            "X-CSRFToken": self.csrf,
            "Referer": self.url,
        })

    def get(self, path: str, **kw) -> Any:
        r = self.s.get(f"{self.url}{path}", timeout=30, **kw)
        r.raise_for_status()
        return r.json()

    def post(self, path: str, payload: dict) -> dict:
        r = self.s.post(f"{self.url}{path}", json=payload, timeout=30)
        if r.status_code >= 400:
            print(f"POST {path} -> {r.status_code}\n{r.text}", file=sys.stderr)
            r.raise_for_status()
        return r.json()

    def put(self, path: str, payload: dict) -> dict:
        r = self.s.put(f"{self.url}{path}", json=payload, timeout=30)
        if r.status_code >= 400:
            print(f"PUT {path} -> {r.status_code}\n{r.text}", file=sys.stderr)
            r.raise_for_status()
        return r.json()

    def delete(self, path: str) -> None:
        r = self.s.delete(f"{self.url}{path}", timeout=30)
        if r.status_code not in (200, 404):
            r.raise_for_status()


def ensure_database(api: Superset) -> int:
    existing = api.get("/api/v1/database/?q=(page_size:100)")
    for row in existing["result"]:
        if row["database_name"] == DB_NAME:
            print(f"  ✓ database '{DB_NAME}' уже есть (id={row['id']})")
            return row["id"]
    payload = {
        "database_name": DB_NAME,
        "sqlalchemy_uri": DB_URI,
        "expose_in_sqllab": True,
        "allow_ctas": False,
        "allow_cvas": False,
        "allow_dml": False,
        "engine": "postgresql",
    }
    res = api.post("/api/v1/database/", payload)
    print(f"  + database '{DB_NAME}' создана (id={res['id']})")
    return res["id"]


def ensure_dataset(api: Superset, db_id: int, table: str) -> int:
    existing = api.get("/api/v1/dataset/?q=(page_size:200)")
    for row in existing["result"]:
        if row["table_name"] == table and row.get("schema") == SCHEMA:
            print(f"  ✓ dataset {SCHEMA}.{table} уже есть (id={row['id']})")
            return row["id"]
    res = api.post("/api/v1/dataset/", {
        "database": db_id,
        "schema": SCHEMA,
        "table_name": table,
    })
    print(f"  + dataset {SCHEMA}.{table} создан (id={res['id']})")
    return res["id"]


def get_dataset_columns(api: Superset, ds_id: int) -> dict[str, str]:
    res = api.get(f"/api/v1/dataset/{ds_id}")
    cols = {c["column_name"]: c.get("type", "NUMERIC") for c in res["result"]["columns"]}
    return cols


def delete_chart_if_exists(api: Superset, name: str) -> None:
    existing = api.get("/api/v1/chart/?q=(page_size:200)")
    for item in existing["result"]:
        if item["slice_name"] == name:
            api.delete(f"/api/v1/chart/{item['id']}")


def delete_dashboard_if_exists(api: Superset, title: str) -> None:
    existing = api.get("/api/v1/dashboard/?q=(page_size:200)")
    for item in existing["result"]:
        if item["dashboard_title"] == title:
            api.delete(f"/api/v1/dashboard/{item['id']}")


def metric(column: str, agg: str, col_type: str = "NUMERIC", label: str | None = None) -> dict:
    label = label or f"{agg}({column})"
    return {
        "expressionType": "SIMPLE",
        "column": {"column_name": column, "type": col_type},
        "aggregate": agg,
        "label": label,
        "optionName": f"metric_{column}_{agg}",
    }


def build_query_context(ds_id: int, viz_type: str, params: dict) -> dict:
    metrics = params.get("metrics") or ([params["metric"]] if params.get("metric") else [])
    columns: list = []
    if "x_axis" in params:
        columns.append(params["x_axis"])
    if "groupby" in params:
        gb = params["groupby"]
        if isinstance(gb, list):
            columns.extend(gb)
        elif gb:
            columns.append(gb)
    if viz_type == "heatmap":
        if params.get("all_columns_x"):
            columns.append(params["all_columns_x"])
        if params.get("all_columns_y"):
            columns.append(params["all_columns_y"])
    if viz_type == "table" and params.get("all_columns"):
        columns = list(params["all_columns"])
        metrics = []

    query = {
        "filters": params.get("adhoc_filters", []) or [],
        "extras": {"having": "", "where": "",
                   "time_grain_sqla": params.get("time_grain_sqla")},
        "applied_time_extras": {},
        "columns": columns,
        "metrics": metrics,
        "annotation_layers": [],
        "row_limit": params.get("row_limit", 10000),
        "series_limit": 0,
        "order_desc": params.get("order_desc", True),
        "url_params": {},
        "custom_params": {},
        "custom_form_data": {},
    }
    return {
        "datasource": {"id": ds_id, "type": "table"},
        "force": False,
        "queries": [query],
        "form_data": {**params, "viz_type": viz_type,
                      "datasource": f"{ds_id}__table"},
        "result_format": "json",
        "result_type": "full",
    }


def make_chart(api: Superset, name: str, ds_id: int, viz_type: str, params: dict) -> int:
    delete_chart_if_exists(api, name)
    params = {**params, "viz_type": viz_type, "datasource": f"{ds_id}__table"}
    query_context = build_query_context(ds_id, viz_type, params)
    res = api.post("/api/v1/chart/", {
        "slice_name": name,
        "viz_type": viz_type,
        "datasource_id": ds_id,
        "datasource_type": "table",
        "params": json.dumps(params, ensure_ascii=False),
        "query_context": json.dumps(query_context, ensure_ascii=False),
    })
    print(f"  + chart '{name}' (id={res['id']})")
    return res["id"]


def make_dashboard(api: Superset, title: str, chart_ids: list[int]) -> int:
    delete_dashboard_if_exists(api, title)
    res = api.post("/api/v1/dashboard/", {
        "dashboard_title": title,
        "published": True,
    })
    dash_id = res["id"]

    position = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {"id": "ROOT_ID", "type": "ROOT", "children": ["GRID_ID"]},
        "GRID_ID": {"id": "GRID_ID", "type": "GRID", "parents": ["ROOT_ID"], "children": []},
    }
    row_idx = 0
    for i in range(0, len(chart_ids), 2):
        row_id = f"ROW-{row_idx}"
        position["GRID_ID"]["children"].append(row_id)
        position[row_id] = {
            "id": row_id, "type": "ROW",
            "parents": ["ROOT_ID", "GRID_ID"],
            "children": [],
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
        }
        for j, ch_id in enumerate(chart_ids[i:i + 2]):
            chart_node = f"CHART-{ch_id}"
            position[row_id]["children"].append(chart_node)
            position[chart_node] = {
                "id": chart_node, "type": "CHART",
                "parents": ["ROOT_ID", "GRID_ID", row_id],
                "children": [],
                "meta": {
                    "chartId": ch_id,
                    "width": 6,
                    "height": 50,
                    "uuid": f"chart-{ch_id}",
                },
            }
        row_idx += 1

    api.put(f"/api/v1/dashboard/{dash_id}", {
        "position_json": json.dumps(position, ensure_ascii=False),
    })
    for ch_id in chart_ids:
        api.put(f"/api/v1/chart/{ch_id}", {"dashboards": [dash_id]})
    print(f"  + dashboard '{title}' (id={dash_id}, {len(chart_ids)} чартов)")
    return dash_id


def build_charts(api: Superset, ds: dict[str, int]) -> dict[str, int]:
    ch: dict[str, int] = {}

    ch["t1_line"] = make_chart(api, "1. Общая добыча нефти по дням",
        ds["mart_production"], "echarts_timeseries_line", {
            "x_axis": "prod_date",
            "time_grain_sqla": "P1D",
            "metrics": [metric("oil_tons", "SUM")],
            "adhoc_filters": [],
            "row_limit": 10000,
            "show_legend": True,
            "color_scheme": "supersetColors",
        })

    ch["t1_bar"] = make_chart(api, "2. TOP скважин по среднему дебиту",
        ds["mart_production"], "echarts_timeseries_bar", {
            "x_axis": "well_name",
            "metrics": [metric("oil_tons", "AVG")],
            "groupby": [],
            "adhoc_filters": [],
            "row_limit": 50,
            "sort_by_metric": True,
            "color_scheme": "supersetColors",
        })

    ch["t1_heatmap"] = make_chart(api, "3. Heatmap: давление × температура → дебит",
        ds["mart_production"], "heatmap", {
            "all_columns_x": "avg_pressure",
            "all_columns_y": "avg_temperature",
            "metric": metric("oil_tons", "AVG"),
            "adhoc_filters": [],
            "row_limit": 10000,
            "linear_color_scheme": "fire_5",
            "xscale_interval": -1,
            "yscale_interval": -1,
            "canvas_image_rendering": "pixelated",
            "normalize_across": "heatmap",
            "left_margin": "auto",
            "bottom_margin": "auto",
            "y_axis_format": "SMART_NUMBER",
            "show_legend": True,
            "show_perc": True,
            "sort_x_axis": "alpha_asc",
            "sort_y_axis": "alpha_asc",
        })

    ch["t2_actual_pred"] = make_chart(api, "4. Actual vs Predicted",
        ds["mart_forecast"], "echarts_timeseries_line", {
            "x_axis": "date",
            "time_grain_sqla": "P1D",
            "metrics": [
                metric("actual", "AVG", label="actual"),
                metric("predicted", "AVG", label="predicted"),
            ],
            "adhoc_filters": [],
            "row_limit": 10000,
            "show_legend": True,
            "color_scheme": "supersetColors",
        })

    ch["t2_error"] = make_chart(api, "5. Ошибка модели по времени",
        ds["mart_forecast"], "echarts_timeseries_line", {
            "x_axis": "date",
            "time_grain_sqla": "P1D",
            "metrics": [metric("abs_error", "AVG", label="MAE")],
            "adhoc_filters": [],
            "row_limit": 10000,
            "color_scheme": "supersetColors",
        })

    ch["t3_anomalies"] = make_chart(api, "6. Аномалии вибрации по времени",
        ds["mart_failures"], "echarts_timeseries_line", {
            "x_axis": "ts",
            "time_grain_sqla": "P1D",
            "metrics": [metric("is_anomaly_iso", "SUM", label="anomalies")],
            "adhoc_filters": [],
            "row_limit": 10000,
            "color_scheme": "supersetColors",
        })

    ch["t3_vibration"] = make_chart(api, "7. Рост вибрации перед отказом",
        ds["mart_failures"], "echarts_timeseries_line", {
            "x_axis": "ts",
            "time_grain_sqla": "P1D",
            "metrics": [metric("vibration_mm_s", "AVG")],
            "groupby": ["pump_id"],
            "adhoc_filters": [],
            "row_limit": 10000,
            "show_legend": True,
            "color_scheme": "supersetColors",
        })

    ch["t3_risk"] = make_chart(api, "8. Risk Score по насосам",
        ds["mart_pump_risk"], "echarts_timeseries_bar", {
            "x_axis": "pump_id",
            "metrics": [metric("avg_risk_pct", "AVG", label="Risk %")],
            "adhoc_filters": [],
            "row_limit": 50,
            "sort_by_metric": True,
            "color_scheme": "supersetColors",
        })

    ch["t4_delay"] = make_chart(api, "9. Delay vs Weather",
        ds["mart_weather_delay"], "echarts_timeseries_bar", {
            "x_axis": "weather",
            "metrics": [metric("avg_delay", "AVG", label="avg delay, h")],
            "adhoc_filters": [],
            "row_limit": 50,
            "sort_by_metric": True,
            "color_scheme": "supersetColors",
        })

    ch["t4_cost"] = make_chart(api, "10. Cost vs Distance",
        ds["mart_logistics"], "echarts_timeseries_scatter", {
            "x_axis": "distance_km",
            "metrics": [metric("cost_rub", "AVG", label="cost")],
            "groupby": ["weather"],
            "adhoc_filters": [],
            "row_limit": 10000,
            "color_scheme": "supersetColors",
        })

    ch["t4_drivers"] = make_chart(api, "11. KPI по водителям",
        ds["mart_driver_kpi"], "table", {
            "all_columns": ["driver", "trips", "avg_delay",
                            "avg_cost_per_km", "delayed_share"],
            "order_by_cols": ['["avg_delay", false]'],
            "row_limit": 50,
            "table_timestamp_format": "smart_date",
            "adhoc_filters": [],
            "query_mode": "raw",
        })

    return ch


def main() -> None:
    print(f"→ Подключаюсь к Superset: {SUPERSET_URL}")
    api = Superset(SUPERSET_URL, USERNAME, PASSWORD)
    print("  ✓ авторизация прошла")

    print("\n→ Database connection")
    db_id = ensure_database(api)

    print("\n→ Datasets")
    ds = {}
    for table in ["mart_production", "mart_forecast", "mart_forecast_metrics",
                  "mart_failures", "mart_pump_risk",
                  "mart_logistics", "mart_driver_kpi", "mart_weather_delay"]:
        ds[table] = ensure_dataset(api, db_id, table)
        time.sleep(0.2)

    print("\n→ Charts")
    ch = build_charts(api, ds)

    print("\n→ Dashboards")
    make_dashboard(api, "Production Analytics",
                   [ch["t1_line"], ch["t1_bar"], ch["t1_heatmap"]])
    make_dashboard(api, "Forecast",
                   [ch["t2_actual_pred"], ch["t2_error"]])
    make_dashboard(api, "Failures",
                   [ch["t3_anomalies"], ch["t3_vibration"], ch["t3_risk"]])
    make_dashboard(api, "Logistics",
                   [ch["t4_delay"], ch["t4_cost"], ch["t4_drivers"]])

    print("\n✅ Готово. Откройте http://localhost:8088/dashboard/list/")


if __name__ == "__main__":
    main()
