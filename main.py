import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QProgressBar, QFrame
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor

WORK_TIME = 25 * 60       # 25 minutes
SHORT_BREAK = 5 * 60      # 5 minutes
LONG_BREAK = 15 * 60     # 15 minutes


class CosyFocusTimer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cosy Focus Timer 🌿")
        self.setFixedSize(420, 560)
        self.setStyleSheet("background-color: #1E222B;")

        # États du minuteur
        self.time_left = WORK_TIME
        self.total_time = WORK_TIME
        self.is_running = False
        self.current_mode = "WORK"  # WORK, SHORT_BREAK, LONG_BREAK
        self.completed_pomodoros = 0

        self.init_ui()

        # QTimer principal
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # --- Carte Principale (Dark Glass) ---
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #282C34;
                border-radius: 20px;
                border: 1px solid #3E4451;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(25, 25, 25, 25)

        # --- Badge de Statut ---
        self.status_label = QLabel("🎯 SESSION DE TRAVAIL")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.status_label.setStyleSheet("""
            color: #98C379;
            background-color: rgba(152, 195, 121, 0.15);
            border-radius: 12px;
            padding: 6px 12px;
            border: none;
        """)
        card_layout.addWidget(self.status_label, alignment=Qt.AlignCenter)

        # --- Affichage du Chronomètre ---
        self.time_display = QLabel("25:00")
        self.time_display.setAlignment(Qt.AlignCenter)
        self.time_display.setFont(QFont("Segoe UI", 48, QFont.Bold))
        self.time_display.setStyleSheet("color: #ECEFF4; border: none; margin-top: 15px;")
        card_layout.addWidget(self.time_display)

        # --- Barre de Progression ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.update_progress_bar_style("#98C379")
        self.progress_bar.setValue(100)
        card_layout.addWidget(self.progress_bar)

        # --- Compteur de Sessions (Série) ---
        self.streak_label = QLabel("🍅 Pomodoros complétés : 0")
        self.streak_label.setAlignment(Qt.AlignCenter)
        self.streak_label.setFont(QFont("Segoe UI", 9))
        self.streak_label.setStyleSheet("color: #ABB2BF; border: none; margin-top: 10px;")
        card_layout.addWidget(self.streak_label)

        # --- Boutons de Contrôle ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        self.start_btn = QPushButton("▶ DÉMARRER")
        self.start_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #98C379;
                color: #1E222B;
                border-radius: 12px;
                padding: 12px;
                border: none;
            }
            QPushButton:hover {
                background-color: #B5E896;
            }
        """)
        self.start_btn.clicked.connect(self.toggle_timer)

        self.reset_btn = QPushButton("🔄 RESET")
        self.reset_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #3E4451;
                color: #ECEFF4;
                border-radius: 12px;
                padding: 12px;
                border: none;
            }
            QPushButton:hover {
                background-color: #4B5263;
            }
        """)
        self.reset_btn.clicked.connect(self.reset_timer)

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.reset_btn)
        card_layout.addLayout(btn_layout)

        # --- Sélecteur de Modes ---
        mode_layout = QHBoxLayout()
        
        self.work_mode_btn = QPushButton("Travail")
        self.short_break_btn = QPushButton("Pause courte")
        self.long_break_btn = QPushButton("Pause longue")

        for btn, mode in [
            (self.work_mode_btn, "WORK"),
            (self.short_break_btn, "SHORT_BREAK"),
            (self.long_break_btn, "LONG_BREAK")
        ]:
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFont(QFont("Segoe UI", 8, QFont.Bold))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #ABB2BF;
                    border: 1px solid #3E4451;
                    border-radius: 8px;
                    padding: 6px;
                }
                QPushButton:hover {
                    border-color: #61AFEF;
                    color: #ECEFF4;
                }
            """)
            btn.clicked.connect(lambda _, m=mode: self.switch_mode(m))

        mode_layout.addWidget(self.work_mode_btn)
        mode_layout.addWidget(self.short_break_btn)
        mode_layout.addWidget(self.long_break_btn)

        card_layout.addLayout(mode_layout)

        main_layout.addWidget(card)

    def update_progress_bar_style(self, color_hex):
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #1E222B;
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {color_hex};
                border-radius: 4px;
            }}
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
            self.start_btn.setStyleSheet(self.start_btn.styleSheet().replace("#E06C75", "#98C379"))
        else:
            self.timer.start(1000)
            self.is_running = True
            self.start_btn.setText("⏸ PAUSE")
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background-color: #E06C75;
                    color: #1E222B;
                    border-radius: 12px;
                    padding: 12px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #E5C07B;
                }
            """)

    def reset_timer(self):
        self.timer.stop()
        self.is_running = False
        self.switch_mode(self.current_mode)
        self.start_btn.setText("▶ DÉMARRER")

    def switch_mode(self, mode):
        self.current_mode = mode
        self.timer.stop()
        self.is_running = False

        if mode == "WORK":
            self.time_left = WORK_TIME
            self.status_label.setText("🎯 SESSION DE TRAVAIL")
            self.status_label.setStyleSheet("color: #98C379; background-color: rgba(152, 195, 121, 0.15); border-radius: 12px; padding: 6px 12px; border: none;")
            self.update_progress_bar_style("#98C379")
            color_accent = "#98C379"
        elif mode == "SHORT_BREAK":
            self.time_left = SHORT_BREAK
            self.status_label.setText("☕ PAUSE COURTE")
            self.status_label.setStyleSheet("color: #61AFEF; background-color: rgba(97, 175, 239, 0.15); border-radius: 12px; padding: 6px 12px; border: none;")
            self.update_progress_bar_style("#61AFEF")
            color_accent = "#61AFEF"
        elif mode == "LONG_BREAK":
            self.time_left = LONG_BREAK
            self.status_label.setText("🌿 PAUSE LONGUE")
            self.status_label.setStyleSheet("color: #C678DD; background-color: rgba(198, 120, 221, 0.15); border-radius: 12px; padding: 6px 12px; border: none;")
            self.update_progress_bar_style("#C678DD")
            color_accent = "#C678DD"

        self.total_time = self.time_left
        self.start_btn.setText("▶ DÉMARRER")
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color_accent};
                color: #1E222B;
                border-radius: 12px;
                padding: 12px;
                border: none;
            }}
            QPushButton:hover {{
                opacity: 0.8;
            }}
        """)
        self.refresh_display()

    def handle_session_complete(self):
        if self.current_mode == "WORK":
            self.completed_pomodoros += 1
            self.streak_label.setText(f"🍅 Pomodoros complétés : {self.completed_pomodoros}")
            if self.completed_pomodoros % 4 == 0:
                self.switch_mode("LONG_BREAK")
            else:
                self.switch_mode("SHORT_BREAK")
        else:
            self.switch_mode("WORK")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    timer = CosyFocusTimer()
    timer.show()
    sys.exit(app.exec_())