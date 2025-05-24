import pywt
import numpy as np
import reedsolo
from PIL import Image
import os

class DWT:
    @staticmethod
    def embed_bits_with_rs(matrix_coeff, binary_message):
        """
        Вбудовує двійкове повідомлення у коефіцієнти DWT.
        
        :param matrix_coeff: Матриця коефіцієнтів DWT (HH_r).
        :param binary_message: Двійкове повідомлення, яке потрібно вбудувати.
        """
        flat = matrix_coeff.flatten()
        data_index = 0
        
        for i in range(len(flat)):
            if data_index >= len(binary_message):
                break
                
            # Використовуємо коефіцієнти з дробовою частиною '00000'
            if f"{flat[i]:.6f}".split('.')[1].startswith('00000'):
                val = int(flat[i])
                
                # Вставляємо 3 біти
                if data_index + 3 <= len(binary_message):
                    bits = binary_message[data_index:data_index+3]
                else:
                    bits = binary_message[data_index:].ljust(3, '0')
                
                # Модифікуємо біти 4-6
                val = (val & ~0x38) | (int(bits[0]) << 3) | (int(bits[1]) << 4) | (int(bits[2]) << 5)
                flat[i] = val
                data_index += 3

        matrix_coeff[:] = flat.reshape(matrix_coeff.shape)

    @staticmethod
    def decode_message_with_rs(matrix_coeff):
        """
        Вилучає повідомлення з коефіцієнтів DWT.
        
        :param matrix_coeff: Матриця коефіцієнтів DWT (HH_r).
        :return: Декодоване повідомлення.
        """
        binary_data = []
        flat = matrix_coeff.flatten()
        
        for val in flat:
            if f"{val:.6f}".split('.')[1].startswith('00000'):
                # Витягуємо біти 4-6
                bits = [
                    (int(val) >> 3) & 1,
                    (int(val) >> 4) & 1,
                    (int(val) >> 5) & 1
                ]
                binary_data.extend(map(str, bits))
                
        return ''.join(binary_data)
    
    @staticmethod
    def encode_message(image_path, message):
        """
        Вбудує повідомлення в зображення, перезаписуючи той самий файл `_encoded.png`.
        """
        original_message = message
        max_attempts = 10
        attempt = 0

        # Фінальний шлях для збереження (завжди однаковий)
        base, ext = os.path.splitext(image_path)
        encoded_image_path = f"{base}_encoded.png"

        while attempt < max_attempts:
            attempt += 1
            print(f"Спроба {attempt}...")

            # Відкриваємо оригінал або останню версію
            img = Image.open(image_path if attempt == 1 else encoded_image_path).convert('RGB')
            arr = np.array(img)

            # DWT для червоного каналу
            coeffs_r = pywt.dwt2(arr[:, :, 0], 'haar')
            LL_r, (LH_r, HL_r, HH_r) = coeffs_r

            # Підготовка повідомлення з Reed-Solomon
            binary_message = ''.join(format(ord(i), '08b') for i in message) + '00000000'
            rs = reedsolo.RSCodec(20)
            
            try:
                byte_data = bytes(int(binary_message[i:i+8], 2) for i in range(0, len(binary_message), 8))
                encoded_data = rs.encode(byte_data)
                encoded_binary = ''.join(format(byte, '08b') for byte in encoded_data)
            except reedsolo.ReedSolomonError as e:
                print(f"Помилка Reed-Solomon: {e}")
                encoded_binary = binary_message

            # Вбудовування даних у HH_r
            DWT.embed_bits_with_rs(HH_r, encoded_binary)

            # Зворотнє DWT
            R_rec = pywt.idwt2((LL_r, (LH_r, HL_r, HH_r)), 'haar')
            h, w = arr.shape[:2]
            R_rec = R_rec[:h, :w]

            # Зшиваємо канали
            reconstructed = np.stack([
                np.clip(R_rec, 0, 255),
                arr[:, :, 1],
                arr[:, :, 2]
            ], axis=-1).astype(np.uint8)

            # Зберігаємо в ТОЙ САМИЙ ФАЙЛ (_encoded.png)
            Image.fromarray(reconstructed).save(encoded_image_path, format='PNG', compress_level=0)

            # Перевірка
            decoded_message = DWT.decode_message(encoded_image_path)
            if decoded_message == original_message:
                print(f"✅ Успіх після {attempt} спроб!")
                return encoded_image_path
            
            print(f"⚠ Не співпало: '{decoded_message}' != '{original_message}'")

        print(f"❌ Досягнуто максимум спроб ({max_attempts}).")
        return encoded_image_path

    @staticmethod
    def decode_message(image_path):
        """
        Виконує декодування повідомлення з зображення за допомогою DWT і Reed-Solomon.
        
        :param image_path: Шлях до зображення з вбудованим повідомленням.
        :return: Декодоване повідомлення.
        """
        image = Image.open(image_path)
        if image is None:
            raise FileNotFoundError("Зображення не знайдено!")

        arr = np.array(image)

        # DWT тільки для червоного каналу
        coeffs_r = pywt.dwt2(arr[:,:,0], 'haar')
        LL_r, (LH_r, HL_r, HH_r) = coeffs_r

        # Декодування повідомлення ТІЛЬКИ з HH_r
        binary_data = DWT.decode_message_with_rs(HH_r)
        
        # Декодування Reed-Solomon
        rs = reedsolo.RSCodec(20)  # Така ж кількість перевірочних символів, як при кодуванні
        decoded_message = ""
        
        try:
            # Перетворення двійкових даних у байти
            byte_data = bytes(int(binary_data[i:i+8], 2) for i in range(0, len(binary_data), 8))
            
            # Декодування з корекцією помилок
            decoded_bytes = rs.decode(byte_data)[0]  # Беремо тільки дані
            
            # Перетворення назад у текст
            decoded_message = ''.join(chr(byte) for byte in decoded_bytes if byte != 0)
            
            # Видаляємо все після стоп-байта
            decoded_message = decoded_message.split('\x00')[0]
        except reedsolo.ReedSolomonError as e:
            print(f"Помилка декодування Reed-Solomon: {e}")
            # Спроба витягнути повідомлення без корекції
            decoded_message = ''.join(chr(int(binary_data[i:i+8], 2)) for i in range(0, len(binary_data), 8))
            decoded_message = decoded_message.split('\x00')[0]

        return decoded_message
