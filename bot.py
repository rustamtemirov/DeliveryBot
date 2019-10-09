from telebot import TeleBot, types
from databaser import Databaser as db
import config


bot = TeleBot(config.token)
state = '0'
status = {}
orders = {}
for a in config.admin_id:
    status[a] = '0'


def keygen(cat_id, uid):
    key = types.InlineKeyboardMarkup()
    cats = db().get_categories(cat_id)
    for c in cats:
        key.add(types.InlineKeyboardButton(c[1], callback_data='cat_'+str(c[0])))
    items = db().get_items(cat_id)
    for i in items:
        key.add(types.InlineKeyboardButton(i[1], callback_data='it_'+str(i[0])))
    if uid in config.admin_id:
        key.add(types.InlineKeyboardButton('[Добавить категорию]', callback_data='add_cat_'+str(cat_id)),
                types.InlineKeyboardButton('[Добавить товар]', callback_data='add_it_'+str(cat_id)))
        if int(cat_id) > 0:
            key.add(types.InlineKeyboardButton('[Удалить категорию]', callback_data='del_cat_'+str(cat_id)))
    if int(cat_id) > 0:
        parent = db().get_parent(cat_id)[0][0]
        key.add(types.InlineKeyboardButton('Назад', callback_data='cat_'+str(parent)))
    return key


def item_keygen(item_id, uid, item_parent):
    key = types.InlineKeyboardMarkup(row_width=1)
    key.add(types.InlineKeyboardButton('Предыдущий товар', callback_data='prev_{}_{}'.format(item_id, item_parent)),
            types.InlineKeyboardButton('Добавить в корзину', callback_data='atc_'+str(item_id)),
            types.InlineKeyboardButton('Назад', callback_data='delmsg'),
            types.InlineKeyboardButton('Следующий товар', callback_data='next_{}_{}'.format(item_id, item_parent)))
    if uid in config.admin_id:
        key.add(types.InlineKeyboardButton('[Удалить товар]', callback_data='del_it_'+str(item_id)))
    return key


@bot.message_handler(content_types=['text', 'location'], func=lambda msg: db().get_state(msg.from_user.id) == 'loca')
def loc_acq(msg: types.Message):
    d = db()
    if msg.content_type == 'text':
        orders[msg.from_user.id] = msg.text
        d.set_addr(msg.from_user.id, msg.text)
    else:
        orders[msg.from_user.id] = msg.location
        d.set_loc(msg.from_user.id, msg.location.latitude, msg.location.longitude)
    key = types.InlineKeyboardMarkup()
    key.add(types.InlineKeyboardButton('Оплата картой', callback_data='pay_with_card'),
            types.InlineKeyboardButton('Оплата наличными', callback_data='pay_with_cash'))
    bot.send_message(msg.chat.id, 'Выберите способ оплаты', reply_markup=key)


@bot.callback_query_handler(func=lambda call: call.data.startswith('atc_'))
def add_to_cart(call):
    dbaser = db()
    dbaser.add_to_cart(call.from_user.id, call.data.split('_')[1])
    bot.send_message(call.from_user.id, 'Добавлено в корзину')


@bot.callback_query_handler(func=lambda call: call.data.startswith('prev_'))
def prev_item(call):
    a, iid, cat_id = call.data.split('_')
    items = db().get_items(cat_id)
    for i in range(len(items)):
        if int(iid) == items[i][0]:
            item_page(call.message, items[i-1][0])
            del_msg(call)


@bot.callback_query_handler(func=lambda call: call.data.startswith('next_'))
def next_item(call):
    a, iid, cat_id = call.data.split('_')
    items = db().get_items(cat_id)
    for i in range(len(items)):
        if int(iid) == items[i][0]:
            if i == len(items) - 1:
                item_page(call.message, items[0][0])
            else:
                item_page(call.message, items[i-1][0])
            del_msg(call)


@bot.message_handler(content_types=['photo'])
def void(msg):
    return


@bot.message_handler(content_types=['text'], func=lambda msg: msg.text.startswith('/start '))
def start_id(msg):
    item_id = msg.text.split()[1]
    item_page(msg, item_id, False)


@bot.message_handler(commands=['start'])
def start(msg):
    db().try_add_user(msg.from_user.id)
    key = types.ReplyKeyboardMarkup(one_time_keyboard=False, resize_keyboard=True)
    key.add(types.KeyboardButton('Каталог'), types.KeyboardButton('Корзина'))
    bot.send_message(msg.chat.id, 'Добро пожаловать в каталог всевозможных товаров', reply_markup=key)


