import pywt
import cv2
import reedsolo
import matplotlib.pyplot as plt

#output_image.png
#"output_image_copy3.png"
#"output_image_copy1.png"
#"output_image_copy.png"
image = cv2.imread("output_image1.png") 

image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)# to RGB

# Відображення зображення
plt.imshow(image)
plt.axis("off")  # Прибрати координатні осі
plt.title("Зображення output_image_copy.png")
plt.show()

# Розділяємо канали
R, G, B = cv2.split(image)

# Виконуємо DWT для кожного каналу
coeffs_r = pywt.dwt2(R, 'haar')
coeffs_g = pywt.dwt2(G, 'haar')
coeffs_b = pywt.dwt2(B, 'haar')

LL_r, (LH_r, HL_r, HH_r) = coeffs_r
LL_g, (LH_g, HL_g, HH_g) = coeffs_g
LL_b, (LH_b, HL_b, HH_b) = coeffs_b

# Функція для вилучення повідомлення з коефіцієнтів DWT
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
        rs = reedsolo.RSCodec()  # Використовуємо той самий рівень надмірності (5 перевірочних бітів)
        corrected_message = rs.decode(bytearray(decoded_message, 'utf-8'))
        # Повертаємо лише оригінальне повідомлення (без перевірочних бітів)
        return corrected_message.decode()
    except reedsolo.ReedSolomonError:
        print("\033[91mПомилка декодування Reed-Solomon! Дані пошкоджені\033[0m")
        return ""

# Вилучення повідомлення
decoded_message = decode_message_with_rs(LL_r)
decoded_message += decode_message_with_rs(LL_g)
decoded_message += decode_message_with_rs(LL_b)
    
print("Декодоване повідомлення:", decoded_message)