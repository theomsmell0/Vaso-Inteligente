#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h> // Necessário para manipular JSON
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// --- CONFIGURAÇÕES DOS PINOS ---
const int umidadePin = 34;
const int led = 2;

const int luzPins[] = {35, 32, 33, 26}; 
const int numLuzSensors = sizeof(luzPins) / sizeof(luzPins[0]); 


const int LUZ_CALIB_ESCURO = 600; 
const int LUZ_CALIB_CLARO = 2300;   
const int UMIDADE_MAX_ADC = 3700; 
const int UMIDADE_MIN_ADC = 400; 

// --- INICIALIZAÇÃO DOS COMPONENTES ---
LiquidCrystal_I2C lcd(0x27, 16, 2);
HTTPClient http;

// --- FUNÇÕES DE LED (sem alterações) ---
void blinkEnviandoDados() {
  for (int i = 0; i < 3; i++) {
    digitalWrite(led, HIGH); delay(100);
    digitalWrite(led, LOW); delay(100);
  }
}
void blinkBuscaServidor(int totalDuration) {
  int patternDuration = 1000;
  int numPatterns = totalDuration / patternDuration;
  for (int i = 0; i < numPatterns; i++) {
    digitalWrite(led, HIGH); delay(150);
    digitalWrite(led, LOW); delay(150);
    digitalWrite(led, HIGH); delay(150);
    digitalWrite(led, LOW); delay(550);
  }
}
void blinkContinuo(int totalDuration) {
  int blinkInterval = 250;
  int numBlinks = totalDuration / blinkInterval;
  for (int i = 0; i < numBlinks; i++) {
    digitalWrite(led, !digitalRead(led));
    delay(blinkInterval);
  }
}

// --- FUNÇÕES AUXILIARES ---
void conectaWifi() {
  WiFi.begin(ssid, password);
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Calibrando...");
  Serial.print("Calibrando...");

  int timeout = 20;
  while (WiFi.status() != WL_CONNECTED && timeout > 0) {
    delay(500);
    Serial.print(".");
    timeout--;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nCalibrado!");
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Calibrado!");
    delay(2000);
  } else {
    Serial.println("\nFalha ao conectar.");
    lcd.clear();
    lcd.print("Falha no WiFi");
    delay(3000);
  }
}

long mapear(long valor, long de_min, long de_max, long para_min, long para_max) {
  if (de_max - de_min == 0) return para_min;
  long valor_mapeado = (valor - de_min) * (para_max - para_min) / (de_max - de_min) + para_min;
  // Garante que o valor final esteja sempre entre para_min e para_max
  return max(min(para_min, para_max), min(max(para_min, para_max), valor_mapeado));
}

void setup() {
  Serial.begin(115200);
  Wire.begin();

  pinMode(umidadePin, INPUT);
  for (int i = 0; i < numLuzSensors; i++) {
    pinMode(luzPins[i], INPUT);
  }
  pinMode(led, OUTPUT);
  digitalWrite(led, LOW);

  lcd.init();
  lcd.backlight();
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Circuito");
  lcd.setCursor(0, 1);
  lcd.print("Inicializado!");
  delay(2000);

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

  // Lendo e processando sensores
  int valorUmidadeRaw = analogRead(umidadePin);
  long umidadePercent = mapear(valorUmidadeRaw, UMIDADE_MAX_ADC, UMIDADE_MIN_ADC, 0, 100);
  
  long totalLuzRaw = 0;
  for (int i = 0; i < numLuzSensors; i++) {
    totalLuzRaw += analogRead(luzPins[i]);
  }
  int valorLuzRaw = totalLuzRaw / numLuzSensors;
  
  // --- CHAMADA DA FUNÇÃO MAPEAMENTO CORRIGIDA ---
  // Mapeia do intervalo [ESCURO, CLARO] para o intervalo [0, 100]
  long luzPercent = mapear(valorLuzRaw, LUZ_CALIB_ESCURO, LUZ_CALIB_CLARO, 0, 100);
  
  Serial.printf("Leitura: Umidade RAW=%d -> %ld%% | Média Luz RAW=%d -> %ld%%\n", valorUmidadeRaw, umidadePercent, valorLuzRaw, luzPercent);
  
  StaticJsonDocument<200> doc;
  doc["umidade"] = umidadePercent;
  doc["luminosidade"] = luzPercent;
  String requestBody;
  serializeJson(doc, requestBody);
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Sincronizando dados...");
 
  http.begin(serverUrl);
  http.addHeader("Content-Type", "application/json");

  Serial.println("Enviando dados para o servidor...");
  blinkEnviandoDados(); 
  int httpResponseCode = http.POST(requestBody);

  if (httpResponseCode > 0) {
    String payload = http.getString();
    StaticJsonDocument<200> responseDoc;
    deserializeJson(responseDoc, payload);
    const char* instrucao = responseDoc["instrucao"];

    // Pula direto para mostrar os dados recebidos.
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.printf("U:%ld%% L:%ld%%", umidadePercent, luzPercent);
    lcd.setCursor(0, 1);
    lcd.print(instrucao);

  } else {
    Serial.printf("Erro na requisição HTTP: %d\n", httpResponseCode);
    lcd.clear();
    lcd.print("Erro Servidor");
    lcd.setCursor(0, 1);
    lcd.printf("Cod: %d", httpResponseCode);
  }

  http.end();

  Serial.println("Aguardando 5 segundos...");
  if (httpResponseCode > 0) {
    blinkContinuo(5000); 
  } else {
    blinkBuscaServidor(5000); 
  }
}
