import urequests as rq

class TelegaW:
    """
    Lightweight Telegram Bot API client 
    for microcontrollers.

    Provides communication with Telegram. 
    Supports sending text messages only.
    """

    def __init__(
            self,
            telegram_host,
            telegram_bot_id,
            telegram_chat_id):
        """
        Initialize the Telegram client.

        :param telegram_host:
            Telegram Bot API server hostname.

        :param telegram_bot_id:
            Telegram bot API bot identifier used for API requests.

        :param telegram_chat_id:
            Telegram chat or channel ID used as the destination
            for outgoing messages.
        """

        self.telegram_host = telegram_host
        self.telegram_bot_id = telegram_bot_id
        self.telegram_chat_id = telegram_chat_id

    def _url_encode(self, text):
        """
        Encodes text for use in a URL.

        :param text:
            Text to encode.

        :return:
            URL-encoded text.
        """

        return text.replace("%", "%25").replace(" ", "%20").replace(":", "%3A")

    def send_message(self, message) -> bool:
        """
        Send a text message through the Telegram Bot API.

        Creates an HTTP POST request for the Telegram sendMessage 
        endpoint, and sends the message.

        :param message:
            Text message to send to the Telegram chat.

        :return:
            True if the message was successfully transmitted.
            False if the data transmission fails.
        """
        
        text = self._url_encode(message)
        try:
            res = rq.post(
                    f'https://{self.telegram_host}/{self.telegram_bot_id}/sendMessage?chat_id={self.telegram_chat_id}&parse_mode=Markdown&text={text}')
            if res.status_code == 200:
                print(f'[TELEGAW] successfully sent: {message}')
                return True
            else:
                print('[TELEGAW] error: ', [res.status_code])
        except Exception as e:
            print(f'[TELEGAW] problem sending message: ', [e])
            return False

        return False