from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, Qt, QThread, Signal
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QLabel,
                               QMainWindow, QMenuBar, QPushButton, QStatusBar,
                               QTableWidget, QWidget, QHeaderView, QTableWidgetItem)
from read_meteo import *
import io
import folium
from wizard import Ui_MainWindow, LottieWindow

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
            print(f"Błąd bazy: {e}")
            self.finished_data.emit(None)

class MyApp(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.okno_lottie = LottieWindow("loading.json")
        self.load_map()

        # Konfiguracja tabeli
        self.ui.tableWidget.setColumnCount(2)
        self.ui.tableWidget.setHorizontalHeaderLabels(["Data", "Średnia"])
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

    def load_map(self):
        start_position = [52.0, 19.0]
        start_zoom = 6
        m = folium.Map(location=start_position, zoom_start=start_zoom)
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
                self.ui.tableWidget.setItem(row_position, 0, QTableWidgetItem(str(row['Dzien'])))
                self.ui.tableWidget.setItem(row_position, 1, QTableWidgetItem(str(row['Srednia'])))
        else:
            print("Błąd: Nie otrzymano danych.")