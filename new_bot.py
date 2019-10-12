#!/usr/local/bin/python
# -*- coding: utf-8 -*-
from telebot import TeleBot, types
from databaser import Databaser as db
from locales import locales
import config
from time import time


bot = TeleBot(config.token)
categories = {}
state = '0'
status = {}
an_stat = False
an_id = 0


def item_keygen(item_id, uid, item_parent):
    try:
        lng = db().get_user_lang(uid)[0][0]
    except IndexError:
        return
    key = types.InlineKeyboardMarkup(row_width=2)
    key.row(types.InlineKeyboardButton('⬅️', callback_data='prev_{}_{}'.format(item_id, item_parent)),
            types.InlineKeyboardButton(locales[lng][0], callback_data='atc_' + str(item_id)),
            types.InlineKeyboardButton('➡️', callback_data='next_{}_{}'.format(item_id, item_parent)))
    key.row(types.InlineKeyboardButton('⬅️'+locales[lng][1], callback_data='delmsg'))
    if uid in config.admin_id:
        key.add(types.InlineKeyboardButton('[{}]'.format(locales[lng][2]), callback_data='del_it_'+str(item_id)))
    return key


def keygen(cat_id, uid):
    try:
        lng = db().get_user_lang(uid)[0][0]
    except IndexError:
        return
    key = types.InlineKeyboardMarkup()
    cats = db().get_categories(cat_id)
    for c in cats:
        key.add(types.InlineKeyboardButton(c[1], callback_data='cat_'+str(c[0])))
    items = db().get_items(cat_id)
    for i in items:
        key.add(types.InlineKeyboardButton(i[1], callback_data='it_'+str(i[0])))
    if uid in config.admin_id:
        if int(cat_id) > 0:
            key.add(types.InlineKeyboardButton('[{}]'.format(locales[lng][3]), callback_data='add_it_'+str(cat_id)),
                    types.InlineKeyboardButton('[{}]'.format(locales[lng][4]), callback_data='add_cat_' + str(cat_id)),
                    types.InlineKeyboardButton('[{}]'.format(locales[lng][5]), callback_data='del_cat_'+str(cat_id)))
        else:
            key.add(types.InlineKeyboardButton('[{}]'.format(locales[lng][4]), callback_data='add_cat_' + str(cat_id)))
    if int(cat_id) > 0:
        parent = db().get_parent(cat_id)[0][0]
        key.add(types.InlineKeyboardButton('⬅️'+locales[lng][1], callback_data='cat_'+str(parent)))
    return key


def item_page(msg, item_id, user_id):
    try:
        lng = db().get_user_lang(user_id)[0][0]
    except IndexError:
        return
    if not db().check_item(item_id):
        bot.send_message(msg.chat.id, locales[lng][6])
    else:
        info = db().get_item_by_id(item_id)[0]
        title, desc, photo, parent, price = info[1], info[2], info[3], info[4], info[6]
        text = '[​​​​​​​​​​​]({}) *{}*\n\n{}\n\n{}: {}'.format(photo, title, desc, locales[lng][7],price)
        key = item_keygen(item_id, msg.chat.id, parent)
        bot.send_message(msg.chat.id, text, reply_markup=key, parse_mode='markdown')


@bot.message_handler(commands=['cancel'], func=lambda msg: msg.from_user.id in config.admin_id and an_stat and
                                                           msg.from_user.id == an_id)
def cancel_an(msg):
    try:
        lng = db().get_user_lang(msg.from_user.id)[0][0]
    except IndexError:
        return
    global an_stat
    global an_id
    an_stat = False
    an_id = 0
    bot.send_message(msg.chat.id, locales[lng][8])


@bot.message_handler(commands=['cancel'], func=lambda msg: msg.from_user.id in config.admin_id and
                                                           (status[msg.from_user.id] == 'add_it' or
                                                           status[msg.from_user.id] == 'add_cat' or
                                                           status[msg.from_user.id] == 'desc' or
                                                           status[msg.from_user.id] == 'price' or
                                                           status[msg.from_user.id] == 'photo'))
