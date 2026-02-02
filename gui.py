from PySide6.QtCore import  Qt, QThread, Signal, QUrl
from PySide6.QtWidgets import (QApplication, QMainWindow, QHeaderView, QTableWidgetItem)
from read_meteo import *
import io
import folium
from wizard import Ui_MainWindow, LottieWindow
import json
from redis_explore import list_facilities_by_powiat, list_facilities_by_woj, list_all_facilities

# Wątek do pracy na danych
class DataWorker(QThread):
    finished_data = Signal(object, object)

    def __init__(self, db, collection_name, measurment_code, station_ids=None):
        super().__init__()
        self.db = db
        self.collection_name = collection_name
        self.measurment_code = measurment_code
        self.station_ids = station_ids

    def run(self):
        try:
            # Rozpakowujemy dwa wyniki z read_meteo
            table_data, map_values = get_data_by_measurment(
                self.db,
                self.collection_name,
                self.measurment_code,
                self.station_ids
            )
            self.finished_data.emit(table_data, map_values)
        except Exception as e:
            print(f"Błąd bazy w wątku: {e}") #żeby się aplikacj nie wywalała przy błędach
            self.finished_data.emit(None, None)


class MyApp(QMainWindow):
    def __init__(self, db, r):
        super().__init__()
        self.db = db
        self.r = r
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.okno_lottie = LottieWindow("loading.json")  #animacja ładowania 

        self.voivodeship_data = None
        self.current_stations = []
        self.current_map_values = {}

        # wczytywanie województw z pliku
        try:
            with open("gadm41_POL_1.json", "r", encoding="utf-8") as f:
                self.voivodeship_data = json.load(f)
        except Exception as e:
            print(f"BŁĄD GADM: {e}")
            self.voivodeship_data = None

        self.voivodeship_coords = {
            "00": {"lat": 52.00, "lon": 19.00, "zoom": 6},
            "02": {"lat": 51.10, "lon": 16.40, "zoom": 8},
            "04": {"lat": 53.05, "lon": 18.50, "zoom": 8},
            "06": {"lat": 51.25, "lon": 22.90, "zoom": 8},
            "08": {"lat": 52.20, "lon": 15.30, "zoom": 8},
            "10": {"lat": 51.60, "lon": 19.40, "zoom": 8},
            "12": {"lat": 49.90, "lon": 20.30, "zoom": 8},
            "14": {"lat": 52.35, "lon": 21.05, "zoom": 8},
            "16": {"lat": 50.65, "lon": 17.90, "zoom": 8},
            "18": {"lat": 50.05, "lon": 22.10, "zoom": 8},
            "20": {"lat": 53.10, "lon": 23.00, "zoom": 8},
            "22": {"lat": 54.20, "lon": 18.00, "zoom": 8},
            "24": {"lat": 50.35, "lon": 19.00, "zoom": 8},
            "26": {"lat": 50.80, "lon": 20.65, "zoom": 8},
            "28": {"lat": 53.80, "lon": 20.80, "zoom": 8},
            "30": {"lat": 52.25, "lon": 17.10, "zoom": 8},
            "32": {"lat": 53.60, "lon": 15.60, "zoom": 8},
        }

        self.load_map()

        # tabelka
        self.ui.tableWidget.setColumnCount(7)
        self.ui.tableWidget.setHorizontalHeaderLabels(
            ["Data", "Śr. dzienna", "śr. nocna", "Mediana dzienna", "Mediana nocna", "śr. ob. dzienna",
             "śr. ob. nocna"])
        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.dictYearMonths = get_available_months(self.db)
        self.ui.yearComboBox.currentTextChanged.connect(self.update_months)
        self.ui.searchButton.clicked.connect(self.on_search_button_clicked)

        # wybór daty
        self.ui.yearComboBox.clear()
        for year in sorted(self.dictYearMonths.keys(), reverse=True):
            self.ui.yearComboBox.addItem(year)
        if self.ui.yearComboBox.count() > 0:
            self.update_months(self.ui.yearComboBox.currentText())

    # warstwa województw
    def add_geojson_layer(self, m, geo_data):
        if not geo_data: return
        style = {'color': 'black', 'weight': 2, 'fillColor': '#00000000'}
        folium.GeoJson(
            geo_data, name="Województwa", style_function=lambda x: style,
            tooltip=folium.GeoJsonTooltip(fields=['NAME_1'], aliases=['Województwo:'])
        ).add_to(m)

    # warstwa stacji
    def add_stations_layer(self, m):
        if not self.current_stations:
            return
        count = 0

        for station in self.current_stations:
            sid = station.get('id')

            if not sid or sid not in self.current_map_values:
                continue

            val = self.current_map_values[sid]
            value_info = f"{val:.2f}"

            coords = station.get('geometry', {}).get('coordinates')
            props = station.get('properties', {})
            ident = props.get('name', 'Stacja') #identyfikatoe
            name = props.get('name1', 'Stacja') #nazwa

            tooltip_text = f"<b>{name}</b><br>id: {ident}<br>Średnia: {value_info}"

            if coords:
                lat, lon = coords[1], coords[0]

                # Rysujemy SZPILECZKĘ 
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=4,          
                    color='black',    
                    weight=1,
                    fill=True,
                    fill_color='red',
                    fill_opacity=1.0,
                    tooltip=tooltip_text,   # Tooltip
                    popup=tooltip_text      # Popup
                ).add_to(m)

                count += 1

        print(f"Narysowano {count} szpileczek na mapie.")

    #zapis mapy do html do wyświetlenia
    def save_and_show_map(self, m):
        data = io.BytesIO()
        m.save(data, close_file=False)
        self.ui.mapView.setHtml(data.getvalue().decode(), QUrl("http://localhost"))

    #pierwsze wczytanie mapy
    def load_map(self):
        start_position = [52.00, 19.00]
        start_zoom = 6
        m = folium.Map(location=start_position, zoom_start=start_zoom)
        self.add_geojson_layer(m, self.voivodeship_data)
        self.save_and_show_map(m)

    #aktualizacja mapy
    def update_map_view(self):
        code = self.ui.voivodeshipComboBox.currentData()
        coords = self.voivodeship_coords.get(code, self.voivodeship_coords["00"])

        m = folium.Map(location=[coords["lat"], coords["lon"]], zoom_start=coords["zoom"])

        self.add_geojson_layer(m, self.voivodeship_data)
        self.add_stations_layer(m)

        self.save_and_show_map(m)

    # aktualizacja miesięcy po wyborze roku
    def update_months(self, selected_year):
        self.ui.monthComboBox.clear()
        if selected_year in self.dictYearMonths:
            for month in sorted(self.dictYearMonths[selected_year], reverse=True):
                self.ui.monthComboBox.addItem(month)

    # przycisk 'szukaj'
    def on_search_button_clicked(self):
        self.okno_lottie.show()             #animacja łapki na czas działania
        self.ui.searchButton.setEnabled(False)
        QApplication.processEvents()

        year = self.ui.yearComboBox.currentText()
        month = self.ui.monthComboBox.currentText()
        collection_name = f"{month}_{year}"
        measurment_code = self.ui.measurComboBox.currentData()

        woj_code = self.ui.voivodeshipComboBox.currentData()
        pow_code = self.ui.districtComboBox.currentData()

        self.current_stations = []

        if woj_code == "00" or woj_code is None:                                    # cała polska
            self.current_stations = list_all_facilities(self.r)
        else:
            if pow_code == "all" or pow_code is None:                               # województwo
                self.current_stations = list_facilities_by_woj(self.r, woj_code)
            else:                                                                   # powiat
                self.current_stations = list_facilities_by_powiat(self.r, pow_code)

        station_ids = [s.get('id') for s in self.current_stations if s.get('id')]

        self.worker = DataWorker(self.db, collection_name, measurment_code, station_ids)
        self.worker.finished_data.connect(self.handle_result)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    # odbiór wyników
    def handle_result(self, result_table, result_map_values):
        self.current_map_values = result_map_values if result_map_values else {}
        self.update_map_view()

        # uzupełnienie tabeli
        if result_table is not None:
            self.ui.tableWidget.setRowCount(0)
            for index, row in result_table.iterrows():
                row_position = self.ui.tableWidget.rowCount()
                self.ui.tableWidget.insertRow(row_position)

                def get_fmt(col):
                    val = row[col]
                    return f"{val:.2f}" if pd.notna(val) else "-"

                def create_item(text, align_right=True):
                    item = QTableWidgetItem(text)
                    if align_right:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    else:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                    return item

                self.ui.tableWidget.setItem(row_position, 0, create_item(str(row['Dzien']), False))
                self.ui.tableWidget.setItem(row_position, 1, create_item(get_fmt('Srednia_Dzien')))
                self.ui.tableWidget.setItem(row_position, 2, create_item(get_fmt('Srednia_Noc')))
                self.ui.tableWidget.setItem(row_position, 3, create_item(get_fmt('Mediana_Dzien')))
                self.ui.tableWidget.setItem(row_position, 4, create_item(get_fmt('Mediana_Noc')))
                self.ui.tableWidget.setItem(row_position, 5, create_item(get_fmt('Srednia_Obcinana_Dzien')))
                self.ui.tableWidget.setItem(row_position, 6, create_item(get_fmt('Srednia_Obcinana_Noc')))
        else:
            print("Brak danych w bazie.")

        self.okno_lottie.close()                                        # wyłączenie animacji wyszukiwania
        self.ui.searchButton.setEnabled(True)