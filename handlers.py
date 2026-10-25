import json
import random

import telebot
from telebot import types

from models import History
from settings import settings
from api_client import search_movies, get_top_movies, get_genres, search_by_genre

bot = telebot.TeleBot(settings.bot_token.get_secret_value())

RANDOM_WORDS = [
    "любовь", "война", "жизнь", "смерть", "деньги", "тайна",
    "побег", "месть", "страх", "семья", "дружба", "космос",
    "дракон", "убийство", "город", "океан", "звезда", "ночь"
]

user_films = {}


@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Обрабатывает команду '/start'."""
    bot.reply_to(message, "Привет! Я бот для поиска фильмов. Напиши /help, чтобы узнать, что я умею.")


@bot.message_handler(commands=['help'])
def send_help(message):
    """Обрабатывает команду '/help'."""
    bot.reply_to(
        message,
        "Я умею искать фильмы по названию.\n"
        "Команды:\n"
        "/search - начать поиск фильма\n"
        "/genre - поиск  фильма по жанру\n"
        "/random - поиск случайного фильма\n"
        "/top - показать топ-250 лучших фильмов\n"
        "/history - показать историю запросов\n"
        "/help - помощь"
    )

@bot.message_handler(commands=['history'])
def send_history(message):
    """Показывает историю последних 10 запросов."""
    records = History.select().where(
        History.user_id == message.chat.id
    ).order_by(History.created_at.desc()).limit(10)

    if records:
        text = "📋 История запросов:\n\n"
        for record in records:
            date = record.created_at.strftime('%d.%m.%Y %H:%M')
            text += (
                f"{record.command} — {record.result} ({record.year})\n"
                f"⭐ {record.rating} | 🎭 {record.genres}\n"
                f"📅 {date}\n\n"
            )

        bot.reply_to(message, text)
    else:
        bot.reply_to(message, "История пуста.")


def show_film(chat_id, film, films=None, index=0, is_top=False, page=1, pages_count=1):
    """Отправляет информацию о фильме с постером и кнопками навигации."""
    description = film.get('description', '') or film.get('shortDescription', '') or 'Описание отсутствует.'
    genres = ', '.join(g.get('genre', '') for g in film.get('genres', []))


    text = (
        f"🎬 {film.get('nameRu', 'Без названия')}\n"
        f"📅 Год: {film.get('year', '—')}\n"
        f"⭐ Рейтинг: {film.get('rating', '—')}\n"
        f"🎭 Жанр: {genres}\n"
        f"📖 {description}..."
    )

    markup = types.InlineKeyboardMarkup()

    # Кнопки переключения фильмов
    if films and len(films) > 1:
        total = len(films)
        prev_prefix = 'top_nav_' if is_top else 'search_'
        next_prefix = 'top_nav_' if is_top else 'search_'

        btn_back = types.InlineKeyboardButton('Назад', callback_data=f'{prev_prefix}prev')
        btn_count = types.InlineKeyboardButton(f'{index + 1}/{total}', callback_data='none')
        btn_next = types.InlineKeyboardButton('Дальше', callback_data=f'{next_prefix}next')
        markup.row(btn_back, btn_count, btn_next)

    # Кнопки переключения страниц (только для топа)
    if is_top:
        btn_prev_page = types.InlineKeyboardButton(
            '◀ Страница',
            callback_data=f'top_page_{page - 1}' if page > 1 else 'none'
        )
        btn_page_info = types.InlineKeyboardButton(
            f'{page}/{pages_count}',
            callback_data='none'
        )
        btn_next_page = types.InlineKeyboardButton(
            'Страница ▶',
            callback_data=f'top_page_{page + 1}' if page < pages_count else 'none'
        )
        markup.row(btn_prev_page, btn_page_info, btn_next_page)

    # Кнопка на Кинопоиск
    film_id = film.get('filmId') or film.get('kinopoiskId', '')
    url = f"https://www.kinopoisk.ru/film/{film_id}/"
    markup.add(types.InlineKeyboardButton('Подробнее на Кинопоиске', url=url))

    # Отправка
    poster = film.get('posterUrl', '')
    if poster and 'no-poster' not in poster:
        try:
            bot.send_photo(chat_id, poster, caption=text, reply_markup=markup)
        except Exception:
            bot.send_message(chat_id, text, reply_markup=markup)
    else:
        bot.send_message(chat_id, text, reply_markup=markup)


@bot.message_handler(commands=['genre'])
def send_genre(message):

    response = get_genres()

    if response and response.get('genres'):
        genres = response['genres']
        markup = types.InlineKeyboardMarkup()
        for g in genres[:15]:
            markup.add(types.InlineKeyboardButton(
                g['genre'],
                callback_data=f'genre_{g["id"]}'
            ))
        bot.reply_to(message, "Выберите жанр:", reply_markup=markup)
    else:
        bot.reply_to(message, "Не удалось загрузить жанры.")


@bot.message_handler(commands=['top'])
def send_top(message):
    """Обрабатывает команду '/top'."""
    response = get_top_movies()

    if response and response.get('films'):
        films = response['films']
        pages_count = response.get('pagesCount', 1)
        user_films[message.chat.id] = {
            'films': films, 'index': 0, 'page': 1,
            'is_top': True, 'pages_count': pages_count
        }
        bot.send_message(message.chat.id, "⚠️ В топе Кинопоиска нет описаний фильмов.")

        History.create(
            user_id=message.chat.id,
            command='/top',
            query='топ-250',
            result=films[0].get('nameRu', '—'),
            year=films[0].get('year', '—'),
            rating=films[0].get('rating', '—'),
            genres=', '.join(g.get('genre', '') for g in films[0].get('genres', [])),
            poster=films[0].get('posterUrl', '')
        )

        show_film(message.chat.id, films[0], films, 0, is_top=True, page=1, pages_count=pages_count)
    else:
        bot.reply_to(message, "Не удалось загрузить топ фильмов.")


@bot.message_handler(commands=['random'])
def random_search(message):
    """Обрабатывает команду '/random'."""
    keyword = random.choice(RANDOM_WORDS)
    result = search_movies(keyword)

    if result and result.get('films'):
        film = random.choice(result['films'])
        user_films[message.chat.id] = {'films': [film], 'index': 0, 'is_top': False}

        History.create(
            user_id=message.chat.id,
            command='/random',
            query=keyword,
            result=film.get('nameRu', '—'),
            year=film.get('year', '—'),
            rating=film.get('rating', '—'),
            genres=', '.join(g.get('genre', '') for g in film.get('genres', [])),
            poster=film.get('posterUrl', '')
        )

        show_film(message.chat.id, film)
    else:
        bot.reply_to(message, "Не удалось найти фильм. Попробуйте ещё раз /random")


@bot.message_handler(commands=['search'])
def send_search(message):
    """Обрабатывает команду '/search'."""
    bot.reply_to(message, "Введите название фильма:")
    bot.register_next_step_handler(message, process_search)


def process_search(message):
    """Обрабатывает поисковый запрос."""
    keyword = message.text
    result = search_movies(keyword)

    with open('search_result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    if result and result.get('films'):
        films = result['films']
        user_films[message.chat.id] = {'films': films, 'index': 0, 'is_top': False}
        film = films[0]

        History.create(
            user_id=message.chat.id,
            command='/search',
            query=keyword,
            result=film.get('nameRu', '—'),
            year=film.get('year', '—'),
            rating=film.get('rating', '—'),
            genres=', '.join(g.get('genre', '') for g in film.get('genres', [])),
            poster=film.get('posterUrl', '')
        )

        show_film(message.chat.id, films[0], films, 0)
    else:
        bot.reply_to(message, "Ничего не найдено.")


# Навигация для поиска
@bot.callback_query_handler(func=lambda call: call.data in ['search_prev', 'search_next'])
def handle_search_navigation(call):
    """Переключает фильмы в поиске."""
    chat_id = call.message.chat.id

    if chat_id not in user_films or user_films[chat_id].get('is_top'):
        bot.answer_callback_query(call.id, 'Данные устарели. Сделайте новый поиск.')
        return

    data = user_films[chat_id]
    films = data['films']
    index = data['index']

    if call.data == 'search_next':
        index = min(index + 1, len(films) - 1)
    elif call.data == 'search_prev':
        index = max(index - 1, 0)

    data['index'] = index
    film = films[index]

    bot.delete_message(chat_id, call.message.message_id)
    show_film(chat_id, film, films, index)


# Навигация для топа
@bot.callback_query_handler(func=lambda call: call.data in ['top_nav_prev', 'top_nav_next'])
def handle_top_navigation(call):
    """Переключает фильмы внутри страницы топа."""
    chat_id = call.message.chat.id

    if chat_id not in user_films or not user_films[chat_id].get('is_top'):
        bot.answer_callback_query(call.id, 'Данные устарели. Сделайте новый поиск.')
        return

    data = user_films[chat_id]
    films = data['films']
    index = data['index']
    page = data.get('page', 1)
    pages_count = data.get('pages_count', 1)

    if call.data == 'top_nav_next':
        index = min(index + 1, len(films) - 1)
    elif call.data == 'top_nav_prev':
        index = max(index - 1, 0)

    data['index'] = index
    film = films[index]

    bot.delete_message(chat_id, call.message.message_id)
    show_film(chat_id, film, films, index, is_top=True, page=page, pages_count=pages_count)


# Переключение страниц топа
@bot.callback_query_handler(func=lambda call: call.data.startswith('top_page_'))
def handle_top_page(call):
    """Загружает новую страницу топа."""
    chat_id = call.message.chat.id
    page = int(call.data.split('_')[-1])

    response = get_top_movies(page)

    if response and response.get('films'):
        films = response['films']
        pages_count = response.get('pagesCount', 1)
        user_films[chat_id] = {
            'films': films, 'index': 0, 'page': page,
            'is_top': True, 'pages_count': pages_count
        }

        bot.delete_message(chat_id, call.message.message_id)
        show_film(chat_id, films[0], films, 0, is_top=True, page=page, pages_count=pages_count)
    else:
        bot.answer_callback_query(call.id, 'Страница не найдена.')

@bot.callback_query_handler(func=lambda call: call.data.startswith('genre_'))
def handle_genre(call):
    chat_id = call.message.chat.id
    genre_id = int(call.data.split('_')[1])

    response = search_by_genre(genre_id)

    if response and response.get('items'):
        films = response['items']
        user_films[chat_id] = {'films': films, 'index': 0, 'is_top': False}

        bot.delete_message(chat_id, call.message.message_id)
        show_film(chat_id, films[0], films, 0)
    else:
        bot.answer_callback_query(call.id, 'Ничего не найдено.')


# Ответ на неизвестные сообщения
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    """Отвечает на любое сообщение, которое не попало под другие обработчики."""
    bot.reply_to(
        message,
        "Я не понимаю ваш запрос.\n"
        "Используйте /help для списка команд."
    )