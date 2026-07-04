import QtQuick
import QtQuick.Window
import "components"

Window {
    id: overlayWindow
    width: qmlOverlayConfig.width
    height: controlHub.open ? (qmlOverlayConfig.tuningMode ? 650 : 360) : qmlOverlayConfig.height
    x: qmlOverlayConfig.x
    y: qmlOverlayConfig.y
    visible: true
    color: qmlOverlayConfig.transparentBackground ? "transparent" : "#101218"
    flags: (qmlOverlayConfig.frameless ? Qt.FramelessWindowHint : Qt.Window)
           | (qmlOverlayConfig.alwaysOnTop ? Qt.WindowStaysOnTopHint : 0)

    property bool popoverOpen: false
    property string popoverTitle: ""
    property var popoverOptions: []
    property string popoverKind: ""

    function openOptions(kind, title, options) {
        popoverKind = kind
        popoverTitle = title
        popoverOptions = options
        popoverOpen = true
    }

    function applyOption(value) {
        if (popoverKind === "sourceLanguage") {
            overlayBridge.setSourceLanguage(value)
        } else if (popoverKind === "targetLanguage") {
            overlayBridge.setTargetLanguage(value)
        } else if (popoverKind === "asrModel") {
            overlayBridge.setAsrModel(value)
        } else if (popoverKind === "deepseekModel") {
            overlayBridge.setDeepseekModel(value)
        }
        popoverOpen = false
    }

    Item {
        anchors.fill: parent

        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.LeftButton
            onClicked: popoverOpen = false
            onPressed: {
                if (!controlHub.open && overlayWindow.startSystemMove) {
                    overlayWindow.startSystemMove()
                }
            }
        }

        SubtitleBar {
            id: subtitleBar
            anchors.left: parent.left
            anchors.right: qmlOverlayConfig.showSettingsIcon ? settingsButton.left : parent.right
            anchors.rightMargin: qmlOverlayConfig.showSettingsIcon ? 12 : 0
            anchors.top: parent.top
            height: qmlOverlayConfig.height
            sourceText: overlayBridge.sourceText
            translatedText: overlayBridge.translatedText
            showSource: overlayBridge.showSource
            showTranslation: overlayBridge.showTranslation
            isPartial: overlayBridge.isPartial
            subtitleOpacity: overlayBridge.subtitleOpacity
            glassOpacity: overlayBridge.glassOpacity
            glassIridescence: overlayBridge.glassIridescence
            translationFontSize: overlayBridge.translationFontSize
            sourceFontSize: overlayBridge.sourceFontSize
            fontFamily: qmlOverlayConfig.fontFamily
            translationColor: qmlOverlayConfig.translationColor
            sourceColor: qmlOverlayConfig.sourceColor
            panelTintOpacity: overlayBridge.panelTintOpacity
            radius: overlayBridge.cornerRadius
            edgeWidth: overlayBridge.edgeWidth
            edgeOpacity: overlayBridge.edgeOpacity
            edgeDarkening: overlayBridge.edgeDarkening
            distortion: overlayBridge.distortion
            reflectPower: overlayBridge.reflectPower
            rgbShift: overlayBridge.rgbShift
            cyanEdgeOpacity: overlayBridge.cyanEdgeOpacity
            magentaEdgeOpacity: overlayBridge.magentaEdgeOpacity
            warmEdgeOpacity: overlayBridge.warmEdgeOpacity
            borderOpacity: overlayBridge.edgeOpacity
            highlightOpacity: overlayBridge.highlightOpacity
            radialHighlightOpacity: overlayBridge.radialHighlightOpacity
            topHighlightHeight: overlayBridge.topHighlightHeight
            shadowOpacity: overlayBridge.shadowOpacity
            shadowRadius: overlayBridge.shadowRadius
            shadowYOffset: overlayBridge.shadowYOffset
            iridescenceWidth: overlayBridge.iridescenceWidth
            animationMs: overlayBridge.animationMs
        }

        SettingsIconButton {
            id: settingsButton
            visible: qmlOverlayConfig.showSettingsIcon
            anchors.right: parent.right
            anchors.top: parent.top
            width: 64
            height: 64
            open: controlHub.open
            onClicked: {
                controlHub.open = !controlHub.open
                popoverOpen = false
            }
        }

        ControlHubCard {
            id: controlHub
            anchors.top: subtitleBar.bottom
            anchors.topMargin: 14
            anchors.right: parent.right
            width: 360
            bridge: overlayBridge
            tuningMode: qmlOverlayConfig.tuningMode
            glassOpacity: overlayBridge.cardOpacity
            panelTintOpacity: overlayBridge.panelTintOpacity
            radius: overlayBridge.cardCornerRadius
            edgeWidth: overlayBridge.edgeWidth
            edgeOpacity: overlayBridge.edgeOpacity
            edgeDarkening: overlayBridge.edgeDarkening
            distortion: overlayBridge.distortion
            reflectPower: overlayBridge.reflectPower
            rgbShift: overlayBridge.rgbShift
            cyanEdgeOpacity: overlayBridge.cyanEdgeOpacity
            magentaEdgeOpacity: overlayBridge.magentaEdgeOpacity
            warmEdgeOpacity: overlayBridge.warmEdgeOpacity
            borderOpacity: overlayBridge.edgeOpacity
            highlightOpacity: overlayBridge.highlightOpacity
            radialHighlightOpacity: overlayBridge.radialHighlightOpacity
            topHighlightHeight: overlayBridge.topHighlightHeight
            shadowOpacity: overlayBridge.shadowOpacity
            shadowRadius: overlayBridge.shadowRadius
            shadowYOffset: overlayBridge.shadowYOffset
            iridescenceOpacity: overlayBridge.glassIridescence
            iridescenceWidth: overlayBridge.iridescenceWidth
            animationMs: overlayBridge.animationMs
            onRowRequested: function(kind) {
                if (kind === "sourceLanguage") {
                    openOptions(kind, "Source language", [
                        {"label": "Auto", "value": "auto"},
                        {"label": "English", "value": "en"},
                        {"label": "Japanese", "value": "ja"}
                    ])
                } else if (kind === "targetLanguage") {
                    openOptions(kind, "Target language", [
                        {"label": "Traditional Chinese", "value": "zh-TW"},
                        {"label": "Simplified Chinese", "value": "zh-CN"}
                    ])
                } else if (kind === "asrModel") {
                    openOptions(kind, "ASR model", [
                        {"label": "Local large-v3", "value": "models/faster-whisper-large-v3"},
                        {"label": "large-v3", "value": "large-v3"},
                        {"label": "medium", "value": "medium"},
                        {"label": "small", "value": "small"}
                    ])
                } else if (kind === "deepseekModel") {
                    openOptions(kind, "DeepSeek model", [
                        {"label": "deepseek-v4-flash", "value": "deepseek-v4-flash"},
                        {"label": "deepseek-v4-pro", "value": "deepseek-v4-pro"}
                    ])
                }
            }
        }

        OptionPopoverCard {
            id: optionPopover
            visible: popoverOpen
            anchors.top: controlHub.top
            anchors.right: controlHub.left
            anchors.rightMargin: 14
            width: 300
            title: popoverTitle
            options: popoverOptions
            glassOpacity: overlayBridge.cardOpacity
            panelTintOpacity: overlayBridge.panelTintOpacity
            radius: overlayBridge.cardCornerRadius
            edgeWidth: overlayBridge.edgeWidth
            edgeOpacity: overlayBridge.edgeOpacity
            edgeDarkening: overlayBridge.edgeDarkening
            rgbShift: overlayBridge.rgbShift
            cyanEdgeOpacity: overlayBridge.cyanEdgeOpacity
            magentaEdgeOpacity: overlayBridge.magentaEdgeOpacity
            warmEdgeOpacity: overlayBridge.warmEdgeOpacity
            borderOpacity: overlayBridge.edgeOpacity
            highlightOpacity: overlayBridge.highlightOpacity
            radialHighlightOpacity: overlayBridge.radialHighlightOpacity
            topHighlightHeight: overlayBridge.topHighlightHeight
            shadowOpacity: overlayBridge.shadowOpacity
            shadowRadius: overlayBridge.shadowRadius
            shadowYOffset: overlayBridge.shadowYOffset
            iridescenceOpacity: overlayBridge.glassIridescence
            iridescenceWidth: overlayBridge.iridescenceWidth
            animationMs: overlayBridge.animationMs
            onSelected: function(value) { applyOption(value) }
            onCloseRequested: popoverOpen = false
        }
    }
}
