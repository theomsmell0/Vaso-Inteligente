// main.ino - Código C++ para o ESP32 do Vaso Inteligente

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h> // Necessário para manipular JSON
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// --- CONFIGURAÇÕES DE WI-FI E SERVIDOR ---
const char* ssid = "ESTUFA 5G";
const char* password = "REDEALUNOS";
// IMPORTANTE: Substitua pelo IP do computador onde o servidor Flask está rodando!
const char* serverUrl = "http://192.168.0.24:5000/update_sensor_data";

// --- CONFIGURAÇÕES DOS PINOS ---
const int umidadePin = 34;
const int luzPin = 35;

// --- CALIBRAÇÃO DOS SENSORES (AJUSTE CONFORME SEU SENSOR) ---
// Mapeamento do ADC (0-4095) para porcentagem (0-100%)
const int UMIDADE_MAX_ADC = 4095; // Valor do ADC quando o sensor está totalmente seco
const int UMIDADE_MIN_ADC = 1800; // Valor do ADC quando o sensor está totalmente molhado

const int LUZ_MAX_ADC = 4095; // Escuro total
const int LUZ_MIN_ADC = 0;    // Luz máxima

// --- INICIALIZAÇÃO DOS COMPONENTES ---
LiquidCrystal_I2C lcd(0x27); // Endereço I2C, 16 colunas, 2 linhas
HTTPClient http;

// --- FUNÇÕES AUXILIARES ---

void conectaWifi() {
  WiFi.begin(ssid, password);
  lcd.clear();
  lcd.print("Conectando WiFi");
  Serial.print("Conectando ao WiFi...");

  int timeout = 20; // Timeout de 10 segundos (20 * 500ms)
  while (WiFi.status() != WL_CONNECTED && timeout > 0) {
    delay(500);
    Serial.print(".");
    lcd.print(".");
    timeout--;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi conectado!");
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

// Função para converter um valor de uma escala para outra
long mapear(long valor, long de_min, long de_max, long para_min, long para_max) {
  if (de_max - de_min == 0) return para_min;
  long valor_mapeado = (valor - de_min) * (para_max - para_min) / (de_max - de_min) + para_min;
  return max(para_min, min(para_max, valor_mapeado));
}


void setup() {
  Serial.begin(115200);
  
  // Inicia o barramento I2C para a comunicação com o LCD
  Wire.begin(); 
  
  // Configura os pinos dos sensores como entrada
  pinMode(umidadePin, INPUT);
  pinMode(luzPin, INPUT);

  // Inicia e liga o backlight do LCD
 lcd.begin(16, 2); // Inicializa com 16 colunas e 2 linhas
 lcd.backlight();
 lcd.print("Iniciando...");
  delay(1000);

  // Conecta ao Wi-Fi
  conectaWifi();
}

void loop() {
  // Verifica se o WiFi ainda está conectado
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Conexão WiFi perdida. Tentando reconectar...");
    conectaWifi();
    // Se não conseguir reconectar, espera um pouco e tenta de novo
    if (WiFi.status() != WL_CONNECTED) {
      delay(5000);
      return;
    }
  }

  // 1. Ler os valores brutos dos sensores
  int valorUmidadeRaw = analogRead(umidadePin);
  int valorLuzRaw = analogRead(luzPin);

  // 2. Converter os valores para porcentagem
  long umidadePercent = mapear(valorUmidadeRaw, UMIDADE_MAX_ADC, UMIDADE_MIN_ADC, 0, 100);
  long luzPercent = mapear(valorLuzRaw, LUZ_MAX_ADC, LUZ_MIN_ADC, 0, 100);

  Serial.printf("Leitura: Umidade RAW=%d -> %ld%% | Luz RAW=%d -> %ld%%\n", valorUmidadeRaw, umidadePercent, valorLuzRaw, luzPercent);

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

    // Desserializa a resposta JSON
    StaticJsonDocument<200> responseDoc;
    deserializeJson(responseDoc, payload);
    
    const char* instrucao = responseDoc["instrucao"]; // Extrai a instrução

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

  http.end(); // Libera os recursos

  // Espera antes da próxima leitura
  Serial.println("Aguardando 30 segundos...");
  delay(30000);
} 
