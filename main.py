import time
import json
import telegram.ext
import telegram
import sys
import datetime
import os
import logging
import threading
import database as db
import importlib

Version_Code = 'v1.0.0'

logging.basicConfig(level=logging.INFO,  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' )

PATH = os.path.dirname(os.path.realpath(__file__)) + '/'

CONFIG = db.read("config")

updater = telegram.ext.Updater(token=CONFIG['Token'])
dispatcher = updater.dispatcher

me = updater.bot.get_me()
CONFIG['ID'] = me.id
CONFIG['Username'] = '@' + me.username

print('Starting... (ID: ' + str(CONFIG['ID']) + ', Username: ' + CONFIG['Username'] + ')')

modules = []
for mod in CONFIG['Modules']:
    modules.append(importlib.import_module(mod))
    print(mod + " Loaded")

def process_msg(bot, update):
    if update.channel_post != None: return
    for mod in modules: mod.process_msg(bot, update)

def process_command(bot, update):
    if update.channel_post != None: return
    command = update.message.text[1:].replace(CONFIG['Username'], '' ).lower()
    if command == 'start':
        bot.send_message(chat_id=update.message.chat_id, text="""可接收的投稿类型：图片、视频""")
        return
    elif command == 'version':
        bot.send_message(chat_id=update.message.chat_id, text='Telegram Submission Bot\n' + Version_Code + '\nhttps://github.com/Netrvin/telegram-submission-bot')
        return
    else:
        for mod in modules: mod.process_command(bot, update)
 
def process_callback(bot, update):
    if update.channel_post != None: return
    for mod in modules: mod.process_callback(bot, update)

dispatcher.add_handler(telegram.ext.MessageHandler(telegram.ext.Filters.text
                       | telegram.ext.Filters.audio
                       | telegram.ext.Filters.photo
                       | telegram.ext.Filters.video
                       | telegram.ext.Filters.voice
                       | telegram.ext.Filters.document, process_msg))

dispatcher.add_handler(telegram.ext.MessageHandler(telegram.ext.Filters.command, process_command))

dispatcher.add_handler(telegram.ext.CallbackQueryHandler(process_callback))

updater.start_polling()
print('Started')
updater.idle()
print('Stopped.')