def cancel_add_cat(msg):
    try:
        lng = db().get_user_lang(msg.from_user.id)[0][0]
    except IndexError:
        return
    db().cancel_item(msg.chat.id)
    global status
    status[msg.chat.id] = '0'
    bot.send_message(msg.chat.id, locales[lng][9])


@bot.message_handler(regexp='Готово|Ready|Tayyor', func=lambda msg: msg.from_user.id in config.admin_id and an_stat and
                     msg.from_user.id == an_id)
def send_an(msg):
    global an_stat
    global an_id
    dbw = db()
    try:
        lng = dbw.get_user_lang(msg.from_user.id)[0][0]
    except IndexError:
        return
    media = dbw.get_media()
    for u in dbw.get_users_list():
        try:
            u = u[0]
            for m in media:
                t = m[0]
                if t == 'text':
                    bot.send_message(u, m[1])
                elif t == 'audio':
                    bot.send_audio(u, m[2])
                elif t == 'document':
                    bot.send_document(u, m[2])
                elif t == 'photo':
                    bot.send_photo(u, m[2])
                elif t == 'sticker':
                    bot.send_sticker(u, m[2])
                elif t == 'video':
                    bot.send_video(u, m[2])
                elif t == 'video_note':
                    bot.send_video_note(u, m[2])
                elif t == 'voice':
                    bot.send_voice(u, m[2])
                elif t == 'location':
                    bot.send_location(u, m[4], m[3])
        except Exception:
            continue
    dbw.clear_media()
    an_stat = False
    an_id = 0
    bot.send_message(msg.chat.id, locales[lng][11])
    catalog(msg)


@bot.message_handler(content_types=['text', 'audio', 'document', 'photo', 'sticker',
                                    'video', 'video_note', 'voice', 'location'],
                     func=lambda msg: msg.from_user.id in config.admin_id and an_stat and msg.from_user.id == an_id)
def accum_an(msg):
    dbw = db()
    if msg.content_type == 'text':
        dbw.add_media('text', text=msg.text)
    elif msg.content_type == 'audio':
        dbw.add_media('audio', file_id=msg.audio.file_id)
    elif msg.content_type == 'document':
        dbw.add_media('document', file_id=msg.document.file_id)
    elif msg.content_type == 'photo':
        dbw.add_media('photo', file_id=msg.photo[-1].file_id)
    elif msg.content_type == 'sticker':
        dbw.add_media('sticker', file_id=msg.sticker.file_id)
    elif msg.content_type == 'video':
        dbw.add_media('video', file_id=msg.video.file_id)
    elif msg.content_type == 'video_note':
        dbw.add_media('video_note', file_id=msg.video_note.file_id)
    elif msg.content_type == 'voice':
        dbw.add_media('voice', file_id=msg.voice.file_id)
    elif msg.content_type == 'location':
        dbw.add_media('location', lon=msg.location.longitude, lat=msg.location.latitude)


# @bot.message_handler(func=lambda msg: msg.from_user.id in config.admin_id and an_stat)
# def send_an(msg):
#     global an_stat
#     an_stat = False
#     for u in db().get_users_list():
#         try:
#             bot.send_message(u[0], msg.text)
#         except Exception:
#             continue


@bot.message_handler(regexp='⬅️(?:Назад|back\(wards\)|Ortga)')
def go_back(msg):
    state = db().get_state(msg.from_user.id)
    if state == 'phone_req':
        form(msg)
    elif state == 'way_req':
        form_addr(msg, ignore=True)
    elif state == 'req_confirm':
        form_phone(msg, ignore=True)
    elif state == 'fb_write' or state.startswith('reply_'):
        catalog(msg)
    elif state.startswith('atc_'):
        iid = state.split('_')[1]
        catalog(msg)
        item_page(msg, iid, msg.from_user.id)
    elif state == 'sub':
        catalog(msg)
    elif state == 'form_start':
        catalog(msg)


