from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QPushButton, QWidget, QHBoxLayout, QFrame, QLineEdit, QGraphicsDropShadowEffect, QLabel

def add_shaddow(obj):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(10)
    shadow.setXOffset(3)
    shadow.setYOffset(3)
    shadow.setColor(QColor(0, 0, 0, 50))  # прозора чорна тінь
    obj.setGraphicsEffect(shadow)
    return obj

def changeWindowButton(callback_func, width=60, height=60, text_input="Go", backButton=False):
    btn = QPushButton()

    if backButton:
        btn.setIcon(QIcon('main_interface/elements/backButton.png'))
        btn.setFlat(True) #щоб без заднього фону і рамок

    else:
        btn.setText(text_input)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #2ecc71;
                color: white;
                height: {height}px;
                border-radius: 10px;
                font-weight: bold;
                min-width: {width}px;
            }}
        """)
    btn.clicked.connect(callback_func)

    return btn

def topContainer(change_page):
    top_container = QWidget()
    top_container.setFixedHeight(45)

    top_layout = QHBoxLayout(top_container)
    top_layout.addSpacing(10)
    top_layout.addWidget(changeWindowButton(change_page, backButton=True))
    top_layout.addStretch()

    return top_container

def shadowedLabel(text: str, font_size: int = 20, color: str = "#82827B"):
    label = QLabel(text)
    # Стилі для шрифту
    label.setStyleSheet(f"""
        QLabel {{
            font-size: {font_size}px;
            color: {color};
            font-family: Arial, sans-serif;
        }}
    """)
    # Додаємо тінь
    label = add_shaddow(label)
    return label

def horLine():
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)

    line.setFixedHeight(1)
    return line

def lineInput(width, prompt):
    line = QLineEdit()
    line.setStyleSheet("""
        QLineEdit {
            border-radius: 10px;
            background-color: white;
            padding-left: 10px;
            font-size: 14px;
        }
    """)

    line.setFixedSize(width, 40)
    line = add_shaddow(line)

    line.setPlaceholderText(prompt)
    return line

def mainContainer(width=700, height=400):
    main_container = QWidget()
    main_container.setMinimumSize(width, height)
    main_layout = QHBoxLayout(main_container)
    return main_container


