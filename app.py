from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# === CONFIGURACIÓN ===
URL1 = "https://pms.mincit.gov.co/one/"
URL2 = "https://pms.mincit.gov.co/two/"
TOKEN = "ujS5y5yFrY678VUvWxKU769KpHUOTDXMKNU3w8BB"

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Content-Type": "application/json"
}


@app.route("/", methods=["GET"])
def home():
    return "✅ Servicio activo. Usa /enviar (POST) para procesar datos del formulario."


@app.route("/enviar", methods=["POST"])
def enviar():
    try:
        # Recibe el JSON completo desde el formulario
        data1 = request.get_json()

        if not data1:
            return jsonify({"error": "No se recibieron datos JSON"}), 400

        print("📩 Datos recibidos:", data1)

        # --- Enviar el primer request ---
        response1 = requests.post(URL1, headers=HEADERS, json=data1)
        print("Request 1 - Código:", response1.status_code)
        print("Request 1 - Respuesta:", response1.text)

        # Si no fue exitoso, devolvemos el error
        if response1.status_code != 201:
            return jsonify({
                "status": "error",
                "msg": "Error al registrar el principal",
                "detalles": response1.text
            }), response1.status_code

        # --- Procesar la respuesta del primer request ---
        resp_json = response1.json()
        padre_id = resp_json.get("code")

        # --- Revisar si hay acompañantes ---
        numero_acompanantes = int(data1.get("numero_acompanantes", 0))

        # Si hay acompañantes y se tiene el padre_id, enviamos un segundo request
        if numero_acompanantes >= 1 and padre_id and "acompanantes" in data1:
            for acomp in data1["acompanantes"]:
                # cada "acomp" es un dict con datos del acompañante
                acomp["padre"] = padre_id
                response2 = requests.post(URL2, headers=HEADERS, json=acomp)
                print("Request 2 - Código:", response2.status_code)
                print("Request 2 - Respuesta:", response2.text)

            return jsonify({
                "status": "ok",
                "msg": f"{numero_acompanantes} acompañantes enviados correctamente",
                "padre_id": padre_id
            }), 200

        else:
            return jsonify({
                "status": "ok",
                "msg": "Solo se envió el registro principal",
                "padre_id": padre_id
            }), 200

    except Exception as e:
        print("❌ Error general:", str(e))
        return jsonify({"status": "error", "msg": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
