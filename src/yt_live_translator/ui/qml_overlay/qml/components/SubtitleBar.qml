import QtQuick

GlassCard {
    id: bar
    property string sourceText: ""
    property string translatedText: ""
    property bool showSource: true
    property bool showTranslation: true
    property bool isPartial: false
    property real subtitleOpacity: 1.0
    property real glassIridescence: 0.0
    property int translationFontSize: 30
    property int sourceFontSize: 18
    property string fontFamily: "Microsoft JhengHei"
    property string translationColor: "#FFFFFF"
    property string sourceColor: "#D8D8D8"
    property int animationMs: 140
    variant: "subtitle"

    iridescenceOpacity: glassIridescence

    Behavior on opacity {
        NumberAnimation { duration: bar.animationMs; easing.type: Easing.OutCubic }
    }

    Behavior on glassOpacity { NumberAnimation { duration: bar.animationMs; easing.type: Easing.OutCubic } }
    Behavior on glassIridescence { NumberAnimation { duration: bar.animationMs; easing.type: Easing.OutCubic } }

    Column {
        z: 3
        anchors.fill: parent
        anchors.margins: 18
        spacing: 4

        Text {
            width: parent.width
            visible: bar.showTranslation
            text: bar.translatedText
            color: bar.translationColor
            opacity: bar.isPartial ? 0.70 : bar.subtitleOpacity
            font.family: bar.fontFamily
            font.pixelSize: bar.translationFontSize
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            wrapMode: Text.Wrap
            maximumLineCount: 2
            elide: Text.ElideRight
            style: Text.Raised
            styleColor: Qt.rgba(0, 0, 0, 0.55)
            Behavior on opacity { NumberAnimation { duration: bar.animationMs; easing.type: Easing.OutCubic } }
            Behavior on font.pixelSize { NumberAnimation { duration: bar.animationMs; easing.type: Easing.OutCubic } }
        }

        Text {
            width: parent.width
            visible: bar.showSource
            text: bar.sourceText
            color: bar.sourceColor
            opacity: bar.isPartial ? 0.58 : Math.min(0.9, bar.subtitleOpacity)
            font.family: bar.fontFamily
            font.pixelSize: bar.sourceFontSize
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            wrapMode: Text.Wrap
            maximumLineCount: 1
            elide: Text.ElideRight
            style: Text.Raised
            styleColor: Qt.rgba(0, 0, 0, 0.55)
            Behavior on opacity { NumberAnimation { duration: bar.animationMs; easing.type: Easing.OutCubic } }
            Behavior on font.pixelSize { NumberAnimation { duration: bar.animationMs; easing.type: Easing.OutCubic } }
        }
    }
}
