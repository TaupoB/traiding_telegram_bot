#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
import re

import numpy as np
import logging
from ai_model import  Model, load_data, TickerModel
import yfinance as yf
from config import TOKEN

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

CHOOSING_TICKERS, PREDICT, EDITING_TICKERS, *_ = range(10)

start_message = 'скинь тикеры через запятую большими буквами'
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        start_message
    )
    return CHOOSING_TICKERS

def is_ticker(ticker_name: str) -> str | bool:
        ticker = yf.Ticker(ticker_name)
        try:
            info = ticker.info
            # return info['longName']
            return True
        except:
            return False
def validate_tickers(tickers: str):
    tickers = tickers.split(', ')
    # long_names = list(map(is_ticker, tickers))
    # isticker_arr = np.array([bool(name) for name in long_names])
    isticker_arr = np.array(list(map(is_ticker, tickers)))
    valid = all(isticker_arr)
    tickers = np.array(tickers)
    return valid, tickers[isticker_arr], tickers[~isticker_arr]


async def invalid_input(update: Update, context) -> int:
    await update.message.reply_text(f"Вы инвалид, даю еще одну попытку")
    return CHOOSING_TICKERS

reply_keyboard = [
    ["Предсказать"],
    ['Начать заново']
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

async def tickers_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask the user for info about the selected predefined choice."""
    tickers = update.message.text
    valid, valid_tickers, invalid_tickers = validate_tickers(tickers)
    context.user_data["tickers"] = valid_tickers

    if valid:
        t = '\n'.join(valid_tickers)
        await update.message.reply_text(f"Ваши тикеры:\n{t}\n")
        await update.message.reply_text(f"Tеперь можно сделать предскзание на завтра",
                                        reply_markup=markup)
        return PREDICT
    else:
        await update.message.reply_text(f"Не найдены тикеры: {invalid_tickers}, даю еще одну попытку")
        return CHOOSING_TICKERS




def strategy_predict(ticker):
    return 0

def make_prediction(ticker, prices):
    prediction_mapping = {1: '📈 покупать', -1: '📉 продавать', 0: '➡️ удерживать'}
    ai_prediction = ai_predictor.predict(prices)
    strategy_prediction = strategy_predict(ticker)
    return f"{ticker}\n🤖: {prediction_mapping[ai_prediction]} 🧮: {prediction_mapping[strategy_prediction]}\n"
#
# def check_and_convert_date(date):
#     try:
#         date_object = datetime.datetime.strptime(date, "%d.%m.%y")
#     except:
#         return "Неверный формат даты"
#     if date_object > datetime.datetime.today() + datetime.timedelta(days=1):
#         return 'Нельзя предсказывать больше чем на день вперед'
#     return date_object

async def write_prediction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    tickers = context.user_data["tickers"]
    context.user_data['companies'] = context.user_data.get('companies', load_data(tickers))
    predictions_for_tickers = [make_prediction(ticker, context.user_data['companies'][ticker]) for ticker in tickers]
    text = '\n'.join(predictions_for_tickers)
    await update.message.reply_text(f"Прогноз:\n🤖 - AI\n🧮 - тех. анализ\n\n{text}")
    return PREDICT

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End the conversation."""
    await update.message.reply_text(
        f"Все",
        reply_markup=ReplyKeyboardRemove(),
    )
    user_data = context.user_data
    user_data.clear()
    return ConversationHandler.END

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_data = context.user_data
    user_data.clear()
    await update.message.reply_text(start_message)
    return CHOOSING_TICKERS

def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_TICKERS: [
                MessageHandler(
                    filters.Regex("^[A-Z]+(,\s*[A-Z]+)*$"), tickers_input
                ),
                MessageHandler((filters.TEXT & ~(filters.COMMAND)), invalid_input)
            ],
            PREDICT: [
                MessageHandler(
                    filters.Regex('^Предсказать$'), write_prediction)
            ],
        },
        fallbacks=[CommandHandler('end', done),
                   MessageHandler(filters.Regex("^Начать заново$"), restart)],
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    ai_predictor = Model('ticker_model_31.99.pth')
    main()