import socket
import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import threading
import simpleaudio as sa
import random
import time
import os
import ctypes
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
import requests
import json
from pathlib import Path

# Receiver configuration
HOST = "0.0.0.0"
PORT = 12345

class ReceiverApp:
    def __init__(self, root):
        self.root = root
        
        # Load configuration from file
        self.load_config()
        
        self.root.title(self.app_name)
        self.root.geometry("600x777")
        self.root.configure(bg="#f0f0f0")
        
        # Disable window closing and resizing
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        self.root.resizable(False, False)

        # Initialize idle detection attributes
        self.warning_shown = False
        self.last_active_time = time.time()
        self.countdown_remaining = 0
        self.is_idle_detection_running = False
        self.idle_threshold = 30
        self.shutdown_delay = 30

        # Volume control
        self.volume_control = self.init_volume_control()
        self.last_slider_update = None
        self.ignore_volume_change = False
        self.saved_volume = self.config.get('volume', 50)
        self.hide_on_startup = self.config.get('hide_on_startup', False)
        self.volume_slider = None  # Initialize as None, will be created in settings popup

        # Menu Bar
        self.menu_bar = tk.Menu(root)
        self.root.config(menu=self.menu_bar)
        
        # Settings Menu
        self.settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Settings", menu=self.settings_menu)
        self.settings_menu.add_command(label="System Settings", command=self.show_settings_popup)

        # Main Frame
        self.main_frame = tk.Frame(root, bg="#f0f0f0")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Welcome Label
        self.welcome_label = tk.Label(
            self.main_frame,
            text=f"Welcome to {self.app_name}",
            font=("Arial", 20, "bold"),
            fg="#333333",
            bg="#f0f0f0"
        )
        self.welcome_label.pack(pady=(20, 10))

        # Rate Label
        self.rate_label = tk.Label(
            self.main_frame,
            text=f"Rate: {self.rate_text}",
            font=("Arial", 16),
            fg="#555555",
            bg="#f0f0f0"
        )
        self.rate_label.pack(pady=(0, 20))

        # Attempts Label
        self.attempts_label = tk.Label(
            self.main_frame,
            text="Attempts available: 1",
            font=("Arial", 16),
            fg="#555555",
            bg="#f0f0f0"
        )
        self.attempts_label.pack(pady=(0, 10))

        # Cooldown Label
        self.cooldown_label = tk.Label(
            self.main_frame,
            text="Come back in: 25:00",
            font=("Arial", 14),
            fg="#777777",
            bg="#f0f0f0"
        )
        self.cooldown_label.pack(pady=(0, 10))

        # Draw Frame
        self.draw_frame = tk.Frame(self.main_frame, bg="#f0f0f0")
        self.draw_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))

        # Draw Button
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
        self.draw_button.pack(pady=50)

        # Prizes Button
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

        # Result Label
        self.result_label = tk.Label(
            self.draw_frame,
            text="",
            font=("Arial", 18),
            fg="black",
            bg="#f0f0f0"
        )
        self.result_label.pack(pady=(10, 20))

        # History Buttons Frame
        self.history_buttons_frame = tk.Frame(self.draw_frame, bg="#f0f0f0")
        self.history_buttons_frame.pack(pady=(0, 20))

        # Draw History Button
        self.history_button = tk.Button(
            self.history_buttons_frame,
            text="Draw History",
            font=("Arial", 12),
            bg="#2196F3",
            fg="white",
            width=15,
            height=1,
            relief="flat",
            command=self.show_draw_history
        )
        self.history_button.pack(side=tk.LEFT, padx=5)

        # Hall of Fame Button
        self.hall_of_fame_button = tk.Button(
            self.history_buttons_frame,
            text="Hall of Fame",
            font=("Arial", 12),
            bg="#9C27B0",
            fg="white",
            width=15,
            height=1,
            relief="flat",
            command=self.show_hall_of_fame
        )
        self.hall_of_fame_button.pack(side=tk.LEFT, padx=5)

        # Log Frame
        self.log_frame = tk.Frame(root, bg="#ffffff")
        self.log_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=(0, 10))

        # Log Text
        self.log_text = scrolledtext.ScrolledText(self.log_frame, wrap=tk.WORD, state='disabled', height=10)
        self.log_text.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        # Initialize variables
        self.draw_attempts = 1
        self.last_draw_time = time.monotonic()
        self.draw_history = []
        self.hall_of_fame = []
        
        # Idle detector - load saved settings
        self.load_settings()
        
        # Start services
        self.update_attempts()
        self.receiver_thread = threading.Thread(target=self.start_receiver, daemon=True)
        self.receiver_thread.start()
        
        # Set initial volume to saved value
        if self.saved_volume is not None and self.volume_control:
            self.set_volume(self.saved_volume)
        
        # Start monitoring volume changes
        self.monitor_volume_changes()
        
        # Auto-start idle detection if enabled
        if self.is_idle_detection_running:
            self.start_idle_detection(initial_load=True)

    def load_config(self):
        """Load configuration from config.txt file"""
        config_file = Path("config.txt")
        self.config = {
            'app_name': "EJS Internet Cafe",
            'rate_text': "5 pesos = 25 mins",
            'lose_weight': 99,
            'win_weight': 0.01,
            'prizes': ["5 pesos coin", "20 pesos coin", "50 pesos", "100 pesos", "500 Robux"],
            'prize_weights': [90, 0.3, 0.2, 0.1],
            'volume': 50,
            'hide_on_startup': False
        }
        
        try:
            if config_file.exists():
                with open(config_file, 'r') as f:
                    current_section = None
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            if line.startswith('#') and '#' in line:
                                current_section = line[1:].strip().lower()
                            continue
                            
                        if current_section == 'app name':
                            self.config['app_name'] = line
                        elif current_section == 'rate':
                            self.config['rate_text'] = line
                        elif current_section == 'lose_win weight':
                            parts = line.split(',')
                            if len(parts) == 2:
                                self.config['lose_weight'] = float(parts[0].strip())
                                self.config['win_weight'] = float(parts[1].strip())
                        elif current_section == 'prizes':
                            self.config['prizes'] = [p.strip() for p in line.split(',')]
                        elif current_section == 'prize_weight':
                            weights = []
                            for weight in line.split(','):
                                weight = weight.strip().replace('%', '')
                                try:
                                    weights.append(float(weight))
                                except ValueError:
                                    weights.append(0.0)
                            self.config['prize_weights'] = weights
                        elif current_section == 'volume':
                            try:
                                self.config['volume'] = int(line.strip())
                            except ValueError:
                                pass
                        elif current_section == 'hide_on_startup':
                            self.config['hide_on_startup'] = line.strip().lower() in ('true', 'yes', '1')
        except Exception as e:
            print(f"Error loading config: {e}")
        
        # Assign to instance variables
        self.app_name = self.config['app_name']
        self.rate_text = self.config['rate_text']
        self.lose_weight = self.config['lose_weight']
        self.win_weight = self.config['win_weight']
        self.prizes = self.config['prizes']
        self.prize_weights = self.config['prize_weights']

    def save_config(self):
        """Save configuration to config.txt file"""
        try:
            with open("config.txt", 'w') as f:
                f.write("#App name\n")
                f.write(f"{self.app_name}\n\n")
                f.write("#Rate\n")
                f.write(f"{self.rate_text}\n\n")
                f.write("#lose_win weight\n")
                f.write(f"{self.lose_weight}, {self.win_weight}\n\n")
                f.write("#prizes\n")
                f.write(", ".join(self.prizes) + "\n\n")
                f.write("#prize_weight\n")
                f.write(", ".join(map(str, self.prize_weights)) + "\n\n")
                f.write("#volume\n")
                f.write(f"{self.saved_volume}\n\n")
                f.write("#hide_on_startup\n")
                f.write(f"{self.hide_on_startup}\n")
        except Exception as e:
            self.log_message(f"Error saving config: {e}")

    def load_settings(self):
        """Load saved settings from file"""
        settings_file = Path("idle_settings.json")
        try:
            if settings_file.exists():
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    self.idle_threshold = settings.get('idle_threshold', 30)
                    self.shutdown_delay = settings.get('shutdown_delay', 30)
                    self.is_idle_detection_running = settings.get('auto_start', False)
            else:
                self.idle_threshold = 30
                self.shutdown_delay = 30
                self.is_idle_detection_running = False
        except Exception as e:
            self.log_message(f"Error loading settings: {e}")
            self.idle_threshold = 30
            self.shutdown_delay = 30
            self.is_idle_detection_running = False

    def save_settings(self):
        """Save current settings to file"""
        settings = {
            'idle_threshold': self.idle_threshold,
            'shutdown_delay': self.shutdown_delay,
            'auto_start': self.is_idle_detection_running
        }
        try:
            with open("idle_settings.json", 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            self.log_message(f"Error saving settings: {e}")

    def init_volume_control(self):
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            return cast(interface, POINTER(IAudioEndpointVolume))
        except Exception as e:
            self.log_message(f"Failed to initialize audio control: {e}")
            return None

    def show_settings_popup(self):
        settings_popup = tk.Toplevel(self.root)
        settings_popup.title("System Settings")
        settings_popup.geometry("500x400")
        settings_popup.resizable(False, False)
        settings_popup.configure(bg="#f0f0f0")

        notebook = ttk.Notebook(settings_popup)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Volume Control Tab
        volume_frame = ttk.Frame(notebook, padding=10)
        notebook.add(volume_frame, text="Volume Control")

        # Current volume display
        self.volume_label_settings = ttk.Label(
            volume_frame,
            text="Current Volume: Checking...",
            font=('Arial', 10)
        )
        self.volume_label_settings.pack(pady=5)

        # Volume slider
        self.volume_slider = ttk.Scale(
            volume_frame,
            from_=0,
            to=100,
            command=self.on_volume_slider_move
        )
        self.volume_slider.pack(fill=tk.X, pady=10)
        
        # Update slider to current volume
        if self.volume_control:
            try:
                current_vol = self.volume_control.GetMasterVolumeLevelScalar()
                self.volume_slider.set(current_vol * 100)
                self.volume_label_settings.config(text=f"Current Volume: {int(current_vol * 100)}%")
            except Exception as e:
                self.log_message(f"Error getting current volume: {e}")
                self.volume_label_settings.config(text="Current Volume: Unknown")

        # Quick set buttons
        quick_buttons_frame = ttk.Frame(volume_frame)
        quick_buttons_frame.pack(pady=10)
        
        for percent in [15, 30, 50, 75]:
            ttk.Button(
                quick_buttons_frame,
                text=f"{percent}%",
                command=lambda p=percent: self.set_volume(p),
                width=5
            ).pack(side=tk.LEFT, padx=5)

        # Custom volume entry
        custom_frame = ttk.Frame(volume_frame)
        custom_frame.pack(pady=10)
        
        ttk.Label(custom_frame, text="Custom %:").pack(side=tk.LEFT)
        
        self.custom_volume_entry = ttk.Entry(
            custom_frame,
            width=5,
            validate='key',
            validatecommand=(self.root.register(self.validate_percent), '%P')
        )
        self.custom_volume_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            custom_frame,
            text="Set",
            command=self.set_custom_volume,
            width=5
        ).pack(side=tk.LEFT)

        # Save current volume button
        ttk.Button(
            volume_frame,
            text="Save Current Volume",
            command=self.save_current_volume,
            width=20
        ).pack(pady=10)

        # Hide on startup checkbox
        self.hide_var = tk.BooleanVar(value=self.hide_on_startup)
        ttk.Checkbutton(
            volume_frame,
            text="Hide program when run",
            variable=self.hide_var,
            command=self.toggle_hide_setting
        ).pack(pady=5)

        # Idle Detector Tab
        idle_frame = ttk.Frame(notebook, padding=10)
        notebook.add(idle_frame, text="Idle Detector")

        ttk.Label(idle_frame, text="Idle Threshold (seconds):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.idle_threshold_entry = ttk.Spinbox(idle_frame, from_=5, to=300, width=5)
        self.idle_threshold_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        self.idle_threshold_entry.delete(0, tk.END)
        self.idle_threshold_entry.insert(0, str(self.idle_threshold))

        ttk.Label(idle_frame, text="Shutdown Delay (seconds):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.shutdown_delay_entry = ttk.Spinbox(idle_frame, from_=5, to=300, width=5)
        self.shutdown_delay_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
        self.shutdown_delay_entry.delete(0, tk.END)
        self.shutdown_delay_entry.insert(0, str(self.shutdown_delay))

        # Auto-start checkbox
        self.auto_start_var = tk.BooleanVar(value=self.is_idle_detection_running)
        ttk.Checkbutton(
            idle_frame,
            text="Auto-start on login",
            variable=self.auto_start_var,
            command=self.toggle_auto_start
        ).grid(row=2, column=0, columnspan=2, pady=5, sticky=tk.W)

        button_frame = ttk.Frame(idle_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        self.start_idle_button = ttk.Button(button_frame, text="Start Detection", command=lambda: self.start_idle_detection())
        self.start_idle_button.pack(side=tk.LEFT, padx=5)
        self.stop_idle_button = ttk.Button(button_frame, text="Stop Detection", command=self.stop_idle_detection, state=tk.DISABLED)
        self.stop_idle_button.pack(side=tk.LEFT, padx=5)

        # Update button states
        if self.is_idle_detection_running:
            self.start_idle_button.config(state=tk.DISABLED)
            self.stop_idle_button.config(state=tk.NORMAL)
        else:
            self.start_idle_button.config(state=tk.NORMAL)
            self.stop_idle_button.config(state=tk.DISABLED)

        self.idle_status_label = ttk.Label(idle_frame, text="Idle detection is currently " + 
                                         ("active." if self.is_idle_detection_running else "inactive."), 
                                         font=('Arial', 10))
        self.idle_status_label.grid(row=4, column=0, columnspan=2, pady=10)

        ttk.Button(settings_popup, text="Close", command=settings_popup.destroy).pack(pady=10)

    def validate_percent(self, text):
        """Validate percentage input"""
        if text == "":
            return True
        try:
            return 0 <= int(text) <= 100
        except ValueError:
            return False

    def on_volume_slider_move(self, value):
        """Handle slider movement with debounce"""
        if self.last_slider_update:
            self.root.after_cancel(self.last_slider_update)
        
        percent = float(value)
        self.last_slider_update = self.root.after(
            100, 
            lambda: self.set_volume(percent, update_slider=False)
        )

    def set_volume(self, percent, update_slider=True):
        """Set system volume with error handling"""
        if not self.volume_control:
            return
            
        try:
            self.ignore_volume_change = True
            percent = max(0, min(100, float(percent)))
            self.volume_control.SetMasterVolumeLevelScalar(percent/100, None)
            
            if update_slider and hasattr(self, 'volume_slider') and self.volume_slider:
                self.volume_slider.set(percent)
            if hasattr(self, 'volume_label_settings') and self.volume_label_settings:
                self.volume_label_settings.config(text=f"Current Volume: {int(percent)}%")
            self.ignore_volume_change = False
        except Exception as e:
            self.ignore_volume_change = False
            self.log_message(f"Volume control failed: {e}")

    def set_custom_volume(self):
        """Set volume from custom entry"""
        try:
            percent = int(self.custom_volume_entry.get())
            self.set_volume(percent)
        except ValueError:
            messagebox.showerror("Error", "Please enter a number 0-100")

    def save_current_volume(self):
        """Save the current volume as the preferred setting"""
        if not self.volume_control:
            return
            
        try:
            current_vol = self.volume_control.GetMasterVolumeLevelScalar()
            percent = int(current_vol * 100)
            self.saved_volume = percent
            self.save_config()
            messagebox.showinfo("Saved", f"Volume setting {percent}% has been saved.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save volume:\n{str(e)}")

    def toggle_hide_setting(self):
        """Toggle the hide on startup setting"""
        self.hide_on_startup = self.hide_var.get()
        self.save_config()

    def monitor_volume_changes(self):
        """Check for volume changes and revert to saved setting if changed externally"""
        if not self.volume_control:
            return
            
        try:
            current_vol = self.volume_control.GetMasterVolumeLevelScalar()
            current_percent = int(current_vol * 100)
            
            if not self.ignore_volume_change and self.saved_volume is not None:
                if current_percent != self.saved_volume:
                    self.set_volume(self.saved_volume)
        except:
            pass
            
        self.root.after(1000, self.monitor_volume_changes)

    def toggle_auto_start(self):
        """Toggle auto-start setting and save it"""
        self.is_idle_detection_running = self.auto_start_var.get()
        self.save_settings()
        
        if hasattr(self, 'idle_status_label'):
            self.idle_status_label.config(text="Idle detection is currently " + 
                                        ("active." if self.is_idle_detection_running else "inactive."))
        
        if hasattr(self, 'start_idle_button') and hasattr(self, 'stop_idle_button'):
            if self.is_idle_detection_running:
                self.start_idle_button.config(state=tk.DISABLED)
                self.stop_idle_button.config(state=tk.NORMAL)
            else:
                self.start_idle_button.config(state=tk.NORMAL)
                self.stop_idle_button.config(state=tk.DISABLED)

    def get_idle_time(self):
        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [('cbSize', ctypes.c_uint), ('dwTime', ctypes.c_uint)]
        
        lastInputInfo = LASTINPUTINFO()
        lastInputInfo.cbSize = ctypes.sizeof(lastInputInfo)
        ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lastInputInfo))
        millis = ctypes.windll.kernel32.GetTickCount() - lastInputInfo.dwTime
        return millis / 1000.0

    def detection_loop(self):
        """Main detection loop with automatic warning dismissal"""
        while self.is_idle_detection_running:
            idle_time = self.get_idle_time()
            
            if idle_time >= self.idle_threshold and not self.warning_shown:
                self.root.after(0, self.show_idle_warning)
            elif idle_time < 1 and self.warning_shown:
                self.root.after(0, self.dismiss_idle_warning)
                
            time.sleep(1)

    def show_idle_warning(self):
        """Show the idle warning popup"""
        if self.warning_shown:
            return
            
        self.warning_shown = True
        self.countdown_remaining = self.shutdown_delay
        
        self.warning_popup = tk.Toplevel(self.root)
        self.warning_popup.title("Idle Warning")
        self.warning_popup.geometry("400x200")
        self.warning_popup.resizable(False, False)
        self.warning_popup.attributes('-topmost', True)
        
        self.warning_label = ttk.Label(
            self.warning_popup,
            text="Idle detected! This computer will shutdown soon.",
            wraplength=380,
            padding=10
        )
        self.warning_label.pack(pady=(10, 0))
        
        self.countdown_label = ttk.Label(
            self.warning_popup,
            text=f"Time remaining: {self.countdown_remaining} seconds",
            font=('Arial', 10, 'bold')
        )
        self.countdown_label.pack(pady=5)
        
        self.update_countdown(self.warning_popup, self.countdown_label)
        
        self.shutdown_timer = self.warning_popup.after(
            self.shutdown_delay * 1000,
            self.shutdown_computer
        )

    def dismiss_idle_warning(self):
        """Dismiss the warning when user becomes active"""
        if not self.warning_shown:
            return
            
        self.warning_shown = False
        self.last_active_time = time.time()
        
        if hasattr(self, 'shutdown_timer'):
            self.warning_popup.after_cancel(self.shutdown_timer)
        
        if hasattr(self, 'warning_popup') and self.warning_popup.winfo_exists():
            self.warning_popup.destroy()
        
        self.log_message("User activity detected - warning dismissed")

    def update_countdown(self, window, label):
        """Update the countdown display"""
        if self.warning_shown and self.countdown_remaining > 0:
            label.config(text=f"Time remaining: {self.countdown_remaining} seconds")
            self.countdown_remaining -= 1
            window.after(1000, self.update_countdown, window, label)

    def start_idle_detection(self, initial_load=False):
        try:
            if not initial_load:
                self.idle_threshold = int(self.idle_threshold_entry.get())
                self.shutdown_delay = int(self.shutdown_delay_entry.get())
                self.is_idle_detection_running = True
                self.auto_start_var.set(True)
                
            if not self.is_idle_detection_running:
                return
                
            if hasattr(self, 'start_idle_button'):
                self.start_idle_button.config(state=tk.DISABLED)
            if hasattr(self, 'stop_idle_button'):
                self.stop_idle_button.config(state=tk.NORMAL)
            if hasattr(self, 'idle_status_label'):
                self.idle_status_label.config(text="Idle detection is active.")
            
            detection_thread = threading.Thread(target=self.detection_loop, daemon=True)
            detection_thread.start()
            
            self.log_message("Idle detection started")
            
            if not initial_load:
                self.save_settings()
                
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers")

    def stop_idle_detection(self):
        self.is_idle_detection_running = False
        self.auto_start_var.set(False)
        
        if hasattr(self, 'start_idle_button'):
            self.start_idle_button.config(state=tk.NORMAL)
        if hasattr(self, 'stop_idle_button'):
            self.stop_idle_button.config(state=tk.DISABLED)
        if hasattr(self, 'idle_status_label'):
            self.idle_status_label.config(text="Idle detection is inactive.")
            
        self.log_message("Idle detection stopped")
        self.save_settings()

    def update_attempts(self):
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

    def on_draw_click(self):
        if self.draw_attempts > 0:
            self.draw_attempts -= 1
            self.attempts_label.config(text=f"Attempts available: {self.draw_attempts}")

            result = random.choices(
                ["Better luck next time", "It's your lucky day, you won!"],
                weights=[self.lose_weight, self.win_weight]
            )[0]

            if result == "It's your lucky day, you won!":
                prize = random.choices(self.prizes, weights=self.prize_weights)[0]
                result_message = f"{result} {prize}"
                self.result_label.config(text=result_message, fg="green", font=("Arial", 18, "bold"))
                self.play_sound("winner.wav")
                
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                self.draw_history.append((timestamp, result_message))
                self.hall_of_fame.append((timestamp, prize))
            else:
                result_message = result
                self.result_label.config(text=result, fg="black", font=("Arial", 18))
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                self.draw_history.append((timestamp, result_message))

            self.log_message(f"{timestamp}: {result_message}")
        else:
            self.result_label.config(text="No attempts available", fg="red", font=("Arial", 18))

    def show_prizes_popup(self):
        prizes_popup = tk.Toplevel(self.root)
        prizes_popup.title("Prizes")
        prizes_popup.geometry("403x378")
        prizes_popup.configure(bg="#f0f0f0")

        title_label = tk.Label(prizes_popup, text="Prizes and Chances", font=("Arial", 18, "bold"), bg="#f0f0f0")
        title_label.pack(pady=(20, 10))

        prizes_frame = tk.Frame(prizes_popup, bg="#f0f0f0")
        prizes_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        total_weight = sum(self.prize_weights)
        
        prize_list = []
        for prize, weight in zip(self.prizes, self.prize_weights):
            percentage = (weight / total_weight) * 100
            prize_list.append((prize, f"{percentage:.2f}% chance"))

        for prize, chance in prize_list:
            tk.Label(prizes_frame, text=f"{prize}: {chance}", font=("Arial", 14), bg="#f0f0f0").pack(pady=5)

        tk.Button(prizes_popup, text="OK", command=prizes_popup.destroy, font=("Arial", 12), bg="#4CAF50", fg="white").pack(pady=(20, 10))

    def show_draw_history(self):
        if not self.draw_history:
            self.show_popup("No draw history available.")
            return

        history_popup = tk.Toplevel(self.root)
        history_popup.title("Draw History")
        history_popup.geometry("401x428")
        history_popup.configure(bg="#f0f0f0")

        tk.Label(history_popup, text="Draw History", font=("Arial", 18, "bold"), bg="#f0f0f0").pack(pady=(20, 10))

        history_text = scrolledtext.ScrolledText(history_popup, wrap=tk.WORD, state='normal', height=15)
        history_text.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        for timestamp, result in self.draw_history:
            history_text.insert(tk.END, f"{timestamp}: {result}\n")

        history_text.config(state='disabled')
        tk.Button(history_popup, text="OK", command=history_popup.destroy, font=("Arial", 12), bg="#4CAF50", fg="white").pack(pady=(20, 10))

    def show_hall_of_fame(self):
        try:
            hof_popup = tk.Toplevel(self.root)
            hof_popup.title("Champions")
            hof_popup.geometry("593x598")
            hof_popup.configure(bg="#f0f0f0")
            
            title_label = tk.Label(
                hof_popup,
                text="Champions Hall of Fame",
                font=("Arial", 18, "bold"),
                fg="#333333",
                bg="#f0f0f0"
            )
            title_label.pack(pady=(10, 5))

            content_frame = tk.Frame(hof_popup, bg="#f0f0f0")
            content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            loading_label = tk.Label(
                content_frame,
                text="Loading champions...",
                font=("Arial", 12),
                bg="#f0f0f0"
            )
            loading_label.pack(pady=50)

            text_widget = scrolledtext.ScrolledText(
                content_frame,
                wrap=tk.WORD,
                font=("Arial", 12),
                bg="white",
                padx=10,
                pady=10,
                state='disabled'
            )

            def fetch_url_content():
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    response = requests.get("https://pastebin.com/raw/xTnpAE4n", headers=headers)
                    response.raise_for_status()
                    content = response.text
                    
                    hof_popup.after(0, lambda: self.display_hof_content(
                        content_frame, loading_label, text_widget, content))
                except Exception as fetch_error:
                    error_msg = f"Failed to load champions:\n{str(fetch_error)}"
                    if "403" in str(fetch_error):
                        error_msg += "\n\nPastebin is blocking the request.\nTry again later or check your internet connection."
                    hof_popup.after(0, lambda: loading_label.config(
                        text=error_msg,
                        fg="red"
                    ))

            threading.Thread(target=fetch_url_content, daemon=True).start()

            close_button = tk.Button(
                hof_popup,
                text="Close",
                command=hof_popup.destroy,
                font=("Arial", 12),
                bg="#4CAF50",
                fg="white",
                width=10
            )
            close_button.pack(pady=(5, 10))

        except Exception as e:
            self.log_message(f"Error showing Hall of Fame: {e}")
            self.show_popup(f"Failed to open Hall of Fame: {e}")

    def display_hof_content(self, parent_frame, loading_label, text_widget, content):
        """Display the fetched content"""
        loading_label.pack_forget()
        text_widget.config(state='normal')
        text_widget.delete(1.0, tk.END)
        text_widget.insert(tk.END, content)
        text_widget.config(state='disabled')
        text_widget.pack(fill=tk.BOTH, expand=True)

    def show_popup(self, message):
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

        tk.Label(popup, text=message, font=("Arial", 14), wraplength=500).pack(pady=20)
        tk.Button(popup, text="OK", command=popup.destroy, font=("Arial", 12), width=10).pack(pady=10)

    def log_message(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.config(state='disabled')
        self.log_text.see(tk.END)

    def play_sound(self, file_path):
        try:
            if not os.path.exists(file_path):
                self.log_message(f"Sound file not found: {file_path}")
                return
            wave_obj = sa.WaveObject.from_wave_file(file_path)
            play_obj = wave_obj.play()
            play_obj.wait_done()
        except Exception as e:
            self.log_message(f"Error playing sound: {e}")

    def shutdown_computer(self):
        try:
            self.log_message("Shutting down the computer...")
            os.system("shutdown /s /t 1")
        except Exception as e:
            self.log_message(f"Error shutting down the computer: {e}")

    def handle_client(self, client_socket, client_address):
        try:
            data = client_socket.recv(1024).decode("utf-8")
            if data:
                self.log_message(f"Received message from {client_address}: {data}")
                if data.strip() == "SHUTDOWN":
                    self.shutdown_computer()
                elif data.startswith("VOLUME:"):
                    try:
                        volume_percent = int(data.split(":")[1])
                        self.root.after(0, lambda: self.set_volume(volume_percent))
                    except (ValueError, IndexError):
                        self.log_message("Invalid volume command format")
                else:
                    self.show_popup(data)
        except Exception as e:
            self.log_message(f"Error handling client {client_address}: {e}")
        finally:
            client_socket.close()

    def start_receiver(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((HOST, PORT))
            server_socket.listen(5)
            self.log_message(f"Server started on {HOST}:{PORT}")

            try:
                while True:
                    client_socket, client_address = server_socket.accept()
                    self.log_message(f"Connection from {client_address}")
                    client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
                    client_thread.start()
            except Exception as e:
                self.log_message(f"Server error: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ReceiverApp(root)
    root.mainloop()
