from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtCore import Qt, Property, QRect, QPoint, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QPainter, QPixmap, QImage, QColor, QPen, QFont, QFontMetrics, QPainterPath

class MkImagePanel(QWidget):
    """
    单个图片面板，负责以 object-fit: contain 方式完整无损渲染图片，并支持悬浮文本标签。
    """
    def __init__(self, label="", align_right=False, parent=None):
        super().__init__(parent)
        self._pixmap = QPixmap()
        self._label = label
        self._align_right = align_right

    def set_pixmap(self, pixmap):
        self._pixmap = pixmap
        self.update()

    def set_label(self, label):
        self._label = label
        self.update()

    def paintEvent(self, event):
        W = self.width()
        H = self.height()
        if W <= 0 or H <= 0:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 默认绘图与标签坐标范围
        draw_x = 0
        draw_y = 0
        draw_w = W
        draw_h = H
        
        # 1. 以 object-fit: contain 方式绘制完整图片 (无损、不裁剪)
        if not self._pixmap.isNull():
            w = self._pixmap.width()
            h = self._pixmap.height()
            
            r_panel = W / H
            r_pixmap = w / h
            
            if r_panel > r_pixmap:
                draw_h = H
                draw_w = int(H * r_pixmap)
                
                # 获取父组件的分割比例，实现平滑对齐过渡
                split_ratio = 0.5
                if self.parent() and hasattr(self.parent(), "splitRatio"):
                    split_ratio = self.parent().splitRatio
                
                draw_x_centered = (W - draw_w) // 2
                
                if self._align_right:
                    # 右面板：默认靠左对齐以贴合分割线；当分割比例收缩至 0.0 时，平滑过渡到居中对齐
                    draw_x_left = 0
                    t = max(0.0, min(1.0, (0.5 - split_ratio) / 0.5)) if split_ratio < 0.5 else 0.0
                    draw_x = int(t * draw_x_centered + (1.0 - t) * draw_x_left)
                else:
                    # 左面板：默认靠右对齐以贴合分割线；当分割比例收缩至 1.0 时，平滑过渡到居中对齐
                    draw_x_right = W - draw_w
                    t = max(0.0, min(1.0, (split_ratio - 0.5) / 0.5)) if split_ratio > 0.5 else 0.0
                    draw_x = int(t * draw_x_centered + (1.0 - t) * draw_x_right)
                draw_y = 0
            else:
                draw_w = W
                draw_h = int(W / r_pixmap)
                draw_x = 0
                draw_y = (H - draw_h) // 2
                
            painter.drawPixmap(QRect(draw_x, draw_y, draw_w, draw_h), self._pixmap)

        # 2. 绘制浮动半透明文本标签 (贴合在图片实际渲染区内部，极致的视觉一致性)
        if self._label:
            font = QFont("Microsoft YaHei", 9, QFont.Weight.Bold)
            painter.setFont(font)
            metrics = QFontMetrics(font)
            text_w = metrics.horizontalAdvance(self._label)
            text_h = metrics.height()
            
            rect_w = text_w + 20
            rect_h = text_h + 10
            
            if self._align_right:
                rect_x = draw_x + draw_w - rect_w - 15
            else:
                rect_x = draw_x + 15
            rect_y = draw_y + 15
            
            # 画圆角卡片底牌
            painter.setBrush(QColor(0, 0, 0, 160))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRect(rect_x, rect_y, rect_w, rect_h), 4, 4)
            
            # 写白色文字
            painter.setPen(QColor("#ffffff"))
            painter.drawText(QRect(rect_x, rect_y, rect_w, rect_h), Qt.AlignmentFlag.AlignCenter, self._label)

