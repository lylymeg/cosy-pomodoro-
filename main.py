import sys
import numpy as np
from scipy import signal
import sounddevice as sd

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar, QFrame, QLineEdit,
    QListWidget, QListWidgetItem, QCheckBox, QComboBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

WORK_TIME = 25 * 60
SHORT_BREAK = 5 * 60
LONG_BREAK = 15 * 60


class ContinuousAmbientEngine:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.current_sound = "Aucun"
        self.stream = None
        
        b_rain, a_rain = signal.butter(2, [200 / (sample_rate / 2), 3000 / (sample_rate / 2)], btype='band')
        self.b_rain, self.a_rain = b_rain, a_rain
        self.zi_rain = signal.lfilter_zi(b_rain, a_rain)

        b_cafe, a_cafe = signal.butter(2, [150 / (sample_rate / 2), 1200 / (sample_rate / 2)], btype='band')
        self.b_cafe, self.a_cafe = b_cafe, a_cafe
        self.zi_cafe = signal.lfilter_zi(b_cafe, a_cafe)

    def _audio_callback(self, outdata, frames, time_info, status):
        if self.current_sound == "🌧️ Pluie":
            white = np.random.normal(0, 0.08, frames)
            rain, self.zi_rain = signal.lfilter(self.b_rain, self.a_rain, white, zi=self.zi_rain)
            drops = np.random.exponential(scale=0.001, size=frames) * np.random.choice([0, 1], size=frames, p=[0.998, 0.002])
            outdata[:, 0] = (rain + drops).astype(np.float32)

        elif self.current_sound == "☕ Café":
            white = np.random.normal(0, 0.08, frames)
            cafe, self.zi_cafe = signal.lfilter(self.b_cafe, self.a_cafe, white, zi=self.zi_cafe)
            chatter = np.random.normal(0, 0.04, frames) * np.random.choice([0, 1], size=frames, p=[0.95, 0.05])
            clinks = np.random.exponential(scale=0.002, size=frames) * np.random.choice([0, 1], size=frames, p=[0.999, 0.001])
            outdata[:, 0] = (cafe + chatter + clinks).astype(np.float32)

        elif self.current_sound == "📻 Bruit Blanc":
            white = np.random.normal(0, 0.025, frames)
            outdata[:, 0] = white.astype(np.float32)

        else:
            outdata.fill(0)

    def set_sound(self, sound_name):
        self.current_sound = sound_name

        if sound_name == "Aucun":
            if self.stream is not None:
                self.stream.stop()
                self.stream.close()
                self.stream = None
        else:
            if self.stream is None:
                self.stream = sd.OutputStream(
                    samplerate=self.sample_rate,
                    channels=1,
                    callback=self._audio_callback,
                    blocksize=2048
                )
                self.stream.start()

    def stop(self):
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None


