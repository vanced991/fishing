from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes
)
import requests

TOKEN = "INSERISCI_IL_TUO_TOKEN_TELEGRAM"
MAKE_WEBHOOK_LISTA = "https://hook.eu1.make.com/tuo_webhook_lista"
MAKE_WEBHOOK_AGGIUNGI = "https://hook.eu1.make.com/tuo_webhook_aggiungi"
MAKE_WEBHOOK_RIMUOVI = "https://hook.eu1.make.com/tuo_webhook_rimuovi"

# --- Stati del ConversationHandler ---
NOME_PESCE, NOME_LUOGO, DISTANZA = range(3)

# -----------------------------
# /start
# -----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 Benvenuto! Ecco i comandi disponibili:\n\n"
        "/start - mostra i comandi\n"
        "/aggiungi - aggiungi un nuovo record\n"
        "/lista - ottieni la lista dei record\n"
        "/rimuovi - rimuovi un record tramite UUID\n"
    )
    await update.message.reply_text(text)

# -----------------------------
# /aggiungi — Step 1
# -----------------------------
async def aggiungi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🐟 Inserisci il *nome del pesce*:")
    return NOME_PESCE

# Step 2
async def nome_pesce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["nome_pesce"] = update.message.text
    await update.message.reply_text("📍 Inserisci il *nome del luogo*:")
    return NOME_LUOGO

# Step 3
async def nome_luogo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["nome_luogo"] = update.message.text
    await update.message.reply_text("📏 Inserisci la *distanza massima in km*:")
    return DISTANZA

# Step finale → invio a Make
async def distanza(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["distanza"] = update.message.text

    payload = {
        "nome_pesce": context.user_data["nome_pesce"],
        "nome_luogo": context.user_data["nome_luogo"],
        "distanza": context.user_data["distanza"]
    }

    requests.post(MAKE_WEBHOOK_AGGIUNGI, json=payload)

    await update.message.reply_text("✅ Record aggiunto correttamente!")
    return ConversationHandler.END

# Cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Procedura annullata.")
    return ConversationHandler.END

# -----------------------------
# /lista — chiama Make
# -----------------------------
async def lista(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.get(MAKE_WEBHOOK_LISTA).json()
        text = "📄 *Lista:*\n\n"

        for item in response:
            text += f"- {item.get('nome_pesce')} ({item.get('luogo')}) – UUID: `{item.get('uuid')}`\n"

        await update.message.reply_text(text, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text("❌ Errore nel recupero della lista.")

# -----------------------------
# /rimuovi — invia UUID a Make
# -----------------------------
async def rimuovi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uuid = update.message.text.replace("/rimuovi", "").strip()

        if not uuid:
            await update.message.reply_text("📌 Usa: `/rimuovi UUID`", parse_mode="Markdown")
            return

        requests.post(MAKE_WEBHOOK_RIMUOVI, json={"uuid": uuid})

        await update.message.reply_text("🗑️ Record rimosso!")

    except Exception:
        await update.message.reply_text("❌ Errore nella rimozione.")

# -----------------------------
# MAIN
# -----------------------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Conversation handler per /aggiungi
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("aggiungi", aggiungi)],
        states={
            NOME_PESCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, nome_pesce)],
            NOME_LUOGO: [MessageHandler(filters.TEXT & ~filters.COMMAND, nome_luogo)],
            DISTANZA: [MessageHandler(filters.TEXT & ~filters.COMMAND, distanza)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("lista", lista))
    app.add_handler(CommandHandler("rimuovi", rimuovi))
    app.add_handler(conv_handler)

    app.run_polling()

if __name__ == "__main__":
    main()
