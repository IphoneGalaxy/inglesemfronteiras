#!/usr/bin/env python3
"""
EnglishFlow Bot — @inglesemfronteiras_bot
Aprenda inglês com professores nativos via Telegram.
"""

import os
import logging
import uuid
import requests
from datetime import datetime, timedelta
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from pix_utils import generate_pix_payload, generate_qr_bytes, get_plano_info
from supabase import create_client

# Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://rrfnfqlijjirxonhtpde.supabase.co")
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
sb = create_client(SUPABASE_URL, SUPABASE_KEY)

# Site URL
SITE_URL = os.environ.get("ENGLISHFLOW_SITE", "https://inglesemfronteiras.vercel.app")
ADMIN_ID = int(os.environ.get("ENGLISHFLOW_ADMIN_ID", "392080710"))

# Pagamentos pendentes
pagamentos_pendentes = {}

# ---------- CONFIG ----------
# ⚠️ Token OBRIGATORIO via variavel de ambiente
TOKEN = os.environ["ENGLISHFLOW_BOT_TOKEN"]

# States for conversation handler (agendamento)
ESCOLHER_PROFESSOR, ESCOLHER_DIA, ESCOLHER_HORARIO = range(3)

# ---------- LOGGING ----------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------- DATA (mock) ----------
PROFESSORES = [
    {"id": "sarah", "nome": "👩‍💼 Sarah Johnson", "especialidade": "Business English", "rating": "⭐ 4.9"},
    {"id": "michael", "nome": "🧔 Michael Torres", "especialidade": "Conversação", "rating": "⭐ 4.8"},
    {"id": "emily", "nome": "👩‍🏫 Emily Parker", "especialidade": "Preparatório TOEFL", "rating": "⭐ 5.0"},
    {"id": "david", "nome": "🧑‍💻 David Chen", "especialidade": "Inglês para Viagem", "rating": "⭐ 4.7"},
]

PLANOS = [
    {"id": "basico",  "nome": "💚 Básico",  "aulas": "4 aulas/mês", "grupo": "Grupos de 3 alunos", "preco": "R$ 30/mês"},
    {"id": "pro",     "nome": "⭐ Pro",      "aulas": "8 aulas/mês", "grupo": "Grupos de 3 alunos", "preco": "R$ 55/mês", "destaque": True},
    {"id": "premium", "nome": "👑 Premium", "aulas": "12 aulas/mês","grupo": "Aulas individuais",  "preco": "R$ 80/mês"},
]

AULAS_MOCK = [
    {"data": "20/06 - 19:00", "professor": "Sarah Johnson", "status": "✅ Confirmada"},
    {"data": "22/06 - 14:00", "professor": "Michael Torres", "status": "⏳ Aguardando"},
]

# ---------- KEYBOARDS ----------

def menu_principal():
    """Keyboard inline do menu principal."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Agendar aula", callback_data="menu_agendar")],
        [InlineKeyboardButton("👩‍🏫 Ver professores", callback_data="menu_professores")],
        [InlineKeyboardButton("💳 Planos e precos", callback_data="menu_planos")],
        [InlineKeyboardButton("📚 Minhas aulas", callback_data="menu_minhasaulas")],
        [InlineKeyboardButton("❓ Ajuda", callback_data="menu_ajuda")],
        [InlineKeyboardButton("💬 Falar com suporte", url=f"https://t.me/{os.environ.get('SUPPORT_USERNAME', 'inglesemfronteiras_bot')}")],
    ])


def voltar_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Voltar ao menu", callback_data="voltar_menu")]
    ])

def professores_keyboard():
    """Inline keyboard com lista de professores."""
    botoes = []
    for p in PROFESSORES:
        botoes.append([InlineKeyboardButton(
            f"{p['nome']} — {p['especialidade']} {p['rating']}",
            callback_data=f"prof_{p['id']}"
        )])
    botoes.append([InlineKeyboardButton("🔙 Voltar ao menu", callback_data="voltar_menu")])
    return InlineKeyboardMarkup(botoes)

def dias_keyboard():
    """Próximos 7 dias para agendamento."""
    botoes = []
    hoje = datetime.now()
    for i in range(1, 8):
        dia = hoje + timedelta(days=i)
        label = dia.strftime("%d/%m (%a)")
        callback = f"dia_{dia.strftime('%Y-%m-%d')}"
        botoes.append([InlineKeyboardButton(label, callback_data=callback)])
    botoes.append([InlineKeyboardButton("🔙 Voltar", callback_data="menu_agendar")])
    return InlineKeyboardMarkup(botoes)

def horarios_keyboard():
    """Slots de horário disponíveis."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🕖 07:00 - 07:30", callback_data="hora_07:00")],
        [InlineKeyboardButton("🕘 09:00 - 09:30", callback_data="hora_09:00")],
        [InlineKeyboardButton("🕑 14:00 - 14:30", callback_data="hora_14:00")],
        [InlineKeyboardButton("🕖 19:00 - 19:30", callback_data="hora_19:00")],
        [InlineKeyboardButton("🕘 21:00 - 21:30", callback_data="hora_21:00")],
        [InlineKeyboardButton("🔙 Escolher outro dia", callback_data="menu_agendar")],
    ])

