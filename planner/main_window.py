from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import *
import io
import re
import serial
import serial.tools.list_ports
import subprocess
import sys
import urllib.request
import webbrowser
from pathlib import Path

import qrcode

from .agopen import (
    default_fields_path,
    import_agshare_zip,
    list_fields,
    load_fence_plan,
    load_field,
    planner_fields_path,
    plans_dir,
    save_as_new_field,
    save_fence_plan,
)
from .cloud_export import export_mobile_cloud
from .geometry import polygon_area, generate_equal_area_fences, signed_cross_track, stake_points_on_line
from .kml_transform import KmlLocalTransform
from .map_canvas import MapCanvas
from .mobile_export import build_mobile_payload, export_mobile_html
from .models import Point
from .nmea import parse_nmea_line
from .sync_server import FenceSyncServer


class GpsReader(QThread):
    fix = Signal(object)
    error = Signal(str)

    def __init__(self, port, baud):
        super().__init__()
        self.port = port
        self.baud = baud
        self.running = True

    def run(self):
        last = None
        try:
            with serial.Serial(self.port, self.baud, timeout=1) as ser:
                while self.running:
                    line = ser.readline().decode("ascii", errors="ignore").strip()
                    if not line:
                        continue
                    last = parse_nmea_line(line, last)
                    if last:
                        self.fix.emit(last)
        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        self.running = False


