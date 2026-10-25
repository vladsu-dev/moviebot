import requests

from settings import settings

BASE_URL = 'https://kinopoiskapiunofficial.tech/api/v2.1/films/search-by-keyword'
TOP_URL = 'https://kinopoiskapiunofficial.tech/api/v2.2/films/top'
GENRES_URL = 'https://kinopoiskapiunofficial.tech/api/v2.2/films/filters'
FILMS_URL = 'https://kinopoiskapiunofficial.tech/api/v2.2/films'

def search_movies(keyword: str) -> dict | None:
    """
        Ищет фильмы по заданному ключевому слову через HTTP GET-запрос к API Кинопоиска.
        Возвращает результаты поиска в формате JSON при успешном запросе или None при ошибке.

        :param keyword: Ключевое слово для поиска фильмов.
        :type keyword: str
        :return: Словарь с результатами поиска или None, если запрос не удался.
        :rtype: dict | None
    """

    headers = {
        'X-API-KEY': settings.api_key,
        'Content-Type': 'application/json'
    }

    params = {'keyword': keyword, 'page': 1}

    response = requests.get(BASE_URL, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()

    else:
        return None





def get_top_movies(page: int = 1) -> dict | None:

    headers = {
        'X-API-KEY': settings.api_key,
        'Content-Type': 'application/json'
    }

    params = {'page': page, 'type': 'TOP_250_BEST_FILMS'}

    response = requests.get(TOP_URL, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()

    else:
        return None



def get_genres() -> dict | None:

    headers = {
        'X-API-KEY': settings.api_key,
        'Content-Type': 'application/json'
    }

    response = requests.get(GENRES_URL, headers=headers)

    if response.status_code == 200:
        return response.json()

    else:
        return None


def search_by_genre(genre_id: int, page: int = 1) -> dict | None:
    headers = {
        'X-API-KEY': settings.api_key,
        'Content-Type': 'application/json'
    }
    params = {
        'genres': genre_id,
        'order': 'RATING',
        'page': page
    }
    response = requests.get(FILMS_URL, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    return None

