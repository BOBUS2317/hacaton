from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import paho.mqtt.client as mqtt
import json
import asyncio
from typing import Dict, Any, Optional

app = FastAPI()

# Модель для управления лампочкой
class LightCommand(BaseModel):
    state: bool  # True для включения, False для выключения
    device_id: Optional[str] = "white"

# MQTT конфигурация
MQTT_BROKER = "mqtt-broker"
MQTT_PORT = 1883
MQTT_TOPIC = "iotik32/commands"

class MQTTManager:
    def __init__(self):
        self.client = mqtt.Client()
        self.connected = False
        self.setup_callbacks()
    
    def setup_callbacks(self):
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                self.connected = True
                # logger.info("Connected to MQTT broker")
                ...
            else:
                # logger.error(f"Failed to connect to MQTT broker. Code: {rc}")
                ...
        
        def on_disconnect(client, userdata, rc):
            self.connected = False
            # logger.info("Disconnected from MQTT broker")
        
        def on_message(client, userdata, msg):
            ...
            # logger.info(f"Received message: {msg.topic} {msg.payload.decode()}")
        
        self.client.on_connect = on_connect
        self.client.on_disconnect = on_disconnect
        self.client.on_message = on_message
    
    async def connect(self):
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()
            
            # Ждем подключения
            for _ in range(10):  # 10 попыток
                if self.connected:
                    break
                await asyncio.sleep(1)
            
            if not self.connected:
                raise ConnectionError("Failed to connect to MQTT broker")
                
        except Exception as e:
            # logger.error(f"MQTT connection error: {e}")
            raise
    
    def publish_command(self, command: dict):
        if not self.connected:
            raise ConnectionError("Not connected to MQTT broker")
        
        try:
            message = json.dumps(command)
            result = self.client.publish(MQTT_TOPIC, message)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                # logger.info(f"Command sent: {message}")
                return True
            else:
                # logger.error(f"Failed to send command. Error code: {result.rc}")
                return False
        except Exception as e:
            # logger.error(f"Error publishing message: {e}")
            return False
    
    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()

# Глобальный MQTT менеджер
mqtt_manager = MQTTManager()

# Простое хранилище состояний ламп
light_states: Dict[str, bool] = {
    "white": False,
    "blue": False,
    "red": False,
}

@app.on_event("startup")
async def startup_event():
    """Подключение к MQTT брокеру при запуске"""
    try:
        await mqtt_manager.connect()
        # logger.info("MQTT manager initialized successfully")
    except Exception as e:
        ...
        # logger.error(f"Failed to initialize MQTT manager: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Отключение от MQTT брокера при остановке"""
    mqtt_manager.disconnect()
    # logger.info("MQTT manager disconnected")

# API endpoints
@app.get("/")
async def read_root():
    """Главная страница с интерфейсом управления"""
    return FileResponse("static/index.html")

@app.post("/api/light/control")
async def control_light(command: LightCommand) -> Dict[str, Any]:
    """Управление лампочкой через MQTT"""
    try:
        mqtt_command = {
            "device_id": command.device_id,
            "state": "on" if command.state else "off",
            "timestamp": str(asyncio.get_event_loop().time())
        }
        
        success = mqtt_manager.publish_command(mqtt_command)
        
        if success:
            if command.device_id and command.device_id in light_states:
                light_states[command.device_id] = command.state
            return {
                "success": True,
                "message": f"Light turned {'on' if command.state else 'off'}",
                "command": mqtt_command
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send MQTT command")
            
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=f"MQTT connection error: {str(e)}")
    except Exception as e:
        # logger.error(f"Error controlling light: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

from typing import Dict, Any

@app.get("/api/light")
async def get_lights_state() -> Dict[str, bool]:
    """Текущее состояние всех ламп"""
    return {lamp: state for lamp, state in light_states.items()}

@app.get("/api/light/status")
async def get_light_status() -> Dict[str, Any]:
    """Получение статуса подключения к MQTT"""
    return {
        "mqtt_connected": mqtt_manager.connected,
        "broker": MQTT_BROKER,
        "topic": MQTT_TOPIC
    }


@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    """Проверка работоспособности сервиса"""
    return {
        "status": "healthy",
        "mqtt_connected": mqtt_manager.connected,
        "version": "1.0.0"
    }

# # Монтируем статические файлы
# app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)