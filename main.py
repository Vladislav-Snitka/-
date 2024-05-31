import telebot
from telebot import types
from mysql.connector import connect

bot = telebot.TeleBot('6967598253:AAEEyJbq66RCuZHc5ptoSCBR07an9_VrppU')

connection = connect(host='localhost',
                     user='root',
                     password='root',
                     database='snitka_project'
                     )

first_name = None
telegram_id = None

user_map = {}
user_info = ''
result_rating = ''
info = ''
total = 0
counter = 0
information = ''


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.from_user.id, '👋 Вітаю!')
    bot.send_message(message.from_user.id,
                     'Правила оцінювання наступні:\nПеремога - 3 бали.\nНічия - 1 бал обом.\nПрограш - 0 балів.')
    cursor = connection.cursor()
    cursor.execute("DELETE FROM rating WHERE first_player")
    connection.commit()
    cursor.close()
    user_map[message.from_user.id] = 'registration'
    markup = types.ReplyKeyboardMarkup()
    button1 = types.KeyboardButton('Реєстрація')
    markup.add(button1)
    bot.send_message(message.from_user.id, 'Для початку пройдіть реєстрацію.', reply_markup=markup)


@bot.message_handler(content_types=['text'])
def registration(message):
    global telegram_id
    telegram_id = message.from_user.id
    if user_map[message.from_user.id] == 'registration' and message.text == 'Реєстрація':
        user_map[message.from_user.id] = "choose_role"
        markup = types.ReplyKeyboardMarkup()
        button2 = types.KeyboardButton('Гравець')
        button3 = types.KeyboardButton('Адміністратор')
        markup.add(button2, button3)
        bot.send_message(message.from_user.id, 'Виберіть ким ви хотіли б зареєструватися.', reply_markup=markup)

    if user_map[message.from_user.id] == 'choose_role' and message.text == 'Адміністратор':
        user_map[message.from_user.id] = 'admin'
        admin(message)

    elif user_map[message.from_user.id] == 'choose_role' and message.text == 'Гравець':
        user_map[message.from_user.id] = 'gamer'
        bot.send_message(message.from_user.id, "Введіть ваше ім'я.")
        bot.register_next_step_handler(message, f_name)


def f_name(message):
    global first_name
    first_name = message.text
    bot.register_next_step_handler(message, s_name)
    bot.send_message(message.from_user.id, 'Введіть ваше прізвище.')


def s_name(message):
    cursor = connection.cursor()
    second_name = message.text
    cursor.execute("INSERT INTO user (user_id, first_name, second_name) VALUES (%s, %s, %s)",
                   (telegram_id, first_name, second_name))
    connection.commit()
    bot.send_message(message.from_user.id, 'Ви зареєстровані як гравець. Welcome!')
    cursor.execute("INSERT INTO gamer (user_id) VALUES (%s)", (telegram_id,))
    connection.commit()
    cursor.close()


def admin(message):
    cursor = connection.cursor()
    cursor.execute("INSERT INTO user (user_id, role) VALUES (%s, 1)",
                   (telegram_id,))
    connection.commit()
    cursor.close()
    bot.send_message(message.from_user.id, 'Успішно авторизовано.')
    markup = types.ReplyKeyboardMarkup()
    history_button = types.KeyboardButton('Вивести список гравців')
    game_button = types.KeyboardButton('Запустити гру')
    markup.add(history_button, game_button)
    bot.send_message(message.from_user.id, 'Виберіть наступний пункт.', reply_markup=markup)
    bot.register_next_step_handler(message, admin_panel)


