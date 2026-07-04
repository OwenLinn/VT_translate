import QtQuick

Rectangle {
    id: button
    signal clicked()
    property string text: "Button"
    property bool active: false
    property bool hovered: false
    property bool pressed: false

    height: 34
    radius: 17
    color: pressed ? Qt.rgba(1, 1, 1, 0.28) : active ? Qt.rgba(0.32, 0.76, 1, 0.32) : Qt.rgba(1, 1, 1, 0.16)
    border.width: 1
    border.color: hovered ? Qt.rgba(1, 1, 1, 0.48) : Qt.rgba(1, 1, 1, 0.22)

    Text {
        anchors.centerIn: parent
        text: button.text
        color: "white"
        font.pixelSize: 13
        font.bold: true
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        onEntered: button.hovered = true
        onExited: button.hovered = false
        onPressed: button.pressed = true
        onReleased: button.pressed = false
        onCanceled: button.pressed = false
        onClicked: button.clicked()
    }
}

