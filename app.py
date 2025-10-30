from flask import Flask, request, jsonify
import requests
import json
import traceback
from datetime import datetime

app = Flask(__name__)

# URLs de los servicios destino
URL_1 = "https://pms.mincit.gov.co/one/"
URL_2 = "https://pms.mincit.gov.co/two/"
TOKEN = "ujS5y5yFrY678VUvWxKU769KpHUOTDXMKNU3w8BB"

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Content-Type": "application/json"
}

def log(title, data=None):
    """Imprime logs con timestamp y formato JSON legible"""
    print("\n" + "="*80)
    print(f"🕒 {datetime.now().isoformat()} | {title}")
    if data is not None:
        try:
            print(json.dumps(data, indent=4, ensure_ascii=False))
        except Exception:
            print(str(data))
    print("="*80 + "\n", flush=True)

@app.route('/', methods=['POST'])
def handle_tally_webhook():
    try:
        payload = request.get_json(force=True)
        log("✅ Webhook recibido de Tally", payload)

        # --- Extraer campos del form ---
        fields = {f["label"]: f.get("value") for f in payload["data"]["fields"]}

        # Normaliza valores que vienen en lista
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
            "numero_habitacion": "706",  # Si este campo viene del form, cámbialo aquí
            "motivo": normalize(fields.get("Motivo")),
            "numero_acompanantes": normalize(fields.get("Número de acompañantes")),
            "check_in": normalize(fields.get("Check-in")),
            "check_out": normalize(fields.get("Check-out")),
            "tipo_acomodacion": "Apartaestudio",  # o agrega al form
            "costo": normalize(fields.get("Valor Pagado")),
            "nombre_establecimiento": "Oikos Infinitum 58 Apto 706",
            "rnt_establecimiento": "183243"
        }

        log("📤 JSON Enviado (Request 1)", data1)
        resp1 = requests.post(URL_1, headers=HEADERS, json=data1)
        log(f"📥 Respuesta Request 1 ({resp1.status_code})", resp1.text)

        if resp1.status_code == 201:
            padre_id = resp1.json().get("code")
            num_acomp = int(data1.get("numero_acompanantes") or 0)

            if num_acomp >= 1 and padre_id:
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

                log("📤 JSON Enviado (Request 2)", data2)
                resp2 = requests.post(URL_2, headers=HEADERS, json=data2)
                log(f"📥 Respuesta Request 2 ({resp2.status_code})", resp2.text)
            else:
                log("ℹ️ No se envió Request 2", {"numero_acompanantes": num_acomp, "padre_id": padre_id})
        else:
            log("❌ Error en Request 1", {"status": resp1.status_code, "body": resp1.text})

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        error_trace = traceback.format_exc()
        log("💥 Error procesando webhook", {"error": str(e), "trace": error_trace})
        return jsonify({"error": str(e)}), 500


@app.route('/', methods=['GET'])
def home():
    return "✅ Servicio activo - Esperando formularios Tally", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
