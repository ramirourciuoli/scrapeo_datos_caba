# app.py
from __future__ import annotations

from flask import Flask, jsonify, request, send_from_directory

import api_datos_catastrales as adc
from api_datos_utiles import consultar_datos_utiles

# Módulo nuevo (Procesos Geográficos USIG)
# Debe existir como api_procesos_geograficos.py en la misma carpeta
import api_procesos_geograficos as pg

app = Flask(__name__)


@app.get("/")
def home():
    """
    Sirve el HTML desde la carpeta actual.
    Acepta 'index.html' o 'Index.html' para evitar problemas de mayúsculas.
    """
    try:
        return send_from_directory(".", "index.html")
    except Exception:
        return send_from_directory(".", "Index.html")


@app.get("/health")
def health():
    return jsonify({"ok": True})


@app.post("/api/catastro")
def api_catastro():
    """
    Body JSON esperado:
      { "direccion": "Davila 1130, CABA" }

    Devuelve:
      - smp
      - parcela (catastro/parcela?smp=...)
      - geometria (catastro/geometria?smp=...&srid=97433)
      - area_m2
      - centroide_xy (en SRID interno 97433)
      - centroide_lonlat (WGS84) usando Procesos Geográficos
      - datos_utiles (por calle/altura)
      - debug (opcional, útil para desarrollo)
    """
    payload = request.get_json(force=True, silent=True) or {}
    address = (payload.get("direccion") or payload.get("address") or "").strip()

    if not address:
        return jsonify({"ok": False, "error": "Falta 'direccion'"}), 400

    dbg: dict = {"address": address}

    try:
        # 1) Resolver SMP y traer debug (incluye dirección elegida de USIG)
        smp, resolver_dbg = adc.resolve_smp_from_address(address)
        if isinstance(resolver_dbg, dict):
            dbg.update(resolver_dbg)

        if not smp:
            return jsonify({
                "ok": False,
                "error": "No pude resolver SMP desde la dirección.",
                "debug": dbg
            }), 404

        # 2) Traer parcela + geometría por SMP (Catastro)
        parcela = adc.catastro_parcela_by_smp(smp)
        geometria = adc.catastro_geometria_by_smp(smp)

        # 3) Área m² desde geometría (si tu geojson_area_m2 está bien)
        try:
            area_m2 = adc.geojson_area_m2(geometria)
        except Exception as e:
            area_m2 = 0
            dbg["area_error"] = str(e)

        # 4) Centroide XY desde geometría (SRID interno 97433)
        cx = cy = None
        try:
            # Si agregaste estas funciones en api_datos_catastrales.py
            cx, cy = adc.geojson_centroid_xy(geometria)
        except Exception as e:
            dbg["centroide_xy_error"] = str(e)

        centroide_xy = {"x": cx, "y": cy} if (cx is not None and cy is not None) else None

        # 5) Centroide lon/lat (WGS84) usando Procesos Geográficos (USIG)
        centroide_lonlat = None
        try:
            if cx is not None and cy is not None:
                lon, lat = pg.gkba_a_lonlat(float(cx), float(cy))
                centroide_lonlat = {"lon": lon, "lat": lat}
        except Exception as e:
            dbg["procesos_geograficos_error"] = str(e)

        # 6) Datos Útiles (por calle/altura) usando tu api_datos_utiles.py
        datos_utiles = None
        try:
            d = (dbg.get("usig_direccion_elegida") or {})
            calle = d.get("nombre_calle") or d.get("calle")
            altura = d.get("altura") or d.get("puerta")
            if calle and altura:
                datos_utiles = consultar_datos_utiles(str(calle), int(altura))
        except Exception as e:
            dbg["datos_utiles_error"] = str(e)

        return jsonify({
            "ok": True,
            "input": address,
            "smp": smp,
            "parcela": parcela,
            "geometria": geometria,
            "area_m2": area_m2,
            "centroide_xy": centroide_xy,
            "centroide_lonlat": centroide_lonlat,
            "datos_utiles": datos_utiles,
            "debug": dbg,   # en producción lo apagamos o lo hacemos opcional
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "debug": dbg}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)