def std_key(msg, parent=0):
    dbw = db()
    cats = dbw.get_categories(parent)
    try:
        lng = dbw.get_user_lang(msg.from_user.id)[0][0]
    except IndexError:
        return
    dbw.set_state(msg.from_user.id, '0')
    key = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    row = []
    for c in cats:
        row.append(types.KeyboardButton(c[1]))
        categories[c[1]] = c[0]
        if len(row) == 2:
            key.row(*row)
            row.clear()
    if len(row) > 0:
        key.row(*row)
    key.row(types.KeyboardButton('📥 '+locales[lng][12]), types.KeyboardButton('🚖 '+locales[lng][13]))
    if parent == 0:
        key.row(types.KeyboardButton(locales[lng][14]))
    else:
        dbw.set_state(msg.from_user.id, 'sub')
        key.row(types.KeyboardButton('⬅️'+locales[lng][1]))

    if msg.from_user.id in config.admin_id:
        key.row(types.KeyboardButton(locales[lng][70]), types.KeyboardButton('Stats'))
    return key


@bot.message_handler(regexp='Stats')
def stats(msg):
    count = db().get_active(int(time()))
    num = 0
    for i in count:
        num += count[i][0]
    text = 'Всего: {}\n'.format(num)
    for lan in count:
        try:
            text += '{}: {} (Активных: {})\n'.format(lan, count[lan][0], count[lan][1])
        except IndexError:
            text += '{}: {} (Активных: 0)\n'.format(lan, count[lan][0])
    text = text.replace('ru', 'Русская')
    text = text.replace('en', 'Английская')
    text = text.replace('uz', 'Узбекская')
    bot.send_message(msg.chat.id, text)


@bot.message_handler(regexp='Каталог|Catalogue|Katalog')
def catalog(msg):
    key = std_key(msg)
    dbw = db()
    try:
        lng = dbw.get_user_lang(msg.from_user.id)[0][0]
    except IndexError:
        return
    dbw.update_last(msg.from_user.id, int(time()))
    bot.send_message(msg.chat.id, locales[lng][16], reply_markup=key)


@bot.message_handler(func=lambda msg: db().get_state(msg.from_user.id) == 'form_start', content_types=['text', 'location'])
def form_addr(msg, ignore=False):
    d = db()
    try:
        lng = d.get_user_lang(msg.from_user.id)[0][0]
    except IndexError:
        return
    if not ignore:
        if msg.content_type == 'text':
            d.set_addr(msg.from_user.id, msg.text)
        else:
            d.set_loc(msg.from_user.id, msg.location.latitude, msg.location.longitude)
    d.set_state(msg.from_user.id, 'phone_req')
    key = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    key.add(types.KeyboardButton('📱 '+locales[lng][17], request_contact=True), types.KeyboardButton('⬅️'+locales[lng][1]))
    bot.send_message(msg.chat.id, locales[lng][18], reply_markup=key)


@bot.message_handler(content_types=['text', 'contact'], func=lambda msg: db().get_state(msg.from_user.id) == 'phone_req')
def form_phone(msg, ignore=False):
    dbw = db()
    try:
        lng = dbw.get_user_lang(msg.from_user.id)[0][0]
    except IndexError:
        return
    if not ignore:
        if msg.content_type == 'text':
            dbw.set_phone(msg.from_user.id, msg.text)
        elif msg.content_type == 'contact':
            dbw.set_phone(msg.from_user.id, msg.contact.phone_number)
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(types.KeyboardButton(locales[lng][19]), types.KeyboardButton(locales[lng][20]))
    key.row(types.KeyboardButton('⬅️'+locales[lng][1]))
    dbw.set_state(msg.from_user.id, 'way_req')
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(types.KeyboardButton('Click'), types.KeyboardButton(locales[lng][19]))
    key.row(types.KeyboardButton('⬅️'+locales[lng][1]), types.KeyboardButton(locales[lng][15]))
    bot.send_message(msg.chat.id, locales[lng][21], reply_markup=key)


