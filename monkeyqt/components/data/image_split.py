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

    def get_image_rect(self):
        """
        计算图片以 contain 模式渲染时的实际区域（独立视口缩放）。
        返回 QRect，表示图片在面板中的渲染位置和尺寸。
        """
        W = self.width()
        H = self.height()
        if self._pixmap.isNull() or W <= 0 or H <= 0:
            return QRect(0, 0, W, H)
        
        w = self._pixmap.width()
        h = self._pixmap.height()
        r_pixmap = w / h
        
        # 获取 parent 中的 W_total 和 split_ratio
        W_total = W
        split_ratio = 0.5
        if isinstance(self.parent(), QWidget):
            W_total = self.parent().width()
            if hasattr(self.parent(), "splitRatio"):
                split_ratio = self.parent().splitRatio
                
        # 计算整个组件中单个图像 contain 时的理想宽度
        r_total = W_total / H
        if r_total > r_pixmap:
            ideal_w = int(H * r_pixmap)
        else:
            ideal_w = W_total
            
        # 根据面板左右对齐，计算实际绘制宽度
        max_w = min(W, int(H * r_pixmap))
        if self._align_right:
            # 右面板：当 split_ratio > 0.5 时收缩至 0
            if split_ratio > 0.5:
                scale = (1.0 - split_ratio) / 0.5
                draw_w = int(max_w * scale)
            else:
                draw_w = max_w
            draw_x = 0
        else:
            # 左面板：当 split_ratio < 0.5 时收缩至 0
            if split_ratio < 0.5:
                scale = split_ratio / 0.5
                draw_w = int(max_w * scale)
            else:
                draw_w = max_w
            draw_x = W - draw_w
            
        draw_h = int(draw_w / r_pixmap) if draw_w > 0 else 0
        draw_y = (H - draw_h) // 2
        
        return QRect(draw_x, draw_y, draw_w, draw_h)

    def paintEvent(self, event):
        W = self.width()
        H = self.height()
        if W <= 0 or H <= 0:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.get_image_rect()
        
        # 1. 独立视口内绘制图片
        if not self._pixmap.isNull():
            painter.drawPixmap(rect, self._pixmap)

        # 2. 绘制浮动半透明文本标签
        if self._label and rect.width() > 0:
            font = QFont("Microsoft YaHei", 9, QFont.Weight.Bold)
            painter.setFont(font)
            metrics = QFontMetrics(font)
            text_w = metrics.horizontalAdvance(self._label)
            text_h = metrics.height()
            
            rect_w = text_w + 20
            rect_h = text_h + 10
            
            # 标签悬浮在图片边缘
            if self._align_right:
                label_x = rect.x() + rect.width() - rect_w - 15
            else:
                label_x = rect.x() + 15
                
            label_y = rect.y() + 15
            
            # 画圆角卡片底牌
            painter.setBrush(QColor(0, 0, 0, 160))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRect(label_x, label_y, rect_w, rect_h), 4, 4)
            
            # 写白色文字
            painter.setPen(QColor("#ffffff"))
            painter.drawText(QRect(label_x, label_y, rect_w, rect_h), Qt.AlignmentFlag.AlignCenter, self._label)

