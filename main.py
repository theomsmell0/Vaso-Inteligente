import network
import urequests
import time
from machine import ADC, Pin, I2C
from lcd_api import LcdApi
from i2c_lcd import I2cLcd

# Config Wi‑Fi
SSID = 'SUA_REDE_WIFI'
PASSWORD = 'SUA_SENHA_WIFI'
SERVER_URL = 'http://SEU_SERVIDOR/api/dados'

# Limiares
UMIDADE_SECA = 3000    # valor ADC alto = solo seco
UMIDADE_UMIDO = 1500   # valor ADC baixo = solo úmido

# Inicia ADC
adc_umidade = ADC(Pin(34)); adc_umidade.atten(ADC.ATTN_11DB)
adc_luz = ADC(Pin(35)); adc_luz.atten(ADC.ATTN_11DB)

# Inicia I2C e LCD
i2c = I2C(0, sda=Pin(21), scl=Pin(22), freq=400000)
lcd = I2cLcd(i2c, 0x27, 2, 16)  # endereço comum 0x27; ajuste se necessário

# Função Wi‑Fi
def conecta_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            time.sleep(1)
    print('Conectado:', wlan.ifconfig())
    lcd.clear()
    lcd.putstr('WiFi conectada')

# Avalia estado da planta
def avalia_umidade(valor):
    if valor > UMIDADE_SECA:
        return 'Preciso de agua'
    elif valor < UMIDADE_UMIDO:
        return 'Estou saciada'
    else:
        return 'Umida ok'

# Loop principal
def loop():
    conecta_wifi()
    time.sleep(1)
    while True:
        umidade = adc_umidade.read()
        luz = adc_luz.read()
        status = avalia_umidade(umidade)

        # Exibe no LCD
        lcd.clear()
        lcd.putstr(f"U:{umidade} L:{luz}")
        lcd.move_to(0,1)
        lcd.putstr(status)

        # Envia para servidor
        try:
            data = {"umidade": umidade, "luz": luz, "status": status}
            resp = urequests.post(SERVER_URL, json=data)
            resp.close()
        except Exception as e:
            print('Erro POST:', e)

        time.sleep(10)

# Executa
loop()