@bot.message_handler(func=lambda msg: db().get_state(msg.from_user.id) == 'way_req')
def form_way(msg):
    way = msg.text
    d = db()
    try:
        lng = d.get_user_lang(msg.from_user.id)[0][0]
    except IndexError:
        return
    provided = d.what_is_provided(msg.from_user.id)
    info = d.get_user_cart(msg.from_user.id)
    items = info[1]
    order = ''
    goods = []
    for i in items:
        if i not in goods:
            goods.append(i)
            try:
                info1 = db().get_item_by_id(i[1])[0]
            except IndexError:
                continue
            order += '{}\n{} x {} = {}\n\n'.format(info1[1], items.count(i), i[2], float(i[2]) * items.count(i))
    order += '\n{}: {}\n{}: {}\n{}: {}'.format(locales[lng][22], info[0][0], locales[lng][23], way,
                                               locales[lng][24], d.get_phone(msg.from_user.id))
    text = '{}\n\n'.format(locales[lng][25]) + order
    if provided == 'addr':
        addr = d.get_addr(msg.from_user.id)
        text += '\n{}: {}'.format(locales[lng][26], addr)
    else:
        text += '\n' + locales[lng][27]
    d.set_state(msg.from_user.id, 'req_confirm')
    d.set_order(msg.from_user.id, order)
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(types.KeyboardButton(locales[lng][28]))
    key.row(types.KeyboardButton('⬅️'+locales[lng][1]), types.KeyboardButton(locales[lng][15]))
    bot.send_message(msg.chat.id, text, reply_markup=key)


@bot.message_handler(func=lambda msg: db().get_state(msg.from_user.id) == 'req_confirm', regexp='Подтверждаю|I confirm\.|Tasdiqlayman')
def send_order(msg):
    print('send order')
    dbw = db()
    try:
        lng = dbw.get_user_lang(msg.from_user.id)[0][0]
    except IndexError:
        print('index error')
        return
    order = dbw.get_order(msg.from_user.id)
    bot.send_message(msg.chat.id, '*{}*, {}\n'
                                  '{}'.format(msg.from_user.first_name, locales[lng][31], locales[lng][32]),
                     parse_mode='markdown')
    dbw.clear_cart(msg.from_user.id)
    catalog(msg)
    key = types.InlineKeyboardMarkup()
    key.add(types.InlineKeyboardButton(locales[lng][33], callback_data='oconf_{}_{}'.format(msg.from_user.id,
                                                                                            msg.from_user.first_name)))
    for i in config.admin_id:
        try:
            lng = dbw.get_user_lang(i)[0][0]
        except IndexError:
            continue
        text = locales[lng][29].format(msg.from_user.first_name, msg.from_user.id, order)
        text = text.replace('\\n', '\n')
        provided = dbw.what_is_provided(msg.from_user.id)
        loc = []
        if provided == 'addr':
            text += '\n{}: {}'.format(locales[lng][26], dbw.get_addr(msg.from_user.id))
        else:
            text += '\n' + locales[lng][30]
            loc = dbw.get_loc(msg.from_user.id)
        try:
            bot.send_message(i, text, parse_mode='markdown', reply_markup=key)
            if provided == 'loc':
                bot.send_location(i, loc[0], loc[1])
        except Exception:
            continue

    provided = dbw.what_is_provided(msg.from_user.id)
    bot.send_message(config.channel_id, text, parse_mode='markdown')
    if provided == 'loc':
        loc = dbw.get_loc(msg.from_user.id)
        bot.send_location(config.channel_id, loc[0], loc[1])


@bot.callback_query_handler(func=lambda call: call.data.startswith('oconf_'))
def order_confirmed(call):
    uid, name = call.data.split('_')[1], call.data.split('_')[2]
    try:
        lng = db().get_user_lang(uid)[0][0]
    except IndexError:
        return
    adtype = locales[lng][34]
    if locales[lng][35] in call.message.text:
        adtype = locales[lng][36]
    bot.send_message(uid, locales[lng][37].replace('\\n', '\n').format(name, adtype), parse_mode='markdown')
    bot.send_message(config.channel_id, 'Заказ {} ({}) принят'.format(uid, name))
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)


