import paho.mqtt.client as mqtt
from flask import Flask, render_template, request, jsonify
import json


MQTT_BROKER_HOST = "mqtt-broker"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "iotik32/commands"
MQTT_SUB_TOPIC = "iotik32/logs"

app = Flask(__name__)

mqtt_client = mqtt.Client()


mqtt_client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, keepalive=60)
mqtt_client.subscribe(MQTT_SUB_TOPIC)

current_page = "base"
current_data = 0
user = 0


def publish_button(button_name: str, data: int = 0) -> None:
    payload = {
        "action": button_name,
        "data": data
    }
    mqtt_client.publish(MQTT_TOPIC, json.dumps(payload), qos=0, retain=False)

def on_message(client, userdata, msg):
    global current_page
    global current_data
    global user
    try:
        payload_str = msg.payload.decode("utf-8")
        print(f"Получено сообщение из {msg.topic}: {payload_str}",flush=True)

        data = json.loads(payload_str)

        action = data.get("action")
        msg_data = data.get("data") 

        if action == "card_read":
            current_page = "password"
            user = msg_data
        if action == "refill_comp":
            current_page = "succ_put"
            current_data = msg_data
        if action == "succesful_withdrawal":
            current_page = "succ_get"

    except json.JSONDecodeError:
        print("Ошибка: получено невалидное JSON-сообщение")
    except Exception as e:
        print("Неожиданная ошибка при обработке сообщения:", e)
mqtt_client.on_message = on_message
mqtt_client.loop_start()

@app.route('/')
def base():
    publish_button("end_work")
    return render_template("base.html")


@app.route("/password")
def about():
    global current_page
    current_page = "base"
    return render_template("about.html")


@app.route("/function")
def function():
    global current_page
    publish_button("new_work")
    current_page = "base"
    return render_template("function.html")

@app.route("/get")
def get_money():
    return render_template("get_money.html")

@app.route("/balance")
def balance():
    global user
    from base import get_balance_by_rf_id
    return render_template("balance.html", balance = get_balance_by_rf_id(user))

@app.route("/put_money")
def put_money():
    return render_template("put_money.html")

@app.route("/successful_put")
def succ_put():
    return render_template("success_put.html", money = str(current_data))

@app.route("/successful_get")
def succ_get():
    return render_template("success_get.html")

@app.route("/publish", methods=["POST"])
def publish():
    data = request.get_json(silent=True) or {}
    button = (data.get("button") or "").strip()
    amount = (data.get("amount") or 0)

    publish_button(button,amount)
    return jsonify({"ok": True, "published_to": MQTT_TOPIC, "button": button})

@app.route("/healthz", methods=["GET"])
def healthz():
    return "ok", 200

@app.route("/state")
def state():
    return jsonify({"page": current_page})



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)