class CosyFocusTimer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cosy Focus Timer & To-Do 🌿")
        self.setFixedSize(780, 580)
        self.setStyleSheet("background-color: #1E222B;")

        self.audio_engine = ContinuousAmbientEngine()

        self.time_left = WORK_TIME
        self.total_time = WORK_TIME
        self.is_running = False
        self.current_mode = "WORK"
        self.completed_pomodoros = 0

        self.init_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        left_card = QFrame()
        left_card.setStyleSheet("""
            QFrame {
                background-color: #282C34;
                border-radius: 16px;
                border: 1px solid #3E4451;
            }
        """)
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(20, 20, 20, 20)

        self.status_label = QLabel("🎯 SESSION DE TRAVAIL")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.status_label.setStyleSheet("color: #98C379; background-color: rgba(152, 195, 121, 0.15); border-radius: 10px; padding: 6px; border: none;")
        left_layout.addWidget(self.status_label)

        self.time_display = QLabel("25:00")
        self.time_display.setAlignment(Qt.AlignCenter)
        self.time_display.setFont(QFont("Segoe UI", 42, QFont.Bold))
        self.time_display.setStyleSheet("color: #ECEFF4; border: none; margin-top: 10px;")
        left_layout.addWidget(self.time_display)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.update_progress_bar_style("#98C379")
        self.progress_bar.setValue(100)
        left_layout.addWidget(self.progress_bar)

        self.streak_label = QLabel("🍅 Pomodoros complétés : 0")
        self.streak_label.setAlignment(Qt.AlignCenter)
        self.streak_label.setFont(QFont("Segoe UI", 8))
        self.streak_label.setStyleSheet("color: #ABB2BF; border: none;")
        left_layout.addWidget(self.streak_label)

        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("▶ DÉMARRER")
        self.start_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.setStyleSheet("background-color: #98C379; color: #1E222B; border-radius: 8px; padding: 10px; border: none;")
        self.start_btn.clicked.connect(self.toggle_timer)

        self.reset_btn = QPushButton("🔄 RESET")
        self.reset_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.setStyleSheet("background-color: #3E4451; color: #ECEFF4; border-radius: 8px; padding: 10px; border: none;")
        self.reset_btn.clicked.connect(self.reset_timer)

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.reset_btn)
        left_layout.addLayout(btn_layout)

        mode_layout = QHBoxLayout()
        for label_text, mode in [("Travail", "WORK"), ("Pause 5m", "SHORT_BREAK"), ("Pause 15m", "LONG_BREAK")]:
            btn = QPushButton(label_text)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFont(QFont("Segoe UI", 8, QFont.Bold))
            btn.setStyleSheet("QPushButton { background-color: transparent; color: #ABB2BF; border: 1px solid #3E4451; border-radius: 6px; padding: 4px; } QPushButton:hover { color: #ECEFF4; }")
            btn.clicked.connect(lambda _, m=mode: self.switch_mode(m))
            mode_layout.addWidget(btn)
        left_layout.addLayout(mode_layout)

        sound_label = QLabel("🎧 Bruit d'ambiance continu :")
        sound_label.setFont(QFont("Segoe UI", 8, QFont.Bold))
        sound_label.setStyleSheet("color: #ABB2BF; border: none; margin-top: 10px;")
        left_layout.addWidget(sound_label)

        self.sound_combo = QComboBox()
        self.sound_combo.addItems(["Aucun", "🌧️ Pluie", "☕ Café", "📻 Bruit Blanc"])
        self.sound_combo.setStyleSheet("""
            QComboBox {
                background-color: #1E222B;
                color: #ECEFF4;
                border: 1px solid #3E4451;
                border-radius: 6px;
                padding: 6px;
            }
        """)
        self.sound_combo.currentTextChanged.connect(self.audio_engine.set_sound)
        left_layout.addWidget(self.sound_combo)

        main_layout.addWidget(left_card, stretch=1)

        right_card = QFrame()
        right_card.setStyleSheet("""
            QFrame {
                background-color: #282C34;
                border-radius: 16px;
                border: 1px solid #3E4451;
            }
        """)
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(20, 20, 20, 20)

        todo_title = QLabel("📝 Tâches de la Session")
        todo_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        todo_title.setStyleSheet("color: #61AFEF; border: none;")
        right_layout.addWidget(todo_title)

        input_layout = QHBoxLayout()
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Ajouter une tâche...")
        self.task_input.setStyleSheet("""
            QLineEdit {
                background-color: #1E222B;
                color: #ECEFF4;
                border: 1px solid #3E4451;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        self.task_input.returnPressed.connect(self.add_task)

        add_task_btn = QPushButton("+")
        add_task_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        add_task_btn.setFixedSize(32, 32)
        add_task_btn.setCursor(Qt.PointingHandCursor)
        add_task_btn.setStyleSheet("background-color: #61AFEF; color: #1E222B; border-radius: 6px; border: none;")
        add_task_btn.clicked.connect(self.add_task)

        input_layout.addWidget(self.task_input)
        input_layout.addWidget(add_task_btn)
        right_layout.addLayout(input_layout)

        self.task_list = QListWidget()
        self.task_list.setStyleSheet("QListWidget { background-color: transparent; border: none; }")
        right_layout.addWidget(self.task_list)

        main_layout.addWidget(right_card, stretch=1)

    def add_task(self):
        text = self.task_input.text().strip()
        if text:
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(5, 5, 5, 5)

            checkbox = QCheckBox(text)
            checkbox.setFont(QFont("Segoe UI", 9))
            checkbox.setStyleSheet("color: #ECEFF4;")
            checkbox.stateChanged.connect(lambda state, cb=checkbox: self.toggle_task_done(state, cb))

            del_btn = QPushButton("✕")
            del_btn.setFixedSize(20, 20)
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setStyleSheet("background-color: transparent; color: #E06C75; border: none; font-weight: bold;")

            item_layout.addWidget(checkbox)
            item_layout.addStretch()
            item_layout.addWidget(del_btn)

            list_item = QListWidgetItem(self.task_list)
            list_item.setSizeHint(item_widget.sizeHint())

            self.task_list.addItem(list_item)
            self.task_list.setItemWidget(list_item, item_widget)

            del_btn.clicked.connect(lambda _, item=list_item: self.delete_task(item))
            self.task_input.clear()

    def toggle_task_done(self, state, checkbox):
        if state == Qt.Checked:
            checkbox.setStyleSheet("color: #5c6370; text-decoration: line-through;")
        else:
            checkbox.setStyleSheet("color: #ECEFF4; text-decoration: none;")

    def delete_task(self, item):
        row = self.task_list.row(item)
        self.task_list.takeItem(row)

    def update_progress_bar_style(self, color_hex):
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{ background-color: #1E222B; border: none; border-radius: 3px; }}
            QProgressBar::chunk {{ background-color: {color_hex}; border-radius: 3px; }}
        """)

    def update_timer(self):
        if self.time_left > 0:
            self.time_left -= 1
            self.refresh_display()
        else:
            self.timer.stop()
            self.is_running = False
            self.handle_session_complete()

    def refresh_display(self):
        mins, secs = divmod(self.time_left, 60)
        self.time_display.setText(f"{mins:02d}:{secs:02d}")
        progress = int((self.time_left / self.total_time) * 100)
        self.progress_bar.setValue(progress)

    def toggle_timer(self):
        if self.is_running:
            self.timer.stop()
            self.is_running = False
            self.start_btn.setText("▶ REPRENDRE")
        else:
            self.timer.start(1000)
            self.is_running = True
            self.start_btn.setText("⏸ PAUSE")

    def reset_timer(self):
        self.timer.stop()
        self.is_running = False
        self.switch_mode(self.current_mode)

    def switch_mode(self, mode):
        self.current_mode = mode
        self.timer.stop()
        self.is_running = False

        if mode == "WORK":
            self.time_left = WORK_TIME
            self.status_label.setText("🎯 SESSION DE TRAVAIL")
            self.status_label.setStyleSheet("color: #98C379; background-color: rgba(152, 195, 121, 0.15); border-radius: 10px; padding: 6px; border: none;")
            self.update_progress_bar_style("#98C379")
        elif mode == "SHORT_BREAK":
            self.time_left = SHORT_BREAK
            self.status_label.setText("☕ PAUSE COURTE")
            self.status_label.setStyleSheet("color: #61AFEF; background-color: rgba(97, 175, 239, 0.15); border-radius: 10px; padding: 6px; border: none;")
            self.update_progress_bar_style("#61AFEF")
        elif mode == "LONG_BREAK":
            self.time_left = LONG_BREAK
            self.status_label.setText("🌿 PAUSE LONGUE")
            self.status_label.setStyleSheet("color: #C678DD; background-color: rgba(198, 120, 221, 0.15); border-radius: 10px; padding: 6px; border: none;")
            self.update_progress_bar_style("#C678DD")

        self.total_time = self.time_left
        self.start_btn.setText("▶ DÉMARRER")
        self.refresh_display()

    def handle_session_complete(self):
        if self.current_mode == "WORK":
            self.completed_pomodoros += 1
            self.streak_label.setText(f"🍅 Pomodoros complétés : {self.completed_pomodoros}")
            self.switch_mode("SHORT_BREAK" if self.completed_pomodoros % 4 != 0 else "LONG_BREAK")
        else:
            self.switch_mode("WORK")

    def closeEvent(self, event):
        self.audio_engine.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    timer = CosyFocusTimer()
    timer.show()
    sys.exit(app.exec_())