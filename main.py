# coding: UTF-8

import threading
import time

import telebot
import schedule

import config
import dbapi
import utils

ModeratorsDatabase = dbapi.ModeratorsDatabase
MessageStack = dbapi.MessageStack
#MessageStack.create_table()
#ModeratorsDatabase.create_table()

bot = telebot.TeleBot(config.BOT_TOKEN)

def link(id, text="click"):
    return "[{}](tg://user?id={})".format(text, id)

markdown = "markdown"
version = "0.6"
print("Current version:", version)

def get_markup(id):
    return utils.create_inlinemarkup(
        [[utils.create_inlinebutton(config.SENDER_NAME, url="t.me/{}".format(bot.get_chat(id).username))],
         [utils.create_inlinebutton(config.ADMIN_NAME, url="t.me/{}".format(config.ADMIN_LINK))],
         [utils.create_inlinebutton(config.BUTTON3_NAME, url=config.BUTTON3_LINK)]])
    

bussy_dict = {}

@bot.message_handler(commands=['version'])
def get_version(message):
    return bot.send_message(message.chat.id, version)

@bot.message_handler(commands=['start'])
def start_talk(message):
    bot.send_message(message.chat.id, config.START_TALK)


@bot.message_handler(func=lambda m: (m.chat.id == config.ADMIN_ID) and (m.text) and (m.text.startswith("/get_id")))
def easy_test(message):
    if len(message.text.split(" ")) != 2:
        return bot.send_message(message.chat.id, "Invalid input!")

    mess = bot.send_message(message.text.split(" ")[1], "Test")
    bot.delete_message(mess.chat.id, mess.message_id)
    return bot.send_message(message.chat.id, str(mess.chat.id))

@bot.message_handler(func=lambda m: (m.chat.id == config.ADMIN_ID) and (m.text == "/ls_m"))
def list_moderator(message):
    text = "Moderators list: \n"
    moderators = ModeratorsDatabase.moderators()

    if not(moderators):
        text += "Empty!"
    else:
        for i, id in enumerate(moderators, 1):
            text += "{}. {}\n".format(i, link(id, id))

    return bot.send_message(config.ADMIN_ID, text, parse_mode=markdown)


@bot.message_handler(func=lambda m: (m.chat.id == config.ADMIN_ID) and (m.text) and (m.text.startswith("/set_m")))
def set_moderator(message):
    if len(message.text.split(" ")) != 2:
        return bot.send_message(message.chat.id, "Invalid id! ❌")

    moder = message.text.split(" ")[1]
    if not(moder.isdigit()):
        return bot.send_message(config.ADMIN_ID, "Invalid id! ❌")

    moder = int(moder)

    if moder in ModeratorsDatabase.moderators():
        return bot.send_message(config.ADMIN_ID, "id already in moderators ✅")

    try:
        user = bot.get_chat(moder)
    except Exception as err:
        print(err)
        return bot.send_message(config.ADMIN_ID, "Please input valid id! ❌")

    if not(user.username):
        return bot.send_message(config.ADMIN_ID, "User must have @username! ❌")

    bot.send_message(config.ADMIN_ID, "Successfully added {} to moders! ✅".format(link(moder, user.first_name)), parse_mode=markdown)
    return ModeratorsDatabase.insert_moderator(moder)


@bot.message_handler(func=lambda m: (m.from_user.id == config.ADMIN_ID) and (m.text) and (m.text.startswith("/del_m")))
def del_moderator(message):
    if len(message.text.split(" ")) != 2:
        return bot.send_message(message.chat.id, "Invalid id! ❌")

    moder = message.text.split(" ")[1]
    if not(moder.isdigit()):
        return bot.send_message(config.ADMIN_ID, "Invalid id! ❌")

    moder = int(moder)

    if not(moder in ModeratorsDatabase.moderators()):
        return bot.send_message(config.ADMIN_ID, "Id already not in moders! ✅")

    user = bot.get_chat(moder)
    
    bot.send_message(config.ADMIN_ID, "Successfully delete {} from moders! ✅".format(link(moder, user.first_name)), parse_mode=markdown)
    return ModeratorsDatabase.delete_moderator(moder)


@bot.message_handler(func=lambda m: (m.chat.id == config.ADMIN_ID) and (m.text) and (m.text.startswith("/commands")))
def commands(message):
    return bot.send_message(config.ADMIN_ID, (
        """
/commands = commands list
/set_m id = add id to moders
/del_m id = delete id from moders
/ls_m = show current moders
"""))



### MODERATOR FUNCTIONS ###

@bot.message_handler(content_types=['document', 'photo', 'video'])
@utils.privateonly
def prepare_transit(message):
    if not(message.chat.id in ModeratorsDatabase.moderators()):
        if message.chat.id != config.ADMIN_ID:
            return bot.send_message(message.chat.id, "(-_-)")
    
    controll = {
        "document":message.document,
        "photo":message.photo,
        "video":message.video,
    }
    
    if message.content_type == "photo":
        controll['photo'] = message.photo[-1]
    
    bussy_dict[message.chat.id] = (message.content_type, controll[message.content_type].file_id, message.caption, message.date)
    
    return bot.send_message(message.chat.id, "Choice method!", reply_markup=utils.create_inlinemarkup(
                [[utils.create_inlinebutton("Channel", "choice channel"), utils.create_inlinebutton("Group", "choice group")]]))



