from pydantic_settings import BaseSettings # Загрузка настроек
from pydantic import SecretStr # Сокрытие токена
from dotenv import load_dotenv # Считывание .env файла

load_dotenv()

class Settings(BaseSettings):
    """
        Управляет настройками конфигурации приложения.

        Класс используется для хранения и управления настройками, такими как ключи API
        и секретные токены. Наследуется от BaseSettings для загрузки настроек
        из переменных окружения или файла .env.

        :ivar bot_token: Токен для аутентификации бота. Секретное значение,
            не должно быть раскрыто.
        :type bot_token: SecretStr
        :ivar api_key: Ключ API для взаимодействия с внешними сервисами.
        :type api_key: str
    """

    bot_token: SecretStr
    api_key: str

    class Config:
        """
            Класс конфигурации для управления настройками файла окружения.

            Определяет расположение и кодировку файла .env, используемого
            для загрузки переменных окружения.

            :ivar env_file: Путь к файлу окружения.
            :type env_file: str
            :ivar env_file_encoding: Кодировка файла окружения.
            :type env_file_encoding: str
        """

        env_file = '.env'
        env_file_encoding = 'utf-8'

settings = Settings()