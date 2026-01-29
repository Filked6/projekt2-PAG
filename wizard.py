import sys
import io
import folium
import os
from PySide6.QtCore import QCoreApplication, QMetaObject, Qt
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame,
                               QMainWindow, QMenuBar, QPushButton, QStatusBar,
                               QTableWidget, QWidget, QHeaderView, QLabel,
                               QAbstractItemView, QVBoxLayout, QHBoxLayout)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtGui import QMovie, QColor, QPalette

#Klasa ui otrzymana z designera + parę dorobionych rzeczy
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1200, 800)

        self.centralwidget = QWidget(MainWindow)
        self.main_layout = QVBoxLayout(self.centralwidget)

        self.frame = QFrame(self.centralwidget)
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)

        self.top_panel_layout = QHBoxLayout(self.frame)
        self.top_panel_layout.setContentsMargins(10, 10, 10, 10)

        self.yearComboBox = QComboBox(self.frame)
        self.monthComboBox = QComboBox(self.frame)
        self.voivodeshipComboBox = QComboBox(self.frame)
        self.measurComboBox = QComboBox(self.frame)
        self.searchButton = QPushButton(self.frame)

        self.top_panel_layout.addWidget(self.yearComboBox)
        self.top_panel_layout.addWidget(self.monthComboBox)
        self.top_panel_layout.addWidget(self.voivodeshipComboBox)
        self.top_panel_layout.addWidget(self.measurComboBox, stretch=1)
        self.top_panel_layout.addWidget(self.searchButton)

        self.main_layout.addWidget(self.frame)

        self.tablemap_layout = QHBoxLayout()

        self.tableWidget = QTableWidget(self.centralwidget)
        self.tableWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tablemap_layout.addWidget(self.tableWidget, stretch = 5)

        self.mapView = QWebEngineView(self.centralwidget)
        self.mapView.setContentsMargins(2, 2, 2, 2)
        #Generowanie mapy
        self.tablemap_layout.addWidget(self.mapView, stretch = 3)
        self.main_layout.addLayout(self.tablemap_layout)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        MainWindow.setStatusBar(self.statusbar)

        self.add_data_to_combo()

        self.retranslateUi(MainWindow)
        QMetaObject.connectSlotsByName(MainWindow)

    def add_data_to_combo(self):
        #możliwe województwa do wyboru, na razie w ten sposób zrobione, później można to zmienić na pobrane z pliku
        voivodeships = [
            ("Cała Polska", "00"),
            ("Dolnośląskie", "02"), ("Kujawsko-pomorskie", "04"),
            ("Lubelskie", "06"), ("Lubuskie", "08"),
            ("Łódzkie", "10"), ("Małopolskie", "12"),
            ("Mazowieckie", "14"), ("Opolskie", "16"),
            ("Podkarpackie", "18"), ("Podlaskie", "20"),
            ("Pomorskie", "22"), ("Śląskie", "24"),
            ("Świętokrzyskie", "26"), ("Warmińsko-mazurskie", "28"),
            ("Wielkopolskie", "30"), ("Zachodniopomorskie", "32")
        ]
        for name, teryt in sorted(voivodeships):
            self.voivodeshipComboBox.addItem(name, teryt)

        #Możliwe typy danych wraz z ich kodami
        measurement_types = [
            ("Temperatura powietrza", "B00300S"), ("Temperatura gruntu", "B00305A"),
            ("Kierunek wiatru", "B00202A"), ("Średnia prędkość wiatru", "B00702A"),
            ("Maksymalna prędkość", "B00703A"), ("Suma opadu 10-minutowego", "B00608S"),
            ("Suma opadu dobowego", "B00604S"), ("Suma opadu godzinnego", "B00606S"),
            ("Wilgotność względna powietrza", "B00802A"),
            ("Największy poryw w okresie 10m", "B00714A"), ("Zapas wody w śniegu", "B00910A")
        ]
        for name, id in measurement_types:
            self.measurComboBox.addItem(name, id)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Meteo Data Browser", None))
        self.searchButton.setText(QCoreApplication.translate("MainWindow", u"Szukaj", None))

class LottieWindow(QWidget):
    def __init__(self, json_path):
        super().__init__()
        self.setFixedSize(300, 300)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        json_content = "null"
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    json_content = f.read()
            except Exception as e:
                print(f"Błąd odczytu pliku JSON: {e}")
        else:
            print(f"Nie znaleziono pliku: {json_path}")

        # Widget przeglądarki
        self.browser = QWebEngineView()
        self.browser.page().setBackgroundColor(Qt.transparent)
        self.browser.setStyleSheet("background: transparent;")

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://unpkg.com/@lottiefiles/lottie-player@latest/dist/lottie-player.js"></script>
            <style>
                body {{ margin: 0; padding: 0; overflow: hidden; background: transparent; }}
                lottie-player {{ width: 100%; height: 100%; }}
            </style>
        </head>
        <body>
            <lottie-player id="anim" background="transparent" speed="1" loop autoplay></lottie-player>
            <script>
                const data = {json_content};
                const player = document.getElementById("anim");
                if(data) {{
                    player.load(data);
                }}
            </script>
        </body>
        </html>
        """
        self.browser.setHtml(html)
        layout.addWidget(self.browser)