@bot.message_handler(commands=['start'])
def start(msg):
    key = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    key.add(types.KeyboardButton('Русский'), types.KeyboardButton('English'), types.KeyboardButton("O'zbek"))
    bot.send_message(msg.chat.id, 'Выберите язык | Select language | Tilni tanlang', reply_markup=key)



@bot.message_handler(regexp="Русский|English|O'zbek")
def start_lang(msg):
    if msg.text == 'Русский':
        lang = 'ru'
    elif msg.text == 'English':
        lang = 'en'
    else:
        lang = 'uz'
    db().try_add_user(msg.from_user.id, lang)
    catalog(msg)


@bot.message_handler(func=lambda msg: msg.text in categories)
def cat_selected(msg):
    dbw = db()
    try:
        lng = dbw.get_user_lang(msg.from_user.id)[0][0]
    except IndexError:
        return
    items = dbw.get_items(categories[msg.text])
    cats = dbw.get_categories(categories[msg.text])
    if len(cats) > 0:
        key = std_key(msg, categories[msg.text])
        bot.send_message(msg.chat.id, locales[lng][39], reply_markup=key)
    if len(items) > 0:
        item_page(msg, items[0][0], msg.from_user.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('prev_'))
def prev_item(call):
    a, iid, cat_id = call.data.split('_')
    items = db().get_items(cat_id)
    for i in range(len(items)):
        if int(iid) == items[i][0]:
            item_page(call.message, items[i-1][0], call.from_user.id)
            del_msg(call)


@bot.callback_query_handler(func=lambda call: call.data.startswith('next_'))
def next_item(call):
    a, iid, cat_id = call.data.split('_')
    items = db().get_items(cat_id)
    for i in range(len(items)):
        if int(iid) == items[i][0]:
            if i == len(items) - 1:
                item_page(call.message, items[0][0], call.from_user.id)
            else:
                item_page(call.message, items[i+1][0], call.from_user.id)
            del_msg(call)


@bot.callback_query_handler(func=lambda call: call.data.startswith('atc_'))
def add_to_cart(call):
    try:
        lng = db().get_user_lang(call.from_user.id)[0][0]
    except IndexError:
        return
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.row(types.KeyboardButton('1'), types.KeyboardButton('2'), types.KeyboardButton('3'))
    key.row(types.KeyboardButton('4'), types.KeyboardButton('5'), types.KeyboardButton('6'))
    key.row(types.KeyboardButton('7'), types.KeyboardButton('8'), types.KeyboardButton('9'))
    key.row(types.KeyboardButton('📥 '+locales[lng][12]), types.KeyboardButton('⬅️'+locales[lng][1]))
    db().set_state(call.from_user.id, call.data)
    bot.send_message(call.message.chat.id, locales[lng][40], reply_markup=key)


@bot.message_handler(func=lambda msg: db().get_state(msg.from_user.id).startswith('atc_') and msg.text.isdigit())
def add_to_cart_amount(msg):
    amount = int(msg.text)
    dbw = db()
    try:
        lng = dbw.get_user_lang(msg.from_user.id)[0][0]
    except IndexError:
        return
    iid = dbw.get_state(msg.from_user.id).split('_')[1]
    for i in range(amount):
        dbw.add_to_cart(msg.from_user.id, iid)
    bot.send_message(msg.chat.id, locales[lng][41])
    catalog(msg)
    dbw.set_state(msg.from_user.id, '0')
    item_page(msg, iid, msg.from_user.id)


