# Importando bibliotecas necessárias
import cv2
import numpy as np
import io
import paho.mqtt.client as mqtt
import time

# Configurações MQTT
mqtt_username = "admin"
mqtt_password = "1221"
mqtt_broker_address = "ec2-3-15-240-117.us-east-2.compute.amazonaws.com"
mqtt_port = 1883
mqtt_topic = "esp32/cam_0"
mqtt_topic_pessoa_detectada = "esp32/pessoa_det"

# Configurações YOLO
whT = 320  # Largura e altura da imagem para a entrada do modelo YOLO
confThreshold = 0.5  # Limiar de confiança para considerar uma detecção válida
nmsThreshold = 0.3  # Limiar para supressão não máxima
classesfile = 'coco.names'  # Arquivo contendo os nomes das classes a serem detectadas
classNames = []

with open(classesfile, 'rt') as f:
    classNames = f.read().rstrip('\n').split('\n')

modelConfig = 'yolov3.cfg'
modelWeights = 'yolov3.weights'
net = cv2.dnn.readNetFromDarknet(modelConfig, modelWeights)
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

# Configurações MQTT
Connected = False
frame_counter = 0

# Callback chamada quando o cliente MQTT se conecta ao broker
def on_connect(client, userdata, flags, rc):
    global Connected
    if rc == 0:
        print('[MQTT] Conectado ao broker')
        client.subscribe(mqtt_topic)
        Connected = True  # Indica que a conexão foi estabelecida
    else:
        print('[MQTT] Falha na conexão com código {}'.format(rc))

# Callback chamada quando uma mensagem MQTT é recebida
def on_message(client, userdata, msg):
    global frame_counter
    try:
        print(f"Recebendo frame {frame_counter}...")
        bytes_image = io.BytesIO(msg.payload)
        image = cv2.imdecode(np.frombuffer(bytes_image.read(), dtype=np.uint8), 1)
        processar_imagem(image)
        frame_counter += 1
    except Exception as e:
        print('Erro:', e)

# Função para processar a imagem usando o modelo YOLO
def processar_imagem(im):
    blob = cv2.dnn.blobFromImage(im, 1/255, (whT, whT), [0, 0, 0], 1, crop=False)
    net.setInput(blob)
    layernames = net.getLayerNames()
    outputNames = [layernames[i - 1] for i in net.getUnconnectedOutLayers()]
    outputs = net.forward(outputNames)
    encontrarPessoa(outputs, im)

# Função para identificar e desenhar caixas delimitadoras ao redor de pessoas na imagem
def encontrarPessoa(outputs, im):
    hT, wT, cT = im.shape
    bbox = []
    classIds = []
    confs = []
    encontrou_pessoa = False

    for output in outputs:
        for det in output:
            scores = det[5:]
            classId = np.argmax(scores)
            confidence = scores[classId]

            if confidence > confThreshold and classNames[classId] == 'person':
                w, h = int(det[2] * wT), int(det[3] * hT)
                x, y = int((det[0] * wT) - w / 2), int((det[1] * hT) - h / 2)
                bbox.append([x, y, w, h])
                classIds.append(classId)
                confs.append(float(confidence))
                encontrou_pessoa = True

    indices = cv2.dnn.NMSBoxes(bbox, confs, confThreshold, nmsThreshold)

    for i in indices:
        box = bbox[i]
        x, y, w, h = box[0], box[1], box[2], box[3]

        if encontrou_pessoa:
            print('Pessoa detectada!')
            
            # Enviar mensagem para o tópico MQTT
            mensagem = "1"
            mqttc.publish(mqtt_topic_pessoa_detectada, mensagem)
            
            cv2.rectangle(im, (x, y), (x + w, y + h), (255, 0, 255), 2)
            cv2.putText(im, f'{classNames[classIds[i]].upper()} {int(confs[i]*100)}%', (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)

# Configurações da MQTT
mqttc = mqtt.Client()
mqttc.on_connect = on_connect
mqttc.on_message = on_message

if mqtt_username and mqtt_password:
    mqttc.username_pw_set(mqtt_username, mqtt_password)

mqttc.connect(mqtt_broker_address, mqtt_port, 60)
mqttc.loop_start()

while not Connected:
    time.sleep(1)  # Aguarda a conexão ser estabelecida antes de prosseguir

while True:
    try:
        pass
    except KeyboardInterrupt:
        break

# Encerra janelas do OpenCV e desconecta o cliente MQTT
cv2.destroyAllWindows()
mqttc.loop_stop()
mqttc.disconnect()
