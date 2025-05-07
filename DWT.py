import pywt  # Бібліотека для виконання дискретного вейвлет-перетворення (DWT)
import cv2  # Бібліотека для роботи з зображеннями
import numpy as np  # Бібліотека для роботи з числовими масивами
import reedsolo  # Бібліотека для кодування та декодування Reed-Solomon

class DWT:
    @staticmethod
    def embed_bits_with_rs(matrix_coeff, binary_message):
        """
        Вбудовує двійкове повідомлення у коефіцієнти DWT.
        
        :param matrix_coeff: Матриця коефіцієнтів DWT (наприклад, HH_r).
        :param binary_message: Двійкове повідомлення, яке потрібно вбудувати.
        """
        rows, cols = matrix_coeff.shape
        for index in range(0, len(binary_message), 2):
            if index + 2 > len(binary_message):
                break  # Якщо залишилося менше 2 бітів, виходимо

            row = (index // 2) // cols  # Визначаємо рядок
            col = (index // 2) % cols   # Визначаємо стовпець

            if row >= rows or col >= cols:
                raise ValueError(f"Індекс ({row}, {col}) виходить за межі матриці.")

            bit_pair = int(binary_message[index:index+2], 2)  # Конвертуємо 2 біти у число

            whole_part = int(matrix_coeff[row][col])  # Беремо цілу частину
            decimal_part = matrix_coeff[row][col] - whole_part   # Виділяємо дробову частину

            # Видаляємо 4-й та 5-й біти та додаємо нові
            new_value = (whole_part & ~0b11000) | (bit_pair << 3)  # Змінюємо 4-5 біти
            matrix_coeff[row][col] = new_value + decimal_part
        
            # Перевірка чи записи відбулись правильно
            stored_bits = (int(matrix_coeff[row][col]) & 0b11000) >> 3
            if stored_bits != bit_pair:
                print(f"Помилка запису в ({row}, {col})! Очікувалося {bit_pair}, отримано {stored_bits}")

                # Корекція
                matrix_coeff[row][col] = int(matrix_coeff[row][col]) & ~0b11000
                matrix_coeff[row][col] = int(matrix_coeff[row][col]) | (bit_pair << 3)

                # Перевірка після корекції
                stored_bits_after_correction = (int(matrix_coeff[row][col]) & 0b11000) >> 3
                if stored_bits_after_correction == bit_pair:
                    print(f"Корекція успішно застосована в ({row}, {col})!")
                else:
                    print(f"Корекція не вдалася в ({row}, {col})! Очікувалося {bit_pair}, отримано {stored_bits_after_correction}")

    @staticmethod
    def decode_message_with_rs(matrix_coeff):
        """
        Вилучає повідомлення з коефіцієнтів DWT.
        
        :param matrix_coeff: Матриця коефіцієнтів DWT (наприклад, HH_r).
        :return: Декодоване повідомлення.
        """
        rows, cols = matrix_coeff.shape
        binary_result = ""
        decoded_message = ""

        for row in range(rows):
            for col in range(cols):
                whole_part = int(matrix_coeff[row][col])  # Беремо цілу частину
                # Витягуємо 4-й та 5-й біти (маска 0b11000 і зсув на 3 біти вправо)
                two_bits = (whole_part & 0b11000) >> 3
                binary_result += format(two_bits, '02b')  # Додаємо біти як рядок

                while len(binary_result) >= 8:
                    byte = binary_result[:8]  # Беремо перші 8 бітів
                    binary_result = binary_result[8:]  # Обрізаємо ці 8 бітів

                    if byte == '00000000':  
                        return decoded_message  # Зупиняємо функцію при стоп-байті

                    decimal_value = int(byte, 2)  # Конвертуємо біти в десяткове число
                    decoded_message += chr(decimal_value)  # Додаємо символ до результату

        # ---- Декодування Reed-Solomon ----
        try:
            rs = reedsolo.RSCodec(20)  # Використовуємо той самий рівень надмірності (5 перевірочних бітів)
            corrected_message = rs.decode(bytearray(decoded_message, 'utf-8'))
            # Повертаємо лише оригінальне повідомлення (без перевірочних бітів)
            return corrected_message.decode()
        except reedsolo.ReedSolomonError:
            print("\033[91mПомилка декодування Reed-Solomon! Дані пошкоджені\033[0m")
            return ""

    @staticmethod
    def encode_message(image_path, message):
        """
        Виконує кодування повідомлення в зображення за допомогою DWT і Reed-Solomon.
        :param image: Зображення для вбудовування повідомлення.
        :param message: Повідомлення для вбудовування.
        """
        image = cv2.imread(image_path)  # Завантажуємо зображення
        if image is None:
            raise FileNotFoundError("Зображення не знайдено!")

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # Перетворення в RGB

        # Розділення каналів
        R, G, B = cv2.split(image)

        # Виконання DWT для кожного каналу
        coeffs_r = pywt.dwt2(R, 'haar')
        coeffs_g = pywt.dwt2(G, 'haar')
        coeffs_b = pywt.dwt2(B, 'haar')

        LL_r, (LH_r, HL_r, HH_r) = coeffs_r
        LL_g, (LH_g, HL_g, HH_g) = coeffs_g
        LL_b, (LH_b, HL_b, HH_b) = coeffs_b

        # Повідомлення для вбудовування
        binary_message = ''.join(format(ord(i), '08b') for i in message)  # Перетворення в двійковий формат
        binary_message += '00000000'  # Додаємо стоп-байт

        # Розділити повідомлення на три частини
        part_size = len(binary_message) // 3
        parts = [
            binary_message[:part_size],
            binary_message[part_size:2*part_size],
            binary_message[2*part_size:]
        ]
        parts[0] += '00000000'
        parts[1] += '00000000'

        # Кодування Ріда-Соломона для кожної частини окремо
        rs = reedsolo.RSCodec(20)  # Використовуємо 20 перевірочних бітів
        encoded_parts = []
        for part in parts:
            # Перетворення частини в байти
            part_bytes = int(part, 2).to_bytes((len(part) + 7) // 8, byteorder='big')
            # Кодування Ріда-Соломона
            encoded_part = rs.encode(part_bytes)
            # Перетворення назад у двійковий рядок
            encoded_binary = ''.join(format(byte, '08b') for byte in encoded_part)
            encoded_parts.append(encoded_binary)

        # Вбудовування закодованих частин у коефіцієнти HH_r, HH_g, HH_b
        DWT.embed_bits_with_rs(LL_r, encoded_parts[0])
        DWT.embed_bits_with_rs(LL_g, encoded_parts[1])
        DWT.embed_bits_with_rs(LL_b, encoded_parts[2])

        # Зворотнє DWT (IDWT)
        R_rec = pywt.idwt2((LL_r, (LH_r, HL_r, HH_r)), 'haar')
        G_rec = pywt.idwt2((LL_g, (LH_g, HL_g, HH_g)), 'haar')
        B_rec = pywt.idwt2((LL_b, (LH_b, HL_b, HH_b)), 'haar')

        # Обмеження значень та перетворення в uint8
        R_rec = np.clip(R_rec, 0, 255).astype(np.uint8)
        G_rec = np.clip(G_rec, 0, 255).astype(np.uint8)
        B_rec = np.clip(B_rec, 0, 255).astype(np.uint8)

        # Об'єднання каналів
        image_rec = cv2.merge((R_rec, G_rec, B_rec))

        # Збереження зображення
        cv2.imwrite(image_path, cv2.cvtColor(image_rec, cv2.COLOR_RGB2BGR)) # поміняти шлях для збереження фотки

    @staticmethod
    def decode_message(image_path):
        """
        Виконує декодування повідомлення з зображення за допомогою DWT і Reed-Solomon.
        
        :param image: Зображення з вбудованим повідомленням.
        :return: Декодоване повідомлення.
        """
        image = cv2.imread(image_path)  # Завантажуємо зображення
        if image is None:
            raise FileNotFoundError("Зображення не знайдено!")
        
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # Перетворення в RGB

        # Розділення каналів
        R, G, B = cv2.split(image)

        # Виконання DWT для кожного каналу
        coeffs_r = pywt.dwt2(R, 'haar')
        coeffs_g = pywt.dwt2(G, 'haar')
        coeffs_b = pywt.dwt2(B, 'haar')

        LL_r, (LH_r, HL_r, HH_r) = coeffs_r
        LL_g, (LH_g, HL_g, HH_g) = coeffs_g
        LL_b, (LH_b, HL_b, HH_b) = coeffs_b

        # Декодування повідомлення
        decoded_message = DWT.decode_message_with_rs(LL_r)
        decoded_message += DWT.decode_message_with_rs(LL_g)
        decoded_message += DWT.decode_message_with_rs(LL_b)

        print("Декодоване повідомлення:", decoded_message)
        return decoded_message
