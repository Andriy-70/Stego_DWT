import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, Label, Frame, StringVar
from PIL import Image, ImageTk
from tkinter.scrolledtext import ScrolledText
from tkinter import Scale, Frame
from PIL import ImageEnhance

from DWT import DWT

class Window:
    def __init__(self, root):
        self.root = root
        self.selected_image_path = None
        self.selected_image = None
        self.image_label = None
        self.mode = StringVar(value=None)  # Спочатку режим не вибрано
        self.setup_ui()

    def setup_ui(self):
        """ Ініціалізація інтерфейсу """
        self.root.title("DWT Steganography")
        self.root.geometry("1200x600")
        self.root.resizable(False, False)

        # Головний контейнер
        main_frame = Frame(self.root, bg="#2C2F33")
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)

        # Заголовок
        labelmain = ttk.Label(main_frame, text="DWT Steganography", font=("Arial", 26, "bold"), 
                              bootstyle="primary", anchor="center")
        labelmain.pack(pady=15)

        # Ліва панель (кнопки)
        self.left_frame = self.create_left_frame(main_frame)
        # Права панель (для вибору та відображення зображення)
        self.right_frame = self.create_right_frame(main_frame)

        # Вікно основних функцій
        self.create_buttons(self.left_frame)
        self.create_input_field()  # Створюємо текстове поле
        self.create_modify_frame()  # Створюємо фрейм для повзунків (спочатку прихований)
        self.create_image_display(self.right_frame)

    def create_left_frame(self, parent):
        """ Створює ліву панель """
        left_frame = Frame(parent, relief="ridge", borderwidth=2, bg="#3B3F42", bd=5)
        left_frame.pack(side='left', padx=20, pady=20, fill='y', expand=False, ipadx=25, ipady=20)
        return left_frame

    def create_right_frame(self, parent):
        """ Створює праву панель """
        right_frame = Frame(parent, relief="ridge", borderwidth=2, bg="#3B3F42", bd=5)
        right_frame.pack(side='right', padx=20, pady=20, fill='both', expand=True)
        return right_frame

    def create_buttons(self, frame):
        """Створює кнопки для вибору режиму (спочатку неактивні)"""
        button_frame = Frame(frame, bg="#3B3F42")
        button_frame.pack(pady=10, padx=10)

        # Всі кнопки створюються з bootstyle="secondary-outline" (сірий контур)
        self.btn_embed = self.create_button(
            button_frame, 
            "Embed Text", 
            "secondary-outline",  # Не активна
            lambda: self.set_mode("embed")
        )
        self.btn_extract = self.create_button(
            button_frame, 
            "Extract Text", 
            "secondary-outline",  # Не активна
            lambda: self.set_mode("extract")
        )
        self.btn_modify = self.create_button(
            button_frame, 
            "Modify photo", 
            "secondary-outline",  # Не активна
            lambda: self.set_mode("modify")
        )

    def create_button(self, parent, text, bootstyle, command):
        """ Створює кнопку """
        button = ttk.Button(parent, text=text, bootstyle=bootstyle, command=command)
        button.configure(width=18)
        button.pack(side="left", padx=10, pady=10)
        return button

    def create_input_field(self):
        """Створює поле введення тексту та виводу результату"""
        self.input_frame = Frame(self.left_frame, bg="#3B3F42")
        self.input_frame.pack(pady=20, padx=10, fill='both', expand=True)

        # Поле введення (для embed)
        self.input_label = ttk.Label(
            self.input_frame, 
            text="Enter text to embed:", 
            bootstyle="primary"
        )  # Зберігаємо як атрибут, щоб керувати видимістю
        
        self.text_input = ScrolledText(
            self.input_frame, 
            font=("Arial", 12), 
            width=40, 
            height=8, 
            bd=2, 
            relief="groove", 
            wrap="word",
            bg="#23272A", 
            fg="white", 
            insertbackground="white"
        )
        
        # Поле виводу (для extract)
        self.output_label = ttk.Label(
            self.input_frame, 
            text="Extracted text:", 
            bootstyle="primary"
        )
        
        self.output_text = ScrolledText(
            self.input_frame, 
            font=("Arial", 12), 
            width=40, 
            height=8,
            bd=2, 
            relief="groove", 
            wrap="word",
            bg="#23272A", 
            fg="white", 
            state="disabled"
        )
        
        # Кнопка виконання
        self.btn_action = ttk.Button(
            self.input_frame, 
            text="Execute", 
            bootstyle="danger-outline", 
            command=lambda: self.execute_action(self.text_input)
        )
        self.btn_action.pack(pady=10)
        self.btn_action.configure(width=20)
        
        # Спочатку нічого не показуємо (режим буде встановлено в set_mode)
        self.hide_all_input_fields()

    def show_input_field(self):
        """ Показує поле введення і ховає поле виводу """
        self.output_label.pack_forget()
        self.output_text.pack_forget()
        self.text_input.pack(padx=10, pady=5, fill='both', expand=True)

    def show_output_field(self, text):
        """ Показує поле виводу з текстом і ховає поле введення """
        self.text_input.pack_forget()
        
        self.output_label.pack(padx=10, pady=(0, 5), anchor="w")
        self.output_text.config(state="normal")
        self.output_text.delete(1.0, "end")
        self.output_text.insert("end", text)
        self.output_text.config(state="disabled")
        self.output_text.pack(padx=10, pady=5, fill='both', expand=True)

    def create_modify_frame(self):
        """ Створює фрейм для налаштувань зображення (спочатку прихований) """
        self.modify_frame = Frame(self.left_frame, bg="#3B3F42")
        
        # Додаємо повзунки для яскравості, контрасту та насиченості
        brightness_label = ttk.Label(self.modify_frame, text="Brightness", bootstyle="primary")
        brightness_label.pack(padx=10, pady=5)

        self.brightness_slider = ttk.Scale(self.modify_frame, from_=0, to=2, orient="horizontal", bootstyle="info", length=200)
        self.brightness_slider.set(1)
        self.brightness_slider.pack(padx=10, pady=10)

        contrast_label = ttk.Label(self.modify_frame, text="Contrast", bootstyle="primary")
        contrast_label.pack(padx=10, pady=5)

        self.contrast_slider = ttk.Scale(self.modify_frame, from_=0, to=2, orient="horizontal", bootstyle="info", length=200)
        self.contrast_slider.set(1)
        self.contrast_slider.pack(padx=10, pady=10)

        saturation_label = ttk.Label(self.modify_frame, text="Saturation", bootstyle="primary")
        saturation_label.pack(padx=10, pady=5)

        self.saturation_slider = ttk.Scale(self.modify_frame, from_=0, to=2, orient="horizontal", bootstyle="info", length=200)
        self.saturation_slider.set(1)
        self.saturation_slider.pack(padx=10, pady=10)

        # Кнопки Apply і Save
        button_frame = Frame(self.modify_frame, bg="#3B3F42")
        button_frame.pack(pady=10)
        
        btn_apply = ttk.Button(button_frame, text="Apply", bootstyle="danger-outline", 
                            command=self.apply_image_changes)
        btn_apply.pack(side="left", padx=5)
        
        btn_save = ttk.Button(button_frame, text="Save Image", bootstyle="success-outline",
                            command=self.save_image)
        btn_save.pack(side="left", padx=5)

    def create_image_display(self, frame):
        """ Створює область для відображення зображення """
        btn_select_image = ttk.Button(frame, text="Choose Photo", bootstyle="primary-outline", 
                                      command=lambda: self.select_image())
        btn_select_image.pack(pady=15)

        self.image_label = Label(frame, bg="#3B3F42", borderwidth=0, highlightthickness=0)
        self.image_label.pack(pady=10, fill='both', expand=True)

    def hide_all_input_fields(self):
        """Приховує всі поля введення/виводу"""
        self.input_label.pack_forget()
        self.text_input.pack_forget()
        self.output_label.pack_forget()
        self.output_text.pack_forget()

    def show_embed_mode(self):
        """Показує поля для вбудовування тексту"""
        self.hide_all_input_fields()
        self.input_label.pack(padx=10, pady=(0, 5), anchor="w")
        self.text_input.pack(padx=10, pady=5, fill='both', expand=True)

    def show_extract_mode(self):
        """Показує поля для витягування тексту"""
        self.hide_all_input_fields()
        self.output_label.pack(padx=10, pady=(0, 5), anchor="w")
        self.output_text.pack(padx=10, pady=5, fill='both', expand=True)

    def set_mode(self, mode):
        """Змінює режим (якщо mode=None - нічого не робимо)"""
        if mode is None:
            return  # Не змінюємо стан кнопок на початку

        self.mode.set(mode)

        # Оновлюємо стилі кнопок (лише обрана стає зеленою)
        self.set_button_style(self.btn_embed, mode == "embed", "success")
        self.set_button_style(self.btn_extract, mode == "extract", "success")
        self.set_button_style(self.btn_modify, mode == "modify", "success")

        # Перемикаємо між текстовим полем та повзунками
        if mode == "modify":
            self.input_frame.pack_forget()
            self.modify_frame.pack(pady=20, padx=10, fill='both', expand=True)
        else:
            self.modify_frame.pack_forget()
            self.input_frame.pack(pady=20, padx=10, fill='both', expand=True)
            
            if mode == "embed":
                self.show_embed_mode()
            elif mode == "extract":
                self.show_extract_mode()

    def set_button_style(self, button, is_active, active_style):
        """ Встановлює стиль кнопки залежно від активності """
        if is_active:
            button.config(bootstyle=active_style)  # Зелена (активна)
        else:
            button.config(bootstyle="secondary-outline")  # Сіра (неактивна)

    def select_image(self):
        """ Вибір зображення через діалогове вікно """
        file_path = filedialog.askopenfilename(title="Chosen photo", 
                                               filetypes=[("Image Files", "*.jpg;*.jpeg;*.png;*.bmp")])
        if file_path:
            self.selected_image_path = file_path
            print(f"Зображення вибрано: {self.selected_image_path}")

            self.selected_image = Image.open(self.selected_image_path)
            self.display_image()

    def display_image(self):
        """ Відображає зображення у вікні """
        if self.selected_image:
            img = self.selected_image.copy()
            img.thumbnail((300, 300))  # Зміна розміру зображення
            img_tk = ImageTk.PhotoImage(img)
            self.image_label.config(image=img_tk)
            self.image_label.image = img_tk  # Зберігаємо посилання, щоб не видалилось

    def execute_action(self, text_widget):
        """ Виконує дію залежно від обраного режиму """
        mode = self.mode.get()
        text = text_widget.get("1.0", "end-1c")  # Отримуємо введений текст
        image_path = self.selected_image_path  # Шлях до вибраного зображення

        if not image_path:
            print("Помилка: Ви не вибрали зображення!")
            return

        if mode == "embed":
            self.embed_text(image_path, text)
        elif mode == "extract":
            self.extract_text(image_path)
        elif mode == "modify":
            print("Modify functionality is handled by sliders")
            
    def apply_image_changes(self):
        """ Застосовує зміни на зображенні на основі значень повзунків """
        if self.selected_image:
            # Застосовуємо яскравість, контраст і насиченість
            enhancer_brightness = ImageEnhance.Brightness(self.selected_image)
            enhanced_image = enhancer_brightness.enhance(self.brightness_slider.get())

            enhancer_contrast = ImageEnhance.Contrast(enhanced_image)
            enhanced_image = enhancer_contrast.enhance(self.contrast_slider.get())

            enhancer_saturation = ImageEnhance.Color(enhanced_image)
            enhanced_image = enhancer_saturation.enhance(self.saturation_slider.get())

            # Оновлюємо зображення
            self.selected_image = enhanced_image
            self.display_image()
            
            return enhanced_image  # Повертаємо модифіковане зображенняОновлюємо відображення

    def save_image(self):
        """ Зберігає модифіковане зображення """
        if not self.selected_image:
            print("Помилка: Немає зображення для збереження!")
            return
        
        # Вибір місця для збереження
        file_path = filedialog.asksaveasfilename(
            title="Save Image As",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg;*.jpeg"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                # Зберігаємо зображення у вибраному форматі
                self.selected_image.save(file_path)
                print(f"Зображення збережено у: {file_path}")
                
                # Оновлюємо шлях до поточного зображення
                self.selected_image_path = file_path
            except Exception as e:
                print(f"Помилка при збереженні: {e}")

    def embed_text(self, image_path, text):
        """ Вставка тексту в зображення """
        if not text:
            self.show_message("Error", "Please enter text to embed")
            return
            
        try:
            DWT.encode_message(image_path, text)
            self.show_message("Success", "Text embedded successfully!")
        except Exception as e:
            self.show_message("Error", f"Failed to embed text: {str(e)}")

    def extract_text(self, image_path):
        """ Витягування тексту з зображення """
        try:
            decoded_message = DWT.decode_message(image_path)
            if decoded_message:
                self.show_output_field(decoded_message)
            else:
                self.show_message("Info", "No hidden message found")
        except Exception as e:
            self.show_message("Error", f"Failed to extract text: {str(e)}")

    def show_message(self, title, message):
        """ Показує повідомлення у вікні """
        msg = ttk.dialogs.Messagebox()
        msg.show_info(message, title=title)