# ---------- HANDLERS ----------

async def enviar_lembrete(context: ContextTypes.DEFAULT_TYPE):
    """Callback do JobQueue — envia lembrete de aula."""
    job = context.job
    data = job.data
    try:
        await context.bot.send_message(
            chat_id=data["chat_id"],
            text=(
                f"⏰ *Lembrete de aula!*\n\n"
                f"👩‍🏫 Professor(a): *{data['prof']}*\n"
                f"📅 Data: {data['data']}\n"
                f"🕐 Horario: {data['hora']} (BRT)\n\n"
                f"{'🔔 Sua aula e amanha!' if data['tipo'] == '24h' else '🚀 Sua aula comeca em 1 hora!'}"
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Erro ao enviar lembrete: {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start — Boas-vindas + menu principal."""
    user = update.effective_user
    mensagem = (
        f"👋 *Hello, {user.first_name}! Welcome to EnglishFlow!*\n\n"
        f"🇺🇸 Aprenda ingles com professores *nativos americanos* "
        f"direto pelo Telegram. Sem apps, sem burocracia.\n\n"
        f"📅 *Agende sua aula* em 2 minutos\n"
        f"👩‍🏫 *Escolha seu professor* entre 4 especialistas\n"
        f"💳 *Pague via PIX* com QR Code\n"
        f"🎓 *Acesse materiais exclusivos* no painel do aluno\n"
        f"🆓 *Primeira aula gratuita* em qualquer plano\n\n"
        f"Escolha uma opcao abaixo para comecar: 👇"
    )
    await update.message.reply_text(
        mensagem,
        parse_mode="Markdown",
        reply_markup=menu_principal()
    )

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /ajuda — FAQ do bot."""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Falar com suporte", url="https://t.me/inglesemfronteiras_bot")],
        [InlineKeyboardButton("🔙 Voltar ao menu", callback_data="voltar_menu")],
    ])
    mensagem = (
        "❓ *Central de Ajuda EnglishFlow*\n\n"
        "*Comandos disponíveis:*\n"
        "/start — Menu principal\n"
        "/agendar — Agendar uma aula\n"
        "/professores — Lista de professores\n"
        "/planos — Planos e preços\n"
        "/minhasaulas — Suas aulas agendadas\n"
        "/ajuda — Esta mensagem\n\n"
        "*Dúvidas frequentes:*\n"
        "• As aulas são via chat de voz e texto no Telegram\n"
        "• Reagendamento grátis com 12h de antecedência\n"
        "• Primeira aula é gratuita em todos os planos\n"
        "• Professores 100% nativos americanos 🇺🇸\n\n"
        "Precisa de ajuda? Toque no botão abaixo! 👇"
    )
    await update.message.reply_text(
        mensagem,
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def agendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /agendar — Inicia fluxo de agendamento."""
    mensagem = (
        "📅 *Agendar Aula*\n\n"
        "Escolha o professor com quem você quer aprender hoje:"
    )
    await update.message.reply_text(
        mensagem,
        parse_mode="Markdown",
        reply_markup=professores_keyboard()
    )

async def professores(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /professores — Lista professores."""
    mensagem = "👩‍🏫 *Nossos Professores Nativos* 🇺🇸\n\n"
    for p in PROFESSORES:
        status = "🟢 Online agora" if p['id'] != 'emily' else "⚫ Visto há 2h"
        mensagem += (
            f"*{p['nome']}*\n"
            f"  📌 {p['especialidade']}\n"
            f"  {p['rating']}  |  {status}\n\n"
        )
    mensagem += "Escolha um professor para agendar:"
    await update.message.reply_text(
        mensagem,
        parse_mode="Markdown",
        reply_markup=professores_keyboard()
    )

async def planos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /planos — Mostra planos disponíveis."""
    mensagem = "💳 *Nossos Planos*\n\n"
    for p in PLANOS:
        destaque = " 🔥 MAIS POPULAR" if p.get("destaque") else ""
        mensagem += (
            f"*{p['nome']}{destaque}*\n"
            f"  📚 {p['aulas']}\n"
            f"  👥 {p['grupo']}\n"
            f"  💰 {p['preco']}\n\n"
        )
    mensagem += "✅ *Primeira aula grátis em todos os planos!*\nEscolha um plano para pagar com PIX:"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💚 Plano Básico — R$ 30/mês", callback_data="pagar_basico")],
        [InlineKeyboardButton("⭐ Plano Pro — R$ 55/mês", callback_data="pagar_pro")],
        [InlineKeyboardButton("👑 Plano Premium — R$ 80/mês", callback_data="pagar_premium")],
        [InlineKeyboardButton("🔙 Voltar ao menu", callback_data="voltar_menu")],
    ])
    await update.message.reply_text(
        mensagem,
        parse_mode="Markdown",
        reply_markup=keyboard
    )

async def minhasaulas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /minhasaulas — Próximas aulas agendadas."""
    if AULAS_MOCK:
        mensagem = "📚 *Suas Aulas*\n\n"
        for a in AULAS_MOCK:
            mensagem += f"{a['status']} *{a['data']}* — com {a['professor']}\n"
        mensagem += "\n⏰ Lembretes automáticos: 24h, 1h e 15min antes de cada aula."
    else:
        mensagem = "📚 *Nenhuma aula agendada*\n\nUse /agendar para marcar sua primeira aula grátis! 🎉"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Agendar nova aula", callback_data="menu_agendar")],
        [InlineKeyboardButton("🔙 Voltar ao menu", callback_data="voltar_menu")],
    ])
    await update.message.reply_text(
        mensagem,
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# ---------- CALLBACK HANDLERS ----------

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processa todos os cliques em botões inline."""
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user.first_name

    # Menu principal
    if data == "voltar_menu":
        await query.edit_message_text(
            f"👋 *Olá, {user}!* O que você quer fazer?",
            parse_mode="Markdown",
            reply_markup=menu_principal()
        )

    elif data == "menu_agendar":
        await query.edit_message_text(
            "📅 *Agendar Aula*\n\nEscolha o professor:",
            parse_mode="Markdown",
            reply_markup=professores_keyboard()
        )

    elif data == "menu_professores":
        mensagem = "👩‍🏫 *Nossos Professores Nativos* 🇺🇸\n\n"
        for p in PROFESSORES:
            status = "🟢 Online" if p['id'] != 'emily' else "⚫ Offline"
            mensagem += f"*{p['nome']}* — {p['especialidade']} {p['rating']} | {status}\n\n"
        mensagem += "Escolha um professor para agendar:"
        await query.edit_message_text(
            mensagem,
            parse_mode="Markdown",
            reply_markup=professores_keyboard()
        )

    elif data == "menu_planos":
        mensagem = "💳 *Planos EnglishFlow*\n\n"
        for p in PLANOS:
            destaque = " 🔥 MAIS POPULAR" if p.get("destaque") else ""
            mensagem += (
                f"*{p['nome']}{destaque}*\n"
                f"📚 {p['aulas']} | 👥 {p['grupo']} | 💰 {p['preco']}\n\n"
            )
        mensagem += "✅ Primeira aula grátis em todos!\nEscolha um plano para pagar via PIX:"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💚 Básico — R$ 30", callback_data="pagar_basico")],
            [InlineKeyboardButton("⭐ Pro — R$ 55", callback_data="pagar_pro")],
            [InlineKeyboardButton("👑 Premium — R$ 80", callback_data="pagar_premium")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="voltar_menu")],
        ])

        await query.edit_message_text(
            mensagem,
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    elif data == "menu_minhasaulas":
        if AULAS_MOCK:
            mensagem = "📚 *Suas Aulas*\n\n"
            for a in AULAS_MOCK:
                mensagem += f"{a['status']} *{a['data']}* — {a['professor']}\n"
            mensagem += "\n⏰ Lembretes: 24h, 1h, 15min antes."
        else:
            mensagem = "📚 Nenhuma aula ainda.\nUse /agendar para começar!"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📅 Agendar aula", callback_data="menu_agendar")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="voltar_menu")],
        ])
        await query.edit_message_text(
            mensagem,
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    elif data == "menu_ajuda":
        ajuda_texto = (
            "❓ *Central de Ajuda*\n\n"
            "/start — Menu\n/agendar — Agendar aula\n"
            "/professores — Professores\n/planos — Planos\n"
            "/minhasaulas — Aulas\n/ajuda — Ajuda\n\n"
            "💡 Dica: primeira aula é grátis!"
        )
        await query.edit_message_text(
            ajuda_texto,
            parse_mode="Markdown",
            reply_markup=voltar_menu()
        )

    # Seleção de professor — mostra dias
    elif data.startswith("prof_"):
        prof_id = data.replace("prof_", "")
        professor = next((p for p in PROFESSORES if p['id'] == prof_id), None)
        if professor:
            context.user_data['professor_escolhido'] = professor
            await query.edit_message_text(
                f"👩‍🏫 *{professor['nome']}* — {professor['especialidade']}\n\n"
                f"📅 Escolha o dia da sua aula:",
                parse_mode="Markdown",
                reply_markup=dias_keyboard()
            )

    # Seleção de dia — mostra horários
    elif data.startswith("dia_"):
        dia = data.replace("dia_", "")
        dia_formatado = datetime.strptime(dia, "%Y-%m-%d").strftime("%d/%m/%Y (%A)")
        context.user_data['dia_escolhido'] = dia
        professor = context.user_data.get('professor_escolhido', PROFESSORES[0])
        await query.edit_message_text(
            f"📅 *Dia escolhido:* {dia_formatado}\n"
            f"👩‍🏫 *Professor(a):* {professor['nome']}\n\n"
            f"🕐 Escolha o horário:",
            parse_mode="Markdown",
            reply_markup=horarios_keyboard()
        )

    # Confirmação do agendamento
    elif data.startswith("hora_"):
        hora = data.replace("hora_", "")
        professor = context.user_data.get('professor_escolhido', PROFESSORES[0])
        dia = context.user_data.get('dia_escolhido', datetime.now().strftime("%Y-%m-%d"))
        dia_fmt = datetime.strptime(dia, "%Y-%m-%d").strftime("%d/%m")

        confirmacao = (
            f"✅ *Aula agendada com sucesso!*\n\n"
            f"👩‍🏫 *Professor(a):* {professor['nome']}\n"
            f"📅 *Data:* {dia_fmt}\n"
            f"🕐 *Horário:* {hora} (BRT)\n"
            f"📌 *Especialidade:* {professor['especialidade']}\n\n"
            f"⏰ Você receberá lembretes:\n"
            f"• 24 horas antes\n"
            f"• 1 hora antes\n"
            f"• 15 minutos antes\n\n"
            f"💬 O link da aula chega aqui no Telegram.\n"
            f"🎉 *Bons estudos!* 🇺🇸"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📚 Ver minhas aulas", callback_data="menu_minhasaulas")],
            [InlineKeyboardButton("🔙 Voltar ao menu", callback_data="voltar_menu")],
        ])
        await query.edit_message_text(
            confirmacao,
            parse_mode="Markdown",
            reply_markup=keyboard
        )

        # ⏰ Agendar lembretes automaticos
        try:
            dt_str = f"{dia} {hora}:00"
            aula_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            chat_id = query.message.chat_id
            prof_nome = professor['nome']

            # Lembrete 24h antes
            remind_24h = aula_dt - timedelta(hours=24)
            if remind_24h > datetime.now():
                context.job_queue.run_once(
                    enviar_lembrete,
                    when=remind_24h,
                    data={"chat_id": chat_id, "prof": prof_nome, "tipo": "24h", "data": dia_fmt, "hora": hora},
                    name=f"lembrete_24h_{chat_id}_{dia}_{hora}"
                )

            # Lembrete 1h antes
            remind_1h = aula_dt - timedelta(hours=1)
            if remind_1h > datetime.now():
                context.job_queue.run_once(
                    enviar_lembrete,
                    when=remind_1h,
                    data={"chat_id": chat_id, "prof": prof_nome, "tipo": "1h", "data": dia_fmt, "hora": hora},
                    name=f"lembrete_1h_{chat_id}_{dia}_{hora}"
                )

            logger.info(f"Lembretes agendados para aula de {chat_id}: {dia_fmt} {hora}")
        except Exception as e:
            logger.error(f"Erro ao agendar lembretes: {e}")

    # ═══════ PAGAMENTO PIX ═══════
    # Confirmação do plano
    elif data.startswith("pagar_"):
        plano_id = data.replace("pagar_", "")
        plano = get_plano_info(plano_id)
        if not plano:
            await query.edit_message_text("Plano não encontrado. Tente novamente.", reply_markup=voltar_menu())
            return

        context.user_data['plano_pagamento'] = plano
        mensagem = (
            f"💳 *{plano['nome']}*\n\n"
            f"📚 4 aulas/mês em grupo\n"
            f"💰 *Valor: R$ {plano['valor']:.2f}*\n\n"
            f"Pagamento via PIX — rápido e seguro.\n"
            f"Deseja prosseguir para o pagamento?"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"💰 Pagar R$ {plano['valor']:.2f} via PIX", callback_data=f"pix_gerar_{plano_id}")],
            [InlineKeyboardButton("🔙 Escolher outro plano", callback_data="menu_planos")],
        ])
        await query.edit_message_text(
            mensagem,
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    # Gerar QR Code PIX
    elif data.startswith("pix_gerar_"):
        plano_id = data.replace("pix_gerar_", "")
        plano = context.user_data.get('plano_pagamento') or get_plano_info(plano_id)
        if not plano:
            await query.edit_message_text("Erro ao gerar pagamento. Tente novamente.", reply_markup=voltar_menu())
            return

        await query.edit_message_text(
            f"⏳ Gerando QR Code PIX para *{plano['nome']}*...",
            parse_mode="Markdown"
        )

        # Gera QR Code
        valor = plano['valor']
        try:
            pix_code = generate_pix_payload(valor, plano['nome'])
            qr_bytes = generate_qr_bytes(valor, plano['nome'])
        except Exception as e:
            logger.error(f"Erro ao gerar PIX: {e}")
            await query.edit_message_text(
                "❌ Erro ao gerar QR Code. Tente novamente mais tarde.",
                reply_markup=voltar_menu()
            )
            return

        # Envia QR Code como foto
        qr_bytes.seek(0)
        await query.message.reply_photo(
            photo=qr_bytes,
            caption=(
                f"📱 *QR Code PIX — {plano['nome']}*\n"
                f"💰 Valor: *R$ {valor:.2f}*\n\n"
                f"📷 *Escaneie o QR Code* no app do seu banco\n"
                f"ou copie o código PIX abaixo 👇"
            ),
            parse_mode="Markdown"
        )

        # Envia código copia-e-cola
        await query.message.reply_text(
            f"📋 *Código PIX copia-e-cola:*\n\n"
            f"`{pix_code}`\n\n"
            f"⬆️ Copie o código acima e cole no app do banco\n"
            f"na opção \"PIX copia e cola\".",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Já paguei! Enviar comprovante", callback_data="comprovante_enviar")],
                [InlineKeyboardButton("🔙 Voltar ao menu", callback_data="voltar_menu")],
            ])
        )

        # Guarda info do pagamento
        context.user_data['pagamento_confirmacao'] = {
            'plano': plano,
            'valor': valor,
            'pix_code': pix_code
        }

    # Usuário clicou "Já paguei"
    elif data == "comprovante_enviar":
        await query.edit_message_text(
            "📸 *Enviar Comprovante*\n\n"
            "Envie uma foto ou print do comprovante de pagamento.\n"
            "Assim que recebermos, seu plano será ativado! ✅\n\n"
            "Basta enviar a imagem aqui no chat 👇",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Cancelar", callback_data="voltar_menu")],
            ])
        )
        context.user_data['aguardando_comprovante'] = True

    # ═══════ ADMIN: APROVAR/REJEITAR PAGAMENTO ═══════
    elif data.startswith("adm_aprovar_"):
        if query.from_user.id != ADMIN_ID:
            await query.answer("Apenas o administrador pode aprovar pagamentos.", show_alert=True)
            return
        comp_id = data.replace("adm_aprovar_", "")
        pagto = pagamentos_pendentes.pop(comp_id, None)
        if not pagto:
            await query.edit_message_caption(caption="Pagamento nao encontrado (ja processado).")
            return

        # Criar usuario no Supabase
        access_code = None
        try:
            code = str(uuid.uuid4())[:8].upper()
            r = sb.table('users').insert({
                'telegram_id': pagto["telegram_id"],
                'name': pagto["user_name"],
                'plan': pagto["plano_id"],
                'access_code': code
            }).execute()
            if r.data:
                access_code = code
                logger.info(f"Usuario Supabase criado: {pagto['user_name']} — code: {code}")
        except Exception as e:
            logger.error(f"Erro Supabase ao aprovar: {e}")

        # Atualiza mensagem do admin
        status = f"✅ APROVADO — Codigo: {access_code}" if access_code else "✅ APROVADO (servidor offline)"
        await query.edit_message_caption(
            caption=f"{query.message.caption}\n\n{status}"
        )

        # Envia codigo ao aluno
        if access_code:
            try:
                await context.bot.send_message(
                    chat_id=pagto["chat_id"],
                    text=(
                        f"🎉 Pagamento aprovado! Acesso liberado!\n"
                        f"━━━━━━━━━━━━━━━━━━\n\n"
                        f"💰 Plano: {pagto['plano_nome']}\n"
                        f"💵 Valor: R$ {pagto['valor']:.2f}\n"
                        f"🔑 Codigo: {access_code}\n\n"
                        f"🌐 Acesse seu painel aqui:\n"
                        f"{SITE_URL}/login\n\n"
                        f"📚 Bons estudos!"
                    )
                )
            except Exception as e:
                logger.error(f"Erro ao notificar aluno aprovado: {e}")
        else:
            try:
                await context.bot.send_message(
                    chat_id=pagto["chat_id"],
                    text="✅ Pagamento aprovado! O codigo de acesso sera enviado em instantes."
                )
            except:
                pass

    elif data.startswith("adm_rejeitar_"):
        if query.from_user.id != ADMIN_ID:
            await query.answer("Apenas o administrador pode rejeitar pagamentos.", show_alert=True)
            return
        comp_id = data.replace("adm_rejeitar_", "")
        pagto = pagamentos_pendentes.pop(comp_id, None)
        if not pagto:
            await query.edit_message_caption(caption="Pagamento nao encontrado (ja processado).")
            return

        await query.edit_message_caption(
            caption=f"{query.message.caption}\n\n❌ REJEITADO"
        )

        # Notifica o aluno
        try:
            await context.bot.send_message(
                chat_id=pagto["chat_id"],
                text=(
                    f"❌ *Pagamento nao confirmado*\n\n"
                    f"Infelizmente nao conseguimos confirmar seu pagamento.\n"
                    f"💰 Plano: *{pagto['plano_nome']}* — R$ {pagto['valor']:.2f}\n\n"
                    f"Verifique se o comprovante esta legivel e tente novamente.\n"
                    f"Use /planos para fazer uma nova tentativa."
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Erro ao notificar aluno rejeitado: {e}")


async def mensagem_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde mensagens de texto não-comando."""
    texto = update.message.text.lower()

    if any(p in texto for p in ["oi", "olá", "ola", "hey", "hi"]):
        await update.message.reply_text(
            f"👋 Olá! Use /start para ver o menu principal ou /agendar para marcar sua aula grátis! 🇺🇸"
        )
    elif any(p in texto for p in ["aula", "agendar", "horario", "horário"]):
        await agendar(update, context)
    elif any(p in texto for p in ["preço", "preco", "preço", "valor", "plano", "planos"]):
        await planos(update, context)
    elif any(p in texto for p in ["professor", "professores", "nativo"]):
        await professores(update, context)
    else:
        await update.message.reply_text(
            "🤔 Não entendi. Use /start para ver o menu ou /ajuda para tirar dúvidas! 💬"
        )

# ---------- HANDLER DE FOTO (COMPROVANTE) ----------

async def foto_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recebe foto/comprovante de pagamento e encaminha para aprovacao do admin."""
    if not context.user_data.get('aguardando_comprovante'):
        await update.message.reply_text(
            "📸 Recebi sua imagem! Se quiser enviar um comprovante de pagamento, "
            "use o botao \"Ja paguei\" no menu de planos.",
            reply_markup=voltar_menu()
        )
        return

    pagto = context.user_data.get('pagamento_confirmacao', {})
    plano = pagto.get('plano', {})
    valor = pagto.get('valor', 0)
    plano_id = plano.get('id', 'basico')

    user = update.effective_user
    telegram_id = str(user.id)
    name = user.full_name or user.first_name
    username = f"@{user.username}" if user.username else "sem username"

    # Pega a foto
    photo = update.message.photo[-1]  # Maior resolucao
    photo_file = await photo.get_file()

    # ── Encaminhar para o ADMIN ──
    comprovante_id = f"pag_{telegram_id}_{datetime.now().strftime('%H%M%S')}"
    pagamentos_pendentes[comprovante_id] = {
        "telegram_id": telegram_id,
        "user_name": name,
        "username": username,
        "plano_id": plano_id,
        "plano_nome": plano.get('nome', plano_id),
        "valor": valor,
        "chat_id": update.message.chat_id
    }

    try:
        # Envia foto pro admin
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo_file.file_id,
            caption=(
                f"📸 *NOVO COMPROVANTE*\n\n"
                f"👤 *Aluno:* {name}\n"
                f"📱 Telegram: {username} (ID: {telegram_id})\n"
                f"💳 *Plano:* {plano.get('nome', '')}\n"
                f"💰 *Valor:* R$ {valor:.2f}\n"
                f"🆔 Ref: {comprovante_id}\n\n"
                f"Verifique o comprovante no seu app do banco."
            ),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ APROVAR", callback_data=f"adm_aprovar_{comprovante_id}"),
                    InlineKeyboardButton("❌ REJEITAR", callback_data=f"adm_rejeitar_{comprovante_id}")
                ]
            ])
        )
        logger.info(f"Comprovante encaminhado ao admin: {comprovante_id}")
    except Exception as e:
        logger.error(f"Erro ao encaminhar comprovante ao admin: {e}")

    # ── Responde ao aluno ──
    await update.message.reply_text(
        f"✅ *Comprovante enviado para analise!*\n\n"
        f"📸 Seu comprovante foi encaminhado para nossa equipe.\n"
        f"💰 Plano: *{plano.get('nome', '')}* — R$ {valor:.2f}\n\n"
        f"⏳ Voce recebera seu codigo de acesso assim que o\n"
        f"pagamento for confirmado (geralmente em ate 5 minutos).",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📅 Agendar aula gratis", callback_data="menu_agendar")],
            [InlineKeyboardButton("🔙 Voltar ao menu", callback_data="voltar_menu")],
        ])
    )

    # Limpa estado
    context.user_data['aguardando_comprovante'] = False
    context.user_data['pagamento_confirmacao'] = {}


# ---------- MAIN ----------

def main():
    """Inicia o bot."""
    app = Application.builder().token(TOKEN).build()

    # Comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("agendar", agendar))
    app.add_handler(CommandHandler("professores", professores))
    app.add_handler(CommandHandler("planos", planos))
    app.add_handler(CommandHandler("minhasaulas", minhasaulas))
    app.add_handler(CommandHandler("ajuda", ajuda))
    app.add_handler(CommandHandler("help", ajuda))  # alias PT-BR

    # Callback queries (botões inline)
    app.add_handler(CallbackQueryHandler(callback_handler))

    # Mensagens de texto
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensagem_handler))

    # Fotos (comprovante PIX)
    app.add_handler(MessageHandler(filters.PHOTO, foto_handler))

    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print("[EnglishFlow Bot] Iniciado! Pressione Ctrl+C para parar.")
    print(f"[EnglishFlow Bot] Acesse: https://t.me/inglesemfronteiras_bot")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
