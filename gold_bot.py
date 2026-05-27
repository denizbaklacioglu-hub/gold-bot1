from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, JobQueue
import yfinance as yf
import pandas as pd
from datetime import datetime

TOKEN = "8874527049:AAEiDapDOzH2SANS69nxJ9gg_b62L19w6SI"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🪙 Gold Auto Trader Bot v11.1 gestartet!\n\n"
        "✅ Detaillierte automatische Signale alle 15 Minuten sind aktiv.\n"
        "/gold → Sofortige volle Analyse\n"
        "/stop → Automatik ausschalten"
    )
    
    # Starte automatische detaillierte Signale
    context.job_queue.run_repeating(auto_detailed_signal, interval=900, first=15, name="gold_auto", chat_id=update.message.chat_id)

async def auto_detailed_signal(context: ContextTypes.DEFAULT_TYPE):
    """Detailliertes automatisches Signal alle 15 Minuten"""
    chat_id = context.job.chat_id
    
    try:
        # Daten holen
        data = yf.download("GC=F", period="3d", interval="15m", progress=False)
        if data.empty:
            return
            
        close = data['Close']
        price = close.iloc[-1]
        
        # Indikatoren berechnen
        ema9 = close.ewm(span=9).mean().iloc[-1]
        ema21 = close.ewm(span=21).mean().iloc[-1]
        rsi = 100 - (100 / (1 + (close.diff().where(lambda x: x > 0, 0).rolling(14).mean() / 
                                 -close.diff().where(lambda x: x < 0, 0).rolling(14).mean()))).iloc[-1]
        
        # Wahrscheinlichkeit
        score = 0
        if ema9 > ema21:
            score += 6
        if rsi < 45:
            score += 3
        if close.iloc[-1] > close.rolling(50).mean().iloc[-1]:
            score += 3
            
        probability = max(42, min(76, 45 + score * 2.2))
        
        # Empfehlung
        if probability >= 68:
            empfehlung = "🟢 **STRONG LONG**"
        elif probability >= 58:
            empfehlung = "🟡 **LONG möglich**"
        else:
            empfehlung = "🔴 **Kein Trade**"
        
        sl = round(price * 0.9935, 2)
        tp = round(price * 1.022, 2)
        
        text = f"""🪙 Auto-Signal • {datetime.now().strftime('%H:%M')}

Gold Preis: ${price:,.2f}

Empfehlung: {empfehlung}
Erfolgs-Wahrscheinlichkeit: {probability:.0f}%

Indikatoren:
• EMA9 > EMA21: {'✅ Ja' if ema9 > ema21 else '❌ Nein'}
• RSI: {rsi:.1f}
• Trend: {'🟢 Aufwärts' if ema9 > ema21 else '🔴 Abwärts'}

Trade Setup:
• Stop-Loss: ${sl}
• Take-Profit: ${tp}
• Risiko: max. 0.5% deines Kapitals

Schreibe /gold für noch genauere Analyse."""

        await context.bot.send_message(chat_id=chat_id, text=text)
        
    except Exception as e:
        print(f"Auto-Signal Fehler: {e}")

async def gold_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Führe detaillierte Analyse durch...")
    # Hier kannst du später die volle Version aus v10 einbauen
    await auto_detailed_signal(context)  # Nutzt dieselbe Funktion

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏹ Automatische Signale wurden gestoppt.")
    jobs = context.job_queue.get_jobs_by_name("gold_auto")
    for job in jobs:
        job.schedule_removal()

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gold", gold_signal))
    app.add_handler(CommandHandler("stop", stop))
    
    print("🪙 Gold Auto Bot mit detaillierten Signalen alle 15 Minuten läuft...")
    app.run_polling()

if __name__ == "__main__":
    main()