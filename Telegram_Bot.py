from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup 
import asyncio
import logging
import requests 

# Configura o sistema de log para ver as mensagens do bot
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- TOKEN DO SEU BOT DO TELEGRAM ---
TELEGRAM_BOT_TOKEN = "7967447224:AAFHL3_vt3f0uxvD2K4h8Swd3daAAy-9VKs" 

# --- ENDEREÇO DO SEU SERVIDOR FLASK ---
FLASK_SERVER_URL = "http://127.0.0.1:5000" 

# --- DESCRIÇÕES E EMOJIS DAS PLANTAS ---
# ATUALIZADO COM AS PLANTAS E DESCRIÇÕES DA SUA TABELA
PLANT_DESCRIPTIONS = {
    "Cacto": "Essas plantas fascinantes, que muitas vezes associamos a paisagens áridas e espinhosas, são verdadeiras campeãs da sobrevivência. Encantando o publico com cores e tamanhos diversos e sua incrível capacidade de sobrevivência.",
    "Samambaia": "Com suas folhas delicadas e exuberantes, a samambaia é perfeita para ambientes com sombra ou luz indireta, trazendo frescor e um toque tropical.",
    "Hortelã": "A hortelã é uma erva aromática vibrante, ideal para chás e culinária. Cresce bem em solo úmido e gosta de luz moderada, sendo fácil de cuidar.",
    "Orquídea": "As orquídeas são símbolos de beleza e elegância. A maioria prefere luz indireta e alta umidade, florescendo com cuidado e atenção.",
    "Nenhuma": "Nenhuma planta específica selecionada. Condições genéricas aplicadas."
}

# EMOJIS ATUALIZADOS PARA AS NOVAS PLANTAS
PLANT_EMOJIS = {
    "Cacto": "🌵",
    "Samambaia": "🌿",
    "Hortelã": "🍃",
    "Orquídea": "🌸" 
}

# --- DEFINIÇÃO DOS TECLADOS INLINE ---

