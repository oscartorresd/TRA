from flask import Flask, request, jsonify
import requests, json, traceback
from datetime import datetime

app = Flask(__name__)

# URLs y cabeceras destino
URL_1 = "https://pms.mincit.gov.co/one/"
URL_2 = "https://pms.mincit.gov.co/two/"
TOKEN = "ujS5y5yFrY678VUvWxKU769KpHUOTDXMKNU3w8BB"
HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Content-Type": "application/json"
}

# ------------------------------------------
# Funciones auxiliares
# ------------------------------------------

def log(title, data=None):
    print("\n" + "="*80)
    print(f"🕒 {datetime.now().isoformat()} | {title}")
    if data is not None:
        try:
            print(json.dumps(data, indent=4, ensure_ascii=False))
        except Exception:
            print(str(data))
    print("="*80 + "\n", flush=True)

def get_text_from_dropdown(field):
    """Convierte un campo de dropdown (con IDs) en su texto visible"""
    if not field:
        return None
    value = field.get("value")
    options = field.get("options", [])
    if isinstance(value, list) and value:
        for opt in options:
            if opt["id"] == value[0]:
                return opt["text"]
    return value if isinstance(value, str) else None

def normalize(field):
    """Extrae el valor limpio según tipo"""
    if not field:
        return None
    if field["type"] == "DROPDOWN":
        return get_text_from_dropdown(field)
    return field.get("value")

# ------------------------------------------
# Lógica principal
# ------------------------------------------

@app.route('/', methods=['POST'])
def handle_tally_webhook():
    try:
        payload = request.get_json(force=True)
        log("✅ Webhook recibido", payload)

        fields = payload["data"]["fields"]

        # --- Mapeo del huésped principal (primer bloque) ---
        data1 = {
            "tipo_identificacion": normalize(fields[0]),
            "numero_identificacion": normalize(fields[1]),
            "nombres": normalize(fields[2]),
            "apellidos": normalize(fields[3]),
            "cuidad_residencia": normalize(fields[4]),
            "cuidad_procedencia": normalize(fields[5]),
            "numero_habitacion": "706",
            "motivo": normalize(fields[6]),
            "numero_acompanantes": normalize(fields[10]),
            "check_in": normalize(fields[7]),
            "check_out": normalize(fields[8]),
            "tipo_acomodacion": "Apartaestudio",
            "costo": normalize(fields[9]),
            "nombre_establecimiento": "Oikos Infinitum 58 Apto 706",
            "rnt_establecimiento": "183243"
        }

        log("📤 Enviando Request 1", data1)
        resp1 = requests.post(URL_1, headers=HEADERS, json=data1)
        log(f"📥 Respuesta Request 1 ({resp1.status_code})", resp1.text)

        if resp1.status_code == 201:
            padre_id = resp1.json().get("code")
            num_acomp = int(data1.get("numero_acompanantes") or 0)

            if num_acomp >= 1 and padre_id:
                # --- Mapeo del acompañante (segundo bloque) ---
                data2 = {
                    "tipo_identificacion": normalize(fields[11]),
                    "numero_identificacion": normalize(fields[12]),
                    "nombres": normalize(fields[13]),
                    "apellidos": normalize(fields[14]),
                    "cuidad_residencia": normalize(fields[15]),
                    "cuidad_procedencia": normalize(fields[16]),
                    "numero_habitacion": "706",
                    "check_in": data1["check_in"],
                    "check_out": data1["check_out"],
                    "padre": padre_id
                }

                log("📤 Enviando Request 2", data2)
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
