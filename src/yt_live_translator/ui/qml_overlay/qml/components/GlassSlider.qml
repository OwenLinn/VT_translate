import QtQuick

Item {
    id: slider
    property real value: 0.5
    property string label: ""
    property string valueText: Math.round(value * 100) + "%"
    signal valueChangedByUser(real value)

    height: 42

    Text {
        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter
        text: slider.label
        color: Qt.rgba(1, 1, 1, 0.72)
        font.pixelSize: 13
    }

    Text {
        anchors.right: track.left
        anchors.rightMargin: 10
        anchors.verticalCenter: parent.verticalCenter
        text: slider.valueText
        color: "white"
        font.pixelSize: 12
        font.bold: true
    }

    Rectangle {
        id: track
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        width: parent.width * 0.55
        height: 8
        radius: 4
        color: Qt.rgba(1, 1, 1, 0.18)

        Rectangle {
            width: track.width * Math.max(0, Math.min(1, slider.value))
            height: parent.height
            radius: parent.radius
            color: Qt.rgba(0.45, 0.80, 1.0, 0.72)
        }

        MouseArea {
            anchors.fill: parent
            onPressed: update(mouse.x)
            onPositionChanged: if (pressed) update(mouse.x)
            function update(xPos) {
                slider.value = Math.max(0, Math.min(1, xPos / track.width))
                slider.valueChangedByUser(slider.value)
            }
        }
    }
}
