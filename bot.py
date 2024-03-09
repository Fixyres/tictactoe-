import telebot
from telebot import types
import random

TOKEN = 'YOUR_BOT_TOKEN'
bot = telebot.TeleBot(TOKEN)

games = {}

class TicTacToeGame:
    def __init__(self):
        self.game_board = [[' ' for _ in range(3)] for _ in range(3)]
        self.players = {'X': None, 'O': None}
        self.current_player = None
        self.player_symbols = {'X': '', 'O': ''}
        self.player_names = {'X': '', 'O': ''}
        self.game_active = False

    def render_board(self):
        keyboard = types.InlineKeyboardMarkup()
        for row in range(3):
            buttons = []
            for col in range(3):
                symbol = self.player_symbols[self.game_board[row][col]] if self.game_board[row][col] in self.player_symbols else ' '
                callback_data = f"move:{row}:{col}"
                buttons.append(types.InlineKeyboardButton(text=symbol, callback_data=callback_data))
            keyboard.row(*buttons)

        if self.game_active:
            leave_button = types.InlineKeyboardButton('Покинуть игру', callback_data='leave')
            keyboard.row(leave_button)

        return keyboard

    def check_winner(self, sign):
        for row in self.game_board:
            if row.count(sign) == 3:
                return True
        for col in range(3):
            if all(self.game_board[row][col] == sign for row in range(3)):
                return True
        if all(self.game_board[i][i] == sign for i in range(3)) or all(self.game_board[i][2 - i] == sign for i in range(3)):
            return True
        return False

    def check_draw(self):
        return all(self.game_board[row][col] != ' ' for row in range(3) for col in range(3))

    def reset_game(self):
        self.game_board = [[' ' for _ in range(3)] for _ in range(3)]
        self.players = {'X': None, 'O': None}
        self.current_player = None
        self.player_names = {'X': '', 'O': ''}
        self.game_active = False

@bot.message_handler(commands=['t'])
def start_game(message):
    chat_id = message.chat.id

    if chat_id in games and games[chat_id][-1].game_active:
        bot.send_message(chat_id, "Вы уже участвуете в активной игре. Дождитесь ее завершения или воспользуйтесь кнопкой 'Покинуть игру'.")
        return

    if chat_id not in games:
        games[chat_id] = []

    new_game = TicTacToeGame()
    games[chat_id].append(new_game)

    user = message.from_user
    new_game.players['X'] = user.id
    new_game.player_names['X'] = user.first_name

    join_button = types.InlineKeyboardButton('Присоединиться', callback_data='join')
    markup = types.InlineKeyboardMarkup().add(join_button)
    bot.send_message(chat_id, f"[{user.first_name}](tg://user?id={user.id}), ожидание второго игрока...", reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id

    if chat_id not in games:
        return

    current_game = games[chat_id][-1]

    if call.data == 'join':
        if not current_game.game_active and current_game.players['O'] is None and call.from_user.id != current_game.players['X']:
            current_game.players['O'] = call.from_user.id
            current_game.player_names['O'] = call.from_user.first_name
            current_game.current_player = random.choice(['X', 'O'])
            current_game.player_symbols['X'] = '❌' if random.random() < 0.5 else '⭕'
            current_game.player_symbols['O'] = '⭕' if current_game.player_symbols['X'] == '❌' else '❌'
            markup = current_game.render_board()
            text = f"[{current_game.player_names['X']}](tg://user?id={current_game.players['X']}) {current_game.player_symbols['X']} против [{current_game.player_names['O']}](tg://user?id={current_game.players['O']}) {current_game.player_symbols['O']}\n\nТекущий ход: [{current_game.player_names[current_game.current_player]}](tg://user?id={current_game.players[current_game.current_player]})"
            bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text, reply_markup=markup, parse_mode='Markdown')
            current_game.game_active = True
            if current_game.current_player == 'O':
                bot.answer_callback_query(call.id, f"Текущий ход: [{current_game.player_names['O']}](tg://user?id={current_game.players['O']})")
        else:
            bot.answer_callback_query(call.id, "Игра уже началась или вы уже участвуете.")
        return

    if call.data == 'leave':
        if current_game.game_active and (call.from_user.id == current_game.players['X'] or call.from_user.id == current_game.players['O']):
            text = f"{current_game.player_names[current_game.current_player]} покинул игру! Игра окончена.\n\n[{current_game.player_names['X']}](tg://user?id={current_game.players['X']}) {current_game.player_symbols['X']} против [{current_game.player_names['O']}](tg://user?id={current_game.players['O']}) {current_game.player_symbols['O']}"
            bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text, parse_mode='Markdown')
            current_game.reset_game()
        return

    if not current_game.game_active:
        bot.answer_callback_query(call.id, "Игра уже окончена!")
        return

    row, col = map(int, call.data.split(':')[1:])
    if current_game.players[current_game.current_player] != call.from_user.id:
        bot.answer_callback_query(call.id, "Сейчас не ваш ход!")
        return
    if current_game.game_board[row][col] != ' ':
        bot.answer_callback_query(call.id, "Клетка уже занята!")
        return

    current_game.game_board[row][col] = current_game.current_player
    if current_game.check_winner(current_game.current_player):
        winner_name = current_game.player_names[current_game.current_player]
        text = f"Победил [{winner_name}](tg://user?id={current_game.players[current_game.current_player]})!\n\n[{current_game.player_names['X']}](tg://user?id={current_game.players['X']}) {current_game.player_symbols['X']} против [{current_game.player_names['O']}](tg://user?id={current_game.players['O']}) {current_game.player_symbols['O']}"
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text, reply_markup=current_game.render_board(), parse_mode='Markdown')
        current_game.reset_game()
        return

    if current_game.check_draw():
        text = f"Игра завершилась вничью!\n\n[{current_game.player_names['X']}](tg://user?id={current_game.players['X']}) {current_game.player_symbols['X']} против [{current_game.player_names['O']}](tg://user?id={current_game.players['O']}) {current_game.player_symbols['O']}"
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text, reply_markup=current_game.render_board(), parse_mode='Markdown')
        current_game.reset_game()
        return

    current_game.current_player = 'X' if current_game.current_player == 'O' else 'O'
    markup = current_game.render_board()
    text = f"[{current_game.player_names['X']}](tg://user?id={current_game.players['X']}) {current_game.player_symbols['X']} против [{current_game.player_names['O']}](tg://user?id={current_game.players['O']}) {current_game.player_symbols['O']}\n\nТекущий ход: [{current_game.player_names[current_game.current_player]}](tg://user?id={current_game.players[current_game.current_player]})"
    bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id, text=text, reply_markup=markup, parse_mode='Markdown')

bot.infinity_polling()