# @bot.message_handler(regexp='Связь с админом')
# def admin_connect(msg):
#     key = types.InlineKeyboardMarkup()
#     key.add(types.InlineKeyboardButton('Связь с админом', url='t.me/'+config.shop_id))
#     bot.send_message(msg.chat.id, 'Вы можете связаться с администрацией, нажав кнопку ниже', reply_markup=key)


@bot.message_handler(regexp='Корзина')
def show_cart(msg):
    info = db().get_user_cart(msg.chat.id)
    items = info[1]
    text = ''
    if len(items) == 0:
        text = 'Ваша корзина пуста'
        bot.send_message(msg.chat.id, text)
        return
    for i in items:
        info1 = db().get_item_by_id(i[1])[0]
        text += '{} {}\n'.format(info1[1], i[2])
    text += '\nИтого: {}'.format(info[0][0])
    key = types.InlineKeyboardMarkup()
    key.add(types.InlineKeyboardButton('Оформить заказ', callback_data='form'),
            types.InlineKeyboardButton('Очистить корзину', callback_data='clear_cart'))
    bot.send_message(msg.chat.id, text, reply_markup=key)


@bot.callback_query_handler(func=lambda call: call.data == 'form')
def form_order(call):
    db().set_state(call.from_user.id, 'loca')
    bot.send_message(call.message.chat.id, 'Отправьте адрес или локацию')


@bot.callback_query_handler(func=lambda call: call.data.startswith('pay_with'))
def order_finish(call):
    d = db()
    provided = d.what_is_provided(call.from_user.id)
    method = 'картой' if call.data.split('_')[2] == 'card' else 'наличными'
    info = d.get_user_cart(call.from_user.id)
    items = info[1]
    order = ''
    for i in items:
        info1 = db().get_item_by_id(i[1])[0]
        order += '{} {}\n'.format(info1[1], i[2])
    order += '\nИтого: {}'.format(info[0][0])
    text = 'Пользователь [{}](tg://user?id={}) сделал заказ\n\n{}\n\nОплата {}'.format(call.from_user.first_name,
                                                                                       call.from_user.id, order,
                                                                                       method)
    loc = [0, 0]
    if provided == 'addr':
        addr = d.get_addr(call.from_user.id)
        text += '\nАдрес: {}'.format(addr)
    else:
        text += '\nЛокация отправлена следующим сообщением'
        loc = d.get_loc(call.from_user.id)
    bot.edit_message_text('Заказ отправлен', call.message.chat.id, call.message.message_id)
    d.set_state(call.from_user.id, '0')
    for i in config.admin_id:
        try:
            bot.send_message(i, text, parse_mode='markdown')
            if provided == 'loc':
                bot.send_location(i, loc[0], loc[1])
        except Exception:
            continue


@bot.callback_query_handler(func=lambda call: call.data == 'clear_cart')
def clear_cart(call):
    db().clear_cart(call.from_user.id)
    bot.edit_message_text('Корзина очищена', call.message.chat.id, call.message.message_id)
        

@bot.message_handler(regexp='Каталог')
def start_catalog(msg):
    catalog(msg, 0)


def catalog(msg, cat_id, edit=False):
    if not db().check_cat(cat_id):
        bot.send_message(msg.chat.id, 'Категория не найдена')
        start_catalog(msg)
    else:
        text = 'Выберите категорию или товар'
        key = keygen(cat_id, msg.chat.id)
        if not edit:
            bot.send_message(msg.chat.id, text, reply_markup=key)
        else:
            bot.edit_message_reply_markup(msg.chat.id, msg.message_id, reply_markup=key)


def item_page(msg, item_id, edit=False):
    if not db().check_item(item_id):
        bot.send_message(msg.chat.id, 'Товар не найден')
        start_catalog(msg)
    else:
        info = db().get_item_by_id(item_id)[0]
        title, desc, photo, parent, price = info[1], info[2], info[3], info[4], info[6]
        text = '[​​​​​​​​​​​]({}) *{}*\n\n{}\n\nСтоимсоть: {}'.format(photo, title, desc, price)
        key = item_keygen(item_id, msg.chat.id, parent)
        bot.send_message(msg.chat.id, text, reply_markup=key, parse_mode='markdown')


@bot.callback_query_handler(func=lambda call: call.data.startswith('add_cat'))
def add_cat(call):
    global state
    global status
    status[call.message.chat.id] = call.data
    bot.send_message(call.message.chat.id, 'Введите название категории   \n\n Для отмены нажмина на /cancel')


