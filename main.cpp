#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h> // Necessário para manipular JSON
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// --- CONFIGURAÇÕES DE WI-FI E SERVIDOR ---
const char* ssid = "NOME DA REDE";
const char* password = "SENHA DA REDE";
const char* serverUrl = "ESCREVA O SERVIDOR AQUI";

// --- CONFIGURAÇÕES DOS PINOS ---
const int umidadePin = 34;
const int led = 23;
const int luzPins[] = {35, 32, 33, 25}; 
const int numLuzSensors = 4; 

// --- CALIBRAÇÃO DOS SENSORES ---
const int UMIDADE_MAX_ADC = 4095;
const int UMIDADE_MIN_ADC = 1800;
const int LUZ_MAX_ADC = 4095;
const int LUZ_MIN_ADC = 0;

// --- INICIALIZAÇÃO DOS COMPONENTES ---
LiquidCrystal_I2C lcd(0x27);
HTTPClient http;

// --- FUNÇÕES AUXILIARES ---
void conectaWifi() {
  WiFi.begin(ssid, password);
  lcd.clear();
  lcd.print("Conectando WiFi");
  Serial.print("Conectando ao WiFi...");

  int timeout = 20;
  while (WiFi.status() != WL_CONNECTED && timeout > 0) {
    delay(500);
    Serial.print(".");
    lcd.print(".");
    timeout--;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi conectado!");
    digitalWrite(led,HIGH);
    Serial.print("Endereço IP: ");
    Serial.println(WiFi.localIP());
    lcd.clear();
    lcd.print("WiFi Conectado!");
    delay(1000);
  } else {
    Serial.println("\nFalha ao conectar.");
    lcd.clear();
    lcd.print("Falha no WiFi");
  }
}

long mapear(long valor, long de_min, long de_max, long para_min, long para_max) {
  if (de_max - de_min == 0) return para_min;
  long valor_mapeado = (valor - de_min) * (para_max - para_min) / (de_max - de_min) + para_min;
  return max(para_min, min(para_max, valor_mapeado));
}

void setup() {
  Serial.begin(115200);
  Wire.begin(); 
  
  pinMode(umidadePin, INPUT);
  
  for (int i = 0; i < numLuzSensors; i++) { 
    pinMode(luzPins[i], INPUT);
  }

  lcd.begin(16, 2);
  lcd.backlight();
  lcd.print("Iniciando...");
  delay(1000);
  pinMode(led,OUTPUT);
  conectaWifi();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Conexão WiFi perdida. Tentando reconectar...");
    conectaWifi();
    if (WiFi.status() != WL_CONNECTED) {
      delay(5000);
      return;
    }
  }

  // 1. Ler os valores brutos dos sensores
  int valorUmidadeRaw = analogRead(umidadePin);

  long totalLuzRaw = 0; 
  for (int i = 0; i < numLuzSensors; i++) { 
    totalLuzRaw += analogRead(luzPins[i]);   
  } // <--- CHAVE FECHADA AQUI

  int valorLuzRaw = totalLuzRaw / numLuzSensors; 

  // 2. Converter os valores para porcentagem
  long umidadePercent = mapear(valorUmidadeRaw, UMIDADE_MAX_ADC, UMIDADE_MIN_ADC, 0, 100);
  long luzPercent = mapear(valorLuzRaw, LUZ_MAX_ADC, LUZ_MIN_ADC, 0, 100);

  Serial.printf("Leitura: Umidade RAW=%d -> %ld%% | Média Luz RAW=%d -> %ld%%\n", valorUmidadeRaw, umidadePercent, valorLuzRaw, luzPercent);

  // 3. Criar o corpo da requisição JSON
  StaticJsonDocument<200> doc;
  doc["umidade"] = umidadePercent;
  doc["luminosidade"] = luzPercent; 

  String requestBody;
  serializeJson(doc, requestBody);

  // 4. Enviar os dados para o servidor
  http.begin(serverUrl);
  http.addHeader("Content-Type", "application/json");

  Serial.println("Enviando dados para o servidor...");
  int httpResponseCode = http.POST(requestBody);
  
  // 5. Processar a resposta do servidor
  if (httpResponseCode > 0) {
    String payload = http.getString();
    Serial.print("Código de resposta HTTP: ");
    Serial.println(httpResponseCode);
    Serial.print("Resposta do servidor: ");
    Serial.println(payload);

    StaticJsonDocument<200> responseDoc;
    deserializeJson(responseDoc, payload);
    const char* instrucao = responseDoc["instrucao"];

    // 6. Exibir no LCD
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.printf("U:%ld%% L:%ld%%", umidadePercent, luzPercent);
    lcd.setCursor(0, 1);
    lcd.print(instrucao);

  } else {
    Serial.print("Erro na requisição HTTP: ");
    Serial.println(httpResponseCode);
    lcd.clear();
    lcd.print("Erro Servidor");
    lcd.setCursor(0, 1);
    lcd.printf("Cod: %d", httpResponseCode);
  }

  http.end();

  Serial.println("Aguardando 30 segundos...");
  delay(30000);
}