@bot.message_handler(regexp='📥 (?:Корзина|Basket|Savat)')
def show_cart(msg):
    info = db().get_user_cart(msg.chat.id)
    try:
        lng = db().get_user_lang(msg.from_user.id)[0][0]
    except IndexError:
        return
    items = info[1]
    text = ''
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.row(types.KeyboardButton(locales[lng][15]), types.KeyboardButton(locales[lng][44]))
    if len(items) == 0:
        text = locales[lng][42]
        bot.send_message(msg.chat.id, text)
        catalog(msg)
        return
    text = '{}:\n\n'.format(locales[lng][43])
    keys = []
    goods = []
    for i in items:
        if i not in goods:
            goods.append(i)
            try:
                info1 = db().get_item_by_id(i[1])[0]
            except IndexError:
                continue
            text += '{}\n{} x {} = {}\n\n'.format(info1[1], items.count(i), i[2], float(i[2])*items.count(i))
            if '❌ {}'.format(info1[1]) not in keys:
                key.add(types.KeyboardButton('❌ {}'.format(info1[1])))
                keys.append('❌ {}'.format(info1[1]))
    key.row(types.KeyboardButton('🚖 '+locales[lng][13]))
    text += '{}: {}'.format(locales[lng][22], info[0][0])
    bot.send_message(msg.chat.id, text, reply_markup=key)


@bot.message_handler(content_types=['text'], func=lambda msg: msg.content_type=='text' and msg.text.startswith('❌'))
def del_item(msg):
    dbw = db()
    info = dbw.get_user_cart(msg.chat.id)
    item_name = msg.text[2:]
    items = info[1]
    for i in items:
        info1 = dbw.get_item_by_id(i[1])[0]
        if info1[1] == item_name:
            dbw.del_from_cart(msg.from_user.id, i[1])
    show_cart(msg)


@bot.message_handler(regexp='Очистить|Clean|Tozalash')
def clear_cart(msg):
    db().clear_cart(msg.from_user.id)
    try:
        lng = db().get_user_lang(msg.from_user.id)[0][0]
    except IndexError:
        return
    bot.send_message(msg.chat.id, locales[lng][42])
    catalog(msg)


@bot.message_handler(regexp='🚖 (?:Оформить заказ|Arrange an order/ make an order|Buyurtmani rasmiylashtirish)')
def form(msg):
    dbw = db()
    try:
        lng = dbw.get_user_lang(msg.from_user.id)[0][0]
    except IndexError:
        return
    if len(dbw.get_user_cart(msg.from_user.id)[1]) == 0:
        bot.send_message(msg.chat.id, locales[lng][45])
        catalog(msg)
        return
    dbw.set_state(msg.from_user.id, 'form_start')
    key = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    key.add(types.KeyboardButton('🏃 '+locales[lng][35]), types.KeyboardButton('📍 '+locales[lng][46], request_location=True),
            types.KeyboardButton('⬅️'+locales[lng][1]))
    bot.send_message(msg.chat.id, locales[lng][47], reply_markup=key)


@bot.callback_query_handler(func=lambda call: call.data.startswith('delmsg'))
def del_msg(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)


@bot.message_handler(regexp="Рассылка|Announce|E'lon", func=lambda msg: msg.from_user.id in config.admin_id)
def start_an(msg):
    global an_stat
    global an_id
    if an_id != 0 and an_id != msg.from_user.id:
        bot.send_message(msg.chat.id, 'Рассылка занята')
        return
    an_stat = True
    an_id = msg.from_user.id
    try:
        lng = db().get_user_lang(msg.from_user.id)[0][0]
    except IndexError:
        return
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(types.KeyboardButton(locales[lng][10]))
    bot.send_message(msg.chat.id, locales[lng][48], reply_markup=key)


@bot.message_handler(func=lambda msg: msg.content_type == 'text' and msg.text.startswith('/admin') and msg.from_user.id in config.admin_id)
def add_cat(msg):
    key = keygen(0, msg.from_user.id)
    try:
        lng = db().get_user_lang(msg.from_user.id)[0][0]
    except IndexError:
        return
    bot.send_message(msg.chat.id, locales[lng][49], reply_markup=key)


@bot.callback_query_handler(func=lambda call: call.data.startswith('add_cat'))
def add_cat(call):
    global state
    global status
    try:
        lng = db().get_user_lang(call.from_user.id)[0][0]
    except IndexError:
        return
    status[call.message.chat.id] = call.data
    bot.send_message(call.message.chat.id, locales[lng][50].replace('\\n', '\n'))


