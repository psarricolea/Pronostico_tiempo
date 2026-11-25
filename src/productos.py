"""Lee el GRIB, recorta Chile y genera meteogramas, mapas y JSON."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import BoundaryNorm, ListedColormap

import config

def _r1(x):
    """Redondea a 1 decimal como float de Python (None si es NaN), apto para JSON."""
    x = float(x)
    return None if np.isnan(x) else round(x, 1)


def _json_np(o):
    """Convierte tipos numpy/pandas que json no sabe serializar."""
    if isinstance(o, np.generic):
        v = o.item()
        return None if isinstance(v, float) and np.isnan(v) else v
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (pd.Timestamp, np.datetime64)):
        return str(o)
    return str(o)


TZ = config.ZONA_HORARIA
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def _eje_dias(x, pos=None):
    d = mdates.num2date(x, tz=TZ)
    return f"{DIAS[d.weekday()][:3]} {d.day}"


# ---------------------------------------------------------------- lectura
def leer_grib(ruta: Path) -> xr.Dataset:
    """Abre el GRIB multivariable y devuelve un Dataset recortado a Chile.

    Variables de salida: t2m (°C), tp (mm acumulados desde el inicio),
    viento (km/h), msl (hPa). Dimensión temporal: 'tiempo' (UTC).
    """
    import cfgrib

    partes = cfgrib.open_datasets(str(ruta), backend_kwargs={"indexpath": ""})
    ds = xr.merge([p.drop_vars(["heightAboveGround", "surface", "meanSea"], errors="ignore")
                   for p in partes], compat="override")
    return preparar(ds)


def preparar(ds: xr.Dataset) -> xr.Dataset:
    # Longitudes a -180..180 si vienen en 0..360
    if float(ds.longitude.max()) > 180:
        ds = ds.assign_coords(longitude=((ds.longitude + 180) % 360) - 180).sortby("longitude")
    lat_desc = bool(ds.latitude[0] > ds.latitude[-1])
    lat_sl = slice(config.LAT_N, config.LAT_S) if lat_desc else slice(config.LAT_S, config.LAT_N)
    ds = ds.sel(latitude=lat_sl, longitude=slice(config.LON_W, config.LON_E))

    tiempo = pd.to_datetime(ds["valid_time"].values)
    out = xr.Dataset(
        {
            "t2m": ds["t2m"] - 273.15,
            "tp": (ds["tp"] * 1000.0).clip(min=0),
            "viento": np.hypot(ds["u10"], ds["v10"]) * 3.6,
            "msl": ds["msl"] / 100.0,
        }
    ).assign_coords(step=tiempo).rename(step="tiempo")
    out = out.drop_vars(["time", "valid_time", "number"], errors="ignore")
    return out.load()


# ---------------------------------------------------------- meteogramas
def serie_ciudad(ds, lat, lon) -> pd.DataFrame:
    p = ds.sel(latitude=lat, longitude=lon, method="nearest")
    df = pd.DataFrame(
        {
            "t2m": p["t2m"].values,
            "tp_acum": p["tp"].values,
            "viento": p["viento"].values,
            "msl": p["msl"].values,
        },
        index=pd.DatetimeIndex(p["tiempo"].values).tz_localize("UTC").tz_convert(TZ),
    )
    df["pp"] = df["tp_acum"].diff().clip(lower=0).fillna(0)  # mm en el intervalo
    df.attrs["punto"] = (float(p.latitude), float(p.longitude))
    return df


def meteograma(nombre, df, info, carpeta: Path):
    fig, axs = plt.subplots(3, 1, figsize=(10, 7.2), sharex=True,
                            gridspec_kw={"height_ratios": [1.3, 1, 1]})
    ax = axs[0]
    ax.plot(df.index, df["t2m"], color="#c0392b", lw=1.8)
    ax.set_ylabel("Temperatura 2 m (°C)")
    ax.grid(alpha=0.3)
    diaria = df["t2m"].resample("D").agg(["max", "min"])
    for d, r in diaria.iterrows():
        mid = d + pd.Timedelta(hours=12)
        if df.index[0] <= mid <= df.index[-1]:
            ax.annotate(f"{r['max']:.0f}°/{r['min']:.0f}°", (mid, ax.get_ylim()[1]),
                        ha="center", va="top", fontsize=8, color="#555")

    ax = axs[1]
    ancho = np.r_[np.diff(df.index.values), np.timedelta64(6, "h")]
    ax.bar(df.index - ancho, df["pp"], width=ancho, align="edge",
           color="#2471a3", alpha=0.85)
    ax.set_ylabel("Precipitación (mm/intervalo)")
    ax.set_ylim(0, max(2, df["pp"].max() * 1.2))
    ax2 = ax.twinx()
    ax2.plot(df.index, df["tp_acum"], color="#1b4f72", lw=1, ls="--")
    ax2.set_ylabel("Acumulada (mm)", fontsize=8)
    ax.grid(alpha=0.3)

    ax = axs[2]
    ax.plot(df.index, df["viento"], color="#117a65", lw=1.5)
    ax.set_ylabel("Viento 10 m (km/h)")
    ax.grid(alpha=0.3)
    ax3 = ax.twinx()
    ax3.plot(df.index, df["msl"], color="#7d3c98", lw=1, alpha=0.7)
    ax3.set_ylabel("PNM (hPa)", fontsize=8, color="#7d3c98")

    axs[-1].xaxis.set_major_locator(mdates.DayLocator(tz=df.index.tz))
    axs[-1].xaxis.set_major_formatter(plt.FuncFormatter(_eje_dias))
    lat, lon = df.attrs["punto"]
    fig.suptitle(f"{nombre} — ECMWF IFS {info['resolucion']}°  |  corrida "
                 f"{pd.Timestamp(info['corrida']):%d-%m-%Y %Hz}", fontsize=11)
    fig.text(0.01, 0.005, f"Punto de grilla {lat:.2f}, {lon:.2f}  ·  Hora de Chile  ·  "
             "Datos: ECMWF Open Data (CC-BY-4.0)", fontsize=7, color="#666")
    fig.tight_layout(rect=(0, 0.02, 1, 0.97))
    fig.savefig(carpeta / f"meteograma_{slug(nombre)}.png", dpi=110)
    plt.close(fig)


# ---------------------------------------------------------------- mapas
def ventanas_diarias(tiempos: pd.DatetimeIndex):
    """Pares (inicio, fin) de 06 UTC a 06 UTC disponibles en el pronóstico."""
    cortes = [t for t in tiempos if t.hour == config.HORA_CORTE_UTC]
    return list(zip(cortes[:-1], cortes[1:]))[: config.DIAS_MAPA]


def _mapa_base(ax):
    try:
        import cartopy.feature as cf
        costa, borde = cf.COASTLINE.with_scale("50m"), cf.BORDERS.with_scale("50m")
        next(iter(costa.geometries()))  # fuerza la descarga ahora, no al guardar
        ax.add_feature(costa, lw=0.6)
        ax.add_feature(borde, lw=0.4, ls=":")
    except Exception as e:  # sin red para Natural Earth
        print(f"[mapas] sin costas: {e}")
    ax.set_extent([config.LON_W, config.LON_E, config.LAT_S, config.LAT_N])


def mapas_diarios(ds, info, carpeta: Path) -> list:
    import cartopy.crs as ccrs

    tiempos = pd.DatetimeIndex(ds["tiempo"].values)
    niveles_pp = [0.5, 1, 2, 5, 10, 20, 30, 50, 75, 100, 150]
    cmap_pp = ListedColormap(["#d6eaf8", "#aed6f1", "#85c1e9", "#5dade2", "#2e86c1",
                              "#1b4f72", "#7d3c98", "#a569bd", "#e74c3c", "#922b21"])
    norm_pp = BoundaryNorm(niveles_pp, cmap_pp.N)
    niveles_t = np.arange(-10, 41, 2)

    salida = []
    for i, (a, b) in enumerate(ventanas_diarias(tiempos), start=1):
        pp = ds["tp"].sel(tiempo=b) - ds["tp"].sel(tiempo=a)
        tsel = ds["t2m"].sel(tiempo=slice(a, b))
        tmax = tsel.max("tiempo")
        dia_local = (a.tz_localize("UTC").tz_convert(TZ) + pd.Timedelta(hours=3)).date()

        fig, axs = plt.subplots(1, 2, figsize=(7.5, 10),
                                subplot_kw={"projection": ccrs.PlateCarree()})
        m = axs[0].pcolormesh(ds.longitude, ds.latitude, pp.where(pp >= 0.5),
                              cmap=cmap_pp, norm=norm_pp, shading="auto")
        _mapa_base(axs[0])
        axs[0].set_title("Precipitación diaria (mm)", fontsize=9)
        fig.colorbar(m, ax=axs[0], shrink=0.6, pad=0.02)

        m = axs[1].contourf(ds.longitude, ds.latitude, tmax, levels=niveles_t,
                            cmap="RdYlBu_r", extend="both")
        _mapa_base(axs[1])
        axs[1].set_title("T máx. 2 m (°C)*", fontsize=9)
        fig.colorbar(m, ax=axs[1], shrink=0.6, pad=0.02)

        fig.suptitle(f"Día {i}: {DIAS[dia_local.weekday()]} {dia_local:%d-%m-%Y}\nECMWF IFS {info['resolucion']}° — "
                     f"corrida {pd.Timestamp(info['corrida']):%d-%m %Hz}", fontsize=10)
        fig.text(0.02, 0.01, "*Máximo entre salidas de 3/6 h (subestima levemente el máximo real). "
                 "Día = 03 a 03 h de Chile.\nDatos: ECMWF Open Data (CC-BY-4.0)",
                 fontsize=6.5, color="#666")
        nombre = f"mapa_dia{i}.png"
        fig.savefig(carpeta / nombre, dpi=100, bbox_inches="tight")
        plt.close(fig)
        salida.append({"dia": i, "fecha": str(dia_local), "archivo": nombre})
    return salida


# ---------------------------------------------------------------- todo
def slug(s):
    import unicodedata
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return s.lower().replace(" ", "-")


def generar(ds, info, carpeta: Path):
    carpeta.mkdir(parents=True, exist_ok=True)
    ciudades = []
    for nombre, (lat, lon) in config.CIUDADES.items():
        df = serie_ciudad(ds, lat, lon)
        meteograma(nombre, df, info, carpeta)
        diaria = df.resample("D").agg({"t2m": ["max", "min"], "pp": "sum"})
        diaria.columns = ["tmax", "tmin", "pp"]
        ciudades.append({
            "nombre": nombre,
            "slug": slug(nombre),
            "imagen": f"meteograma_{slug(nombre)}.png",
            "diario": [{"fecha": str(d.date()), "tmax": _r1(r.tmax),
                        "tmin": _r1(r.tmin), "pp": _r1(r.pp)}
                       for d, r in diaria.iterrows()],
        })
    mapas = mapas_diarios(ds, info, carpeta)
    meta = {**info, "generado": pd.Timestamp.now(tz=TZ).isoformat(timespec="minutes"),
            "ciudades": ciudades, "mapas": mapas}
    (carpeta / "pronostico.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=1, default=_json_np))
    return meta
