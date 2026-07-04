import QtQuick

GlassCard {
    id: popover
    signal selected(string value)
    signal closeRequested()
    property string title: ""
    property var options: []
    variant: "popover"

    height: visible ? content.implicitHeight + 28 : 0
    opacity: visible ? 1 : 0
    clip: true

    Column {
        id: content
        z: 3
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 14
        spacing: 8

        Row {
            width: parent.width
            height: 30
            Text {
                text: popover.title
                color: "white"
                font.pixelSize: 15
                font.bold: true
                anchors.verticalCenter: parent.verticalCenter
            }
            Item { width: parent.width - 170; height: 1 }
            PillButton {
                width: 62
                text: "Close"
                onClicked: popover.closeRequested()
            }
        }

        Repeater {
            model: popover.options
            delegate: SettingRow {
                width: content.width
                label: modelData.label
                value: modelData.value
                onClicked: popover.selected(modelData.value)
            }
        }
    }
}
