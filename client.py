import asyncio
import threading
import tkinter as tk
from tkinter import scrolledtext, ttk, filedialog
from datetime import datetime
from PIL import Image, ImageTk
import base64
import io

# Глобальные переменные для хранения объектов reader и writer
reader = None
writer = None

async def receive_messages(reader, text_widget):
    while True:
        data = await reader.read(100000)  # Увеличиваем размер буфера для приема больших сообщений
        message = data.decode()
        if message.startswith("IMAGE:"):
            # Если сообщение начинается с "IMAGE:", это изображение
            image_data = message[6:]
            display_image(text_widget, image_data)
            print("Получено изображение")
        else:
            # Если это текст
            display_message(text_widget, message)
            print(f"Получено сообщение: {message}")

async def send_messages(writer, message):
    while True:
        message = await get_user_input("")
        writer.write(message.encode())
        await writer.drain()

async def get_user_input(prompt):
    loop = asyncio.get_event_loop()
    user_input = await loop.run_in_executor(None, input, prompt)
    return user_input

def send_message():
    global writer

    message = entry_widget.get()
    entry_widget.delete(0, tk.END)
    writer.write(message.encode())

def send_image():
    global writer

    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")])
    if file_path:
        with open(file_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
            writer.write(f"IMAGE:{encoded_string}".encode())

def display_message(text_widget, message):
    current_time = datetime.now().strftime("%H:%M")
    message_with_time = f"[{current_time}] {message}\n"
    text_widget.insert(tk.END, message_with_time)
    text_widget.see(tk.END)

def display_image(text_widget, image_data):
    image = Image.open(io.BytesIO(base64.b64decode(image_data)))
    image.thumbnail((200, 200))  # Уменьшаем изображение для отображения в чате
    photo = ImageTk.PhotoImage(image)
    text_widget.image_create(tk.END, image=photo)
    text_widget.insert(tk.END, "\n")
    text_widget.see(tk.END)
    text_widget.image = photo  # Сохраняем ссылку на изображение, чтобы оно не было удалено сборщиком мусора

async def connect_to_server(text_widget):
    global reader
    global writer

    reader, writer = await asyncio.open_connection('127.0.0.1', 8888)
    print("Подключено к серверу")

    receive_task = asyncio.create_task(receive_messages(reader, text_widget))

    name = "*"
    message = await get_user_input("Введите ваше имя: ")
    name = message
    writer.write(message.encode())
    await writer.drain()

    room = await get_user_input("Введите название комнаты: ")
    writer.write(room.encode())
    await writer.drain()

    send_task = asyncio.create_task(send_messages(writer, name))

    await receive_task
    await send_task

def run_client_loop(text_widget):
    asyncio.run(connect_to_server(text_widget))

if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("800x600")
    root.title("Client")
    root.configure(bg="#f0f0f0")

    style = ttk.Style()
    style.configure("TFrame", background="#f0f0f0")
    style.configure("TLabel", background="#f0f0f0", font=("Arial", 12))
    style.configure("TButton", font=("Arial", 12))

    main_frame = ttk.Frame(root, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)

    chat_frame = ttk.LabelFrame(main_frame, text="Чат", padding="10")
    chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    text_widget = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, height=20, width=80, font=("Arial", 12), bg="#ffffff")
    text_widget.pack(fill=tk.BOTH, expand=True)

    input_frame = ttk.Frame(main_frame, padding="10")
    input_frame.pack(fill=tk.X, padx=10, pady=10)

    entry_widget = ttk.Entry(input_frame, width=60, font=("Arial", 12))
    entry_widget.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

    send_button = ttk.Button(input_frame, text="Отправить", command=send_message)
    send_button.pack(side=tk.LEFT)

    send_image_button = ttk.Button(input_frame, text="Отправить изображение", command=send_image)
    send_image_button.pack(side=tk.LEFT, padx=(10, 0))

    asyncio_thread = threading.Thread(target=run_client_loop, args=(text_widget,))
    asyncio_thread.start()

    root.mainloop()