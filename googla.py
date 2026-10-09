import gc
import ubinascii
import urequests

class GooglA:
    """
    Lightweight Gemini client for microcontrollers Pi Pico W.

    Provides AI for devices.
    """

    def __init__(self, api_key, api_url):
        """
        Initialize the Gemini client.

        :param api_key:
            Google AI Studio API key.

        :param api_url:
            Gemini model URL.
        """

        self.api_key = api_key
        self.api_url = api_url


    def ask_gemini(self, prompt) -> str:
        """
        Ask Gemini AI model about something.

        :param prompt:
            Prompt for Gemini.

        :return:
            Gemini response.
        """

        gc.collect()

        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
            "Connection": "close"
        }

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 300
            }
        }

        return self._send_to_gemini(payload, headers)


    def recognize_photo(self, photo_file, prompt=None) -> str:
        """
        Ask Gemini AI model to recognize what on photo.

        :param photo_file:
            File to be sent to Gemini.
        
        :param prompt:
            Prompt for Gemini.
            If None or not set uses default prompt

        :return:
            Gemini response.
        """

        if prompt is None:
            prompt = ("Is there a person, animal, or something else in this image?"
                      "Reply with just the category name.")

        gc.collect()

        b64_string = None
        try:
            print(f"[GOOGLA] reading and encoding {photo_file} ...")
            with open(photo_file, "rb") as image_file:
                raw_data = image_file.read()
                b64_bytes = ubinascii.b2a_base64(raw_data)
                b64_string = b64_bytes.decode("utf-8").strip()
        except Exception as eef:
            print(f"[GOOGLA] file exception: {repr(eef)}")
            return "[GEMINI] file exception"

        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
            "Connection": "close"
        }

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {  
                                "mime_type": "image/jpeg",
                                "data": b64_string
                            }
                        }
                    ]
                }
            ]
        }

        return self._send_to_gemini(payload, headers)


    def _send_to_gemini(self, payload: dict, headers: dict) -> str:
        """
        Send a POST request containing text or multimodal data to the Gemini API.

        :param payload:
            A dictionary containing the structured Gemini prompt payload 
            (e.g., 'contents', 'parts', and 'inline_data').
        
        :param headers:
            A dictionary containing necessary HTTP request headers 
            (e.g., 'Content-Type': 'application/json').

        :return:
            The extracted text response string from the model if successful; 
            otherwise, an error message string prefixed with '[GEMINI]'.
        """

        response = None

        try:
            print("[GOOGLA] sending prompt to Gemini...")

            response = urequests.post(
                        self.api_url,
                        json=payload,
                        headers=headers)
        
            if response.status_code == 200:
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        
            print(
                f"[GOOGLA] error: response status {response.status_code}"
                f"\n[GOOGLA] error details: {response.text}"
            )
            return f"[GEMINI] error: {response.status_code}"
        
        except Exception as e:
            print(f"[GOOGLA] exception: {repr(e)}")
            return "[GEMINI] exception"

        finally:
            if response is not None:
                response.close()
