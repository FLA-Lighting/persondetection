import io
import queue
import traceback
import paho.mqtt.client as mqtt
import PySimpleGUI as sg
from PIL import Image

class Application:
    def __init__(self):
        self.mqtt_client = None
        self.gui_queue = queue.Queue()

        middle_font = ('Helvetica', 14)
        context_font = ('Helvetica', 12)
        sg.theme('DarkGrey14')

        col1 = [[sg.Column([
            [sg.Frame('MQTT Panel', [[sg.Column([
                [sg.Text('Client Id:', font=middle_font)],
                [sg.Input('Python_Client', key='_CLIENTID_IN_', size=(19, 1), font=context_font),
                 sg.Button('Connect', key='_CONNECT_BTN_', font=context_font)],
                [sg.Text('Notes:', font=middle_font)],
                [sg.Multiline(key='_NOTES_', autoscroll=True, size=(26, 34), font=context_font, )],
            ], size=(235, 640), pad=(0, 0))]], font=middle_font)], ], pad=(0, 0), element_justification='c')]]

        col2 = [[sg.Column([[sg.Frame('CAM {}'.format((row + col)), [
            [sg.Image(key='_ESP32/CAM_{}_'.format((row + col)), size=(480, 320))],
        ], font=middle_font) for row in range(0, 3, 2)]], pad=(0, 0), element_justification='c')] for col in range(2)]

        layout = [[
            sg.Column(col1), sg.Column(col2)
        ]]

        self.window = sg.Window('Python MQTT Client', layout)

        while True:
            event, values = self.window.Read(timeout=5)
            if event is None or event == 'Exit':
                break

            if event == '_CONNECT_BTN_':
                if self.window[event].get_text() == 'Connect':

                    if len(self.window['_CLIENTID_IN_'].get()) == 0:
                        self.popup_dialog('Client Id is empty', 'Error', context_font)
                    else:
                        self.window['_CONNECT_BTN_'].update('Disconnect')
                        self.connect_mqtt(self.window['_CLIENTID_IN_'].get())

                else:
                    self.window['_CONNECT_BTN_'].update('Connect')
                    self.disconnect_mqtt()

            try:
                message = self.gui_queue.get_nowait()
            except queue.Empty:
                message = None
            if message is not None:
                _target_ui = message.get("Target_UI")
                _image = message.get("Image")
                self.window[_target_ui].update(data=_image)

        self.window.Close()

    def connect_mqtt(self, client_id):
        self.mqtt_client = mqtt.Client(client_id)
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        mqtt_username = "admin"
        mqtt_password = "1221"
        mqtt_broker_address = "ec2-13-58-196-72.us-east-2.compute.amazonaws.com"
        mqtt_port = 1883
        mqtt_topic_prefix = "esp32/cam_"

        self.mqtt_client.username_pw_set(mqtt_username, mqtt_password)
        self.mqtt_client.connect(mqtt_broker_address, mqtt_port, 60)

        for i in range(4):
            self.mqtt_subscribe('{}{}'.format(mqtt_topic_prefix, i))

        self.add_note('[MQTT] Connected')

    def disconnect_mqtt(self):
        if self.mqtt_client is not None:
            self.mqtt_client.disconnect()
            self.add_note('[MQTT] Successfully Disconnected!')

    def mqtt_subscribe(self, topic):
        self.mqtt_client.subscribe(topic)

    def on_connect(self, client, userdata, flags, rc):
        self.add_note('[MQTT] Connected with result code {}'.format(rc))

    def on_message(self, client, userdata, msg):
        self.gui_queue.put({"Target_UI": "_{}_".format(str(msg.topic).upper()),
                            "Image": self.byte_image_to_png(msg)})

    def add_note(self, note):
        note_history = self.window['_NOTES_'].get()
        self.window['_NOTES_'].update(note_history + note if len(note_history) > 1 else note)

    def byte_image_to_png(self, message):
        bytes_image = io.BytesIO(message.payload)
        picture = Image.open(bytes_image)

        im_bytes = io.BytesIO()
        picture.save(im_bytes, format="PNG")
        return im_bytes.getvalue()

    def popup_dialog(self, contents, title, font):
        sg.Popup(contents, title=title, keep_on_top=True, font=font)

if __name__ == '__main__':
    Application()