# Teclado do Menu Principal
def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🪴 Gerenciar Vaso", callback_data="gerenciar_vaso")],
        [InlineKeyboardButton("❓ Sobre o Bot", callback_data="sobre_o_bot")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Teclado do Menu de Gerenciamento do Vaso
def get_manage_pot_keyboard():
    keyboard = [
        [InlineKeyboardButton("🌱 Selecionar Planta no Vaso", callback_data="selecionar_planta")],
        [InlineKeyboardButton("📊 Status da Planta", callback_data="status_planta")],
        [InlineKeyboardButton("💡 Dicas de Cultivo", callback_data="dicas_cultivo")],
        [InlineKeyboardButton("↩️ Voltar ao Início", callback_data="selecionar_menu_principal")] 
    ]
    return InlineKeyboardMarkup(keyboard)

# Teclado para seleção de plantas
def get_plant_selection_keyboard():
    keyboard_plants = []
    for plant_name in PLANT_DESCRIPTIONS.keys():
        if plant_name != "Nenhuma":
            emoji = PLANT_EMOJIS.get(plant_name, "🌱")
            keyboard_plants.append(
                [InlineKeyboardButton(f"{emoji} {plant_name}", callback_data=f"PLANT_{plant_name}")]
            )
    keyboard_plants.append([InlineKeyboardButton("↩️ Voltar ao Gerenciamento", callback_data="gerenciar_vaso")]) 
    return InlineKeyboardMarkup(keyboard_plants)


# Função para o comando /start
async def start(update: Update, context):
    welcome_message = (
        "BOAS VINDAS!\n"
        "Agora você é dono de um vaso inteligente, pronto para começar?"
    )
    await update.message.reply_text(welcome_message, reply_markup=get_main_menu_keyboard())

# Função para lidar com callbacks dos botões
async def button_callback(update: Update, context):
    query = update.callback_query
    await query.answer() 

    if query.data == "selecionar_menu_principal":
        await query.edit_message_text(
            "Bem-vindo(a) de volta ao menu principal!", 
            reply_markup=get_main_menu_keyboard()
        )
    elif query.data == "gerenciar_vaso":
        await query.edit_message_text(
            "O que você gostaria de fazer com seu vaso?", 
            reply_markup=get_manage_pot_keyboard()
        )
    elif query.data == "sobre_o_bot":
        await query.edit_message_text(
            "Este é o seu Vaso Inteligente Bot! Desenvolvido para te ajudar a cuidar das suas plantas.\n"
            "Ele monitora umidade e luminosidade e te avisa quando sua planta precisa de algo.\n\n"
            "↩️ Voltar ao Início",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Voltar ao Início", callback_data="selecionar_menu_principal")]])
        )

    elif query.data == "selecionar_planta":
        await query.edit_message_text(
            "Certo! Qual planta está no vaso agora? Escolha uma das opções abaixo:", 
            reply_markup=get_plant_selection_keyboard()
        )
    elif query.data == "status_planta":
        try:
            response = requests.get(f"{FLASK_SERVER_URL}/get_full_status")
            status_data = response.json()

            if response.status_code == 200:
                plant_name = status_data.get("planta_selecionada", "Nenhuma")
                humidity = status_data.get("umidade_atual", 0)
                luminosity = status_data.get("luminosidade_atual", 0)
                instruction = status_data.get("instrucao_para_lcd", "Aguardando dados...")

                status_message = (
                    f"📊 STATUS ATUAL DO VASO\n\n"
                    f"🌱 Planta: {plant_name}\n"
                    f"💧 Umidade: {humidity}%\n"
                    f"☀️ Luminosidade: {luminosity}\n"
                    f"💬 Instrução para o LCD: {instruction}\n\n"
                    "↩️ Voltar ao Gerenciamento"
                )
                await query.edit_message_text(
                    status_message,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Voltar ao Gerenciamento", callback_data="gerenciar_vaso")]])
                )
            else:
                await query.edit_message_text(
                    f"❌ Erro ao obter status do servidor: {status_data.get('message', 'Erro desconhecido.')}\n\n↩️ Voltar ao Gerenciamento",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Voltar ao Gerenciamento", callback_data="gerenciar_vaso")]])
                )
                logger.error(f"Erro do servidor Flask ao obter status ({response.status_code}): {status_data.get('message')}")
        except requests.exceptions.ConnectionError:
            await query.edit_message_text(
                '❌ Não foi possível conectar ao servidor para obter o status. Verifique se ele está rodando.\n\n↩️ Voltar ao Gerenciamento',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Voltar ao Gerenciamento", callback_data="gerenciar_vaso")]])
            )
            logger.error("Erro de conexão com o servidor Flask ao obter status.")
        except Exception as e:
            await query.edit_message_text(
                f'❌ Ocorreu um erro inesperado ao obter o status: {e}\n\n↩️ Voltar ao Gerenciamento',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Voltar ao Gerenciamento", callback_data="gerenciar_vaso")]])
            )
            logger.error(f"Erro inesperado no bot ao obter status: {e}")

    elif query.data == "dicas_cultivo":
        try:
            response = requests.get(f"{FLASK_SERVER_URL}/get_full_status")
            status_data = response.json()

            if response.status_code == 200:
                all_plant_params = status_data.get("parametros_todas_plantas", {}) 
                
                tips_list_messages = []
                tips_list_messages.append("💡 DICAS DE CULTIVO IDEAL POR PLANTA\n")

                for plant_name, params in all_plant_params.items():
                    if plant_name == "Nenhuma": 
                        continue
                    
                    emoji = PLANT_EMOJIS.get(plant_name, "🌱")
                    umidade_min = params.get("umidade_min", "N/A")
                    umidade_max = params.get("umidade_max", "N/A")
                    luminosidade_min = params.get("luminosidade_min", "N/A")
                    luminosidade_max = params.get("luminosidade_max", "N/A")

                    tips_list_messages.append(
                        f"{emoji} <b>{plant_name}</b>\n" 
                        f"  💧 Umidade: {umidade_min}% a {umidade_max}%\n"
                        f"  ☀️ Luminosidade: {luminosidade_min} a {luminosidade_max}\n"
                    )
                
                tips_message = "\n".join(tips_list_messages) + "\n↩️ Voltar ao Gerenciamento"
                
                await query.edit_message_text(
                    tips_message,
                    parse_mode='HTML', 
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Voltar ao Gerenciamento", callback_data="gerenciar_vaso")]])
                )
            else:
                await query.edit_message_text(
                    f"❌ Erro ao obter dicas do servidor: {status_data.get('message', 'Erro desconhecido.')}\n\n↩️ Voltar ao Gerenciamento",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Voltar ao Gerenciamento", callback_data="gerenciar_vaso")]])
                )
                logger.error(f"Erro do servidor Flask ao obter dicas ({response.status_code}): {status_data.get('message')}")
        except requests.exceptions.ConnectionError:
            await query.edit_message_text(
                '❌ Não foi possível conectar ao servidor para obter as dicas. Verifique se ele está rodando.\n\n↩️ Voltar ao Gerenciamento',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Voltar ao Gerenciamento", callback_data="gerenciar_vaso")]])
            )
            logger.error("Erro de conexão com o servidor Flask ao obter dicas.")
        except Exception as e:
            await query.edit_message_text(
                f'❌ Ocorreu um erro inesperado ao obter as dicas: {e}\n\n↩️ Voltar ao Gerenciamento',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Voltar ao Gerenciamento", callback_data="gerenciar_vaso")]])
            )
            logger.error(f"Erro inesperado no bot ao obter dicas: {e}")
    
    # Lida com a seleção da planta pelos botões (PLANT_Cacto, PLANT_Manjericão, etc.)
    elif query.data.startswith("PLANT_"):
        nome_planta = query.data.replace("PLANT_", "").strip()
        user_chat_id = update.effective_chat.id 
        logger.info(f"Seleção de planta via botão: {nome_planta} do chat ID: {user_chat_id}")

        try:
            response = requests.post(
                f"{FLASK_SERVER_URL}/set_plant",
                json={"planta": nome_planta, "chat_id": user_chat_id} 
            )
            response_data = response.json() 

            if response.status_code == 200: 
                await query.edit_message_text(
                    f'✅ Planta definida para {nome_planta}!. Alertas de necessidades disponíveis no chat.\n\n↩️ Voltar ao Gerenciamento',
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Voltar ao Gerenciamento", callback_data="gerenciar_vaso")]])
                )
                description_text = PLANT_DESCRIPTIONS.get(nome_planta, "Descrição não encontrada.")
                charmed_description = (
                    f"✨🌿✨ DESCRIÇÃO {nome_planta.upper()} ✨🌿✨\n\n"
                    f"{description_text}\n\n"
                    f"💚💧☀️" 
                )
                await context.bot.send_message(chat_id=user_chat_id, text=charmed_description)
                logger.info(f"Servidor Flask respondeu: {response_data.get('message')}")
            else: 
                await query.edit_message_text(
                    f'❌ Erro ao definir planta: {response_data.get("message", "Erro desconhecido.")}\n\n↩️ Voltar ao Gerenciamento',
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Voltar ao Gerenciamento", callback_data="gerenciar_vaso")]])
                )
                logger.error(f"Erro do servidor Flask ({response.status_code}): {response_data.get('message')}")
        except requests.exceptions.ConnectionError as e:
            await query.edit_message_text(
                '❌ Não foi possível conectar ao servidor. Verifique se ele está rodando.\n\n↩️ Voltar ao Gerenciamento',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Voltar ao Gerenciamento", callback_data="gerenciar_vaso")]])
            )
            logger.error(f"Erro de conexão com o servidor Flask: {e}")
        except Exception as e:
            await query.edit_message_text(
                f'❌ Ocorreu um erro inesperado: {e}\n\n↩️ Voltar ao Gerenciamento',
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Voltar ao Gerenciamento", callback_data="gerenciar_vaso")]])
            )
            logger.error(f"Erro inesperado no bot: {e}")


# Função para o comando /planta [Nome da Planta] - Mantida para compatibilidade
async def definir_planta(update: Update, context): 
    if not context.args:
        await update.message.reply_text(
            'Por favor, use o formato: /planta [Nome da Planta]. '
            'Ex: /planta Cacto\n\n'
            'Ou use o menu "🌱 Selecionar Planta no Vaso" para uma experiência interativa.'
        )
        return

    nome_planta = " ".join(context.args).strip()
    user_chat_id = update.effective_chat.id 
    logger.info(f"Comando /planta recebido: {nome_planta} do chat ID: {user_chat_id}")

    if nome_planta not in PLANT_DESCRIPTIONS or nome_planta == "Nenhuma":
        await update.message.reply_text(
            f"Planta '{nome_planta}' não reconhecida. Plantas disponíveis: {', '.join(PLANT_DESCRIPTIONS.keys() - {'Nenhuma'})}."
        )
        return

    try:
        response = requests.post(
            f"{FLASK_SERVER_URL}/set_plant",
            json={"planta": nome_planta, "chat_id": user_chat_id} 
        )
        response_data = response.json() 

        if response.status_code == 200: 
            await update.message.reply_text(f'✅ Planta definida para {nome_planta}!. Alertas de necessidades disponíveis no chat.')
            description_text = PLANT_DESCRIPTIONS.get(nome_planta, "Descrição não encontrada.")
            charmed_description = (
                f"✨🌿✨ DESCRIÇÃO {nome_planta.upper()} ✨🌿✨\n\n"
                f"{description_text}\n\n"
                f"💚💧☀️" 
            )
            await context.bot.send_message(chat_id=user_chat_id, text=charmed_description)
            logger.info(f"Servidor Flask respondeu: {response_data.get('message')}")
        else: 
            await update.message.reply_text(f'❌ Erro ao definir planta: {response_data.get("message", "Erro desconhecido.")}')
            logger.error(f"Erro do servidor Flask ({response.status_code}): {response_data.get('message')}")
    except requests.exceptions.ConnectionError as e:
        await update.message.reply_text(
            '❌ Não foi possível conectar ao servidor. Verifique se ele está rodando.'
        )
        logger.error(f"Erro de conexão com o servidor Flask: {e}")
    except Exception as e:
        await update.message.reply_text(f'❌ Ocorreu um erro inesperado: {e}')
        logger.error(f"Erro inesperado no bot: {e}")

# Função para lidar com mensagens de texto que não são comandos
async def eco(update: Update, context):
    await update.message.reply_text(
        f'Eu só entendo comandos como /start ou /planta. Você disse: "{update.message.text}"'
    )

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build() 

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("planta", definir_planta)) 
    
    application.add_handler(CallbackQueryHandler(button_callback)) 

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, eco))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()














    
