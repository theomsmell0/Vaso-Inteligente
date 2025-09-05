from flask import Flask, request, jsonify
from telegram import Bot
import asyncio
import threading
import logging
import queue 

# --- Configurações Iniciais do Flask e Logging ---
app = Flask(__name__)

# Configura o sistema de log para ver as mensagens do servidor
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO 
)
logger = logging.getLogger(__name__)

# --- CONFIGURAÇÕES DO TELEGRAM ---
TELEGRAM_BOT_TOKEN = 'YOUR TELEGRAM TOKEN' 
bot = Bot(token=TELEGRAM_BOT_TOKEN) 

TELEGRAM_CHAT_ID = 'CHAT ID' 

# --- VARIÁVEIS DE ESTADO DO VASO ---
estado_vaso = {
    "planta_selecionada": "Nenhuma", 
    "umidade_atual": 0,
    "luminosidade_atual": 0,
    "instrucao_para_lcd": "Aguardando dados...", 
    "ultima_notificacao_telegram": "",
    "chat_id_notificacao": None 
}

# --- PARÂMETROS DAS PLANTAS ---
parametros_plantas = {
    "Cacto": {
        "umidade_min": 10,  
        "umidade_max": 25,  
        "luminosidade_min": 700, 
        "luminosidade_max": 1000
    },
    "Samambaia": {
        "umidade_min": 70,  
        "umidade_max": 85,
        "luminosidade_min": 150, 
        "luminosidade_max": 400
    },
    "Hortelã": {
        "umidade_min": 55,  
        "umidade_max": 75,
        "luminosidade_min": 350, 
        "luminosidade_max": 650
    },
    "Orquídea": { 
        "umidade_min": 40,  
        "umidade_max": 60,  
        "luminosidade_min": 450, 
        "luminosidade_max": 750
    },
    "Nenhuma": { 
        "umidade_min": 0, "umidade_max": 100,
        "luminosidade_min": 0, "luminosidade_max": 1000
    }
}

# --- FILA DE MENSAGENS PARA O TELEGRAM E WORKER DEDICADO ---
telegram_message_queue = queue.Queue() 

async def enviar_mensagem_telegram(chat_id, mensagem):
    try:
        await bot.send_message(chat_id=chat_id, text=mensagem)
        logger.info(f"Mensagem Telegram enviada para {chat_id}: {mensagem}")
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem Telegram para {chat_id}: {e}")

async def telegram_worker():
    logger.info("Worker do Telegram iniciado.")
    while True:
        try:
            chat_id, message = await asyncio.to_thread(telegram_message_queue.get)
            if chat_id is None: 
                logger.info("Sinal de parada recebido para o worker do Telegram.")
                break
            await enviar_mensagem_telegram(chat_id, message)
            telegram_message_queue.task_done() 
        except Exception as e:
            logger.error(f"Erro no worker do Telegram: {e}")

def start_telegram_worker():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(telegram_worker())
    loop.close() 

# --- LÓGICA DE DECISÃO DA PLANTA ---
def tomar_decisao_planta():
    planta = estado_vaso["planta_selecionada"]
    umidade = estado_vaso["umidade_atual"]
    luminosidade = estado_vaso["luminosidade_atual"]
    chat_id_para_notificar = estado_vaso["chat_id_notificacao"] 

    if chat_id_para_notificar is None:
        logger.warning("Nenhum chat ID configurado para notificações. Mensagem não será enviada para o Telegram.")
        return estado_vaso["instrucao_para_lcd"]

    params = parametros_plantas.get(planta, parametros_plantas["Nenhuma"])

    instrucoes_lcd = [] 
    notificacoes_telegram = [] 

    # Lógica de Umidade
    if umidade < params["umidade_min"]:
        instrucoes_lcd.append("mais agua")
        notificacoes_telegram.append(f"🚨 Atenção! Sua {planta} precisa ser regada. Umidade atual: {umidade}%.")
    elif umidade > params["umidade_max"]:
        instrucoes_lcd.append("menos agua")
        notificacoes_telegram.append(f"💧 Excesso de água! Sua {planta} está com umidade muito alta: {umidade}%.")
    else:
        instrucoes_lcd.append("umidade ideal")

    # Lógica de Luminosidade
    if luminosidade < params["luminosidade_min"]:
        instrucoes_lcd.append("mais sol")
        notificacoes_telegram.append(f"☀️ Sua {planta} precisa de mais luz. Luminosidade atual: {luminosidade}.")
    elif luminosidade > params["luminosidade_max"]:
        instrucoes_lcd.append("menos sol")
        notificacoes_telegram.append(f"🔥 Sua {planta} está pegando muito sol. Luminosidade atual: {luminosidade}.")
    else:
        instrucoes_lcd.append("luz ideal") # ALTERADO AQUI!

    # Define a instrução final para o LCD
    instrucao_final_lcd = ", ".join(instrucoes_lcd) 
    estado_vaso["instrucao_para_lcd"] = instrucao_final_lcd

    # Lógica para as notificações do Telegram
    if not notificacoes_telegram:
        if estado_vaso["ultima_notificacao_telegram"] != "✅ Tudo certo!":
            notificacao_telegram_final = f"✅ Sua {planta} está com condições perfeitas agora!"
            estado_vaso["ultima_notificacao_telegram"] = "✅ Tudo certo!"
            telegram_message_queue.put((chat_id_para_notificar, notificacao_telegram_final))
            logger.info(f"Mensagem de 'tudo certo' enfileirada para Telegram (Chat ID: {chat_id_para_notificar}).")
    else:
        notificacao_telegram_final = "\n".join(notificacoes_telegram) 
        if notificacao_telegram_final != estado_vaso["ultima_notificacao_telegram"]:
            telegram_message_queue.put((chat_id_para_notificar, notificacao_telegram_final))
            estado_vaso["ultima_notificacao_telegram"] = notificacao_telegram_final
            logger.info(f"Mensagem enfileirada para Telegram (Chat ID: {chat_id_para_notificar}): '{notificacao_telegram_final}'")


    logger.info(f"Decisão para {planta}: {instrucao_final_lcd}.")
    return instrucao_final_lcd

