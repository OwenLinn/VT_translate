import QtQuick

Rectangle {
    id: badge
    property bool running: false
    property string text: running ? "Running" : "Stopped"

    width: label.implicitWidth + 24
    height: 28
    radius: 14
    color: running ? Qt.rgba(0.12, 0.62, 0.42, 0.45) : Qt.rgba(0.78, 0.78, 0.82, 0.18)
    border.width: 1
    border.color: running ? Qt.rgba(0.65, 1.0, 0.82, 0.45) : Qt.rgba(1, 1, 1, 0.22)

    Text {
        id: label
        anchors.centerIn: parent
        text: badge.text
        color: "white"
        font.pixelSize: 12
        font.bold: true
    }
}