@bot.message_handler(func=lambda msg: msg.from_user.id in config.admin_id and status[msg.chat.id].startswith('add_cat'))
def add_category(msg):
    global state
    global status
    cat_id = status[msg.chat.id].split('_')[2]
    name = msg.text
    db().add_cat(cat_id, name)
    status[msg.chat.id] = '0'
    catalog(msg, cat_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('cat_'))
def show_page(call):
    cat_id = call.data.split('_')[1]
    catalog(call.message, cat_id, True)


@bot.callback_query_handler(func=lambda call: call.data.startswith('it_'))
def show_item(call):
    item_id = call.data.split('_')[1]
    item_page(call.message, item_id, True)


@bot.callback_query_handler(func=lambda call: call.data.startswith('del_cat_'))
def del_cat_confirm(call):
    key = types.InlineKeyboardMarkup()
    key.add(types.InlineKeyboardButton('ДА', callback_data='y'+call.data),
            types.InlineKeyboardButton('НЕТ', callback_data='delmsg'))
    bot.send_message(call.message.chat.id, 'Вы действительно хотите удалить категорию?', reply_markup=key)


@bot.callback_query_handler(func=lambda call: call.data.startswith('del_it_'))
def del_item_confirm(call):
    key = types.InlineKeyboardMarkup()
    key.add(types.InlineKeyboardButton('ДА', callback_data='y' + call.data),
            types.InlineKeyboardButton('НЕТ', callback_data='delmsg'))
    bot.send_message(call.message.chat.id, 'Вы действительно хотите удалить товар?', reply_markup=key)


@bot.callback_query_handler(func=lambda call: call.data.startswith('delmsg'))
def del_msg(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('ydel_cat_'))
def del_cat(call):
    cat_id = call.data.split('_')[2]
    parent = db().del_cat(cat_id)
    catalog(call.message, parent, False)
    bot.delete_message(call.message.chat.id, call.message.message_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('ydel_it_'))
def del_item(call):
    item_id = call.data.split('_')[2]
    parent = db().get_item_by_id(item_id)[0][4]
    db().del_item(item_id)
    catalog(call.message, parent, False)


@bot.callback_query_handler(func=lambda call: call.data.startswith('add_it'))
def add_item_start(call):
    global state
    global status
    status[call.from_user.id] = call.data
    parent = call.data.split('_')[2]
    db().create_item(parent, call.from_user.id)
    bot.send_message(call.message.chat.id, 'Введите название товара   \n\n Для отмены нажмина на /cancel')


@bot.message_handler(func=lambda msg: msg.from_user.id in config.admin_id and status[msg.chat.id].startswith('add_it'))
def set_title(msg):
    global state
    global status
    status[msg.chat.id] = 'desc'
    db().set_title(msg.text, msg.chat.id)
    bot.send_message(msg.chat.id, 'Введите описание   \n\n Для отмены нажмите на на /cancel')


@bot.message_handler(func=lambda msg: msg.from_user.id in config.admin_id and status[msg.chat.id].startswith('desc'))
def set_desc(msg):
    global state
    global status
    if len(msg.text) > 120:
        bot.send_message(msg.chat.id, 'Описание должно быть не длиннее 120 символов')
        return
    status[msg.chat.id] = 'price'
    db().set_desc(msg.text, msg.chat.id)
    bot.send_message(msg.chat.id, 'Введите цену   \n\n Для отмены нажмите на на /cancel')


@bot.message_handler(func=lambda msg: msg.from_user.id in config.admin_id and status[msg.chat.id].startswith('price'))
def set_price(msg):
    global state
    global status
    try:
        price = float(msg.text)
    except ValueError:
        bot.send_message(msg.chat.id, 'Введите число')
        return
    status[msg.chat.id] = 'photo'
    db().set_price(msg.text, msg.chat.id)
    bot.send_message(msg.chat.id, 'Пришлите ссылку на фото товара   \n\n Для отмены нажмите на на /cancel')


@bot.message_handler(func=lambda msg: msg.from_user.id in config.admin_id and status[msg.chat.id].startswith('photo'))
def set_photo(msg):
    global status
    item_id = db().set_photo(msg.text, msg.chat.id)
    status[msg.chat.id] = '0'
    item_page(msg, item_id, False)


@bot.message_handler(commands=['cancel'], func=lambda msg: msg.from_user.id in config.admin_id)
def cancel(msg):
    db().cancel_item(msg.chat.id)
    global status
    status[msg.chat.id] = '0'
    bot.send_message(msg.chat.id, 'Отменено')


if __name__ == '__main__':
    bot.polling(none_stop=True, timeout=7200)