class MkSplitterHandle(QWidget):
    """
    分屏器的玻璃手柄，支持拖动、悬浮高亮、点击左/右键独立折叠或展开侧边栏。
    手柄的分割线和胶囊会自动对齐图片实际渲染区域的边界。
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.SizeHorCursor)
        self._hover_area = None  # None, "left", "right"
        self._drag_start_x = 0
        self._drag_start_ratio = 0.5
        # 图片实际渲染区域的纵向边界
        self._image_top = 0
        self._image_bottom = 0

    def set_image_bounds(self, top, bottom):
        """设置图片渲染区域的纵向边界，手柄将据此对齐。"""
        self._image_top = top
        self._image_bottom = bottom
        self.update()

    def _capsule_center_y(self):
        """计算胶囊的纵向中心位置——在图片渲染区域内垂直居中。"""
        img_top = self._image_top
        img_bottom = self._image_bottom if self._image_bottom > self._image_top else self.height()
        return (img_top + img_bottom) // 2

    def _get_area(self, pos):
        # 玻璃胶囊的高度为 60px 宽度 20px，贴合图片底部边框
        cy = self._capsule_center_y()
        if cy - 30 <= pos.y() <= cy + 30:
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
            ideal_w = self.parent().get_ideal_image_width()
            if ideal_w <= 0:
                ideal_w = self.parent().width()
            new_ratio = self._drag_start_ratio + delta_x / ideal_w
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
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 获取图片渲染区域的纵向边界
        img_top = self._image_top
        img_bottom = self._image_bottom if self._image_bottom > self._image_top else self.height()
        
        # 1. 绘制纵向极细分割线 —— 仅在图片渲染区域内绘制
        line_pen = QPen(QColor("#ebeef5"))
        line_pen.setWidth(1.5)
        painter.setPen(line_pen)
        painter.drawLine(12, img_top, 12, img_bottom)
        
        # 2. 绘制磨砂玻璃胶囊 —— 贴合图片底部边框
        cy = self._capsule_center_y()
        capsule_rect = QRect(2, cy - 30, 20, 60)
        
        # 半透明磨砂背景
        painter.setBrush(QColor(255, 255, 255, 240))
        painter.setPen(QPen(QColor("#dcdfe6"), 1))
        painter.drawRoundedRect(capsule_rect, 10, 10)
        
        # 3. 绘制胶囊内部的短中分线
        painter.setPen(QPen(QColor("#ebeef5"), 1))
        painter.drawLine(12, cy - 20, 12, cy + 20)
        
        # 4. 绘制左/右侧悬浮高亮状态的矢量方向箭头
        # 左箭头
        if self._hover_area == "left":
            painter.setPen(QPen(QColor("#409eff"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        else:
            painter.setPen(QPen(QColor("#909399"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            
        left_path = QPainterPath()
        left_path.moveTo(8, cy - 4)
        left_path.lineTo(5, cy)
        left_path.lineTo(8, cy + 4)
        painter.drawPath(left_path)
        
        # 右箭头
        if self._hover_area == "right":
            painter.setPen(QPen(QColor("#409eff"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        else:
            painter.setPen(QPen(QColor("#909399"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            
        right_path = QPainterPath()
        right_path.moveTo(16, cy - 4)
        right_path.lineTo(19, cy)
        right_path.lineTo(16, cy + 4)
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
        - 两者均为 None：重置为均等分屏（保持手柄可见）。
        - left 有值但 right 为 None：仅展示原图，隐藏手柄并动画收缩。
        - 两者均有值：显示手柄并执行向左滑开对比的平滑动画。
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
            if left is None:
                # 全部重置：保持均等分屏，手柄可见
                self.handle.show()
                self.splitRatio = 0.5
            else:
                # 仅有原图，隐藏手柄，全屏展示左侧
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

    def get_ideal_image_width(self):
        """
        计算在当前组件尺寸 (W, H) 下，单个图片以 contain 模式渲染时的理想宽度。
        """
        W = self.width()
        H = self.height()
        if W <= 0 or H <= 0:
            return W
            
        pixmap = None
        if not self.left_panel._pixmap.isNull():
            pixmap = self.left_panel._pixmap
        elif not self.right_panel._pixmap.isNull():
            pixmap = self.right_panel._pixmap
            
        if pixmap is None or pixmap.isNull():
            return W
            
        w = pixmap.width()
        h = pixmap.height()
        if h <= 0:
            return W
            
        r_pixmap = w / h
        r_total = W / H
        if r_total > r_pixmap:
            return int(H * r_pixmap)
        else:
            return W

    def update_layout(self):
        W = self.width()
        H = self.height()
        if W <= 0 or H <= 0:
            return
            
        ideal_w = self.get_ideal_image_width()
        
        # 计算基于实际图片边界映射的 split_x
        min_x = (W - ideal_w) // 2
        max_x = (W + ideal_w) // 2
        split_x = int(min_x + self._split_ratio * (max_x - min_x))
        
        # 胶囊手柄 x 轴计算，放置在 split_x 处
        handle_x = split_x - 12
        self.handle.setGeometry(handle_x, 0, 24, H)
        
        # 左面板几何位置
        self.left_panel.setGeometry(0, 0, split_x, H)
        
        # 右面板几何位置
        self.right_panel.setGeometry(split_x, 0, W - split_x, H)
        
        # 计算图片实际渲染区域的联合边界，让手柄对齐图片内容
        top = 0
        bottom = H
        if not self.left_panel._pixmap.isNull() and not self.right_panel._pixmap.isNull():
            rect_l = self.left_panel.get_image_rect()
            rect_r = self.right_panel.get_image_rect()
            top = min(rect_l.y(), rect_r.y())
            bottom = max(rect_l.y() + rect_l.height(), rect_r.y() + rect_r.height())
        elif not self.left_panel._pixmap.isNull():
            rect = self.left_panel.get_image_rect()
            top = rect.y()
            bottom = rect.y() + rect.height()
        elif not self.right_panel._pixmap.isNull():
            rect = self.right_panel.get_image_rect()
            top = rect.y()
            bottom = rect.y() + rect.height()
            
        self.handle.set_image_bounds(top, bottom)
        
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
        左箭头控制：若处于全开/全闭状态，则恢复到上次比例；否则平滑向左收缩到 0.0。
        """
        if self._split_ratio in (0.0, 1.0):
            target = self._last_split_ratio if 0.0 < self._last_split_ratio < 1.0 else 0.5
            self._animate_split_ratio(target)
        else:
            self._last_split_ratio = self._split_ratio
            self._animate_split_ratio(0.0)

    def _on_right_arrow_clicked(self):
        """
        右箭头控制：若处于全开/全闭状态，则恢复到上次比例；否则平滑向右收缩到 1.0。
        """
        if self._split_ratio in (0.0, 1.0):
            target = self._last_split_ratio if 0.0 < self._last_split_ratio < 1.0 else 0.5
            self._animate_split_ratio(target)
        else:
            self._last_split_ratio = self._split_ratio
            self._animate_split_ratio(1.0)