# --- ROTAS DA API FLASK ---

@app.route('/update_sensor_data', methods=['POST'])
def update_sensor_data():
    logger.info(f"CONFIRMAÇÃO: Conexão recebida do ESP32 no IP {request.remote_addr}")

    data = request.json
    if not data:
        logger.warning("Requisição /update_sensor_data: Nenhum dado JSON recebido.")
        return jsonify({"status": "error", "message": "Nenhum dado JSON recebido"}), 400

    umidade = data.get('umidade')
    luminosidade = data.get('luminosidade')

    if umidade is None or luminosidade is None:
        logger.warning(f"Requisição /update_sensor_data: Dados ausentes - umidade={umidade}, luminosidade={luminosidade}")
        return jsonify({"status": "error", "message": "Dados de umidade ou luminosidade ausentes"}), 400

    try:
        estado_vaso["umidade_atual"] = float(umidade)
        estado_vaso["luminosidade_atual"] = float(luminosidade)
        logger.info(f"--> Dados recebidos: Umidade={umidade}%, Luminosidade={luminosidade}")

        instrucao = tomar_decisao_planta()

        return jsonify({"status": "success", "message": "Dados recebidos", "instrucao": instrucao})
    except ValueError:
        logger.error(f"Requisição /update_sensor_data: Valores inválidos - umidade={umidade}, luminosidade={luminosidade}")
        return jsonify({"status": "error", "message": "Valores de umidade/luminosidade inválidos"}), 400


@app.route('/get_instruction', methods=['GET'])
def get_instruction():
    instrucao = estado_vaso["instrucao_para_lcd"]
    logger.info(f"ESP32 solicitou instrução para LCD: '{instrucao}'")
    return jsonify({"instrucao": instrucao})

@app.route('/get_full_status', methods=['GET'])
def get_full_status():
    planta_selecionada = estado_vaso["planta_selecionada"]
    
    current_status = {
        "planta_selecionada": planta_selecionada,
        "umidade_atual": estado_vaso["umidade_atual"],
        "luminosidade_atual": estado_vaso["luminosidade_atual"],
        "instrucao_para_lcd": estado_vaso["instrucao_para_lcd"],
        "parametros_todas_plantas": parametros_plantas
    }
    logger.info(f"Bot solicitou status completo: {current_status}")
    return jsonify(current_status)


@app.route('/set_plant', methods=['POST'])
def set_plant():
    data = request.json
    if not data or 'planta' not in data or 'chat_id' not in data:
        logger.warning("Requisição /set_plant: Dados ausentes (planta ou chat_id).")
        return jsonify({"status": "error", "message": "Nome da planta ou chat_id ausente"}), 400

    nova_planta = data['planta'].strip()
    novo_chat_id = data['chat_id']

    if nova_planta in parametros_plantas:
        estado_vaso["planta_selecionada"] = nova_planta
        estado_vaso["chat_id_notificacao"] = novo_chat_id

        estado_vaso["ultima_notificacao_telegram"] = "Planta definida e notificações ativadas para este chat."
        logger.info(f"Planta selecionada atualizada para: {nova_planta}. Notificações para chat ID: {novo_chat_id}")

        tomar_decisao_planta()
        return jsonify({"status": "success", "message": f"Planta definida para {nova_planta}. O bot enviará a confirmação."})
    else:
        logger.warning(f"Requisição /set_plant: Planta '{nova_planta}' não encontrada nos parâmetros.")
        return jsonify({"status": "error", "message": f"Planta '{nova_planta}' não encontrada na base de dados. Plantas disponíveis: {', '.join(parametros_plantas.keys())}"}), 404

@app.route('/status', methods=['GET'])
def get_status():
    logger.info("Requisição /status: Retornando estado atual.")
    return jsonify(estado_vaso)

# --- INICIALIZAÇÃO DO SERVIDOR FLASK ---
if __name__ == '__main__':
    telegram_thread = threading.Thread(target=start_telegram_worker, daemon=True)
    telegram_thread.start()
    logger.info("Thread do worker do Telegram iniciada.")

    app.run(host='0.0.0.0', port=5000, debug=False)
