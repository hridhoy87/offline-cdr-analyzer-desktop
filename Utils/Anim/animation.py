from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QPoint, QSize
from PyQt6.QtWidgets import QGraphicsOpacityEffect

def apply_mac_open_animation(widget, duration=300):
    """
    Applies a macOS-style zoom + fade-in elastic transition to a window/widget.
    """
    # 1. Setup Opacity (Fade In)
    opacity_effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(opacity_effect)
    
    opacity_anim = QPropertyAnimation(opacity_effect, b"opacity")
    opacity_anim.setDuration(duration)
    opacity_anim.setStartValue(0.0)
    opacity_anim.setEndValue(1.0)
    opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    # 2. Setup Geometry (Scale up from center)
    geom = widget.geometry()
    center = geom.center()
    
    # Start slightly smaller and centered
    start_width = int(geom.width() * 0.85)
    start_height = int(geom.height() * 0.85)
    start_x = center.x() - (start_width // 2)
    start_y = center.y() - (start_height // 2)
    
    geom_anim = QPropertyAnimation(widget, b"geometry")
    geom_anim.setDuration(duration)
    geom_anim.setStartValue(QPoint(start_x, start_y))
    geom_anim.setEndValue(geom)
    
    # OutBack gives it that signature subtle macOS elastic "bounce" at the end
    geom_anim.setEasingCurve(QEasingCurve.Type.OutBack) 
    
    # 3. Group them together to play in parallel
    widget._anim_group = QParallelAnimationGroup(widget)
    widget._anim_group.addAnimation(opacity_anim)
    widget._anim_group.addAnimation(geom_anim)
    
    # Keep reference alive
    widget._opacity_effect = opacity_effect 
    
    widget._anim_group.start()