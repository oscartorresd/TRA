from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# URLs de los servicios destino
URL_1 = "https://pms.mincit.gov.co/one/"
URL_2 = "https://pms.mincit.gov.co/two/"
TOKEN = "ujS5y5yFrY678VUvWxKU769KpHUOTDXMKNU3w8BB"

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Content-Type": "application/json"
}

@app.route('/', methods=['POST'])
def handle_tally_webhook():
    try:
        payload = request.get_json()
        print("✅ Webhook recibido de Tally:", payload)

        # --- Extraer campos ---
        fields = {f["label"]: f.get("value") for f in payload["data"]["fields"]}

        # Algunos valores vienen como listas (por ejemplo dropdowns)
        def normalize(v):
            if isinstance(v, list):
                return v[0] if v else None
            return v

        # --- Crear JSON del Request 1 ---
        data1 = {
            "tipo_identificacion": normalize(fields.get("Tipo de identificación")),
            "numero_identificacion": normalize(fields.get("Número de identificación")),
            "nombres": normalize(fields.get("Nombres")),
            "apellidos": normalize(fields.get("Apellidos")),
            "cuidad_residencia": normalize(fields.get("Ciudad de residencia")),
            "cuidad_procedencia": normalize(fields.get("Ciudad de procedencia")),
            "numero_habitacion": "706",  # Si este campo viene del form, reemplázalo aquí
            "motivo": normalize(fields.get("Motivo")),
            "numero_acompanantes": normalize(fields.get("Número de acompañantes")),
            "check_in": normalize(fields.get("Check-in")),
            "check_out": normalize(fields.get("Check-out")),
            "tipo_acomodacion": "Apartaestudio",  # o agrega al form
            "costo": normalize(fields.get("Valor Pagado")),
            "nombre_establecimiento": "Oikos Infinitum 58 Apto 706",
            "rnt_establecimiento": "183243"
        }

        print("📦 Enviando Request 1:", data1)
        resp1 = requests.post(URL_1, headers=HEADERS, json=data1)
        print("Response 1:", resp1.status_code, resp1.text)

        if resp1.status_code == 201:
            padre_id = resp1.json().get("code")
            num_acomp = int(data1.get("numero_acompanantes") or 0)

            if num_acomp >= 1 and padre_id:
                # --- Crear JSON del Request 2 ---
                data2 = {
                    "tipo_identificacion": normalize(fields.get("Tipo de identificación (acompañante)")),
                    "numero_identificacion": normalize(fields.get("Número de identificación (acompañante)")),
                    "nombres": normalize(fields.get("Nombres (acompañante)")),
                    "apellidos": normalize(fields.get("Apellidos (acompañante)")),
                    "cuidad_residencia": normalize(fields.get("Ciudad de residencia (acompañante)")),
                    "cuidad_procedencia": normalize(fields.get("Ciudad de procedencia (acompañante)")),
                    "numero_habitacion": "706",
                    "check_in": data1["check_in"],
                    "check_out": data1["check_out"],
                    "padre": padre_id
                }
                print("📦 Enviando Request 2:", data2)
                resp2 = requests.post(URL_2, headers=HEADERS, json=data2)
                print("Response 2:", resp2.status_code, resp2.text)
            else:
                print("ℹ️ No se envió el request 2: sin acompañantes o sin padre_id.")
        else:
            print("❌ Error en request 1:", resp1.status_code)

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print("❌ Error procesando webhook:", str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/', methods=['GET'])
def home():
    return "Servicio activo - Esperando formularios Tally", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
