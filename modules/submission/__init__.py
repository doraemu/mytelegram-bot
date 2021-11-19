import telegram
import database as db
import threading

MAIN_CONFIG = db.read("config")
CONFIG = db.read("sub_config")
DB = db.read("sub_data")

def submission_post(bot, msg, editor, ptype, cid):    
    if ptype =="real":
        r = bot.forward_message(chat_id=cid, from_chat_id=CONFIG['Group_ID'], message_id=msg.message_id)
    else:    
        if msg.audio != None:
            r = bot.send_audio(chat_id=cid,  audio=msg.audio, caption=msg.caption)
        elif msg.document != None:
            r = bot.send_document(chat_id=cid, document=msg.document, caption=msg.caption)
        elif msg.voice != None:
            r = bot.send_voice(chat_id=cid, voice=msg.voice, caption=msg.caption)
        elif msg.video != None:
            r = bot.send_video(chat_id=cid, video=msg.video, caption=msg.caption)
        elif msg.photo:
            r = bot.send_photo(chat_id=cid, photo=msg.photo[0], caption=msg.caption)
        else:
            r = bot.send_message(chat_id=cid, text=msg.text_markdown, parse_mode=telegram.ParseMode.MARKDOWN)
        
    root = DB[str(CONFIG['Group_ID']) + ':' + str(msg.message_id)]
    root['posted'] = True
    root['Channel_ID'] = cid
    
    msg = "已采纳\n投稿人: [{0}](tg://user?id={1})\n来源: ".format(root['Sender_Name'], root['Sender_ID'])
    if root['type'] == 'real': msg += "保留\n"
    else: msg += "匿名\n"
    msg += "审核人: [{0}](tg://user?id={1})".format(editor.name, editor.id)
    
    bot.edit_message_text(text=msg, chat_id=CONFIG['Group_ID'], parse_mode=telegram.ParseMode.MARKDOWN, message_id=root['Markup_ID'])
    bot.send_message(chat_id=root['Sender_ID'], text="您的稿件已过审，感谢您对我们的支持", reply_to_message_id=root['Original_MsgID'])
    threading.Thread(target=db.save("sub_data", DB, True)).start()
    return r

def gen_buttons(ptype):
    button = []
    for i in range(len(CONFIG['Publish_Channel_ID'])):
        button.append(telegram.InlineKeyboardButton("采纳至[" + CONFIG['Publish_Channel_Name'][i] + "]", callback_data="receive:{0}:{1}".format(ptype, CONFIG['Publish_Channel_ID'][i])))
    return button

def process_msg(bot, update):
    if update.channel_post != None: return        
    if update.message.from_user.id == update.message.chat_id:
        markup =  telegram.InlineKeyboardMarkup([[telegram.InlineKeyboardButton("是" , callback_data='submission_type:real'), 
                                                  telegram.InlineKeyboardButton("否",  callback_data='submission_type:anonymous')],
                                                 [telegram.InlineKeyboardButton("取消投稿", callback_data='cancel:submission')]])
        if update.message.forward_from != None or update.message.forward_from_chat != None:
            if update.message.forward_from_chat != None:
                markup = telegram.InlineKeyboardMarkup([[telegram.InlineKeyboardButton("是", callback_data='submission_type:real')], [telegram.InlineKeyboardButton("取消投稿", callback_data='cancel:submission')]])
            elif update.message.forward_from.id  != update.message.from_user.id:
                markup = telegram.InlineKeyboardMarkup([[telegram.InlineKeyboardButton("是", callback_data='submission_type:real')], [telegram.InlineKeyboardButton("取消投稿", callback_data='cancel:submission')]])
        bot.send_message(chat_id=update.message.chat_id,  text="即将完成投稿...\n⁠您是否想要保留消息来源(保留消息发送者用户名)", reply_to_message_id=update.message.message_id, reply_markup=markup)

def process_command(bot, update):
    if update.channel_post != None: return
    command = update.message.text[1:].replace(MAIN_CONFIG['Username'], '' ).lower()
    if update.message.from_user.id == MAIN_CONFIG['Admin']:
        if command == 'setsubgroup':
            CONFIG['Group_ID'] = update.message.chat_id
            db.save("sub_config", CONFIG)
            bot.send_message(chat_id=update.message.chat_id,  text="已设置本群为审稿群")
            return
          
def process_callback(bot, update):
    if update.channel_post != None: return
    query = update.callback_query
    cmds = query.data.split(":")
    if query.message.chat_id == CONFIG['Group_ID'] and cmds[0] == 'receive':
        submission_post(bot, query.message.reply_to_message, query.from_user, cmds[1], cmds[2])
        return
    
    if cmds[0] == 'cancel' and cmds[1] == 'submission':
        bot.edit_message_text(text="已取消投稿", chat_id=query.message.chat_id, message_id=query.message.message_id)
        return
        
    if cmds[0] == 'submission_type' :  
        msg = "新投稿\n投稿人: [" + query.message.reply_to_message.from_user.name + "](tg://user?id=" + str(query.message.reply_to_message.from_user.id) + ")\n来源: "
        fwd_msg = bot.forward_message(chat_id=CONFIG['Group_ID'], from_chat_id=query.message.chat_id, message_id=query.message.reply_to_message.message_id)        
            
        root = DB[str(CONFIG['Group_ID']) + ':' + str(fwd_msg.message_id)] = {}
        root['posted'] = False
        root['Sender_Name'] = query.message.reply_to_message.from_user.name
        root['Sender_ID'] = query.message.reply_to_message.from_user.id
        root['Original_MsgID'] = query.message.reply_to_message.message_id
        root['Channel_ID'] = ""

        if cmds[1] == 'real':
            msg += "保留"
            root['type'] = 'real'
        else:
            msg += "匿名"
            root['type'] = 'anonymous'

        buttons = []
        for i in range(len(CONFIG['Publish_Channel_ID'])):
            buttons.append(telegram.InlineKeyboardButton("采纳至[" + CONFIG['Publish_Channel_Name'][i] + "]", callback_data="receive:{0}:{1}".format(cmds[1], CONFIG['Publish_Channel_ID'][i])))
        markup = telegram.InlineKeyboardMarkup([buttons])
        markup_msg = bot.send_message(chat_id=CONFIG['Group_ID'], text=msg, reply_to_message_id=fwd_msg.message_id, reply_markup=markup, parse_mode=telegram.ParseMode.MARKDOWN)    
        root['Markup_ID'] = markup_msg.message_id   
        bot.edit_message_text(text="感谢您的投稿，稍后管理员会进行审核", chat_id=query.message.chat_id, message_id=query.message.message_id)
        threading.Thread(target=db.save("sub_data", DB, True)).start()
        
            