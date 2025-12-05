from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QLineEdit, QPushButton, QVBoxLayout, QWidget, QLabel, QComboBox
import g4f
import sys
import re
import sqlite3
from datetime import datetime

# ====================== НАСТРОЙКИ ======================
ANSWER_MAX_CHARS = 300

LANGUAGES = {
    "ru": {
        "title": "ИИ-Помощник для Диагностики",
        "label": "ИИ-Помощник: Введите симптомы пациента",
        "placeholder": "Например: Болит горло, температура 37.5, насморк",
        "button": "Получить диагноз",
        "welcome": "Привет! Введите симптомы пациента, и я предложу возможные диагнозы.",
        "empty_input": "ИИ-Помощник: Пожалуйста, введите симптомы.",
        "doctor_prefix": "Врач",
        "assistant_prefix": "ИИ-Помощник",
        "disclaimer": "Это не замена врачу, проконсультируйтесь со специалистом.",
        "system_prompt": """
        Ты ИИ-помощник для врачей, анализирующий симптомы и предлагающий до 3 возможных диагнозов. 
        Отвечай кратко, структурированно (список диагнозов), избегай окончательных выводов. 
        В конце каждого ответа обязательно добавляй: "Это не замена врачу, проконсультируйтесь со специалистом."
        """
    },
    "kk": {
        "title": "Диагнозға арналған ИИ-Көмекші",
        "label": "ИИ-Көмекші: Пациенттің белгілерін енгізіңіз",
        "placeholder": "Мысалы: Көмей ауырады, температура 37.5, мұрын ағады",
        "button": "Диагноз алу",
        "welcome": "Сәлем! Пациенттің белгілерін енгізіңіз, мен мүмкін диагноздарды ұсынамын.",
        "empty_input": "ИИ-Көмекші: Белгілерді енгізіңіз.",
        "doctor_prefix": "Дәрігер",
        "assistant_prefix": "ИИ-Көмекші",
        "disclaimer": "Бұл дәрігердің орнын баспайды, маманмен кеңесіңіз.",
        "system_prompt": """
        Сен дәрігерлерге арналған ИИ-көмекшісің, белгілерді талдап, 3-ке дейін мүмкін диагноздарды ұсынасың. 
        Жауаптарың қысқа, құрылымдалған (диагноздар тізімі) болсын, нақты қорытындылардан аулақ бол. 
        Әр жауаптың соңына міндетті түрде мына мәтінді қос: "Бұл дәрігердің орнын баспайды, маманмен кеңесіңіз."
        """
    }
}

current_lang = "ru"

# ================== ВСПОМОГАТЕЛЬНЫЕ ==================
def clean_text(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"`[^`]*`", "", text)
    text = re.sub(r"[*_~#>]", "", text)
    text = re.sub(r":[a-zA-Z0-9_+\-]+:", "", text)
    text = re.sub(r"[^\w\s.,!?-]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def short_answer(txt: str) -> str:
    txt = clean_text(txt)
    if len(txt) > ANSWER_MAX_CHARS:
        txt = txt[:ANSWER_MAX_CHARS].rsplit(" ", 1)[0] + "..."
    return txt

def log_request(symptoms: str, diagnosis: str):
    conn = sqlite3.connect('diagnoses.db')
    c = conn.cursor()
    c.execute(
        'CREATE TABLE IF NOT EXISTS logs (symptoms TEXT, diagnosis TEXT, timestamp TEXT)'
    )
    c.execute(
        'INSERT INTO logs VALUES (?, ?, ?)',
        (symptoms, diagnosis, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )
    conn.commit()
    conn.close()

# ================== ГЛАВНОЕ ОКНО ==================
class DiagnosisApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.lang = current_lang

        self.setWindowTitle(LANGUAGES[self.lang]["title"])
        self.setGeometry(100, 100, 600, 400)

        # Зеленая тема
        self.setStyleSheet("""
            QWidget {
                background-color: #2E7D32;
                color: #FFFFFF;
            }
            QTextEdit, QLineEdit {
                background-color: #4CAF50;
                border: 1px solid #81C784;
                color: #FFFFFF;
            }
            QPushButton {
                background-color: #66BB6A;
                color: #FFFFFF;
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #A5D6A7;
            }
            QComboBox {
                background-color: #66BB6A;
                color: #FFFFFF;
                border: 1px solid #81C784;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Переключатель языка
        self.lang_selector = QComboBox()
        self.lang_selector.addItems(["Русский (ru)", "Қазақша (kk)"])
        self.lang_selector.currentTextChanged.connect(self.change_language)
        layout.addWidget(self.lang_selector)

        self.label = QLabel(LANGUAGES[self.lang]["label"], self)
        self.label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.label)

        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        layout.addWidget(self.chat_area)

        self.entry = QLineEdit()
        self.entry.setPlaceholderText(LANGUAGES[self.lang]["placeholder"])
        layout.addWidget(self.entry)

        self.send_button = QPushButton(LANGUAGES[self.lang]["button"])
        self.send_button.clicked.connect(self.send_message)
        layout.addWidget(self.send_button)

        self.chat_area.append(LANGUAGES[self.lang]["welcome"])

    def change_language(self, lang_text):
        if "Қазақша" in lang_text:
            self.lang = "kk"
        else:
            self.lang = "ru"

        self.setWindowTitle(LANGUAGES[self.lang]["title"])
        self.label.setText(LANGUAGES[self.lang]["label"])
        self.entry.setPlaceholderText(LANGUAGES[self.lang]["placeholder"])
        self.send_button.setText(LANGUAGES[self.lang]["button"])

        self.chat_area.clear()
        self.chat_area.append(LANGUAGES[self.lang]["welcome"])

    def send_message(self):
        user_input = self.entry.text().strip()
        if not user_input:
            self.chat_area.append(LANGUAGES[self.lang]["empty_input"])
            return

        doctor_prefix = LANGUAGES[self.lang]["doctor_prefix"]
        assistant_prefix = LANGUAGES[self.lang]["assistant_prefix"]
        disclaimer = LANGUAGES[self.lang]["disclaimer"]

        self.chat_area.append(f"{doctor_prefix}: {user_input}")
        self.entry.clear()

        try:
            response = g4f.ChatCompletion.create(
                model=g4f.models.default,
                messages=[
                    {"role": "system", "content": LANGUAGES[self.lang]["system_prompt"]},
                    {"role": "user", "content": f"Симптомы: {user_input}"}
                ]
            )

            if isinstance(response, dict) and "choices" in response:
                raw_answer = response["choices"][0]["message"]["content"]
            else:
                raw_answer = str(response)

            answer = short_answer(raw_answer)

            if disclaimer not in answer:
                answer = answer.rstrip(". ") + ". " + disclaimer

            log_request(user_input, answer)

        except Exception as e:
            print("Ошибка g4f:", e)
            answer = f"Извините, произошла ошибка. {disclaimer}"
            log_request(user_input, "Ошибка")

        self.chat_area.append(f"{assistant_prefix}: {answer}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DiagnosisApp()
    window.show()
    sys.exit(app.exec_())

