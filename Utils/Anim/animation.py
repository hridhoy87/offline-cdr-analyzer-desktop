from PyQt6.QtCore import (
    QPropertyAnimation,
    QEasingCurve,
    QParallelAnimationGroup,
    QRect
)
from PyQt6.QtWidgets import QGraphicsOpacityEffect


def apply_mac_open_animation(widget, duration=400):
    """
    Very close to the real macOS window opening animation.
    """

    geom = widget.geometry()
    center = geom.center()

    # Start at 97% size
    scale = 0.10

    start_w = int(geom.width() * scale)
    start_h = int(geom.height() * scale)

    start_x = center.x() - start_w // 2
    start_y = center.y() - start_h // 2

    start_rect = QRect(
        start_x,
        start_y,
        start_w,
        start_h
    )

    # Fade
    opacity_effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(opacity_effect)

    opacity_anim = QPropertyAnimation(opacity_effect, b"opacity")
    opacity_anim.setDuration(duration)
    opacity_anim.setStartValue(0.75)
    opacity_anim.setEndValue(1.0)
    opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    # Scale
    geom_anim = QPropertyAnimation(widget, b"geometry")
    geom_anim.setDuration(duration)
    geom_anim.setStartValue(start_rect)
    geom_anim.setEndValue(geom)
    geom_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    group = QParallelAnimationGroup(widget)
    group.addAnimation(opacity_anim)
    group.addAnimation(geom_anim)

    widget._anim_group = group
    widget._opacity_effect = opacity_effect

    group.start()