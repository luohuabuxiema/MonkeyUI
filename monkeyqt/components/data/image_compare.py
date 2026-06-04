from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtCore import Qt, Property, QRect, QPoint, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QPainter, QPixmap, QImage, QColor, QPen, QFont, QFontMetrics, QPainterPath

class MkImageCompare(QWidget):
    """
    MkImageCompare - Before/After Image Comparison Slider Component.
    Inspired by modern Web design, it lets users interactively slide to compare two images
    (e.g., input vs style transfer, low-res vs high-res).
    Features smooth start-up glide animation, floating glassmorphic labels, and vector arrow handles.
    """

    def __init__(self, before_img=None, after_img=None, parent=None):
        super().__init__(parent)
        
        self._before_pixmap = QPixmap()
        self._after_pixmap = QPixmap()
        self._slider_ratio = 0.5
        self._before_label = "迁移结果"
        self._after_label = "原图"
        self._show_labels = True
        self._is_dragging = False
        self._animate_on_show = True

        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.ArrowCursor)

        # 配置布局的大小的自适应策略 (Expanding in both directions)
        size_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setSizePolicy(size_policy)

        # Set initial images if provided
        if before_img is not None and after_img is not None:
            self.set_images(before_img, after_img)

    def set_images(self, before, after):
        """
        设置对比图片。支持传入文件路径、QPixmap 或 QImage。
        """
        if isinstance(before, str):
            self._before_pixmap = QPixmap(before)
        elif isinstance(before, QPixmap):
            self._before_pixmap = before
        elif isinstance(before, QImage):
            self._before_pixmap = QPixmap.fromImage(before)
        else:
            self._before_pixmap = QPixmap()

        if isinstance(after, str):
            self._after_pixmap = QPixmap(after)
        elif isinstance(after, QPixmap):
            self._after_pixmap = after
        elif isinstance(after, QImage):
            self._after_pixmap = QPixmap.fromImage(after)
        else:
            self._after_pixmap = QPixmap()

        self.update()

    def set_labels(self, before_label: str, after_label: str):
        """
        设置左右侧浮动的文字标签。
        """
        self._before_label = before_label
        self._after_label = after_label
        self.update()

    @Property(float)
    def sliderRatio(self):
        return self._slider_ratio

    @sliderRatio.setter
    def sliderRatio(self, value):
        self.set_slider_ratio(value)

    def set_slider_ratio(self, value):
        # Bound value between 0.0 and 1.0
        val = max(0.0, min(1.0, float(value)))
        if self._slider_ratio == val:
            return
        self._slider_ratio = val
        self.update()

    @Property(bool)
    def showLabels(self):
        return self._show_labels

    @showLabels.setter
    def showLabels(self, value):
        if self._show_labels == value:
            return
        self._show_labels = value
        self.update()

    @Property(bool)
    def animateOnShow(self):
        return self._animate_on_show

    @animateOnShow.setter
    def animateOnShow(self, value):
        self._animate_on_show = value

    @Property(str)
    def beforeLabel(self):
        return self._before_label

    @beforeLabel.setter
    def beforeLabel(self, value):
        self._before_label = value
        self.update()

    @Property(str)
    def afterLabel(self):
        return self._after_label

    @afterLabel.setter
    def afterLabel(self, value):
        self._after_label = value
        self.update()

    def showEvent(self, event):
        super().showEvent(event)
        if self._animate_on_show:
            # 开启炫酷的初始滑块拉伸展示动效
            self._animation = QPropertyAnimation(self, b"sliderRatio")
            self._animation.setDuration(900)
            self._animation.setStartValue(0.0)
            self._animation.setEndValue(0.5)
            self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._animation.start()

    def sizeHint(self):
        """
        为布局提供一个默认初始大小提示
        """
        return QSize(400, 300)

    def minimumSizeHint(self):
        """
        允许组件在布局中缩小到很小的值，彻底解除对主窗口缩小的硬性限制
        """
        return QSize(100, 100)

    def _calculate_draw_rect(self):
        """
        在组件尺寸 rect 内，以 object-fit: contain 方式计算出图片完整渲染所需的 QRect（居中且不失真）
        """
        W = self.width()
        H = self.height()
        if self._before_pixmap.isNull() or W <= 0 or H <= 0:
            return QRect(0, 0, W, H)
            
        w = self._before_pixmap.width()
        h = self._before_pixmap.height()
        if w <= 0 or h <= 0:
            return QRect(0, 0, W, H)
            
        r_widget = W / H
        r_pixmap = w / h
        
        if r_widget > r_pixmap:
            # 视口比图片更宽，高度填满，宽度缩减并水平居中
            draw_h = H
            draw_w = int(H * r_pixmap)
            draw_x = (W - draw_w) // 2
            draw_y = 0
        else:
            # 视口比图片更高，宽度填满，高度缩减并垂直居中
            draw_w = W
            draw_h = int(W / r_pixmap)
            draw_x = 0
            draw_y = (H - draw_h) // 2
            
        return QRect(draw_x, draw_y, draw_w, draw_h)

    def _is_on_handle(self, pos):
        draw_rect = self._calculate_draw_rect()
        split_x = draw_rect.x() + int(draw_rect.width() * self._slider_ratio)
        # 允许左右有 10px 的可触及误差范围
        return abs(pos.x() - split_x) <= 10

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            pos = event.position()
            draw_rect = self._calculate_draw_rect()
            draw_x = draw_rect.x()
            draw_w = draw_rect.width()
            if draw_w > 0:
                ratio = (pos.x() - draw_x) / draw_w
                self.set_slider_ratio(ratio)
            self.setCursor(Qt.CursorShape.SizeHorCursor)
            event.accept()

    def mouseMoveEvent(self, event):
        pos = event.position()
        if self._is_dragging:
            draw_rect = self._calculate_draw_rect()
            draw_x = draw_rect.x()
            draw_w = draw_rect.width()
            if draw_w > 0:
                ratio = (pos.x() - draw_x) / draw_w
                self.set_slider_ratio(ratio)
            event.accept()
        else:
            if self._is_on_handle(pos):
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = False
            pos = event.position()
            if self._is_on_handle(pos):
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()

    def _draw_fitted_pixmap(self, painter, pixmap, draw_rect, clip_rect):
        """
        利用计算好的目标矩形与遮罩裁剪区绘制对应的 Pixmap
        """
        if pixmap.isNull():
            return
        painter.save()
        painter.setClipRect(clip_rect)
        painter.drawPixmap(draw_rect, pixmap)
        painter.restore()

    def paintEvent(self, event):
        width = self.width()
        height = self.height()
        if width <= 0 or height <= 0:
            return

        draw_rect = self._calculate_draw_rect()
        draw_x = draw_rect.x()
        draw_y = draw_rect.y()
        draw_w = draw_rect.width()
        draw_h = draw_rect.height()

        split_x = draw_x + int(draw_w * self._slider_ratio)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 1. 绘制左侧的图片 (迁移结果/Before)
        if not self._before_pixmap.isNull():
            self._draw_fitted_pixmap(painter, self._before_pixmap, draw_rect, QRect(0, 0, split_x, height))

        # 2. 绘制右侧的图片 (原图/After)
        if not self._after_pixmap.isNull():
            self._draw_fitted_pixmap(painter, self._after_pixmap, draw_rect, QRect(split_x, 0, width - split_x, height))

        # 3. 绘制垂直分割线 (限制在图片实际绘制的高宽内，保证极致的边角美感)
        painter.save()
        line_pen = QPen(QColor(255, 255, 255, 200))
        line_pen.setWidth(2)
        painter.setPen(line_pen)
        painter.drawLine(split_x, draw_y, split_x, draw_y + draw_h)
        painter.restore()

        # 4. 绘制中心圆形滑动磨砂玻璃手柄 (置于图片真实的垂直中线上)
        handle_y = draw_y + draw_h // 2
        handle_radius = 18
        
        painter.save()
        painter.setBrush(QColor(255, 255, 255, 230))
        border_pen = QPen(QColor("#dcdfe6"))
        border_pen.setWidth(1.5)
        painter.setPen(border_pen)
        painter.drawEllipse(QPoint(split_x, handle_y), handle_radius, handle_radius)

        # 绘制矢量左、右小箭头：❮ ❯
        arrow_pen = QPen(QColor("#606266"))
        arrow_pen.setWidth(2)
        arrow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        arrow_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(arrow_pen)
        
        # 左箭头 ❮
        left_arrow = QPainterPath()
        left_arrow.moveTo(split_x - 3, handle_y - 4)
        left_arrow.lineTo(split_x - 7, handle_y)
        left_arrow.lineTo(split_x - 3, handle_y + 4)
        painter.drawPath(left_arrow)
        
        # 右箭头 ❯
        right_arrow = QPainterPath()
        right_arrow.moveTo(split_x + 3, handle_y - 4)
        right_arrow.lineTo(split_x + 7, handle_y)
        right_arrow.lineTo(split_x + 3, handle_y + 4)
        painter.drawPath(right_arrow)
        painter.restore()

        # 5. 绘制浮动半透明文本标签 (贴合在图片内部四个角落，更符合 Web 惯例)
        if self._show_labels:
            font = QFont("Microsoft YaHei", 9, QFont.Weight.Bold)
            
            # 左侧文本标签
            if self._before_label:
                painter.save()
                painter.setFont(font)
                metrics = QFontMetrics(font)
                text_w = metrics.horizontalAdvance(self._before_label)
                text_h = metrics.height()
                
                rect_w = text_w + 20
                rect_h = text_h + 10
                rect_x = draw_x + 15
                rect_y = draw_y + 15
                
                painter.setBrush(QColor(0, 0, 0, 160))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(QRect(rect_x, rect_y, rect_w, rect_h), 4, 4)
                
                painter.setPen(QColor("#ffffff"))
                painter.drawText(QRect(rect_x, rect_y, rect_w, rect_h), Qt.AlignmentFlag.AlignCenter, self._before_label)
                painter.restore()

            # 右侧文本标签
            if self._after_label:
                painter.save()
                painter.setFont(font)
                metrics = QFontMetrics(font)
                text_w = metrics.horizontalAdvance(self._after_label)
                text_h = metrics.height()
                
                rect_w = text_w + 20
                rect_h = text_h + 10
                rect_x = draw_x + draw_w - rect_w - 15
                rect_y = draw_y + 15
                
                painter.setBrush(QColor(0, 0, 0, 160))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(QRect(rect_x, rect_y, rect_w, rect_h), 4, 4)
                
                painter.setPen(QColor("#ffffff"))
                painter.drawText(QRect(rect_x, rect_y, rect_w, rect_h), Qt.AlignmentFlag.AlignCenter, self._after_label)
                painter.restore()