class MkSplitterHandle(QWidget):
    """
    分屏器的玻璃手柄，支持拖动、悬浮高亮、点击左/右键独立折叠或展开侧边栏。
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.SizeHorCursor)
        self._hover_area = None  # None, "left", "right"
        self._drag_start_x = 0
        self._drag_start_ratio = 0.5

    def _get_area(self, pos):
        # 玻璃胶囊的高度为 60px 宽度 20px，在手柄中央
        h_y = self.height() // 2
        if h_y - 30 <= pos.y() <= h_y + 30:
            if 2 <= pos.x() < 12:
                return "left"
            elif 12 <= pos.x() <= 22:
                return "right"
        return "drag"

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            area = self._get_area(pos)
            if area == "left":
                self.parent()._on_left_arrow_clicked()
                event.accept()
            elif area == "right":
                self.parent()._on_right_arrow_clicked()
                event.accept()
            else:
                self.parent()._is_dragging = True
                self._drag_start_x = event.globalPosition().x()
                self._drag_start_ratio = self.parent().splitRatio
                event.accept()

    def mouseMoveEvent(self, event):
        pos = event.position()
        if self.parent()._is_dragging:
            delta_x = event.globalPosition().x() - self._drag_start_x
            new_ratio = self._drag_start_ratio + delta_x / self.parent().width()
            self.parent().splitRatio = new_ratio
            event.accept()
        else:
            area = self._get_area(pos)
            if area != self._hover_area:
                self._hover_area = area
                self.update()
                
            if area in ["left", "right"]:
                self.setCursor(Qt.CursorShape.PointingHandCursor)
            else:
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            event.accept()

    def leaveEvent(self, event):
        self._hover_area = None
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.update()
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.parent()._is_dragging = False
            event.accept()

    def paintEvent(self, event):
        height = self.height()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 1. 绘制纵向极细分割线
        line_pen = QPen(QColor("#ebeef5"))
        line_pen.setWidth(1.5)
        painter.setPen(line_pen)
        painter.drawLine(12, 0, 12, height)
        
        # 2. 绘制磨砂玻璃胶囊
        handle_y = height // 2
        capsule_rect = QRect(2, handle_y - 30, 20, 60)
        
        # 半透明磨砂背景
        painter.setBrush(QColor(255, 255, 255, 240))
        painter.setPen(QPen(QColor("#dcdfe6"), 1))
        painter.drawRoundedRect(capsule_rect, 10, 10)
        
        # 3. 绘制胶囊内部的短中分线
        painter.setPen(QPen(QColor("#ebeef5"), 1))
        painter.drawLine(12, handle_y - 20, 12, handle_y + 20)
        
        # 4. 绘制左/右侧悬浮高亮状态的矢量方向箭头
        # 左箭头
        if self._hover_area == "left":
            painter.setPen(QPen(QColor("#409eff"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        else:
            painter.setPen(QPen(QColor("#909399"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            
        left_path = QPainterPath()
        left_path.moveTo(8, handle_y - 4)
        left_path.lineTo(5, handle_y)
        left_path.lineTo(8, handle_y + 4)
        painter.drawPath(left_path)
        
        # 右箭头
        if self._hover_area == "right":
            painter.setPen(QPen(QColor("#409eff"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        else:
            painter.setPen(QPen(QColor("#909399"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            
        right_path = QPainterPath()
        right_path.moveTo(16, handle_y - 4)
        right_path.lineTo(19, handle_y)
        right_path.lineTo(16, handle_y + 4)
        painter.drawPath(right_path)

class MkImageSplit(QWidget):
    """
    MkImageSplit - Resizable & Collapsible Side-by-Side Image Split Container.
    Features:
    - Side-by-side full image rendering (contain fit).
    - Drag to resize division horizontally.
    - Click left/right arrows on a capsule glass handle to smoothly collapse/expand either panel.
    - Integrates QPropertyAnimation for premium desktop transition effects.
    - Fully compatible with QSizePolicy and heightForWidth to adapt size dynamically.
    """
    
    def __init__(self, left_img=None, right_img=None, parent=None):
        super().__init__(parent)
        
        self._split_ratio = 0.5
        self._last_split_ratio = 0.5
        self._is_dragging = False
        self._animate_duration = 400
        
        # 配置布局的大小的自适应策略 (Expanding in both directions)
        size_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setSizePolicy(size_policy)
        
        # 实例化左、右面板及手柄 (左侧为原图，右侧为修复/迁移结果)
        self.left_panel = MkImagePanel(label="原图", align_right=False, parent=self)
        self.right_panel = MkImagePanel(label="迁移结果", align_right=True, parent=self)
        self.handle = MkSplitterHandle(parent=self)
        
        if left_img is not None and right_img is not None:
            self.set_images(left_img, right_img)
            
        self.update_layout()

    def set_images(self, left, right):
        """
        设置对比图片。支持传入文件路径、QPixmap 或 QImage。
        如果 right 为 None，则隐藏手柄，只居中显示原图；
        当传入有效的 right 时，显示手柄并执行向左滑开对比的平滑动画。
        """
        if left is None:
            self.left_panel.set_pixmap(QPixmap())
        elif isinstance(left, str):
            self.left_panel.set_pixmap(QPixmap(left))
        elif isinstance(left, QPixmap):
            self.left_panel.set_pixmap(left)
        elif isinstance(left, QImage):
            self.left_panel.set_pixmap(QPixmap.fromImage(left))
            
        if right is None:
            self.right_panel.set_pixmap(QPixmap())
            self.handle.hide()
            self.splitRatio = 1.0
        else:
            if isinstance(right, str):
                self.right_panel.set_pixmap(QPixmap(right))
            elif isinstance(right, QPixmap):
                self.right_panel.set_pixmap(right)
            elif isinstance(right, QImage):
                self.right_panel.set_pixmap(QPixmap.fromImage(right))
            
            self.handle.show()
            if self._split_ratio >= 0.99:
                self._animate_split_ratio(0.5)
            else:
                self.update_layout()

    def set_labels(self, left_label: str, right_label: str):
        """
        设置左、右面板的浮动文本标签。
        """
        self.left_panel.set_label(left_label)
        self.right_panel.set_label(right_label)

    @Property(float)
    def splitRatio(self):
        return self._split_ratio

    @splitRatio.setter
    def splitRatio(self, value):
        val = max(0.0, min(1.0, float(value)))
        if self._split_ratio == val:
            return
        self._split_ratio = val
        self.update_layout()
        self.update()

    def update_layout(self):
        W = self.width()
        H = self.height()
        if W <= 0 or H <= 0:
            return
            
        split_x = int(W * self._split_ratio)
        
        # 胶囊手柄 x 轴计算，并确保不会划出可视区域
        handle_x = max(0, min(W - 24, split_x - 12))
        self.handle.setGeometry(handle_x, 0, 24, H)
        
        # 左面板几何位置
        self.left_panel.setGeometry(0, 0, split_x, H)
        
        # 右面板几何位置
        self.right_panel.setGeometry(split_x, 0, W - split_x, H)
        
        self.handle.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_layout()

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

    def _animate_split_ratio(self, target):
        self._anim = QPropertyAnimation(self, b"splitRatio")
        self._anim.setDuration(self._animate_duration)
        self._anim.setStartValue(self._split_ratio)
        self._anim.setEndValue(target)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()

    def _on_left_arrow_clicked(self):
        """
        左箭头控制：若左侧有宽度，则平滑向左收缩到 0.0；若已处于收缩状态，则还原。
        """
        if self._split_ratio > 0.0:
            self._last_split_ratio = self._split_ratio
            self._animate_split_ratio(0.0)
        else:
            target = self._last_split_ratio if self._last_split_ratio > 0.0 else 0.5
            self._animate_split_ratio(target)

    def _on_right_arrow_clicked(self):
        """
        右箭头控制：若右侧有宽度，则平滑向右收缩到 1.0；若已处于收缩状态，则还原。
        """
        if self._split_ratio < 1.0:
            self._last_split_ratio = self._split_ratio
            self._animate_split_ratio(1.0)
        else:
            target = self._last_split_ratio if self._last_split_ratio < 1.0 else 0.5
            self._animate_split_ratio(target)
