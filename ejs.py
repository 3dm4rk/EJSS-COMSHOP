import socket
import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import threading
import simpleaudio as sa
import random
import time
import os
import requests

# Receiver configuration
HOST = "0.0.0.0"  # Listen on all network interfaces
PORT = 12345       # Port to listen on

class CheatWarningPopup:
    def __init__(self, parent):
        self.popup = tk.Toplevel(parent)
        self.popup.attributes('-fullscreen', True)
        self.popup.attributes('-topmost', True)
        
        # Disable window controls
        self.popup.overrideredirect(True)  # Removes title bar and window controls
        
        # Warning message
        warning_frame = tk.Frame(self.popup, bg='red')
        warning_frame.pack(expand=True, fill='both')
        
        tk.Label(
            warning_frame, 
            text="WARNING: PALIHOG HINAYA INYO TINGOG!!!", 
            font=('Arial', 36, 'bold'), 
            fg='white', 
            bg='red'
        ).pack(expand=True)
        
        tk.Label(
            warning_frame, 
            text="CCTV IS MONITORING YOUR ACTIVITY!.\n\n"
                 "This behavior has been logged and reported.", 
            font=('Arial', 24), 
            fg='white', 
            bg='red'
        ).pack(expand=True)
        
        # Close button (only works after delay)
        self.close_button = tk.Button(
            warning_frame, 
            text="I UNDERSTAND (10)", 
            font=('Arial', 18), 
            state=tk.DISABLED,
            command=self.popup.destroy
        )
        self.close_button.pack(pady=50)
        
        # Start countdown
        self.countdown(10)
    
    def countdown(self, remaining):
        if remaining > 0:
            self.close_button.config(text=f"I UNDERSTAND ({remaining})")
            self.popup.after(1000, self.countdown, remaining-1)
        else:
            self.close_button.config(state=tk.NORMAL, text="I UNDERSTAND")

class ReceiverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EJS Comshop v1.2")
        self.root.geometry("600x650")  # Increased height to accommodate new button
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        self.root.resizable(False, False)

        # Main frame
        self.main_frame = tk.Frame(root, bg="#f0f0f0")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Welcome label
        self.welcome_label = tk.Label(
            self.main_frame,
            text="Welcome to EJS Internet Cafe",
            font=("Arial", 20, "bold"),
            fg="#333333",
            bg="#f0f0f0"
        )
        self.welcome_label.pack(pady=(20, 10))

        # Rate label
        self.rate_label = tk.Label(
            self.main_frame,
            text="Rate: 5 pesos = 25 mins",
            font=("Arial", 16),
            fg="#555555",
            bg="#f0f0f0"
        )
        self.rate_label.pack(pady=(0, 20))

        # Attempts label
        self.attempts_label = tk.Label(
            self.main_frame,
            text="Attempts available: 1",
            font=("Arial", 16),
            fg="#555555",
            bg="#f0f0f0"
        )
        self.attempts_label.pack(pady=(0, 10))

        # Cooldown label
        self.cooldown_label = tk.Label(
            self.main_frame,
            text="Come back in: 25:00",
            font=("Arial", 14),
            fg="#777777",
            bg="#f0f0f0"
        )
        self.cooldown_label.pack(pady=(0, 10))

        # Draw frame
        self.draw_frame = tk.Frame(self.main_frame, bg="#f0f0f0")
        self.draw_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))

        # Hall of Fame button
        self.hall_of_fame_button = tk.Button(
            self.draw_frame,
            text="Hall of Fame",
            font=("Arial", 14),
            bg="#9C27B0",
            fg="white",
            width=15,
            height=1,
            relief="flat",
            command=self.show_hall_of_fame
        )
        self.hall_of_fame_button.pack(pady=(0, 10))

        # Draw button
        self.draw_button = tk.Button(
            self.draw_frame,
            text="Draw",
            font=("Arial", 24, "bold"),
            bg="#4CAF50",
            fg="white",
            width=10,
            height=3,
            relief="flat",
            command=self.on_draw_click
        )
        self.draw_button.pack(pady=10)

        # Prizes button
        self.prizes_button = tk.Button(
            self.draw_frame,
            text="Prizes",
            font=("Arial", 14),
            bg="#FF9800",
            fg="white",
            width=15,
            height=1,
            relief="flat",
            command=self.show_prizes_popup
        )
        self.prizes_button.pack(pady=(0, 20))

        # Result label
        self.result_label = tk.Label(
            self.draw_frame,
            text="",
            font=("Arial", 18),
            fg="black",
            bg="#f0f0f0"
        )
        self.result_label.pack(pady=(10, 20))

        # History button
        self.history_button = tk.Button(
            self.draw_frame,
            text="Draw History",
            font=("Arial", 14),
            bg="#2196F3",
            fg="white",
            width=15,
            height=1,
            relief="flat",
            command=self.show_draw_history
        )
        self.history_button.pack(pady=(0, 10))

        

        # Log frame
        self.log_frame = tk.Frame(root, bg="#ffffff")
        self.log_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=(0, 10))

        # Log text
        self.log_text = scrolledtext.ScrolledText(self.log_frame, wrap=tk.WORD, state='disabled', height=10)
        self.log_text.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        # Initialize variables
        self.draw_attempts = 1
        self.last_draw_time = time.monotonic()
        self.draw_history = []
        self.update_attempts()

        # Start receiver thread
        self.receiver_thread = threading.Thread(target=self.start_receiver, daemon=True)
        self.receiver_thread.start()

    

    def on_draw_click(self):
        """Handle the draw button click event."""
        if self.draw_attempts > 0:
            self.draw_attempts -= 1
            self.attempts_label.config(text=f"Attempts available: {self.draw_attempts}")

            result = random.choices(
                ["Better luck next time", "It's your lucky day, you won!"],
                weights=[99, 0.2]
            )[0]

            if result == "It's your lucky day, you won!":
                prizes = ["5 pesos coin", "20 pesos coin", "50 pesos", "skin bundle"]
                prize_chances = [99, 0.2, 0.1, 0]
                prize = random.choices(prizes, weights=prize_chances)[0]
                result_message = f"{result} {prize}"
                self.result_label.config(text=result_message, fg="green", font=("Arial", 18, "bold"))
                self.play_sound("winner.wav")
            else:
                result_message = result
                self.result_label.config(text=result, fg="black", font=("Arial", 18))

            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            self.draw_history.append((timestamp, result_message))
            self.attempts_label.config(text=f"Attempts available: {self.draw_attempts}")
        else:
            self.result_label.config(text="No attempts available", fg="red", font=("Arial", 18))

    def show_hall_of_fame(self):
        """Display the Hall of Fame from Pastebin."""
        try:
            response = requests.get("https://pastebin.com/raw/xTnpAE4n")
            if response.status_code == 200:
                content = response.text
            else:
                content = "Failed to load Hall of Fame data. Please try again later."
        except Exception as e:
            content = f"Error fetching Hall of Fame: {str(e)}"

        hall_of_fame_popup = tk.Toplevel(self.root)
        hall_of_fame_popup.title("Hall of Fame")
        hall_of_fame_popup.geometry("604x552")
        hall_of_fame_popup.configure(bg="#f0f0f0")

        title_label = tk.Label(
            hall_of_fame_popup,
            text="Champion",
            font=("Arial", 18, "bold"),
            fg="#333333",
            bg="#f0f0f0"
        )
        title_label.pack(pady=(20, 10))

        content_text = scrolledtext.ScrolledText(
            hall_of_fame_popup,
            wrap=tk.WORD,
            state='normal',
            height=20,
            font=("Arial", 12)
        )
        content_text.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)
        content_text.insert(tk.END, content)
        content_text.config(state='disabled')

        ok_button = tk.Button(
            hall_of_fame_popup,
            text="OK",
            font=("Arial", 12),
            bg="#4CAF50",
            fg="white",
            width=10,
            command=hall_of_fame_popup.destroy
        )
        ok_button.pack(pady=(10, 20))

        hall_of_fame_popup.update_idletasks()
        width = hall_of_fame_popup.winfo_width()
        height = hall_of_fame_popup.winfo_height()
        x = (hall_of_fame_popup.winfo_screenwidth() // 2) - (width // 2)
        y = (hall_of_fame_popup.winfo_screenheight() // 2) - (height // 2)
        hall_of_fame_popup.geometry(f"+{x}+{y}")

    def update_attempts(self):
        """Update the number of draw attempts every 25 minutes and the cooldown timer."""
        current_time = time.monotonic()
        elapsed_time = current_time - self.last_draw_time

        if elapsed_time >= 1500:
            self.draw_attempts += 1
            self.last_draw_time = current_time
            self.attempts_label.config(text=f"Attempts available: {self.draw_attempts}")

        remaining_time = max(0, 1500 - elapsed_time)
        minutes = int(remaining_time // 60)
        seconds = int(remaining_time % 60)
        self.cooldown_label.config(text=f"Come back in: {minutes:02}:{seconds:02}")

        self.root.after(1000, self.update_attempts)

    def show_prizes_popup(self):
        """Display a popup with the prizes and their chances."""
        prizes_popup = tk.Toplevel(self.root)
        prizes_popup.title("Prizes")
        prizes_popup.geometry("400x390")
        prizes_popup.configure(bg="#f0f0f0")

        title_label = tk.Label(
            prizes_popup,
            text="Prizes and Chances",
            font=("Arial", 18, "bold"),
            fg="#333333",
            bg="#f0f0f0"
        )
        title_label.pack(pady=(20, 10))

        prizes_frame = tk.Frame(prizes_popup, bg="#f0f0f0")
        prizes_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        prizes = [
            ("5 pesos coin", "70% chance"),
            ("20 pesos coin", "50% chance"),
            ("50 pesos", "30% chance"),
            ("Rivals skin bundle", "10% chance"),
            ("500 Robux", "1% chance")
        ]

        for prize, chance in prizes:
            prize_label = tk.Label(
                prizes_frame,
                text=f"{prize}: {chance}",
                font=("Arial", 14),
                fg="#555555",
                bg="#f0f0f0"
            )
            prize_label.pack(pady=5)

        ok_button = tk.Button(
            prizes_popup,
            text="OK",
            font=("Arial", 12),
            bg="#4CAF50",
            fg="white",
            width=10,
            command=prizes_popup.destroy
        )
        ok_button.pack(pady=(20, 10))

        prizes_popup.update_idletasks()
        width = prizes_popup.winfo_width()
        height = prizes_popup.winfo_height()
        x = (prizes_popup.winfo_screenwidth() // 2) - (width // 2)
        y = (prizes_popup.winfo_screenheight() // 2) - (height // 2)
        prizes_popup.geometry(f"+{x}+{y}")

    def show_draw_history(self):
        """Display the draw history in a popup window."""
        if not self.draw_history:
            self.show_popup("No draw history available.")
            return

        history_popup = tk.Toplevel(self.root)
        history_popup.title("Draw History")
        history_popup.geometry("400x438")
        history_popup.configure(bg="#f0f0f0")

        title_label = tk.Label(
            history_popup,
            text="Draw History",
            font=("Arial", 18, "bold"),
            fg="#333333",
            bg="#f0f0f0"
        )
        title_label.pack(pady=(20, 10))

        history_text = scrolledtext.ScrolledText(history_popup, wrap=tk.WORD, state='normal', height=15)
        history_text.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        for timestamp, result in self.draw_history:
            history_text.insert(tk.END, f"{timestamp}: {result}\n")

        history_text.config(state='disabled')

        ok_button = tk.Button(
            history_popup,
            text="OK",
            font=("Arial", 12),
            bg="#4CAF50",
            fg="white",
            width=10,
            command=history_popup.destroy
        )
        ok_button.pack(pady=(20, 10))

        history_popup.update_idletasks()
        width = history_popup.winfo_width()
        height = history_popup.winfo_height()
        x = (history_popup.winfo_screenwidth() // 2) - (width // 2)
        y = (history_popup.winfo_screenheight() // 2) - (height // 2)
        history_popup.geometry(f"+{x}+{y}")

    def log_message(self, message):
        """Log a message to the GUI."""
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.config(state='disabled')
        self.log_text.see(tk.END)

    def play_sound(self, file_path):
        """Play a sound using the simpleaudio library."""
        try:
            wave_obj = sa.WaveObject.from_wave_file(file_path)
            play_obj = wave_obj.play()
            play_obj.wait_done()
        except Exception as e:
            self.log_message(f"Error playing sound: {e}")

    def show_popup(self, message):
        """Display a pop-up message using tkinter with an exclamation icon, fixed size, and custom title."""
        self.root.after(0, self._show_popup_in_main_thread, message)

    def _show_popup_in_main_thread(self, message):
        """Internal method to show the popup in the main thread."""
        try:
            self.play_sound("alert.wav")
        except Exception as e:
            self.log_message(f"Error playing sound: {e}")

        popup = tk.Toplevel(self.root)
        popup.attributes("-topmost", True)
        popup.title("Message From Admin")
        popup.geometry("482x574")
        popup.protocol("WM_DELETE_WINDOW", lambda: None)

        try:
            icon = tk.PhotoImage(file="exclamation.png")
            icon_label = tk.Label(popup, image=icon)
            icon_label.image = icon
            icon_label.pack(pady=10)
        except Exception as e:
            self.log_message(f"Error loading icon: {e}")

        label = tk.Label(popup, text=message, font=("Arial", 14), wraplength=500)
        label.pack(pady=20)

        ok_button = tk.Button(popup, text="OK", command=popup.destroy, font=("Arial", 12), width=10)
        ok_button.pack(pady=10)

        popup.update_idletasks()
        width = popup.winfo_width()
        height = popup.winfo_height()
        x = (popup.winfo_screenwidth() // 2) - (width // 2)
        y = (popup.winfo_screenheight() // 2) - (height // 2)
        popup.geometry(f"+{x}+{y}")

    def shutdown_computer(self):
        """Shutdown the computer."""
        try:
            self.log_message("Shutting down the computer...")
            os.system("shutdown /s /t 1")
        except Exception as e:
            self.log_message(f"Error shutting down the computer: {e}")

    def handle_client(self, client_socket, client_address):
        """Handle a client connection and display the received message."""
        try:
            data = client_socket.recv(1024).decode("utf-8")
            if data:
                self.log_message(f"Received message from {client_address}: {data}")
                if data.strip() == "SHUTDOWN":
                    self.shutdown_computer()
                elif data.strip() == "CHEAT_WARNING":
                    self.root.after(0, CheatWarningPopup, self.root)
                else:
                    self.show_popup(data)
        except Exception as e:
            self.log_message(f"Error handling client {client_address}: {e}")
        finally:
            client_socket.close()

    def start_receiver(self):
        """Start the receiver to listen for messages."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((HOST, PORT))
            server_socket.listen(5)
            self.log_message(f"{HOST}:{PORT}...")

            try:
                while True:
                    client_socket, client_address = server_socket.accept()
                    self.log_message(f"Connection from {client_address}")

                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.start()
            except KeyboardInterrupt:
                self.log_message("\nReceiver is shutting down...")
            except Exception as e:
                self.log_message(f"An error occurred: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ReceiverApp(root)
    root.mainloop()
