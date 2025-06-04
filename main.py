import GUI  # Імпортуємо клас Window з модуля GUI
import ttkbootstrap as ttk

def main():
    # Викликаємо метод StartWindow для запуску інтерфейсу
    #GUI.Window.StartWindow()


    # Створення вікна
    root = ttk.Window(themename="darkly")
    window = GUI.Window(root)
    root.mainloop()


if __name__ == "__main__":
    main()