import QtQuick

GlassCard {
    id: card
    signal rowRequested(string kind)
    property var bridge
    property bool open: false
    property bool tuningMode: false
    variant: "card"

    height: open ? content.implicitHeight + 28 : 0
    opacity: open ? 1 : 0
    visible: opacity > 0.01
    clip: true

    Behavior on height { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
    Behavior on opacity { NumberAnimation { duration: 160; easing.type: Easing.OutCubic } }

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
            height: 34
            spacing: 10
            Text {
                text: "Glass Control Hub"
                color: "white"
                font.pixelSize: 15
                font.bold: true
                anchors.verticalCenter: parent.verticalCenter
            }
            Item { width: parent.width - 210; height: 1 }
            StatusBadge {
                running: bridge ? bridge.isRunning : false
                anchors.verticalCenter: parent.verticalCenter
            }
        }

        Item {
            width: parent.width
            height: 38
            LiquidThumb {
                anchors.fill: parent
                selectedIndex: bridge && bridge.isRunning ? 0 : 1
                itemCount: 2
                moveMs: bridge ? bridge.thumbMoveMs : 220
                stretchScale: bridge ? bridge.thumbStretchScale : 1.10
                compressScale: bridge ? bridge.thumbCompressScale : 0.96
            }
            PillButton {
                anchors.left: parent.left
                width: parent.width / 2
                height: parent.height
                text: "Start"
                active: bridge ? bridge.isRunning : false
                onClicked: if (bridge) bridge.startTranslation()
            }
            PillButton {
                anchors.right: parent.right
                width: parent.width / 2
                height: parent.height
                text: "Stop"
                onClicked: if (bridge) bridge.stopTranslation()
            }
        }

        SettingRow {
            width: parent.width
            label: "API Key"
            value: bridge ? bridge.apiKeyStatus : "missing"
            interactive: false
        }
        SettingRow {
            width: parent.width
            label: "Source"
            value: bridge ? bridge.sourceLanguage : "auto"
            onClicked: card.rowRequested("sourceLanguage")
        }
        SettingRow {
            width: parent.width
            label: "Target"
            value: bridge ? bridge.targetLanguage : "zh-TW"
            onClicked: card.rowRequested("targetLanguage")
        }
        SettingRow {
            width: parent.width
            label: "ASR Model"
            value: bridge ? bridge.asrModel : ""
            onClicked: card.rowRequested("asrModel")
        }
        SettingRow {
            width: parent.width
            label: "DeepSeek"
            value: bridge ? bridge.deepseekModel : ""
            onClicked: card.rowRequested("deepseekModel")
        }
        SettingRow {
            width: parent.width
            label: "Source Text"
            value: bridge && bridge.showSource ? "Shown" : "Hidden"
            onClicked: if (bridge) bridge.setShowSource(!bridge.showSource)
        }

        TuningPanel {
            width: parent.width
            visible: card.tuningMode
            bridge: card.bridge
        }
    }
}
