import os

os.environ['QT_LOGGING_RULES'] = '*.debug=false'
import sys
import numpy as np
import cv2
from pythonosc import udp_client
from PyQt5.QtWidgets import (QApplication, QWidget, QTabWidget, QVBoxLayout,
                             QLabel, QColorDialog, QMessageBox, QMainWindow)
from PyQt5.QtGui import (QPainter, QPen, QPixmap, QTabletEvent,
                         QColor, QImage)
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QSize


class Shape:
    def __init__(self, shape_category, contour, color, pressure):
        self.shape_category = shape_category
        self.contour = contour
        self.color = color
        self.pressure = pressure

        # Calculate position (centroid)
        moments = cv2.moments(contour)
        if moments["m00"] != 0:
            cx = int(moments["m10"] / moments["m00"])
            cy = int(moments["m01"] / moments["m00"])
            self.position = QPoint(cx, cy)
        else:
            self.position = QPoint(0, 0)

        # Calculate size
        x, y, w, h = cv2.boundingRect(contour)
        self.size = (w, h)

    def __str__(self):
        return (f"{self.shape_category} (RGB: {self.color.red()},{self.color.green()},{self.color.blue()}) "
                f"at {self.position.x()},{self.position.y()} "
                f"size {self.size[0]}x{self.size[1]} "
                f"pressure {self.pressure:.2f}")

    def to_osc_dict(self):

        return {
            'category': self.shape_category,
            'color_r': self.color.red() / 255.0,
            'color_g': self.color.green() / 255.0,
            'color_b': self.color.blue() / 255.0,
            'x': self.position.x() / self.size[0] if self.size[0] > 0 else 0,
            'y': 1.0 - (self.position.y() / self.size[1]) if self.size[1] > 0 else 0,

            'width': self.size[0],
            'height': self.size[1],
            'pressure': self.pressure
        }


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drawing App with Sound Output")
        self.setMinimumSize(400, 300)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.drawing_tab = TabletWidget()
        self.tab_widget.addTab(self.drawing_tab, "Drawing")

        self.results_tab = QWidget()
        self.results_layout = QVBoxLayout()
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        self.results_tab.setLayout(self.results_layout)
        self.tab_widget.addTab(self.results_tab, "Results")

        self.results_canvas = QPixmap(self.drawing_tab.size())
        self.results_canvas.fill(Qt.white)
        self.results_label = QLabel()
        self.results_label.setPixmap(self.results_canvas)
        self.results_label.setScaledContents(True)
        self.results_layout.addWidget(self.results_label)

        self.drawing_tab.shape_detected.connect(self.update_results)

    def resizeEvent(self, event):
        if not self.isMaximized():
            current_size = self.size()
            new_size = QSize(
                min(max(400, current_size.width()), 1920),
                min(max(300, current_size.height()), 1080)
            )
            if current_size != new_size:
                self.resize(new_size)
        super().resizeEvent(event)

    def update_results(self, shape_info):
        self.results_canvas.fill(Qt.white)
        painter = QPainter(self.results_canvas)

        for shape in self.drawing_tab.perfect_shapes:
            painter.setPen(QPen(shape.color, 2))

            if shape.shape_category == "Circle":
                (x, y), radius = cv2.minEnclosingCircle(shape.contour)
                painter.drawEllipse(QPoint(int(x), int(y)), int(radius), int(radius))
            else:
                points = [QPoint(p[0][0], p[0][1]) for p in shape.contour]
                if len(points) > 1:
                    for i in range(len(points) - 1):
                        painter.drawLine(points[i], points[i + 1])
                    if shape.shape_category != "Line":
                        painter.drawLine(points[-1], points[0])

        self.results_label.setPixmap(self.results_canvas)


