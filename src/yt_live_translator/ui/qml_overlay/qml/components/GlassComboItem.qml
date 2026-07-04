import QtQuick

SettingRow {
    id: comboItem
    property bool selected: false
    color: selected ? Qt.rgba(0.32, 0.76, 1, 0.20) : hovered ? Qt.rgba(1, 1, 1, 0.12) : "transparent"
}

