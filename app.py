"""app.py

Backend local (Flask) para tu interfaz web.

Qué hace:
- Sirve el frontend (index.html) en GET /
- Expone POST /api/catastro: recibe una dirección en texto, resuelve SMP usando lógica de
  api_datos_catastrales.py y devuelve:
    - SMP
    - Parcela (catastro/parcela)
    - Geometría (catastro/geometria)
    - Área en m² (calculada desde GeoJSON, sin shapely)

Requisitos:
  pip install flask requests

Estructura esperada de carpeta:
  PrefactibilidadWeb/
    app.py
    index.html
    api_datos_catastrales.py

Ejecución:
  python app.py
  Abrir: http://127.0.0.1:8000/
"""

from __future__ import annotations

from flask import Flask, jsonify, request, send_from_directory

# Importamos tu “motor” de catastro (tu script actual, renombrado a módulo)
# IMPORTANTE: api_datos_catastrales.py debe estar en la misma carpeta.
import api_datos_catastrales as adc

app = Flask(__name__)


@app.get("/")
def home():
    """Sirve el archivo index.html desde la carpeta actual."""
    return send_from_directory(".", "index.html")


@app.get("/health")
def health():
    """Chequeo rápido para saber si el server está vivo."""
    return jsonify({"ok": True})


@app.post("/api/catastro")
def api_catastro():
    """Recibe {"direccion": "..."} y devuelve datos de Catastro + geometría + área."""
    payload = request.get_json(force=True, silent=True) or {}
    address = (payload.get("direccion") or "").strip()

    if not address:
        return jsonify({"ok": False, "error": "Falta 'direccion'"}), 400

    try:
        # 1) Resolver SMP desde la dirección (usa tu lógica actual)
        smp, dbg = adc.resolve_smp_from_address(address)

        if not smp:
            return jsonify({
                "ok": False,
                "error": "No pude resolver SMP desde la dirección.",
                "debug": dbg,
            }), 404

        # 2) Traer parcela y geometría por SMP
        parcela = adc.catastro_parcela_by_smp(smp)
        geometria = adc.catastro_geometria_by_smp(smp)

        # 3) Calcular área (m²) desde la geometría (GeoJSON) — sin shapely
        try:
            area_m2 = adc.geojson_area_m2(geometria)
        except Exception as e:
            area_m2 = None
            dbg["area_error"] = str(e)

        return jsonify({
            "ok": True,
            "input": address,
            "smp": smp,
            "parcela": parcela,
            "geometria": geometria,
            "area_m2": area_m2,
            # útil en etapa de pruebas (podés apagarlo después)
            "debug": dbg,
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    # Nota: debug=True es solo para desarrollo
    app.run(host="127.0.0.1", port=8000, debug=True)
