import QtQuick

Rectangle {
    id: row
    signal clicked()
    property string label: ""
    property string value: ""
    property bool interactive: true
    property bool hovered: false

    height: 40
    radius: 14
    color: hovered && interactive ? Qt.rgba(1, 1, 1, 0.12) : "transparent"

    Text {
        anchors.left: parent.left
        anchors.leftMargin: 12
        anchors.verticalCenter: parent.verticalCenter
        text: row.label
        color: Qt.rgba(1, 1, 1, 0.72)
        font.pixelSize: 13
    }

    Text {
        anchors.right: parent.right
        anchors.rightMargin: 12
        anchors.verticalCenter: parent.verticalCenter
        width: parent.width * 0.52
        text: row.value
        color: "white"
        font.pixelSize: 13
        font.bold: true
        horizontalAlignment: Text.AlignRight
        elide: Text.ElideMiddle
    }

    MouseArea {
        anchors.fill: parent
        enabled: row.interactive
        hoverEnabled: true
        onEntered: row.hovered = true
        onExited: row.hovered = false
        onClicked: row.clicked()
    }
}

