from __future__ import annotations

import json
import pathlib
from typing import Iterable

ROOT = pathlib.Path(__file__).resolve().parent.parent
NB_DIR = ROOT / "notebooks"
NB_DIR.mkdir(exist_ok=True)


def cell_md(src: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": src.splitlines(keepends=True),
    }


def cell_code(src: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": src.splitlines(keepends=True),
    }


def make_nb(cells: Iterable[dict]) -> dict:
    return {
        "cells": list(cells),
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def save(nb: dict, name: str) -> None:
    path = NB_DIR / name
    with path.open("w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
    print(f"  written: {path.relative_to(ROOT)}")


BOILERPLATE = """\
import sys, os
sys.path.insert(0, '/home/jovyan/work/etl')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from io_utils import read_table, write_mart, write_mart_to_pg, pg_engine

pd.set_option('display.max_columns', 50)
plt.rcParams['figure.figsize'] = (12, 5)
sns.set_theme(style='whitegrid')
"""

nb1 = make_nb([
    cell_md("# Задание 1. Аналитика добычи"),
    cell_code(BOILERPLATE),
    cell_md("## Загрузка"),
    cell_code("""\
wells       = read_table('wells')
production  = read_table('production')
telemetry   = read_table('telemetry')

print('wells     :', wells.shape)
print('production:', production.shape)
print('telemetry :', telemetry.shape)
wells.head()
"""),
    cell_md("## NULL %"),
    cell_code("""\
def null_pct(df):
    return (df.isna().mean() * 100).round(2).sort_values(ascending=False)

print('production:'); print(null_pct(production)); print()
print('telemetry :'); print(null_pct(telemetry))
"""),
    cell_md("## Очистка"),
    cell_code("""\
prod = production.copy()
prod['oil_tons']   = prod.groupby('well_id')['oil_tons'].transform(lambda s: s.fillna(s.median()))
prod['water_tons'] = prod.groupby('well_id')['water_tons'].transform(lambda s: s.fillna(s.median()))

tel = telemetry.copy()
tel['pressure_bar'] = tel.groupby('well_id')['pressure_bar'].transform(lambda s: s.fillna(s.median()))

q1, q3 = tel['pressure_bar'].quantile([0.25, 0.75])
iqr = q3 - q1
lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
before = len(tel)
tel = tel[(tel['pressure_bar'] >= lo) & (tel['pressure_bar'] <= hi)]
print(f'Удалено выбросов: {before - len(tel)} строк ({(before-len(tel))/before:.1%})')
"""),
    cell_md("## Добыча по дням"),
    cell_code("""\
daily_production = (
    prod.groupby('prod_date', as_index=False)
        .agg(total_oil_tons=('oil_tons', 'sum'),
             total_gas_m3=('gas_m3', 'sum'),
             total_water_tons=('water_tons', 'sum'),
             active_wells=('well_id', 'nunique'))
        .sort_values('prod_date')
)
daily_production['prod_date'] = pd.to_datetime(daily_production['prod_date'])
daily_production.head()
"""),
    cell_code("""\
ax = daily_production.plot(x='prod_date', y='total_oil_tons', legend=False, color='#c0392b')
ax.set_title('Общая добыча нефти по дням', fontsize=14)
ax.set_ylabel('тонн / сутки'); ax.set_xlabel('Дата')
plt.tight_layout(); plt.show()
"""),
    cell_md("## KPI по скважинам"),
    cell_code("""\
kpi = (
    prod.groupby('well_id', as_index=False)
        .agg(avg_oil_tons=('oil_tons', 'mean'),
             total_oil_tons=('oil_tons', 'sum'),
             avg_downtime=('downtime_hours', 'mean'),
             days=('prod_date', 'count'))
)
kpi['downtime_pct'] = (kpi['avg_downtime'] / 24 * 100).round(2)
kpi['avg_oil_tons'] = kpi['avg_oil_tons'].round(2)
kpi = kpi.merge(wells[['well_id', 'well_name', 'field_name', 'well_type']], on='well_id')

best  = kpi.nlargest(3, 'avg_oil_tons')[['well_name', 'field_name', 'avg_oil_tons', 'downtime_pct']]
worst = kpi.nsmallest(3, 'avg_oil_tons')[['well_name', 'field_name', 'avg_oil_tons', 'downtime_pct']]
print('TOP-3:'); print(best.to_string(index=False))
print('\\nBOTTOM-3:'); print(worst.to_string(index=False))
kpi
"""),
    cell_code("""\
plot_df = kpi.sort_values('avg_oil_tons', ascending=False)
ax = sns.barplot(data=plot_df, x='well_name', y='avg_oil_tons',
                 hue='field_name', dodge=False)
ax.set_title('Средний суточный дебит по скважинам')
ax.set_ylabel('тонн/сут'); ax.set_xlabel('Скважина')
plt.tight_layout(); plt.show()
"""),
    cell_md("## Влияние давления и температуры"),
    cell_code("""\
tel['date'] = pd.to_datetime(tel['ts']).dt.date
tel_daily = (
    tel.groupby(['well_id', 'date'], as_index=False)
       .agg(avg_pressure=('pressure_bar', 'mean'),
            avg_temperature=('temperature_c', 'mean'),
            avg_power=('power_kw', 'mean'),
            sum_pump_hours=('pump_hours', 'sum'))
)
tel_daily['date'] = pd.to_datetime(tel_daily['date'])
prod['prod_date'] = pd.to_datetime(prod['prod_date'])

mart_production = (
    prod.merge(tel_daily, left_on=['well_id', 'prod_date'], right_on=['well_id', 'date'])
        .merge(wells[['well_id', 'well_name', 'field_name', 'region', 'well_type']], on='well_id')
        .drop(columns=['date'])
)
mart_production['downtime_pct'] = (mart_production['downtime_hours'] / 24 * 100).round(2)
mart_production.head()
"""),
    cell_code("""\
corr = mart_production[['oil_tons', 'avg_pressure', 'avg_temperature', 'avg_power', 'downtime_hours']].corr()
sns.heatmap(corr, annot=True, cmap='RdBu_r', center=0, fmt='.2f')
plt.title('Корреляции'); plt.tight_layout(); plt.show()
"""),
    cell_code("""\
plot_df = mart_production.copy()
plot_df['pressure_bin'] = pd.cut(plot_df['avg_pressure'], bins=8)
plot_df['temp_bin']     = pd.cut(plot_df['avg_temperature'], bins=8)
pivot = plot_df.pivot_table(index='temp_bin', columns='pressure_bin',
                            values='oil_tons', aggfunc='mean', observed=True)
sns.heatmap(pivot, cmap='YlOrRd', annot=False)
plt.title('Дебит: температура × давление'); plt.tight_layout(); plt.show()
"""),
    cell_md("## Сохранение витрины"),
    cell_code("""\
uri = write_mart(mart_production, 'mart_production')
write_mart_to_pg(mart_production, 'mart_production')
print('Saved:', uri)
"""),
])
save(nb1, "01_production_analytics.ipynb")

nb2 = make_nb([
    cell_md("# Задание 2. Прогноз дебита (ML)"),
    cell_code(BOILERPLATE + """
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
"""),
    cell_md("## Датасет"),
    cell_code("""\
telemetry    = read_table('telemetry')
well_targets = read_table('well_targets')
wells        = read_table('wells')

telemetry['date'] = pd.to_datetime(telemetry['ts']).dt.date
features = (
    telemetry.groupby(['well_id', 'date'], as_index=False)
             .agg(avg_pressure=('pressure_bar', 'mean'),
                  avg_temperature=('temperature_c', 'mean'),
                  avg_power=('power_kw', 'mean'),
                  sum_pump_hours=('pump_hours', 'sum'))
)
features['date'] = pd.to_datetime(features['date'])
well_targets['target_date'] = pd.to_datetime(well_targets['target_date'])

dataset = (
    features.merge(well_targets,
                   left_on=['well_id', 'date'],
                   right_on=['well_id', 'target_date'])
            .merge(wells[['well_id', 'well_type']], on='well_id')
)
dataset = pd.get_dummies(dataset, columns=['well_type'], drop_first=True)
dataset = dataset.dropna()
print('dataset:', dataset.shape)
dataset.head()
"""),
    cell_md("## Train/test"),
    cell_code("""\
feature_cols = ['avg_pressure', 'avg_temperature', 'avg_power', 'sum_pump_hours'] + \\
               [c for c in dataset.columns if c.startswith('well_type_')]
X = dataset[feature_cols]
y = dataset['daily_oil_tons']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print(f'train: {X_train.shape}  test: {X_test.shape}')
"""),
    cell_md("## Обучение"),
    cell_code("""\
def score(name, model, X_tr, y_tr, X_te, y_te):
    model.fit(X_tr, y_tr)
    pred = model.predict(X_te)
    mae  = mean_absolute_error(y_te, pred)
    rmse = np.sqrt(mean_squared_error(y_te, pred))
    r2   = r2_score(y_te, pred)
    print(f'{name:18s}  MAE={mae:.2f}  RMSE={rmse:.2f}  R²={r2:.3f}')
    return model, pred, dict(model=name, mae=mae, rmse=rmse, r2=r2)

lr_model, lr_pred, lr_metrics = score('LinearRegression',
                                      LinearRegression(),
                                      X_train, y_train, X_test, y_test)
rf_model, rf_pred, rf_metrics = score('RandomForest',
                                      RandomForestRegressor(n_estimators=200,
                                                            max_depth=10,
                                                            random_state=42,
                                                            n_jobs=-1),
                                      X_train, y_train, X_test, y_test)

metrics_df = pd.DataFrame([lr_metrics, rf_metrics])
metrics_df
"""),
    cell_md("## Важность признаков"),
    cell_code("""\
fi = pd.DataFrame({
    'feature': feature_cols,
    'importance': rf_model.feature_importances_
}).sort_values('importance', ascending=False)

sns.barplot(data=fi, x='importance', y='feature', color='#2980b9')
plt.title('Важность признаков (RandomForest)'); plt.tight_layout(); plt.show()
fi
"""),
    cell_md("## Actual vs Predicted"),
    cell_code("""\
plot_df = X_test.copy()
plot_df['date']      = dataset.loc[X_test.index, 'target_date'].values
plot_df['well_id']   = dataset.loc[X_test.index, 'well_id'].values
plot_df['actual']    = y_test.values
plot_df['predicted'] = rf_pred
plot_df['error']     = plot_df['actual'] - plot_df['predicted']

fig, ax = plt.subplots(figsize=(7, 7))
ax.scatter(plot_df['actual'], plot_df['predicted'], alpha=0.5, s=20)
lims = [plot_df[['actual', 'predicted']].min().min(),
        plot_df[['actual', 'predicted']].max().max()]
ax.plot(lims, lims, 'r--')
ax.set_xlabel('Actual'); ax.set_ylabel('Predicted')
ax.set_title('Actual vs Predicted (RandomForest)')
plt.tight_layout(); plt.show()
"""),
    cell_code("""\
err_by_day = (plot_df.groupby('date', as_index=False)
                     .agg(mae=('error', lambda x: np.abs(x).mean())))
ax = err_by_day.plot(x='date', y='mae', legend=False, color='#8e44ad')
ax.set_title('MAE по дням'); ax.set_ylabel('тонн/сут'); plt.tight_layout(); plt.show()
"""),
    cell_md("## Сохранение"),
    cell_code("""\
mart_forecast = plot_df[['date', 'well_id', 'actual', 'predicted', 'error']].copy()
mart_forecast['abs_error'] = mart_forecast['error'].abs()
uri = write_mart(mart_forecast, 'mart_forecast')
write_mart_to_pg(mart_forecast, 'mart_forecast')
write_mart_to_pg(metrics_df, 'mart_forecast_metrics')
print('Saved:', uri)
mart_forecast.head()
"""),
])
save(nb2, "02_ml_forecast.ipynb")

nb3 = make_nb([
    cell_md("# Задание 3. Аномалии и отказы насосов"),
    cell_code(BOILERPLATE + """
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
"""),
    cell_md("## Загрузка"),
    cell_code("""\
pump_sensors  = read_table('pump_sensors')
pump_failures = read_table('pump_failures')
pump_sensors['ts'] = pd.to_datetime(pump_sensors['ts'])
pump_failures['failure_ts'] = pd.to_datetime(pump_failures['failure_ts'])
print('sensors :', pump_sensors.shape)
print('failures:', pump_failures.shape)
pump_failures
"""),
    cell_md("## z-score"),
    cell_code("""\
df = pump_sensors.copy()
for col in ['vibration_mm_s', 'temperature_c', 'current_a']:
    grp = df.groupby('pump_id')[col]
    df[f'{col}_z'] = (df[col] - grp.transform('mean')) / grp.transform('std')

df['is_anomaly_z'] = (df[['vibration_mm_s_z', 'temperature_c_z', 'current_a_z']]
                      .abs() > 3).any(axis=1).astype(int)
print('Доля по z-score:', df['is_anomaly_z'].mean().round(4))
"""),
    cell_md("## Isolation Forest"),
    cell_code("""\
iso = IsolationForest(contamination=0.02, random_state=42)
df['is_anomaly_iso'] = (iso.fit_predict(
    df[['vibration_mm_s', 'temperature_c', 'current_a', 'rpm']]
) == -1).astype(int)
print('Доля по IsolationForest:', df['is_anomaly_iso'].mean().round(4))
"""),
    cell_code("""\
fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
for pid in sorted(df['pump_id'].unique())[:3]:
    sub = df[df['pump_id'] == pid].sort_values('ts')
    axes[0].plot(sub['ts'], sub['vibration_mm_s'], label=f'pump {pid}', alpha=0.7)
    anom = sub[sub['is_anomaly_iso'] == 1]
    axes[0].scatter(anom['ts'], anom['vibration_mm_s'], color='red', s=15, zorder=5)
axes[0].set_title('Вибрация и аномалии'); axes[0].legend()

for _, f in pump_failures.iterrows():
    axes[0].axvline(f['failure_ts'], color='black', linestyle='--', alpha=0.5)
    axes[1].axvline(f['failure_ts'], color='black', linestyle='--', alpha=0.5)

for pid in sorted(df['pump_id'].unique())[:3]:
    sub = df[df['pump_id'] == pid].sort_values('ts')
    axes[1].plot(sub['ts'], sub['temperature_c'], label=f'pump {pid}', alpha=0.7)
axes[1].set_title('Температура; пунктир — отказы'); axes[1].legend()
plt.tight_layout(); plt.show()
"""),
    cell_md("## Метка failure_soon"),
    cell_code("""\
df['failure_soon'] = 0
for _, f in pump_failures.iterrows():
    mask = ((df['pump_id'] == f['pump_id'])
            & (df['ts'] >= f['failure_ts'] - pd.Timedelta(hours=24))
            & (df['ts'] < f['failure_ts']))
    df.loc[mask, 'failure_soon'] = 1
print('Положительный класс:', df['failure_soon'].sum(),
      f"({df['failure_soon'].mean():.3%})")
"""),
    cell_md("## Сравнение признаков"),
    cell_code("""\
agg = df.groupby('failure_soon')[['vibration_mm_s', 'temperature_c', 'current_a', 'rpm']].mean()
agg.index = ['обычно', 'перед отказом']
agg.round(2)
"""),
    cell_md("## Модель"),
    cell_code("""\
feature_cols = ['vibration_mm_s', 'temperature_c', 'current_a', 'rpm',
                'vibration_mm_s_z', 'temperature_c_z', 'current_a_z']
X = df[feature_cols].fillna(0)
y = df['failure_soon']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)

clf = RandomForestClassifier(
    n_estimators=300, max_depth=10, class_weight='balanced',
    random_state=42, n_jobs=-1
)
clf.fit(X_train, y_train)

proba_test = clf.predict_proba(X_test)[:, 1]
pred_test  = clf.predict(X_test)
print(classification_report(y_test, pred_test, digits=3))
print('ROC-AUC:', round(roc_auc_score(y_test, proba_test), 3))
"""),
    cell_md("## Risk score"),
    cell_code("""\
df['risk_score'] = clf.predict_proba(df[feature_cols].fillna(0))[:, 1]

last_day = df['ts'].max() - pd.Timedelta(days=1)
risk_now = (df[df['ts'] >= last_day]
            .groupby('pump_id', as_index=False)
            .agg(avg_risk=('risk_score', 'mean'),
                 max_vibration=('vibration_mm_s', 'max')))
risk_now['avg_risk_pct'] = (risk_now['avg_risk'] * 100).round(1)
risk_now.sort_values('avg_risk', ascending=False)
"""),
    cell_md("## Сохранение"),
    cell_code("""\
mart_failures = df[['ts', 'pump_id', 'vibration_mm_s', 'temperature_c',
                    'current_a', 'rpm',
                    'is_anomaly_z', 'is_anomaly_iso',
                    'failure_soon', 'risk_score']].copy()

write_mart(mart_failures.head(50000), 'mart_failures')
write_mart_to_pg(mart_failures, 'mart_failures')
write_mart_to_pg(risk_now, 'mart_pump_risk')
print('Saved')
"""),
])
save(nb3, "03_anomaly_detection.ipynb")

nb4 = make_nb([
    cell_md("# Задание 4. Логистика и поставки"),
    cell_code(BOILERPLATE),
    cell_md("## Загрузка"),
    cell_code("""\
deliveries = read_table('deliveries')
deliveries['delivery_date'] = pd.to_datetime(deliveries['delivery_date'])
print(deliveries.shape)
print('NULL:'); print(deliveries.isna().sum())
deliveries.head()
"""),
    cell_md("## Фичи"),
    cell_code("""\
df = deliveries.copy()
df = df[df['distance_km'] > 0]
df['cost_per_km']  = (df['cost_rub'] / df['distance_km']).round(2)
df['cost_per_ton'] = (df['cost_rub'] / df['volume_tons']).round(2)
df['route']        = df['route_from'] + ' → ' + df['route_to']
df['is_delayed']   = (df['delay_hours'] > 2).astype(int)
df.head()
"""),
    cell_md("## Влияние погоды"),
    cell_code("""\
weather_stats = (
    df.groupby('weather', as_index=False)
      .agg(avg_delay=('delay_hours', 'mean'),
           delayed_pct=('is_delayed', 'mean'),
           count=('delivery_id', 'count'))
)
weather_stats['delayed_pct'] = (weather_stats['delayed_pct'] * 100).round(1)
weather_stats['avg_delay']   = weather_stats['avg_delay'].round(2)
weather_stats.sort_values('avg_delay', ascending=False)
"""),
    cell_code("""\
sns.barplot(data=weather_stats, x='weather', y='avg_delay',
            order=weather_stats.sort_values('avg_delay')['weather'])
plt.title('Среднее время задержки по погоде')
plt.ylabel('часы'); plt.tight_layout(); plt.show()
"""),
    cell_md("## Cost vs Distance"),
    cell_code("""\
sns.scatterplot(data=df, x='distance_km', y='cost_rub', hue='weather', alpha=0.6, s=18)
plt.title('Стоимость vs расстояние'); plt.tight_layout(); plt.show()

corr = df[['distance_km', 'volume_tons', 'cost_rub', 'delay_hours']].corr()
sns.heatmap(corr, annot=True, cmap='RdBu_r', center=0)
plt.title('Корреляции'); plt.tight_layout(); plt.show()
"""),
    cell_md("## KPI водителей"),
    cell_code("""\
driver_kpi = (
    df.groupby('driver', as_index=False)
      .agg(trips=('delivery_id', 'count'),
           avg_delay=('delay_hours', 'mean'),
           avg_cost_per_km=('cost_per_km', 'mean'),
           total_volume=('volume_tons', 'sum'),
           delayed_share=('is_delayed', 'mean'))
)
driver_kpi['delayed_share']  = (driver_kpi['delayed_share'] * 100).round(1)
driver_kpi['avg_delay']      = driver_kpi['avg_delay'].round(2)
driver_kpi['avg_cost_per_km']= driver_kpi['avg_cost_per_km'].round(2)
driver_kpi.sort_values('avg_delay')
"""),
    cell_md("## Маршруты"),
    cell_code("""\
route_stats = (
    df.groupby('route', as_index=False)
      .agg(trips=('delivery_id', 'count'),
           avg_cost_per_km=('cost_per_km', 'mean'),
           avg_delay=('delay_hours', 'mean'),
           total_cost=('cost_rub', 'sum'))
      .sort_values('avg_cost_per_km', ascending=False)
)
route_stats.head(10)
"""),
    cell_md("## Сохранение"),
    cell_code("""\
mart_logistics = df[['delivery_date', 'route', 'route_from', 'route_to',
                     'distance_km', 'volume_tons', 'cost_rub',
                     'cost_per_km', 'cost_per_ton',
                     'delay_hours', 'is_delayed', 'weather', 'driver']].copy()

write_mart(mart_logistics, 'mart_logistics')
write_mart_to_pg(mart_logistics, 'mart_logistics')
write_mart_to_pg(driver_kpi,    'mart_driver_kpi')
write_mart_to_pg(weather_stats, 'mart_weather_delay')
print('Saved')
"""),
])
save(nb4, "04_logistics.ipynb")

print('Готово.')
