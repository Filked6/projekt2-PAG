from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, Qt, QThread, Signal
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QLabel,
                               QMainWindow, QMenuBar, QPushButton, QStatusBar,
                               QTableWidget, QWidget, QHeaderView, QTableWidgetItem)
from read_meteo import *
import io
import folium
from wizard import Ui_MainWindow, LottieWindow
import json

class DataWorker(QThread):
    finished_data = Signal(object)

    def __init__(self, db, collection_name, measurment_code):
        super().__init__()
        self.db = db
        self.collection_name = collection_name
        self.measurment_code = measurment_code

    def run(self):
        try:
            result = get_data_by_measurment(self.db, self.collection_name, self.measurment_code)
            self.finished_data.emit(result)
        except Exception as e:
            print(f"Błąd bazy w wątku: {e}")
            self.finished_data.emit(None)

class MyApp(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.okno_lottie = LottieWindow("loading.json")
        self.woj_geojson = None
        try:
            with open("gadm41_POL_1.json", "r", encoding="utf-8") as f:
                self.woj_geojson = json.load(f)
            print("Pomyślnie wczytano granice z GeoJSON.")
        except Exception as e:
            print(f"Nie udało się wczytać granic. {e}")

        self.voivodeship_coords = {
            "00": {"lat": 52.00, "lon": 19.00, "zoom": 6},  # Cała Polska
            "02": {"lat": 51.10, "lon": 16.40, "zoom": 8},  # Dolnośląskie
            "04": {"lat": 53.05, "lon": 18.50, "zoom": 8},  # Kujawsko-pomorskie
            "06": {"lat": 51.25, "lon": 22.90, "zoom": 8},  # Lubelskie
            "08": {"lat": 52.20, "lon": 15.30, "zoom": 8},  # Lubuskie
            "10": {"lat": 51.60, "lon": 19.40, "zoom": 8},  # Łódzkie
            "12": {"lat": 49.90, "lon": 20.30, "zoom": 8},  # Małopolskie
            "14": {"lat": 52.35, "lon": 21.05, "zoom": 8},  # Mazowieckie
            "16": {"lat": 50.65, "lon": 17.90, "zoom": 8},  # Opolskie
            "18": {"lat": 50.05, "lon": 22.10, "zoom": 8},  # Podkarpackie
            "20": {"lat": 53.10, "lon": 23.00, "zoom": 8},  # Podlaskie
            "22": {"lat": 54.20, "lon": 18.00, "zoom": 8},  # Pomorskie
            "24": {"lat": 50.35, "lon": 19.00, "zoom": 8},  # Śląskie
            "26": {"lat": 50.80, "lon": 20.65, "zoom": 8},  # Świętokrzyskie
            "28": {"lat": 53.80, "lon": 20.80, "zoom": 8},  # Warmińsko-mazurskie
            "30": {"lat": 52.25, "lon": 17.10, "zoom": 8},  # Wielkopolskie
            "32": {"lat": 53.60, "lon": 15.60, "zoom": 8},  # Zachodniopomorskie
        }

        self.load_map()

        # Konfiguracja tabeli
        self.ui.tableWidget.setColumnCount(7)
        self.ui.tableWidget.setHorizontalHeaderLabels(["Data", "Śr. dzienna", "śr. nocna", "Mediana dzienna", "Mediana nocna", "śr. ob. dzienna", "śr. ob. nocna"])
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Dane startowe
        self.dictYearMonths = get_available_months(self.db)
        self.ui.yearComboBox.currentTextChanged.connect(self.update_months)
        self.ui.searchButton.clicked.connect(self.on_search_button_clicked)

        self.ui.yearComboBox.clear()
        for year in sorted(self.dictYearMonths.keys(), reverse=True):
            self.ui.yearComboBox.addItem(year)

        if self.ui.yearComboBox.count() > 0:
            self.update_months(self.ui.yearComboBox.currentText())

    def add_borders_to_map(self, m, width):
        if self.woj_geojson:
            folium.GeoJson(
                self.woj_geojson,
                name="Granice województw",
                style_function=lambda x: {
                    'fillColor': '#00000000',  # Przezroczyste
                    'color': 'black',  # Kolor linii
                    'weight': width,  # Grubość
                    'opacity': 0.7
                },
                tooltip=folium.GeoJsonTooltip(fields=['NAME_1'], aliases=['Województwo:'])
            ).add_to(m)

    def load_map(self):
        start_position = [52.00, 19.00]
        start_zoom = 6
        m = folium.Map(location=start_position, zoom_start=start_zoom)
        self.add_borders_to_map(m, 1)
        data = io.BytesIO()
        m.save(data, close_file=False)
        self.ui.mapView.setHtml(data.getvalue().decode())

    def update_map_view(self):
        code = self.ui.voivodeshipComboBox.currentData()

        if code in self.voivodeship_coords:
            coords = self.voivodeship_coords[code]
            m = folium.Map(location=[coords["lat"], coords["lon"]], zoom_start=coords["zoom"])
            if code == "00":
                self.add_borders_to_map(m, 1)
            else:
                self.add_borders_to_map(m, 2)

            data = io.BytesIO()
            m.save(data, close_file=False)
            self.ui.mapView.setHtml(data.getvalue().decode())

    def update_months(self, selected_year):
        self.ui.monthComboBox.clear()
        if selected_year in self.dictYearMonths:
            for month in sorted(self.dictYearMonths[selected_year], reverse=True):
                self.ui.monthComboBox.addItem(month)

    def on_search_button_clicked(self):
        self.okno_lottie.show()

        self.ui.searchButton.setEnabled(False)

        year = self.ui.yearComboBox.currentText()
        month = self.ui.monthComboBox.currentText()
        collection_name = f"{month}_{year}"
        measurment_code = self.ui.measurComboBox.currentData()

        # Uruchomienie wątku
        self.worker = DataWorker(self.db, collection_name, measurment_code)
        self.worker.finished_data.connect(self.handle_result)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    def handle_result(self, result):
        self.okno_lottie.close()
        self.ui.searchButton.setEnabled(True)

        if result is not None:
            self.ui.tableWidget.setRowCount(0)
            for index, row in result.iterrows():
                row_position = self.ui.tableWidget.rowCount()
                self.ui.tableWidget.insertRow(row_position)

                def get_formatted_str(col_name):
                    val = row[col_name]
                    if pd.notna(val):
                        return f"{val:.2f}"
                    return "-"

                def create_item(text, align_right=True):
                    item = QTableWidgetItem(text)
                    if align_right:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    else:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    return item

                self.ui.tableWidget.setItem(row_position, 0, create_item(str(row['Dzien']), align_right=False))

                self.ui.tableWidget.setItem(row_position, 1, create_item(get_formatted_str('Srednia_Dzien')))
                self.ui.tableWidget.setItem(row_position, 2, create_item(get_formatted_str('Srednia_Noc')))
                self.ui.tableWidget.setItem(row_position, 3, create_item(get_formatted_str('Mediana_Dzien')))
                self.ui.tableWidget.setItem(row_position, 4, create_item(get_formatted_str('Mediana_Noc')))
                self.ui.tableWidget.setItem(row_position, 5, create_item(get_formatted_str('Srednia_Obcinana_Dzien')))
                self.ui.tableWidget.setItem(row_position, 6, create_item(get_formatted_str('Srednia_Obcinana_Noc')))

            self.update_map_view()
        else:
            print("Błąd: Nie otrzymano danych.")