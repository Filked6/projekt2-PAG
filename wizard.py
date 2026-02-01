import os
from PySide6.QtCore import QCoreApplication, QMetaObject, Qt
from PySide6.QtWidgets import (QComboBox, QFrame,QMenuBar, QPushButton, QStatusBar,
                               QTableWidget, QWidget,
                               QAbstractItemView, QVBoxLayout, QHBoxLayout)
from PySide6.QtWebEngineWidgets import QWebEngineView
from start import redis_con
from redis_explore import *

#Klasa ui otrzymana z designera + parę dorobionych rzeczy
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1400, 800)

        self.centralwidget = QWidget(MainWindow)
        self.main_layout = QVBoxLayout(self.centralwidget)

        self.frame = QFrame(self.centralwidget)
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)

        self.top_panel_layout = QHBoxLayout(self.frame)
        self.top_panel_layout.setContentsMargins(10, 10, 10, 10)

        self.yearComboBox = QComboBox(self.frame)
        self.monthComboBox = QComboBox(self.frame)

        self.voivodeshipComboBox = QComboBox(self.frame)
        self.voivodeshipComboBox.currentIndexChanged.connect(self.update_districts)

        self.districtComboBox = QComboBox(self.frame)
        self.districtComboBox.setFixedWidth(200)
        self.measurComboBox = QComboBox(self.frame)
        self.searchButton = QPushButton(self.frame)

        self.top_panel_layout.addWidget(self.yearComboBox)
        self.top_panel_layout.addWidget(self.monthComboBox)
        self.top_panel_layout.addWidget(self.voivodeshipComboBox)
        self.top_panel_layout.addWidget(self.districtComboBox)
        self.top_panel_layout.addWidget(self.measurComboBox, stretch=1)
        self.top_panel_layout.addWidget(self.searchButton)

        self.main_layout.addWidget(self.frame)

        self.tablemap_layout = QHBoxLayout()

        self.tableWidget = QTableWidget(self.centralwidget)
        self.tableWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tablemap_layout.addWidget(self.tableWidget, stretch=5)

        self.mapView = QWebEngineView(self.centralwidget)
        self.mapView.setContentsMargins(2, 2, 2, 2)
        self.tablemap_layout.addWidget(self.mapView, stretch=3)
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
        r = redis_con()
        voivodeships = get_voivodeships_dict(r)
        for teryt, name in voivodeships.items():
            self.voivodeshipComboBox.addItem(name, teryt)

        self.all_districts = get_districts_grouped(r)
        self.update_districts()

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

    def update_districts(self):
        self.districtComboBox.clear()

        current_voivodeship_code = self.voivodeshipComboBox.currentData()

        if current_voivodeship_code == "00" or current_voivodeship_code is None:
            self.districtComboBox.addItem("-", None)
            self.districtComboBox.setEnabled(False)

        else:
            self.districtComboBox.setEnabled(True)
            districts_for_voivodeship = self.all_districts.get(current_voivodeship_code, {})

            self.districtComboBox.addItem(f"Wszystkie powiaty", "all")

            for d_id, d_name in districts_for_voivodeship.items():
                self.districtComboBox.addItem(d_name, d_id)

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

def get_voivodeships_dict(r):
    geo_data = get_geojson(r, "woj")
    wojewodztwa = {}

    for feature in geo_data['features']:
        teryt = feature.get('id')

        props = feature['properties']
        nazwa = props.get('name')

        if teryt and nazwa:
            wojewodztwa[teryt] = nazwa.title()

    wojewodztwa["00"] = "Cała Polska"

    return dict(sorted(wojewodztwa.items()))


def get_districts_grouped(r):
    geo_data = get_geojson(r, "powiat")

    grouped_districts = {}

    for feature in geo_data['features']:
        p_id = feature.get('id')
        props = feature['properties']
        name = props.get('name')
        parent = props.get('parent')

        if p_id and name and parent:
            if parent not in grouped_districts:
                grouped_districts[parent] = {}

            grouped_districts[parent][p_id] = name.title()

    for parent in grouped_districts:
        grouped_districts[parent] = dict(sorted(grouped_districts[parent].items(), key=lambda item: item[1]))

    return grouped_districts