@bot.callback_query_handler(func=lambda call: call.data.startswith("choice") and (call.from_user.id in (ModeratorsDatabase.moderators() + [config.ADMIN_ID])) )
def choice_method(call):
    _, type = call.data.split(" ")
    
    processor = {
        "channel": config.CHANNELS.keys(),
        "group": config.GROUPS.keys(),
    }    
    
    translate = {
        "weed": "Травка",
        "other": "Прочее",
    }
    
    return bot.edit_message_text("Choice:", call.message.chat.id, call.message.message_id, reply_markup=utils.create_vanillainlinemarkup(            
            [utils.create_inlinebutton(translate[channel], "view {} {}".format(type, channel)) for channel in processor[type]], 1))

    #if call.data == "choice channel":
    #    return bot.edit_message_text("Choice subchannel:", call.message.chat.id, call.message.message_id, reply_markup=utils.create_vanillainlinemarkup(            
    #        [utils.create_inlinebutton(channel.title, "view channel " + str(channel.id)) for channel in [bot.get_chat(id) for id in config.CHANNELS]], 3))
    #
    #if call.data == "choice group":
    #    return bot.edit_message_text("Choice subgroup:", call.message.chat.id, call.message.message_id,  reply_markup=utils.create_vanillainlinemarkup(
    #        [utils.create_inlinebutton(group.title, "view group " + str(group.id)) for group in [bot.get_chat(id) for id in config.GROUPS]], 3))


@bot.callback_query_handler(func=lambda call: call.data.startswith("view") and (call.from_user.id in (ModeratorsDatabase.moderators() + [config.ADMIN_ID])) )
def view_method(call):
    _, type, name = call.data.split(" ")
    
    processor = {
        "channel": config.CHANNELS,
        "group": config.GROUPS,
    }
    
    return bot.edit_message_text("Choice {}:".format(type), call.message.chat.id, call.message.message_id, reply_markup=utils.create_vanillainlinemarkup(            
            [utils.create_inlinebutton(channel.title, "sendto {} {}".format(type, channel.id)) for channel in [bot.get_chat(id) for id in processor[type][name]]]+
            [utils.create_inlinebutton("Назад", "choice {}".format(type))] , 1))

    
    #if call.data == "choice channel":
    #    return bot.edit_message_text("Choice channel:", call.message.chat.id, call.message.message_id, reply_markup=utils.create_vanillainlinemarkup(            
    #        [utils.create_inlinebutton(channel.title, "sendto channel " + str(channel.id)) for channel in [bot.get_chat(id) for id in config.CHANNELS]], 3))
    #
    #if call.data == " group":
    #   return bot.edit_message_text("Choice group:", call.message.chat.id, call.message.message_id,  reply_markup=utils.create_vanillainlinemarkup(
    #       [utils.create_inlinebutton(group.title, "sendto group " + str(group.id)) for group in [bot.get_chat(id) for id in config.GROUPS]], 3))
@bot.callback_query_handler(func=lambda call: call.data.startswith("sendto") and (call.from_user.id in (ModeratorsDatabase.moderators() + [config.ADMIN_ID])))
def callback_inline(call):
    _, to, tid = call.data.split(" ")

    if not(call.message.chat.id in bussy_dict):
        return bot.send_message(call.from_user.id, "Button does not work! ❌")

    format, file_id, caption, date = bussy_dict.pop(call.message.chat.id)
    target_id = int(tid)
    
    method = {"photo":bot.send_photo,
              "video":bot.send_video,
              "document":bot.send_document,}
    
    if to == "channel":
        MessageStack.insert_message(format, call.message.chat.id, target_id, file_id, caption, date)
        bot.edit_message_text("Post soon to appear on the channel! ✅", call.message.chat.id, call.message.message_id)

    if to == "group":
        bot.edit_message_text("Successfully! ✅", call.message.chat.id, call.message.message_id)
        return method[format](target_id, file_id, caption=caption, reply_markup=get_markup(call.message.chat.id))

def process_all_channel():
    for name, value in config.CHANNELS.items():
        for channelid in value:
            for format, senderid, channelid, photolink, caption, date in MessageStack.order_messages(channelid):
    
                MessageStack.delete_message(date)
    
                method = {"photo":bot.send_photo,
                          "video":bot.send_video,
                          "document":bot.send_document,
                      }
    
                method[format](channelid, photolink, caption=caption, reply_markup=get_markup(senderid))

if __name__ == "__main__":
    schedule.every(1).minutes.do(process_all_channel)
    #for x in ["00:00", "1:30", "3:00", "4:30", "6:00", "7:30", "9:00", "10:30", "12:00", "13:30", "15:00", "16:30", "18:00", "19:30", "21:00", "22:30"]:
    #    schedule.every().day.at(x).do(process_all_channel)

    def thread_poll():
        while 1:
            schedule.run_pending()
            time.sleep(5)
    threading.Thread(target=thread_poll).start()
    
    print("Bot started!")
    while True: 
        try:
            bot.polling(none_stop=True, interval=1, timeout=3600)
        except ConnectionError as error:
            bot.stop_polling()
            print("Connection error!")
            time.sleep(10)
