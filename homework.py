import time  # Отправка сообщений: класс Bot()
from telegram import Bot  # Обработка входящих сообщений.Класс Updater()
import requests  # Импортируем библиотеку для работы с запросами
import os  # Импортируем библиотеку для безопасного хранения токенов
from dotenv import load_dotenv
import logging  # Импортируем библиотеку для безопасного хранения логов
from logging.handlers import RotatingFileHandler
# from pprint import pprint # Печатаем грасиво с коассом pprint
import telegram
load_dotenv()

# Здесь задана глобальная конфигурация для всех логгеров
logging.basicConfig(
    level=logging.DEBUG,
    filename='program.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)

# А тут установлены настройки логгера для текущего файла
logger = logging.getLogger(__name__)
# Устанавливаем уровень, с которого логи будут сохраняться в файл
logger.setLevel(logging.INFO)
# Указываем обработчик логов
handler = RotatingFileHandler('my_logger.log',
                              maxBytes=50000000, backupCount=5
                              )
logger.addHandler(handler)

# блок проверки логов
# logger.debug('123')
# logger.info('Сообщение отправлено')
# logger.warning('Большая нагрузка!')
# logger.error('Бот не смог отправить сообщение')
# logger.critical('Всё упало! Зовите админа!1!111')


# Теперь переменная TOKEN, описанная в файле .env,
# доступна в пространстве переменных окружения
URL = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
PRACTICUM_TOKEN = os.getenv('TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')
RETRY_TIME = 600


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

# bot = Bot(token=TELEGRAM_TOKEN) # создан для пробы send_message


def send_message(bot, message):
    """
    отправляет сообщение.
    в Telegram чат, определяемый переменной.
    окружения TELEGRAM_CHAT_ID. Принимает на вход два параметра:
    экземпляр класса Bot и строку с текстом сообщения.
    """
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except telegram.TelegramError as error:
        logger.error(f'Ошиька при отправке сообщения: {error}')
    else:
        pass


# тест метода send_message
# send_message(bot, 'test send_message')

def get_api_answer(current_timestamp):
    """
    делает запрос к единственному эндпоинту API-сервиса.
    В качестве параметра функция получает временную метку.
    В случае успешного запроса должна вернуть ответ API,
    преобразовав его из формата JSON к типам данных Python.
    """
    timestamp = current_timestamp or int(time.time())
    # Делаем GET-запрос к эндпоинту url с заголовком headers и параметрами par
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    params = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(URL, headers=headers, params=params)
        # Приведем ответ сервера к типам данных Python...
        if homework_statuses.status_code != requests.codes.ok:
            logging.error('Сервер возвращает код, отличный от 200')
            raise
        homework_statuses = homework_statuses.json()
        return homework_statuses
    except requests.RequestException as error:
        logging.error(f'Ошибка отправки запроса. {error}')


# тестирование get_api_answer
# result_get_api_answer = get_api_answer(1646125721)
# send_message(bot, result_get_api_answer)

def check_response(response):
    """
    проверяет ответ API на корректность.
    В качестве параметра функция получает ответ API, приведенный
    к типам данных Python. Если ответ API соответствует ожиданиям,
    то функция должна вернуть список домашних работ (он может быть и пустым),
    доступный в ответе API по ключу 'homeworks'.
    """
    logger.info('Проверка АПИ')
    if not isinstance(response, dict):
        raise TypeError('Нет словаря')
    try:
        list_homeworks = response['homeworks']
        if isinstance(list_homeworks, list):
            return list_homeworks
        # homework = list_homeworks[0]
        raise Exception('Нет списка работ')
    except IndexError:
        raise IndexError('Нет списка работ')


# тестирование check_response
# result_get_api_answer = get_api_answer(1646125721)
# result_check_response = check_response(result_get_api_answer)
# send_message(bot, result_check_response)


def parse_status(homework):
    """
    извлекает из информации.
    этой работы. В качестве параметра функция получает только один.
    элемент из списка домашних работ. В случае успеха, функция возвращает.
    подготовленную для отправки в Telegram строку, содержащую один из.
    вердиктов словаря HOMEWORK_STATUSES.
    """
    try:
        homework_name = homework['homework_name']
    except KeyError as error:
        error_message = f'В словаре нет ключа homework_name {error}'
        logger.error(error_message)
        raise KeyError(error_message)
    try:
        homework_status = homework['status']
    except KeyError as error:
        error_message = f'В словаре нет ключа status {error}'
        logger.error(error_message)
        raise KeyError(error_message)
    homework_statuses = HOMEWORK_STATUSES[homework_status]
    if homework_statuses is None:
        error_message = 'Нет сообщения о статусе'
        logger.error(error_message)
        raise logging.exception.StatusException(error_message)
    return f'Изменился статус проверки работы "{homework_name}".{homework_statuses}'


# тестирование parse_status
# result_get_api_answer = get_api_answer(1646125721)
# result_check_response = check_response(result_get_api_answer)
# parse_status_result = parse_status(result_check_response)
# send_message(bot, parse_status_result)


def check_tokens():
    """Проверка переменных окружения."""
    if PRACTICUM_TOKEN == "":
        result = True
    elif TELEGRAM_TOKEN == "":
        result = True
    elif TELEGRAM_CHAT_ID != 0 and type(TELEGRAM_CHAT_ID) == int:
        result = True
    else:
        result = False
        logger.critical('Нет токенов!')
    return result

# тестирование check_tokens
# result_check_tokens = check_tokens()
# print(result_check_tokens)


def main():
    """Основная логика работы бота."""
    check_token = check_tokens()  # проверяем токены
    if check_token is True:
        raise KeyError('Похерелись все токены, надо проверить')
    bot = Bot(token=TELEGRAM_TOKEN)  # создаем экземпляр бота
    # current_timestamp = int(time.time())
    current_timestamp = 1646162259
    last_status = ""  # храним прошлый статус
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)  # получили список дом работ
            message = parse_status(homework[0])
            previous_status = message
            if last_status != previous_status:
                last_status = previous_status
                send_message(bot, message)
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_TIME)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