@bot.message_handler(func=lambda msg: msg.from_user.id in config.admin_id and status[msg.chat.id].startswith('add_cat'))
def add_category(msg):
    global state
    global status
    cat_id = status[msg.chat.id].split('_')[2]
    name = msg.text
    db().add_cat(cat_id, name)
    status[msg.chat.id] = '0'
    catalog1(msg, 0, uid=msg.from_user.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('del_cat_'))
def del_cat_confirm(call):
    key = types.InlineKeyboardMarkup()
    try:
        lng = db().get_user_lang(call.from_user.id)[0][0]
    except IndexError:
        return
    key.add(types.InlineKeyboardButton(locales[lng][51], callback_data='y'+call.data),
            types.InlineKeyboardButton(locales[lng][52], callback_data='delmsg'))
    bot.send_message(call.message.chat.id, locales[lng][53], reply_markup=key)


@bot.callback_query_handler(func=lambda call: call.data.startswith('del_it_'))
def del_item_confirm(call):
    key = types.InlineKeyboardMarkup()
    try:
        lng = db().get_user_lang(call.from_user.id)[0][0]
    except IndexError:
        return
    key.add(types.InlineKeyboardButton(locales[lng][51], callback_data='y' + call.data),
            types.InlineKeyboardButton(locales[lng][52], callback_data='delmsg'))
    bot.send_message(call.message.chat.id, locales[lng][54], reply_markup=key)


@bot.callback_query_handler(func=lambda call: call.data.startswith('ydel_cat_'))
def del_cat(call):
    cat_id = call.data.split('_')[2]
    parent = db().del_cat(cat_id)
    catalog1(call.message, parent, edit=False, uid=call.from_user.id)
    bot.delete_message(call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('ydel_it_'))
def del_item(call):
    item_id = call.data.split('_')[2]
    try:
        parent = db().get_item_by_id(item_id)[0][4]
    except IndexError:
        return
    db().del_item(item_id)
    catalog1(call.message, parent, edit=False, uid=call.from_user.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('add_it'))
def add_item_start(call):
    global state
    global status
    status[call.from_user.id] = call.data
    parent = call.data.split('_')[2]
    db().create_item(parent, call.from_user.id)
    try:
        lng = db().get_user_lang(call.from_user.id)[0][0]
    except IndexError:
        return
    bot.send_message(call.message.chat.id, locales[lng][55].replace('\\n', '\n'))


@bot.message_handler(func=lambda msg: msg.from_user.id in config.admin_id and status[msg.chat.id].startswith('add_it'))
def set_title(msg):
    global state
    global status
    status[msg.chat.id] = 'desc'
    db().set_title(msg.text, msg.chat.id)
    try:
        lng = db().get_user_lang(msg.from_user.id)[0][0]
    except IndexError:
        return
    bot.send_message(msg.chat.id, locales[lng][56].replace('\\n', '\n'))


@bot.message_handler(func=lambda msg: msg.from_user.id in config.admin_id and status[msg.chat.id].startswith('desc'))
def set_desc(msg):
    global state
    global status
    try:
        lng = db().get_user_lang(msg.from_user.id)[0][0]
    except IndexError:
        return
    if len(msg.text) > 120:
        bot.send_message(msg.chat.id, locales[lng][57])
        return
    status[msg.chat.id] = 'price'
    db().set_desc(msg.text, msg.chat.id)
    bot.send_message(msg.chat.id, locales[lng][58].replace('\\n', '\n'))


@bot.message_handler(func=lambda msg: msg.from_user.id in config.admin_id and status[msg.chat.id].startswith('price'))
def set_price(msg):
    global state
    global status
    try:
        lng = db().get_user_lang(msg.from_user.id)[0][0]
    except IndexError:
        return
    try:
        float(msg.text)
    except ValueError:
        bot.send_message(msg.chat.id, locales[lng][59])
        return
    status[msg.chat.id] = 'photo'
    db().set_price(msg.text, msg.chat.id)
    bot.send_message(msg.chat.id, locales[lng][60].replace('\\n', '\n'))


