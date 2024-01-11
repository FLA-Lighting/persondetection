import cv2
import numpy as np
import io
import paho.mqtt.client as mqtt
import tkinter as tk
from PIL import Image, ImageTk

# Configurações MQTT
mqtt_username = "admin"
mqtt_password = "1221"
mqtt_broker_address = "35.208.123.29"
mqtt_port = 1883
mqtt_topic_image = "esp32/cam_0"
mqtt_topic_sensor_data = "esp32/bme280"

# Configurações MQTT
Connected = False
frame_counter = 0

# Variáveis para armazenar a imagem e dados do sensor
current_image = None
sensor_data = {}

# Callback chamada quando o cliente MQTT se conecta ao broker
def on_connect(client, userdata, flags, rc):
    global Connected
    if rc == 0:
        print('[MQTT] Conectado ao broker')
        client.subscribe(mqtt_topic_image)
        client.subscribe(mqtt_topic_sensor_data)
        Connected = True  # Indica que a conexão foi estabelecida
    else:
        print('[MQTT] Falha na conexão com código {}'.format(rc))

# Callback chamada quando uma mensagem MQTT é recebida
def on_message(client, userdata, msg):
    global frame_counter, current_image, sensor_data
    try:
        if msg.topic == mqtt_topic_image:
            print(f"Recebendo frame {frame_counter}...")
            bytes_image = io.BytesIO(msg.payload)
            current_image = cv2.imdecode(np.frombuffer(bytes_image.read(), dtype=np.uint8), 1)
            frame_counter += 1
            mostrar_video(current_image)
        elif msg.topic == mqtt_topic_sensor_data:
            print("Recebendo dados do sensor...")
            sensor_data = eval(msg.payload.decode("utf-8"))
            mostrar_dados_sensor(sensor_data)
    except Exception as e:
        print('Erro:', e)

# Função para mostrar o vídeo recebido
def mostrar_video(im):
    image = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(image)
    image = ImageTk.PhotoImage(image)
    label_video.config(image=image)
    label_video.image = image

# Função para mostrar os dados do sensor
def mostrar_dados_sensor(data):
    label_sensor_data.config(text=data)

# Configurações da MQTT
mqttc = mqtt.Client()
mqttc.on_connect = on_connect
mqttc.on_message = on_message

if mqtt_username and mqtt_password:
    mqttc.username_pw_set(mqtt_username, mqtt_password)

mqttc.connect(mqtt_broker_address, mqtt_port, 60)
mqttc.loop_start()

# Criando a interface gráfica
root = tk.Tk()
root.title("ESP32-CAM & BME280")

# Rótulo para exibir a imagem
label_video = tk.Label(root)
label_video.pack()

# Rótulo para exibir os dados do sensor
label_sensor_data = tk.Label(root, text="Dados do Sensor")
label_sensor_data.pack()

# Inicia o loop principal da interface gráfica
root.mainloop()
