from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, Qt
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QLabel,
                               QMainWindow, QMenuBar, QPushButton, QStatusBar,
                               QTableWidget, QWidget, QHeaderView, QTableWidgetItem, QAbstractItemView, QAbstractItemView)
from read_meteo import *

#Klasa ui otrzymana z designera + parę dorobionych rzeczy
class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(u"MainWindow")
        MainWindow.setFixedSize(800, 560)
        self.centralwidget = QWidget(MainWindow)
        self.frame = QFrame(self.centralwidget)
        self.frame.setGeometry(QRect(0, 0, 791, 71))
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)

        self.yearComboBox = QComboBox(self.frame)
        self.yearComboBox.setGeometry(QRect(10, 20, 71, 31))

        self.monthComboBox = QComboBox(self.frame)
        self.monthComboBox.setGeometry(QRect(85, 20, 60, 31))

        self.voivodeshipComboBox = QComboBox(self.frame)
        self.voivodeshipComboBox.setGeometry(QRect(150, 20, 150, 31))

        self.measurComboBox = QComboBox(self.frame)
        self.measurComboBox.setGeometry(QRect(305, 20, 210, 31))

        self.searchButton = QPushButton(self.frame)
        self.searchButton.setGeometry(QRect(620, 10, 161, 51))

        self.frame_2 = QFrame(self.centralwidget)
        self.frame_2.setGeometry(QRect(0, 80, 791, 461))
        self.tableWidget = QTableWidget(self.frame_2)
        self.tableWidget.setGeometry(QRect(10, 10, 771, 441))
        self.tableWidget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        MainWindow.setStatusBar(self.statusbar)

        #możliwe województwa do wyboru, na razie w ten sposób zrobione, później można to zmienić na pobrane z pliku
        voivodeships = [
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

        self.retranslateUi(MainWindow)
        QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Meteo Data Browser", None))
        self.searchButton.setText(QCoreApplication.translate("MainWindow", u"Szukaj", None))

#Główna alpikacja
class MyApp(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        #Nadanie ilości kolumn i ich nazw
        self.ui.tableWidget.setColumnCount(2)
        self.ui.tableWidget.setHorizontalHeaderLabels(["Data", "Średnia"])
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        #pobranie dostępnych lat z bazy
        self.dictYearMonths = get_available_months(self.db)
        self.ui.yearComboBox.currentTextChanged.connect(self.update_months)

        #Uruchomienie szukania
        self.ui.searchButton.clicked.connect(self.on_search_button_clicked)

        #dodanie miesięcy i lat
        self.ui.yearComboBox.clear()
        for year in sorted(self.dictYearMonths.keys(), reverse=True):
            self.ui.yearComboBox.addItem(year)

        if self.ui.yearComboBox.count() > 0:
            self.update_months(self.ui.yearComboBox.currentText())

    #Updatujemy miesiące przy zmianie roku
    def update_months(self, selected_year):
        self.ui.monthComboBox.clear()
        if selected_year in self.dictYearMonths:
            for month in sorted(self.dictYearMonths[selected_year], reverse=True):
                self.ui.monthComboBox.addItem(month)

    #pobieramy aktualny kod danych aby dla niego później wyszukać dane
    def get_measurement_type(self):
        return self.ui.measurComboBox.currentData()

    #To samo dla województw (nie zrobione TODO)
    def get_selected_voivodeship(self):
        return self.ui.voivodeshipComboBox.currentData()

    #Pobieranie danych i wyświetlenie w tabelce
    def on_search_button_clicked(self):
        year = self.ui.yearComboBox.currentText()
        month = self.ui.monthComboBox.currentText()

        collection_name = f"{month}_{year}"
        measurment_code = self.ui.measurComboBox.currentData()

        result = get_data_by_measurment(self.db, collection_name, measurment_code)

        if result is not None:
            self.ui.tableWidget.setRowCount(0)

            for index, row in result.iterrows():
                row_position = self.ui.tableWidget.rowCount()
                self.ui.tableWidget.insertRow(row_position)

                # Kolumna 0: Dzień
                self.ui.tableWidget.setItem(row_position, 0, QTableWidgetItem(str(row['Dzien'])))

                # Kolumna 1: Średnia
                self.ui.tableWidget.setItem(row_position, 1, QTableWidgetItem(str(row['Srednia'])))
        else:
            print("Nie znaleziono danych lub wystąpił błąd.")