def admin_panel(message):
    if message.text == 'Вивести список гравців':
        global user_info
        cursor = connection.cursor()
        cursor.execute("select first_name, second_name from user u join gamer g on u.user_id = g.user_id")
        result = cursor.fetchall()
        for count, user in enumerate(result, start=1):
            user_info += f"{count}. {user[0]} {user[1]}\n"
        bot.send_message(message.chat.id, user_info)
        user_info = ''
        bot.register_next_step_handler(message, admin_panel)
    elif message.text == 'Запустити гру':
        cursor = connection.cursor()
        cursor.execute("select player_id from gamer")
        result = cursor.fetchall()
        for i in range(len(result)):
            for j in range(i + 1, len(result)):
                first_player = result[i][0]
                second_player = result[j][0]
                cursor.execute("insert into rating(first_player, second_player) values (%s, %s)",
                               (first_player, second_player))
                connection.commit()
        global result_rating
        cursor.execute("select first_player, second_player from rating")
        result_rating = cursor.fetchall()
        cursor.close()
        bot.send_message(message.from_user.id, "Список гравців сформовано.")
        bot.send_message(message.from_user.id, "Пропоную перейти до виставлення результатів.")
        tournament_buttons(message)


def tournament_buttons(message):
    markup = types.ReplyKeyboardMarkup()
    button2 = types.KeyboardButton('Перший гравець виграв')
    button3 = types.KeyboardButton('Другий гравець виграв')
    button4 = types.KeyboardButton('Нічия')
    markup.add(button2, button3, button4)
    if counter < len(result_rating):
        cursor = connection.cursor()
        cursor.execute(
            'SELECT r.first_player, u1.first_name, u1.second_name, r.second_player, u2.first_name, u2.second_name '
            'FROM rating r INNER JOIN gamer g1 ON r.first_player = g1.player_id '
            'INNER JOIN user u1 ON g1.user_id = u1.user_ID '
            'INNER JOIN gamer g2 ON r.second_player = g2.player_id '
            'INNER JOIN user u2 ON g2.user_id = u2.user_ID')
        opponents = cursor.fetchall()
        cursor.close()
        bot.send_message(message.from_user.id,
                         f'{counter + 1} пара: \n{opponents[counter][1]} {opponents[counter][2]} - '
                         f'{opponents[counter][4]} {opponents[counter][5]}.',
                         reply_markup=markup)
        bot.register_next_step_handler(message, tournament)
    else:
        bot.send_message(message.from_user.id, 'Перерахунок закінчено.')
        markup = types.ReplyKeyboardMarkup()
        result_button = types.KeyboardButton('Вивести кінцеві результати')
        markup.add(result_button)
        bot.send_message(message.from_user.id, 'Ви можете перейти до загальних результатів.', reply_markup=markup)
        bot.register_next_step_handler(message, result_update)


def tournament(message):
    global info
    global counter
    f_player = result_rating[counter][0]
    s_player = result_rating[counter][1]
    if message.text == 'Перший гравець виграв':
        info = 'first_win'
    elif message.text == 'Другий гравець виграв':
        info = 'second_win'
    else:
        info = 'draw'
    cursor = connection.cursor()
    cursor.execute('UPDATE rating SET result = %s where first_player = %s and second_player = %s',
                   (info, f_player, s_player))
    connection.commit()
    cursor.close()
    counter += 1
    tournament_buttons(message)


def result_update(message):
    global information
    if message.text == 'Вивести кінцеві результати':
        cursor = connection.cursor()
        cursor.execute('SELECT first_player, second_player, result FROM rating')
        result = cursor.fetchall()
        scores = {}
        for row in result:
            player1, player2, result = row
            if result == "first_win":
                scores[player1] = scores.get(player1, 0) + 3
            elif result == "second_win":
                scores[player2] = scores.get(player2, 0) + 3
            elif result == "draw":
                scores[player1] = scores.get(player1, 0) + 1
                scores[player2] = scores.get(player2, 0) + 1
    scores = sorted(scores.items(), key=lambda item: item[1])
    for key, value in scores:
        cursor = connection.cursor()
        cursor.execute('SELECT u.first_name, u.second_name '
                       'FROM user u '
                       'JOIN gamer g ON u.user_ID = g.user_id '
                       'JOIN rating r ON g.player_id = %s OR g.player_id = %s '
                       'GROUP BY u.first_name, u.second_name', (key, key))
        result = cursor.fetchall()
        information += f"У {result[0][0]} {result[0][1]} - {value} очка(ів).\n"
    information += "\nВсі інші не виграли ні разу."
    bot.send_message(message.from_user.id, information)


bot.polling(none_stop=True, interval=0)
