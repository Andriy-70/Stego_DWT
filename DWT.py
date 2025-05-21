import pywt
import numpy as np
import reedsolo
from PIL import Image

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
        Виконує кодування повідомлення в зображення за допомогою DWT і Reed-Solomon.
        :param image_path: Шлях до зображення для вбудовування повідомлення.
        :param message: Повідомлення для вбудовування.
        """
        image = Image.open(image_path)
        if image is None:
            raise FileNotFoundError("Зображення не знайдено!")

        arr = np.array(image)

        # DWT тільки для червоного каналу
        coeffs_r = pywt.dwt2(arr[:,:,0], 'haar')
        LL_r, (LH_r, HL_r, HH_r) = coeffs_r

        # Повідомлення для вбудовування
        binary_message = ''.join(format(ord(i), '08b') for i in message)
        binary_message += '00000000'  # Додаємо стоп-байт

        # Кодування Ріда-Соломона
        rs = reedsolo.RSCodec(20)  # Збільшено кількість перевірочних символів
        
        try:
            # Перетворення повідомлення в байти
            byte_data = bytes(int(binary_message[i:i+8], 2) for i in range(0, len(binary_message), 8))
            
            # Кодування Ріда-Соломона
            encoded_data = rs.encode(byte_data)
            encoded_binary = ''.join(format(byte, '08b') for byte in encoded_data)
        except reedsolo.ReedSolomonError as e:
            print(f"Помилка кодування Reed-Solomon: {e}")
            encoded_binary = binary_message  # Якщо помилка, використовуємо оригінал

        # Вбудовування закодованого повідомлення ТІЛЬКИ в HH_r
        DWT.embed_bits_with_rs(HH_r, encoded_binary)

        # Зворотнє DWT (IDWT) тільки для червоного каналу
        R_rec = pywt.idwt2((LL_r, (LH_r, HL_r, HH_r)), 'haar')
        
        # Зберігаємо інші канали без змін
        G_rec = arr[:,:,1]
        B_rec = arr[:,:,2]

        # Об'єднання каналів
        reconstructed = np.stack([
            np.clip(R_rec, 0, 255),
            G_rec,
            B_rec
        ], axis=-1).astype(np.uint8)

        # Збереження у форматі PNG
        #Image.fromarray(reconstructed).save(image_path, compress_level=0)

        Image.fromarray(reconstructed).save(image_path.replace('.jpg', '.png'), format='PNG', compress_level=0)

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