class TabletWidget(QWidget):
    shape_detected = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tablet Drawing with Sound Output")
        self.setMinimumSize(800, 600)
        self.setMaximumSize(1920, 1080)

        self.canvas = QPixmap(self.size())
        self.canvas.fill(Qt.white)
        self.last_pos = None
        self.pen_color = QColor(0, 0, 0)
        self.using_mouse = False
        self.last_pressure = 0.5

        self.preview_canvas = QPixmap(self.canvas.size())
        self.preview_canvas.fill(Qt.transparent)

        self.strokes = []
        self.perfect_shapes = []

        self.osc_client = udp_client.SimpleUDPClient("127.0.0.1", 57120)  # Default SC port
        self.osc_address = "/shape"

        self.info_label = QLabel(self)
        self.info_label.setStyleSheet("background-color: white; padding: 20px;")
        self.info_label.move(10, self.height() - 30)
        self.info_label.resize(self.width() - 20, 20)

        self.color_dialog = QColorDialog(self.pen_color, self)
        self.color_dialog.setOption(QColorDialog.ShowAlphaChannel, False)
        self.color_dialog.setWindowTitle("Color Picker")
        self.color_dialog.currentColorChanged.connect(self.set_pen_color)

        self.setFocusPolicy(Qt.StrongFocus)

        self.help_label = QLabel("Press 'H' for help", self)
        self.help_label.setStyleSheet("""
            QLabel {
                color: #666666;
                background-color: rgba(255, 255, 255, 180);
                padding: 5px;
                border-radius: 5px;
            }
        """)
        self.help_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.help_label.setGeometry(self.width() - 150, 10, 140, 30)

        '''
        try:
            self.osc_client._sock.connect(('127.0.0.1', 57120))
            print("Successfully connected to SuperCollider")
        except Exception as e:
            print(f"OSC Connection Error: {str(e)}")
        '''

    def set_pen_color(self, color):
        self.pen_color = color
        self.update_info(f"🎨 Color selected: RGB({color.red()}, {color.green()}, {color.blue()})")

    def update_info(self, text):
        self.info_label.setText(text)

    def send_shape_to_sc(self, shape):
        try:
            total_length = 0
            for i in range(len(self.current_stroke) - 1):
                p1 = self.current_stroke[i]
                p2 = self.current_stroke[i + 1]
                total_length += ((p2.x() - p1.x()) ** 2 + (p2.y() - p1.y()) ** 2) ** 0.5

            x_pos = shape.position.x() / self.width()
            y_pos = shape.position.y() / self.height()

            canvas_width = self.canvas.width()
            canvas_height = self.canvas.height()
            contour_points = shape.contour.squeeze()
            contour_normalized = []
            for (x, y) in contour_points:
                nx = x / canvas_width
                ny = y / canvas_height
                contour_normalized.extend([nx, ny])
            num_points = len(contour_normalized) // 2
            contour_floats = [float(coord) for coord in contour_normalized]

            self.osc_client.send_message("/shape", [
                str(shape.shape_category),
                float(x_pos),
                float(y_pos),
                float(shape.size[0]),
                float(shape.size[1]),
                float(shape.color.red() / 255.0),
                float(shape.color.green() / 255.0),
                float(shape.color.blue() / 255.0),
                float(shape.pressure),
                float(total_length),
                num_points,
                *contour_floats
            ])
            print(f"Sent shape: {shape.shape_category}, pos: ({x_pos:.2f}, {y_pos:.2f}), length: {total_length:.2f}")
        except Exception as e:
            print(f"Error sending OSC message: {str(e)}")

    def tabletEvent(self, event: QTabletEvent):
        self.using_mouse = False
        pos = event.pos()
        pressure = max(0.0, min(1.0, event.pressure()))

        if not hasattr(self, 'stroke_pressures'):
            self.stroke_pressures = []
        self.stroke_pressures.append(pressure)
        print(f"Pressure: {pressure:.3f}")

        rgb = (self.pen_color.red(), self.pen_color.green(), self.pen_color.blue())
        self.update_info(f"🖊️ Tablet - Pos: ({pos.x()}, {pos.y()}), Pressure: {pressure:.3f}, RGB{rgb}")

        if event.type() == QTabletEvent.TabletPress:
            self.last_pos = pos
            self.current_stroke = [pos]
            self.stroke_pressures = [pressure]
        elif event.type() == QTabletEvent.TabletMove and self.last_pos is not None:
            self.draw_line(self.last_pos, pos, pressure)

            self.last_pos = pos
            self.current_stroke.append(pos)
            self.update()
        elif event.type() == QTabletEvent.TabletRelease:
            if self.current_stroke:
                self.strokes.append((self.current_stroke.copy(), self.stroke_pressures.copy(), self.pen_color))

                shapes = self.detect_shapes(self.pixmap_to_cvimg(self.canvas))
                if shapes:
                    shape = shapes[0]
                    shape.pressure = sum(self.stroke_pressures) / len(self.stroke_pressures)
                    self.perfect_shapes.append(shape)
                    self.shape_detected.emit(shape)
                    self.send_shape_to_sc(shape)

                self.current_stroke = []
                self.stroke_pressures = []
            self.last_pos = None
            self.update()

        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.using_mouse = True
            self.last_pos = event.pos()
            self.current_stroke = [self.last_pos]
            self.last_pressure = 0.5

    def mouseMoveEvent(self, event):
        if self.using_mouse and self.last_pos is not None:
            pressure = 0.5
            pos = event.pos()
            rgb = (self.pen_color.red(), self.pen_color.green(), self.pen_color.blue())
            self.update_info(f"🖱️ Mouse - Pos: ({pos.x()}, {pos.y()}), Pressure: {pressure:.3f}, RGB{rgb}")

            self.draw_line(self.last_pos, pos, pressure)
            self.last_pos = pos
            self.last_pressure = pressure

            self.preview_canvas.fill(Qt.transparent)
            hint_img = self.pixmap_to_cvimg(self.canvas)
            shapes = self.detect_shapes(hint_img)
            if shapes:
                hinted = self.draw_detected_shapes(hint_img.copy(), shapes, hint_only=True)
                self.preview_canvas = self.cvimg_to_qpixmap(hinted)
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_pos = None
            if self.current_stroke:
                fixed_pressures = [0.5] * len(self.current_stroke)
                self.strokes.append((self.current_stroke, fixed_pressures, self.pen_color))
                shapes = self.detect_shapes(self.pixmap_to_cvimg(self.canvas))
                if shapes:
                    shape = shapes[0]
                    self.perfect_shapes.append(shape)
                    self.shape_detected.emit(shape)
                    self.send_shape_to_sc(shape)
                self.current_stroke = []
            self.preview_canvas.fill(Qt.transparent)
            self.update()
        event.accept()

    def draw_line(self, start: QPoint, end: QPoint, pressure: float):
        painter = QPainter(self.canvas)
        pen = QPen(self.pen_color, pressure * 10)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.drawLine(start, end)

        if not self.current_stroke:
            self.current_stroke = [start]
        self.current_stroke.append(end)

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.canvas)
        painter.end()

    def resizeEvent(self, event):
        new_canvas = QPixmap(event.size())
        new_canvas.fill(Qt.white)
        painter = QPainter(new_canvas)
        painter.drawPixmap(0, 0, self.canvas)
        painter.end()
        self.canvas = new_canvas

        self.preview_canvas = QPixmap(self.canvas.size())
        self.preview_canvas.fill(Qt.transparent)

        self.info_label.move(10, self.height() - 30)
        self.info_label.resize(self.width() - 20, 20)

        self.help_label.setGeometry(self.width() - 150, 10, 140, 30)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_C:
            self.color_dialog.show()
        elif event.key() == Qt.Key_H:
            self.show_help()

        elif event.key() == Qt.Key_Z:
            self.clear_canvas()
        event.accept()



    def show_help(self):
        help_text = """
        <h2>Drawing Controls</h2>
        <p><b>Mouse/Tablet:</b> Draw on the canvas</p>
        <p><b>Pressure:</b> Controls line thickness and sound amplitude</p>
        <p><b>Position:</b> Controls sound frequency and panning</p>

        <h2>Keyboard Shortcuts</h2>
        <p><b>C:</b> Open color picker</p>
        <p><b>H:</b> Show this help</p>
        <p><b>Z:</b> Clear canvas</p>

        <h2>Shape Detection</h2>
        <p>Draw shapes to trigger different sounds:</p>
        <ul>
            <li>Lines → Sawtooth wave</li>
            <li>Triangles → Triangle wave</li>
            <li>Rectangles → Square wave</li>
            <li>Other shapes → Sine wave</li>
        </ul>
        """
        QMessageBox.information(self, "Help", help_text)

    def pixmap_to_cvimg(self, pixmap):
        image = pixmap.toImage().convertToFormat(QImage.Format_ARGB32)
        width = image.width()
        height = image.height()
        ptr = image.bits()
        ptr.setsize(image.byteCount())
        arr = np.array(ptr).reshape((height, width, 4))
        bgr = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
        return bgr

    def cvimg_to_qpixmap(self, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        return QPixmap.fromImage(q_img)

    def detect_shapes(self, img):
        if not self.current_stroke:
            return []

        points = np.array([[p.x(), p.y()] for p in self.current_stroke])
        points = points.reshape((-1, 1, 2)).astype(np.int32)

        epsilon = 0.02 * cv2.arcLength(points, True)
        approx = cv2.approxPolyDP(points, epsilon, True)

        shape_category = "Polygon"
        if len(approx) == 2:
            shape_category = "Line"
        elif len(approx) == 3:
            shape_category = "Triangle"
        elif len(approx) == 4:
            shape_category = "Rectangle"
        elif len(approx) > 6:
            shape_category = "Circle"

        x, y, w, h = cv2.boundingRect(points)
        center_x = int(x + w / 2)
        center_y = int(y + h / 2)

        shape = Shape(shape_category, approx, self.pen_color, self.last_pressure)
        shape.position = QPoint(center_x, center_y)
        shape.size = (w, h)

        return [shape]

    def draw_detected_shapes(self, img, shapes, hint_only=False):
        for shape in shapes:
            color = (0, 255, 0) if hint_only else (255, 0, 0)
            cv2.drawContours(img, [shape.contour], -1, color, 2)
            if not hint_only:
                x, y = shape.contour[0][0]
                cv2.putText(img, shape.shape_category, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        return img

    def clear_canvas(self):
        """Clear the canvas and reset all stroke data"""
        self.canvas.fill(Qt.white)
        self.strokes = []
        self.perfect_shapes = []
        self.current_stroke = []
        self.stroke_pressures = []
        self.update()

        try:
            self.osc_client.send_message("/clearVisuals", [1])  # 1 means "clear"
        except Exception as e:
            print(f"Error sending clear command: {str(e)}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

    # client = udp_client.SimpleUDPClient("127.0.0.1", 57120)
    # client.send_message("/test", [440, 0.2])  # freq, amp