@bot.message_handler(func=lambda msg: msg.from_user.id in config.admin_id and status[msg.chat.id].startswith('photo'))
def set_photo(msg):
    global status
    item_id = db().set_photo(msg.text, msg.chat.id)
    status[msg.chat.id] = '0'
    catalog1(msg, 0, uid=msg.from_user.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('cat_'))
def show_page(call):
    cat_id = call.data.split('_')[1]
    catalog1(call.message, cat_id, edit=True, uid=call.from_user.id)


def catalog1(msg, cat_id, uid, edit=False):
    try:
        lng = db().get_user_lang(uid)[0][0]
    except IndexError:
        print('Index in cat1')
        return
    if not db().check_cat(cat_id):
        bot.send_message(msg.chat.id, locales[lng][61])
        catalog(msg)
    else:
        text = locales[lng][62]
        key = keygen(cat_id, msg.chat.id)
        if not edit:
            bot.send_message(msg.chat.id, text, reply_markup=key)
        else:
            bot.edit_message_reply_markup(msg.chat.id, msg.message_id, reply_markup=key)


@bot.message_handler(regexp='Оставить отзыв|Leave a comment/ feedback|Fikr qoldirish')
def feedback_start(msg):
    db().set_state(msg.from_user.id, 'fb_write')
    try:
        lng = db().get_user_lang(msg.from_user.id)[0][0]
    except IndexError:
        return
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(types.KeyboardButton('⬅️'+locales[lng][1]))
    bot.send_message(msg.chat.id, locales[lng][63], reply_markup=key)


@bot.message_handler(func=lambda msg: db().get_state(msg.from_user.id) == 'fb_write')
def feedback_send(msg):
    db().set_state(msg.from_user.id, '0')
    try:
        lng = db().get_user_lang(msg.from_user.id)[0][0]
    except IndexError:
        return

    for i in config.admin_id:
        try:
            lng = db().get_user_lang(i)[0][0]
        except IndexError:
            continue
        text = '[{}](tg://user?id={}) {}\n\n{}'.format(msg.from_user.first_name, msg.from_user.id, locales[lng][64],
                                                       msg.text)
        key = types.InlineKeyboardMarkup()
        key.add(types.InlineKeyboardButton(locales[lng][65], callback_data='reply_{}'.format(msg.from_user.id)))
        try:
            bot.send_message(i, text, reply_markup=key, parse_mode='markdown')
        except Exception:
            continue
    bot.send_message(msg.chat.id, locales[lng][66], reply_markup=std_key(msg))


@bot.callback_query_handler(func=lambda call: call.data.startswith('reply_') and call.from_user.id in config.admin_id)
def reply_start(call):
    db().set_state(call.from_user.id, call.data)
    try:
        lng = db().get_user_lang(call.from_user.id)[0][0]
    except IndexError:
        return
    key = types.ReplyKeyboardMarkup(resize_keyboard=True)
    key.add(types.KeyboardButton('⬅️'+locales[lng][1]))
    bot.send_message(call.from_user.id, locales[lng][67], reply_markup=key)


@bot.message_handler(func=lambda msg: msg.from_user.id in config.admin_id and db().get_state(msg.from_user.id).startswith('reply_'))
def reply_send(msg):
    dbw = db()
    user = dbw.get_state(msg.from_user.id).split('_')[1]
    try:
        lng = dbw.get_user_lang(user)[0][0]
        bot.send_message(user, locales[lng][68]+'\n\n'+msg.text)
        dbw.set_state(msg.from_user.id, '0')
        lng = dbw.get_user_lang(msg.from_user.id)[0][0]
    except IndexError:
        return
    bot.send_message(msg.chat.id, locales[lng][69])
    catalog(msg)


@bot.channel_post_handler()
def chan_post(msg):
    bot.send_message(89848329, str(msg))


if __name__ == '__main__':
        db().com()
        cats = db().get_categories(0)
        for c in cats:
            categories[c[1]] = c[0]
        for a in config.admin_id:
            status[a] = ''
        bot.polling(none_stop=True, timeout=7200)




