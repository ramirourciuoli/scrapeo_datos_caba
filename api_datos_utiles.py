import requests


def consultar_datos_utiles(calle: str, altura: int) -> dict:
    """
    Consulta la API "Datos útiles" de CABA por calle y altura.
    Devuelve JSON o un error bien explicado.
    """

    # ✅ Endpoint correcto (BA Data / USIG APIs)
    url = "https://datosabiertos-usig-apis.buenosaires.gob.ar/datos_utiles"

    params = {
        "calle": calle.strip(),
        "altura": int(altura),
    }

    headers = {
        "Accept": "application/json"
    }

    try:
        # allow_redirects=False para ver si te están redirigiendo a una web (HTML)
        r = requests.get(url, params=params, headers=headers, timeout=15, allow_redirects=False)

        # 1) Si hay redirección, te lo informo (esto explica el HTML que estabas viendo)
        if 300 <= r.status_code < 400:
            return {
                "error": "Redirección detectada (no es respuesta JSON directa).",
                "status_code": r.status_code,
                "location": r.headers.get("Location"),
                "url_pedida": r.url,
            }

        # 2) Si no es 200, devolvemos diagnóstico
        if r.status_code != 200:
            return {
                "error": "La API devolvió un status inesperado",
                "status_code": r.status_code,
                "url_pedida": r.url,
                "contenido": r.text[:500],  # recorto para que no te explote la consola
            }

        # 3) Validar que sea JSON por header Content-Type
        content_type = (r.headers.get("Content-Type") or "").lower()
        if "json" not in content_type:
            return {
                "error": "La respuesta no parece JSON (Content-Type no es JSON).",
                "content_type": content_type,
                "url_pedida": r.url,
                "contenido": r.text[:500],
            }

        # 4) Parsear JSON
        return r.json()

    except requests.exceptions.RequestException as e:
        return {"error": "Error de conexión con la API", "detalle": str(e)}


if __name__ == "__main__":
    datos = consultar_datos_utiles("Monroe", 4848)
    print(datos)