class MobileGuideStarter(QThread):
    ready = Signal(str)
    error = Signal(str)

    def __init__(self, npx_path):
        super().__init__()
        self.npx_path = Path(npx_path)
        self.process = None

    def run(self):
        try:
            if not self.local_webguide_works():
                raise RuntimeError("Webguiden kører ikke. Start trådløs sync først.")

            self.process = subprocess.Popen(
                [str(self.npx_path), "--yes", "localtunnel", "--port", "8765"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(self.npx_path.parent),
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
            )

            output = ""
            for _ in range(90):
                if self.process.poll() is not None:
                    rest = self.process.stdout.read() if self.process.stdout else ""
                    raise RuntimeError((output + rest).strip() or "HTTPS-linket stoppede før det var klar.")

                line = self.process.stdout.readline() if self.process.stdout else ""
                if line:
                    output += line
                    match = re.search(r"https://[a-zA-Z0-9-]+\.loca\.lt", output)
                    if match:
                        url = match.group(0)
                        if self.remote_webguide_works(url):
                            self.ready.emit(url)
                            return
                self.msleep(1000)

            raise RuntimeError("Kunne ikke lave et virkende HTTPS-link inden timeout.")
        except Exception as e:
            self.error.emit(str(e))

    def local_webguide_works(self):
        return self.url_works("http://127.0.0.1:8765")

    def remote_webguide_works(self, url):
        return self.url_works(url)

    def url_works(self, url):
        try:
            with urllib.request.urlopen(url.rstrip("/") + "/guide.json", timeout=8) as response:
                body = response.read(300).decode("utf-8", errors="ignore")
                return response.status == 200 and "FenceGuide" in body
        except Exception:
            return False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AgOpenGPS Fence Planner v1.3")
        self.fields_path = default_fields_path()
        self.field = None
        self.fences = []
        self.fold_areas = []
        self.a = None
        self.b = None
        self.await_ab = False
        self.transform = None
        self.gps_thread = None
        self.gps_local = None
        self.sync_server = None
        self.mobile_guide_thread = None
        self.mobile_tunnel_process = None
        self.setup_ui()
        self.refresh_fields()

    def setup_ui(self):
        self.tabs = QTabWidget()
        self.tabs.addTab(self.build_plan_tab(), "Planlæg")
        self.tabs.addTab(self.build_drive_tab(), "KØR")
        self.tabs.addTab(self.build_about_tab(), "Om / Android")
        self.setCentralWidget(self.tabs)

    def build_plan_tab(self):
        w = QWidget()
        outer = QHBoxLayout(w)

        left = QVBoxLayout()
        self.path_label = QLabel()
        btn_path = QPushButton("Vælg Fields-mappe")
        btn_path.clicked.connect(self.choose_fields_path)
        btn_agshare = QPushButton("Importer AgShare/TASKDATA ZIP")
        btn_agshare.clicked.connect(self.import_agshare)
        self.field_list = QListWidget()
        self.field_list.currentRowChanged.connect(self.load_selected_field)
        left.addWidget(QLabel("AgOpenGPS Fields"))
        left.addWidget(self.path_label)
        left.addWidget(btn_path)
        left.addWidget(btn_agshare)
        left.addWidget(QLabel("Marker"))
        left.addWidget(self.field_list)

        center = QVBoxLayout()
        self.map = MapCanvas()
        self.map.clicked.connect(self.map_clicked)
        self.map.point_moved.connect(self.ab_point_moved)
        center.addWidget(self.map)

        right = QVBoxLayout()
        self.zone_count_spin = QSpinBox()
        self.zone_count_spin.setMinimum(2)
        self.zone_count_spin.setMaximum(100)
        self.zone_count_spin.setValue(3)
        self.zone_count_spin.valueChanged.connect(self.regenerate_live)

        self.stake_spacing_combo = QComboBox()
        self.stake_spacing_combo.setEditable(True)
        self.stake_spacing_combo.addItems(["10 m", "25 m", "50 m"])
        self.stake_spacing_combo.setCurrentText("25 m")
        self.stake_spacing_combo.currentIndexChanged.connect(self.regenerate_live)
        self.stake_spacing_combo.lineEdit().editingFinished.connect(self.normalize_stake_spacing)

        self.basemap_combo = QComboBox()
        self.basemap_combo.addItems(["Esri nyeste", "Esri Clarity"])
        self.basemap_combo.currentTextChanged.connect(self.change_basemap)

        self.map_quality_combo = QComboBox()
        self.map_quality_combo.addItems(["Høj", "Normal"])
        self.map_quality_combo.currentTextChanged.connect(self.change_map_quality)

        btn_ab = QPushButton("Vælg A/B")
        btn_ab.clicked.connect(self.choose_ab)
        btn_gen = QPushButton("Generér zoner")
        btn_gen.clicked.connect(self.generate)
        btn_save = QPushButton("Gem som ny mark")
        btn_save.clicked.connect(self.save_new_field)
        btn_save_plan = QPushButton("Gem hegnsplan")
        btn_save_plan.clicked.connect(self.save_plan)
        btn_load_plan = QPushButton("Indlaes hegnsplan")
        btn_load_plan.clicked.connect(self.load_plan)
        btn_drive_field = QPushButton("Koer mark")
        btn_drive_field.clicked.connect(self.go_to_drive)
        self.btn_mobile_guide = QPushButton("Start mobilguide")
        self.btn_mobile_guide.clicked.connect(self.start_mobile_guide)
        btn_mobile_cloud = QPushButton("Eksporter mobilsky")
        btn_mobile_cloud.clicked.connect(self.export_mobile_cloud)
        self.btn_sync = QPushButton("Start trådløs sync")
        self.btn_sync.clicked.connect(self.toggle_sync_server)
        self.sync_label = QLabel("Sync: stoppet")
        self.sync_label.setWordWrap(True)
        self.info = QTextEdit()
        self.info.setReadOnly(True)

        right.addWidget(QLabel("Antal zoner"))
        right.addWidget(self.zone_count_spin)
        right.addWidget(QLabel("Pæleafstand"))
        right.addWidget(self.stake_spacing_combo)
        right.addWidget(QLabel("Satellitkort"))
        right.addWidget(self.basemap_combo)
        right.addWidget(QLabel("Kortkvalitet"))
        right.addWidget(self.map_quality_combo)
        right.addWidget(btn_ab)
        right.addWidget(btn_gen)
        right.addWidget(btn_save_plan)
        right.addWidget(btn_load_plan)
        right.addWidget(btn_drive_field)
        right.addWidget(btn_save)
        right.addWidget(self.btn_mobile_guide)
        right.addWidget(btn_mobile_cloud)
        right.addWidget(self.btn_sync)
        right.addWidget(self.sync_label)
        right.addWidget(QLabel("Resultat"))
        right.addWidget(self.info)

        outer.addLayout(left, 1)
        outer.addLayout(center, 4)
        outer.addLayout(right, 2)
        return w

    def change_basemap(self, name):
        if hasattr(self, "map"):
            self.map.set_basemap(name)
        if hasattr(self, "drive_map"):
            self.drive_map.set_basemap(name)

    def change_map_quality(self, quality):
        if hasattr(self, "map"):
            self.map.set_quality(quality)
        if hasattr(self, "drive_map"):
            self.drive_map.set_quality(quality)

    def build_drive_tab(self):
        w = QWidget()
        outer = QHBoxLayout(w)
        self.drive_map = MapCanvas()
        outer.addWidget(self.drive_map, 4)

        right = QVBoxLayout()
        self.port_combo = QComboBox()
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["115200", "38400", "9600"])
        btn_ports = QPushButton("Opdater COM")
        btn_ports.clicked.connect(self.refresh_ports)
        btn_start = QPushButton("Start GPS")
        btn_start.clicked.connect(self.start_gps)
        btn_stop = QPushButton("Stop GPS")
        btn_stop.clicked.connect(self.stop_gps)
        self.fence_combo = QComboBox()
        self.fence_combo.currentIndexChanged.connect(self.update_drive_line_info)
        self.big_distance = QLabel("INGEN GPS")
        self.big_distance.setObjectName("BigNumber")
        self.drive_info = QTextEdit()
        self.drive_info.setReadOnly(True)
        right.addWidget(QLabel("COM-port"))
        right.addWidget(self.port_combo)
        right.addWidget(QLabel("Baud"))
        right.addWidget(self.baud_combo)
        right.addWidget(btn_ports)
        right.addWidget(btn_start)
        right.addWidget(btn_stop)
        right.addWidget(QLabel("Valgt hegnslinje"))
        right.addWidget(self.fence_combo)
        right.addWidget(QLabel("Afstand til linje"))
        right.addWidget(self.big_distance)
        right.addWidget(self.drive_info)

        outer.addLayout(right, 2)
        self.refresh_ports()
        return w

    def build_about_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        t = QTextEdit()
        t.setReadOnly(True)
        t.setPlainText(
            "AgOpenGPS Fence Planner v1.3\n\n"
            "Satellitkort kan skiftes mellem Esri Clarity og Esri nyeste. "
            "Clarity kan være klarere, men ikke altid nyest. A/B-punkter kan flyttes direkte på kortet."
        )
        layout.addWidget(t)
        return w

    def refresh_fields(self):
        self.path_label.setText(str(self.fields_path))
        self.field_list.clear()
        for p in list_fields(self.fields_path):
            self.field_list.addItem(p.name)

    def choose_fields_path(self):
        from pathlib import Path

        p = QFileDialog.getExistingDirectory(self, "Vælg AgOpenGPS Fields-mappe", str(self.fields_path))
        if p:
            self.fields_path = Path(p)
            self.refresh_fields()

    def import_agshare(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Vaelg AgShare/TASKDATA ZIP",
            str(Path.home() / "Downloads"),
            "AgShare ZIP (*.zip);;Alle filer (*.*)",
        )
        if not path:
            return
        try:
            dst, count = import_agshare_zip(path, self.fields_path)
            self.fields_path = planner_fields_path()
            self.refresh_fields()
            QMessageBox.information(
                self,
                "AgShare importeret",
                f"{count} marker er oprettet under:\n{self.fields_path}\n\nImportfil:\n{dst}",
            )
        except Exception as e:
            QMessageBox.critical(self, "AgShare fejl", str(e))

    def load_selected_field(self, row):
        if row < 0:
            return
        try:
            self.field = load_field(self.fields_path / self.field_list.item(row).text())
            self.a = self.b = None
            self.fences = []
            self.fold_areas = []
            self.transform = KmlLocalTransform(self.field.boundary, self.field.field_kml_ring) if self.field.field_kml_ring else None
            self.map.fit_to_boundary(self.field.boundary, self.transform)
            self.drive_map.fit_to_boundary(self.field.boundary, self.transform)
            ha = polygon_area(self.field.boundary) / 10000
            georef_source = self.field.georef_source or "mangler"
            map_status = "satellitkort OK" if self.transform else "satellitkort kræver Field.kml, TASKDATA.XML eller AgShare ZIP"
            self.info.setPlainText(
                f"Mark: {self.field.name}\n"
                f"Areal: {ha:.2f} ha\n"
                f"Georeference: {georef_source}\n"
                f"{map_status}\n"
                f"Kort: {self.basemap_combo.currentText()} / {self.map_quality_combo.currentText()}"
            )
            self.refresh_fence_combo()
            self.update_drive_line_info()
        except Exception as e:
            QMessageBox.critical(self, "Fejl", str(e))

    def choose_ab(self):
        if not self.field:
            QMessageBox.warning(self, "Ingen mark", "Vælg mark først.")
            return
        self.await_ab = True
        self.a = self.b = None
        self.fences = []
        self.fold_areas = []
        self.map.draw(self.field.boundary, self.fences, self.a, self.b)
        self.drive_map.draw(self.field.boundary, self.fences, self.a, self.b, self.gps_local)
        self.info.setPlainText("Klik A og derefter B på kortet. Derefter kan punkterne trækkes rundt.")

    def map_clicked(self, x, y):
        if not self.await_ab:
            return
        if self.a is None:
            self.a = Point(x, y)
            self.map.draw(self.field.boundary, self.fences, self.a, self.b)
            self.info.setPlainText("A valgt. Klik B.")
        else:
            self.b = Point(x, y)
            self.await_ab = False
            self.generate(silent=True)

    def ab_point_moved(self, label, x, y):
        if not self.field:
            return
        if label == "A":
            self.a = Point(x, y)
        elif label == "B":
            self.b = Point(x, y)
        self.generate(silent=True)

    def regenerate_live(self, *_):
        if self.field and self.a and self.b:
            self.generate(silent=True)

    def stake_spacing(self):
        text = self.stake_spacing_combo.currentText().strip().lower().replace(",", ".").replace("m", "").strip()
        try:
            spacing = float(text)
        except ValueError:
            return 25.0
        return max(0.1, spacing)

    def stake_spacing_label(self):
        return self.spacing_text(self.stake_spacing())

    def spacing_text(self, spacing):
        if abs(spacing - round(spacing)) < 1e-6:
            return f"{int(round(spacing))} m"
        return f"{spacing:.2f}".rstrip("0").rstrip(".").replace(".", ",") + " m"

    def normalize_stake_spacing(self):
        self.stake_spacing_combo.setCurrentText(self.stake_spacing_label())
        self.regenerate_live()

    def zone_count(self):
        return self.zone_count_spin.value()

    def fence_count(self):
        return self.zone_count() - 1

    def generate(self, silent=False):
        if not self.field or not self.a or not self.b:
            if not silent:
                QMessageBox.warning(self, "Mangler data", "Vælg mark og A/B først.")
            return
        try:
            selected_fence = self.fence_combo.currentText() if self.fence_combo.count() else ""
            self.fences, self.fold_areas = generate_equal_area_fences(self.field.boundary, self.a, self.b, self.zone_count())
            self.map.update_dynamic(self.fences, self.a, self.b, sync_handles=False)
            self.drive_map.update_dynamic(self.fences, self.a, self.b, self.gps_local, sync_handles=True)
            self.refresh_fence_combo(selected_fence)
            self.update_result_text()
        except Exception as e:
            if not silent:
                QMessageBox.critical(self, "Fejl", str(e))
            else:
                self.info.setPlainText(f"Kan ikke generere hegn endnu:\n{e}")

    def refresh_fence_combo(self, selected_fence=""):
        self.fence_combo.blockSignals(True)
        self.fence_combo.clear()
        for f in self.fences:
            self.fence_combo.addItem(f.name)
        if selected_fence:
            idx = self.fence_combo.findText(selected_fence)
            if idx >= 0:
                self.fence_combo.setCurrentIndex(idx)
        self.fence_combo.blockSignals(False)
        self.update_drive_line_info()

    def go_to_drive(self):
        if not self.field:
            QMessageBox.warning(self, "Ingen mark", "Vaelg mark foerst.")
            return
        if not self.fences:
            QMessageBox.warning(self, "Ingen hegnslinjer", "Generer zoner eller indlaes en hegnsplan foerst.")
            return
        self.drive_map.draw(self.field.boundary, self.fences, self.a, self.b, self.gps_local)
        self.update_drive_line_info()
        self.tabs.setCurrentIndex(1)

    def update_drive_line_info(self, *_):
        if not hasattr(self, "drive_info"):
            return
        lines = []
        if self.field:
            lines.append(f"Mark: {self.field.name}")
            lines.append(f"Georeference: {self.field.georef_source or 'mangler'}")
        else:
            lines.append("Vaelg en mark paa Planlaeg-fanen.")

        if self.fences and self.fence_combo.currentIndex() >= 0:
            fence = self.fences[self.fence_combo.currentIndex()]
            stakes = stake_points_on_line(fence.start, fence.end, self.stake_spacing())
            lines += [
                "",
                f"Valgt linje: {fence.name}",
                f"Laengde: {fence.length_m:.1f} m",
                f"Paele: {len(stakes)} stk ved {self.stake_spacing_label()}",
            ]
            if self.transform:
                lat1, lon1 = self.transform.local_to_latlon(fence.start)
                lat2, lon2 = self.transform.local_to_latlon(fence.end)
                lines.append(f"Start GPS: {lat1:.7f}, {lon1:.7f}")
                lines.append(f"Slut GPS:  {lat2:.7f}, {lon2:.7f}")
            if self.gps_local:
                xt = signed_cross_track(self.gps_local, fence.start, fence.end)
                side = "VENSTRE" if xt > 0 else "HOJRE"
                self.big_distance.setText(f"{abs(xt):.2f} m {side}")
        else:
            lines += ["", "Ingen hegnslinje valgt."]
            if self.gps_thread:
                self.big_distance.setText("INGEN LINJE")

        self.drive_info.setPlainText("\n".join(lines))

    def update_result_text(self):
        spacing = self.stake_spacing()
        total = polygon_area(self.field.boundary) / 10000
        lines = [
            f"Total: {total:.2f} ha",
            f"Zoner: {self.zone_count()}",
            f"Hegn: {self.fence_count()}",
            f"Pæleafstand: {self.stake_spacing_label()}",
            f"Kort: {self.basemap_combo.currentText()} / {self.map_quality_combo.currentText()}",
            "",
        ]
        for i, area in enumerate(self.fold_areas, 1):
            lines.append(f"Fold {i}: {area / 10000:.2f} ha")

        lines += ["", "Hegn:"]
        total_stakes = 0
        for f in self.fences:
            stakes = stake_points_on_line(f.start, f.end, spacing)
            total_stakes += len(stakes)
            lines.append(f"{f.name}: {f.length_m:.1f} m")
            lines.append(f"  Pæle: {len(stakes)} stk ved {self.stake_spacing_label()}")
            if self.transform:
                lat1, lon1 = self.transform.local_to_latlon(f.start)
                lat2, lon2 = self.transform.local_to_latlon(f.end)
                lines.append(f"  Start GPS: {lat1:.7f}, {lon1:.7f}")
                lines.append(f"  Slut GPS:  {lat2:.7f}, {lon2:.7f}")

        lines += ["", f"Pæle i alt: {total_stakes} stk"]
        self.info.setPlainText("\n".join(lines))

    def save_new_field(self):
        if not self.field or not self.fences:
            QMessageBox.warning(self, "Mangler hegn", "Generér zoner først.")
            return
        try:
            dst = save_as_new_field(self.field, self.fences, self.zone_count())
            QMessageBox.information(self, "Gemt", f"Ny mark gemt:\n{dst}")
            self.refresh_fields()
        except Exception as e:
            QMessageBox.critical(self, "Fejl", str(e))

    def save_plan(self):
        if not self.field or not self.fences:
            QMessageBox.warning(self, "Mangler hegnsplan", "Generer zoner/hegn foerst.")
            return
        try:
            default_path = plans_dir(self.field) / f"{self.field.name}_{self.zone_count()}_zoner.json"
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Gem hegnsplan",
                str(default_path),
                "Fence Planner plan (*.json)",
            )
            if not path:
                return
            dst = save_fence_plan(
                self.field,
                self.fences,
                self.fold_areas,
                self.zone_count(),
                self.stake_spacing(),
                self.a,
                self.b,
                path,
            )
            QMessageBox.information(self, "Hegnsplan gemt", f"Hegnsplan gemt:\n{dst}")
        except Exception as e:
            QMessageBox.critical(self, "Fejl", str(e))

    def load_plan(self):
        if not self.field:
            QMessageBox.warning(self, "Ingen mark", "Vaelg mark foerst.")
            return
        try:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Indlaes hegnsplan",
                str(plans_dir(self.field)),
                "Fence Planner plan (*.json)",
            )
            if not path:
                return
            plan = load_fence_plan(path)
            self.zone_count_spin.blockSignals(True)
            self.stake_spacing_combo.blockSignals(True)
            self.zone_count_spin.setValue(max(2, plan["zone_count"]))
            self.stake_spacing_combo.setCurrentText(self.spacing_text(plan["stake_spacing_m"]))
            self.zone_count_spin.blockSignals(False)
            self.stake_spacing_combo.blockSignals(False)
            self.a = plan["a"]
            self.b = plan["b"]
            self.fences = plan["fences"]
            self.fold_areas = plan["fold_areas"]
            self.await_ab = False
            self.refresh_fence_combo()
            self.map.draw(self.field.boundary, self.fences, self.a, self.b)
            self.drive_map.draw(self.field.boundary, self.fences, self.a, self.b, self.gps_local)
            self.update_result_text()
            QMessageBox.information(self, "Hegnsplan indlaest", f"Hegnsplan indlaest:\n{plan['path']}")
        except Exception as e:
            QMessageBox.critical(self, "Fejl", str(e))

    def export_mobile(self):
        if not self.field or not self.fences:
            QMessageBox.warning(self, "Mangler zoner", "Generér zoner først.")
            return
        if not self.transform:
            QMessageBox.warning(self, "Mangler georeference", "Mobil-eksport kræver Field.kml, TASKDATA.XML eller AgShare ZIP/georeference.")
            return

        default_name = f"{self.field.name}_FenceGuide.html"
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Gem mobilside",
            str(self.field.path.parent / default_name),
            "FenceGuide HTML (*.html)",
        )
        if not path:
            return

        try:
            dst = export_mobile_html(
                path,
                self.field,
                self.fences,
                self.fold_areas,
                self.transform,
                self.zone_count(),
                self.stake_spacing(),
                self.a,
                self.b,
            )
            QMessageBox.information(self, "Mobilside gemt", f"Mobilside gemt:\n{dst}\n\nSend HTML-filen til telefonen og åbn den i Chrome.")
        except Exception as e:
            QMessageBox.critical(self, "Fejl", str(e))

    def mobile_payload(self):
        if not self.field or not self.fences:
            raise ValueError("Generér zoner først.")
        if not self.transform:
            raise ValueError("Trådløs sync kræver Field.kml, TASKDATA.XML eller AgShare ZIP/georeference.")
        return build_mobile_payload(
            self.field,
            self.fences,
            self.fold_areas,
            self.transform,
            self.zone_count(),
            self.stake_spacing(),
            self.a,
            self.b,
        )

    def export_mobile_cloud(self):
        default_dir = Path.home() / "Documents" / "FencePlanner" / "MobileCloud"
        folder = QFileDialog.getExistingDirectory(self, "Vaelg mappe til mobilsky", str(default_dir.parent))
        if not folder:
            return
        try:
            dst, count = export_mobile_cloud(folder)
            QMessageBox.information(
                self,
                "Mobilsky eksporteret",
                f"{count} hegnsplaner er eksporteret.\n\nAabn eller upload:\n{dst / 'index.html'}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Mobilsky fejl", str(e))

    def toggle_sync_server(self):
        if self.sync_server:
            self.sync_server.stop()
            self.sync_server = None
            self.btn_sync.setText("Start trådløs sync")
            self.sync_label.setText("Sync: stoppet")
            return

        try:
            self.mobile_payload()
            self.sync_server = FenceSyncServer(self.mobile_payload)
            self.sync_server.start()
            self.btn_sync.setText("Stop trådløs sync")
            self.sync_label.setText(
                "Webguide kører:\n"
                f"{self.sync_server.url}\n\n"
                "Telefon og computer skal være på samme Wi-Fi.\n"
                "GPS i browser kræver HTTPS/tunnel."
            )
            webbrowser.open(self.sync_server.url)
        except Exception as e:
            if self.sync_server:
                self.sync_server.stop()
                self.sync_server = None
            QMessageBox.critical(self, "Sync fejl", str(e))

    def ensure_sync_server(self):
        self.mobile_payload()
        if not self.sync_server:
            self.sync_server = FenceSyncServer(self.mobile_payload)
            self.sync_server.start()
            self.btn_sync.setText("Stop trådløs sync")
            self.sync_label.setText(
                "Webguide kører:\n"
                f"{self.sync_server.url}\n\n"
                "Tryk Start mobilguide for QR-kode."
            )

    def start_mobile_guide(self):
        try:
            self.ensure_sync_server()
        except Exception as e:
            QMessageBox.critical(self, "Mobilguide fejl", str(e))
            return

        npx_path = self.find_npx()
        if not npx_path:
            QMessageBox.critical(
                self,
                "Mangler Node",
                "Kunne ikke finde Node/npm i .tools-mappen. Kør start_https_webguide.bat én gang eller sig til, så sætter vi det op igen.",
            )
            return

        if self.mobile_tunnel_process and self.mobile_tunnel_process.poll() is None:
            self.mobile_tunnel_process.terminate()
            self.mobile_tunnel_process = None

        self.btn_mobile_guide.setEnabled(False)
        self.btn_mobile_guide.setText("Starter mobilguide...")
        self.sync_label.setText("Starter HTTPS-link og QR-kode...")

        self.mobile_guide_thread = MobileGuideStarter(npx_path)
        self.mobile_guide_thread.ready.connect(self.on_mobile_guide_ready)
        self.mobile_guide_thread.error.connect(self.on_mobile_guide_error)
        self.mobile_guide_thread.start()

    def on_mobile_guide_ready(self, url):
        self.mobile_tunnel_process = self.mobile_guide_thread.process if self.mobile_guide_thread else None
        self.btn_mobile_guide.setEnabled(True)
        self.btn_mobile_guide.setText("Start mobilguide")
        self.sync_label.setText(f"Mobilguide klar:\n{url}")
        self.save_webguide_shortcut(url)
        QApplication.clipboard().setText(url)
        self.show_qr_dialog(url)

    def on_mobile_guide_error(self, message):
        self.btn_mobile_guide.setEnabled(True)
        self.btn_mobile_guide.setText("Start mobilguide")
        self.sync_label.setText("Mobilguide kunne ikke starte.")
        QMessageBox.critical(self, "Mobilguide fejl", message)

    def find_npx(self):
        candidates = [
            Path(sys.executable).resolve().parent / ".tools" / "node-v22.22.3-win-x64" / "npx.cmd",
            Path.home() / "Documents" / "FencePlanner" / ".tools" / "node-v22.22.3-win-x64" / "npx.cmd",
            Path.cwd() / ".tools" / "node-v22.22.3-win-x64" / "npx.cmd",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def save_webguide_shortcut(self, url):
        shortcut = Path.home() / "Desktop" / "Fence Webguide.url"
        shortcut.write_text(f"[InternetShortcut]\nURL={url}\n", encoding="ascii")

    def show_qr_dialog(self, url):
        img = qrcode.make(url)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue(), "PNG")

        dialog = QDialog(self)
        dialog.setWindowTitle("Mobilguide QR-kode")
        layout = QVBoxLayout(dialog)
        title = QLabel("Scan med mobilens kamera")
        title.setStyleSheet("font-size: 16px; font-weight: 700;")
        title.setAlignment(Qt.AlignCenter)
        qr = QLabel()
        qr.setPixmap(pixmap.scaled(320, 320, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        qr.setAlignment(Qt.AlignCenter)
        link = QLineEdit(url)
        link.setReadOnly(True)
        link.selectAll()
        note = QLabel("Linket er også kopieret til udklipsholderen.")
        note.setAlignment(Qt.AlignCenter)
        btn_close = QPushButton("Luk")
        btn_close.clicked.connect(dialog.accept)

        layout.addWidget(title)
        layout.addWidget(qr)
        layout.addWidget(link)
        layout.addWidget(note)
        layout.addWidget(btn_close)
        dialog.resize(380, 470)
        dialog.exec()

    def copy_webguide_link(self):
        url = None
        source = "lokalt link"

        shortcut = Path.home() / "Desktop" / "Fence Webguide.url"
        if shortcut.exists():
            try:
                for line in shortcut.read_text(encoding="ascii", errors="ignore").splitlines():
                    if line.startswith("URL=https://"):
                        url = line.split("=", 1)[1].strip()
                        source = "HTTPS-link"
                        break
            except OSError:
                url = None

        if url and not self.webguide_url_works(url):
            url = None
            source = "lokalt link"

        if not url and self.sync_server:
            url = self.sync_server.url

        if not url:
            QMessageBox.warning(
                self,
                "Intet link",
                "Start trådløs sync først. Kør start_https_webguide.bat hvis linket skal sendes udenfor samme Wi-Fi.",
            )
            return

        QApplication.clipboard().setText(url)
        QMessageBox.information(self, "Link kopieret", f"{source} kopieret til udklipsholderen:\n{url}")

    def start_https_webguide(self):
        if not self.sync_server:
            QMessageBox.warning(self, "Start sync først", "Tryk 'Start trådløs sync' før du starter HTTPS-linket.")
            return

        script = self.find_https_script()
        if not script:
            QMessageBox.critical(
                self,
                "Mangler script",
                "Kunne ikke finde start_https_webguide.bat i FencePlanner-mappen.",
            )
            return

        try:
            subprocess.Popen(
                ["cmd.exe", "/c", "start", "Fence HTTPS Webguide", str(script)],
                cwd=str(script.parent),
                shell=False,
            )
            QMessageBox.information(
                self,
                "HTTPS-link starter",
                "HTTPS-linket starter i et nyt vindue.\n\n"
                "Når vinduet skriver 'Klar', er linket kopieret til udklipsholderen og kan sendes til mobilen.",
            )
        except Exception as e:
            QMessageBox.critical(self, "HTTPS fejl", str(e))

    def find_https_script(self):
        candidates = [
            Path.cwd() / "start_https_webguide.bat",
            Path.home() / "Documents" / "FencePlanner" / "start_https_webguide.bat",
            Path(__file__).resolve().parents[1] / "start_https_webguide.bat",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def webguide_url_works(self, url):
        try:
            with urllib.request.urlopen(url.rstrip("/") + "/guide.json", timeout=5) as response:
                body = response.read(200).decode("utf-8", errors="ignore")
                return response.status == 200 and "FenceGuide" in body
        except Exception:
            return False

    def refresh_ports(self):
        self.port_combo.clear()
        for p in serial.tools.list_ports.comports():
            self.port_combo.addItem(p.device)

    def start_gps(self):
        if self.gps_thread:
            self.stop_gps()
        port = self.port_combo.currentText()
        if not port:
            QMessageBox.warning(self, "Ingen COM", "Vælg COM-port.")
            return
        self.gps_thread = GpsReader(port, int(self.baud_combo.currentText()))
        self.gps_thread.fix.connect(self.on_gps_fix)
        self.gps_thread.error.connect(lambda e: self.drive_info.setPlainText("GPS fejl: " + e))
        self.gps_thread.start()

    def stop_gps(self):
        if self.gps_thread:
            self.gps_thread.stop()
            self.gps_thread.wait(1500)
            self.gps_thread = None
            self.big_distance.setText("STOPPET")

    def closeEvent(self, event):
        if self.mobile_tunnel_process and self.mobile_tunnel_process.poll() is None:
            self.mobile_tunnel_process.terminate()
            self.mobile_tunnel_process = None
        if self.sync_server:
            self.sync_server.stop()
            self.sync_server = None
        self.stop_gps()
        event.accept()

    def on_gps_fix(self, fix):
        lines = [
            f"Lat/Lon: {fix.lat:.8f}, {fix.lon:.8f}",
            f"Fix quality: {fix.fix_quality}  Satellitter: {fix.sats}  HDOP: {fix.hdop}",
            f"Hastighed: {fix.speed_kmh:.1f} km/t",
        ]
        if not self.transform:
            self.big_distance.setText("MANGLER GEO")
            lines.append("Ingen Field.kml, TASKDATA.XML eller AgShare ZIP/georeference fundet.")
        elif self.fences and self.fence_combo.currentIndex() >= 0:
            self.gps_local = self.transform.latlon_to_local(fix.lat, fix.lon)
            f = self.fences[self.fence_combo.currentIndex()]
            xt = signed_cross_track(self.gps_local, f.start, f.end)
            side = "VENSTRE" if xt > 0 else "HØJRE"
            self.big_distance.setText(f"{abs(xt):.2f} m {side}")
            lines.append(f"Valgt: {f.name}")
            lines.append(f"Laengde: {f.length_m:.1f} m")
            lines.append(f"Paele: {len(stake_points_on_line(f.start, f.end, self.stake_spacing()))} stk ved {self.stake_spacing_label()}")
            lines.append(f"Afstand til linje: {abs(xt):.2f} m {side}")
            self.drive_map.update_dynamic(self.fences, self.a, self.b, self.gps_local, sync_handles=True)
        self.drive_info.setPlainText("\n".join(lines))

    def closeEvent(self, event):
        self.stop_gps()
        super().closeEvent(event)
