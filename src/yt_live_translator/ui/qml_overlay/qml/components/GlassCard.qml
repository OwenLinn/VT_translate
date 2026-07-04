import QtQuick

Rectangle {
    id: card
    property string variant: "card"
    property real glassOpacity: 0.52
    property real panelTintOpacity: 0.32
    property real borderOpacity: 0.36
    property real highlightOpacity: 0.30
    property real topHighlightHeight: 0.36
    property real radialHighlightOpacity: 0.18
    property real shadowOpacity: 0.30
    property int shadowRadius: 28
    property int shadowYOffset: 8
    property real iridescenceOpacity: 0.0
    property real iridescenceWidth: 2.0
    property real edgeWidth: iridescenceWidth
    property real edgeOpacity: borderOpacity
    property real edgeDarkening: 0.08
    property real distortion: 0.018
    property real reflectPower: 0.28
    property real rgbShift: 0.012
    property real cyanEdgeOpacity: 0.22
    property real magentaEdgeOpacity: 0.18
    property real warmEdgeOpacity: 0.12
    property int animationMs: 140

    radius: 28
    color: Qt.rgba(0.05, 0.06, 0.08, glassOpacity)
    border.width: 0
    antialiasing: true

    Rectangle {
        anchors.fill: parent
        anchors.margins: -Math.max(3, shadowRadius / 4)
        radius: parent.radius + Math.max(3, shadowRadius / 4)
        z: -2
        y: shadowYOffset * 0.55
        color: Qt.rgba(0, 0, 0, shadowOpacity * 0.20)
        antialiasing: true
    }

    Rectangle {
        anchors.fill: parent
        anchors.margins: -Math.max(1, shadowRadius / 10)
        radius: parent.radius + Math.max(1, shadowRadius / 10)
        z: -1
        y: shadowYOffset * 0.30
        color: Qt.rgba(0, 0, 0, shadowOpacity * 0.18)
        antialiasing: true
    }

    Rectangle {
        anchors.fill: parent
        radius: parent.radius
        color: Qt.rgba(1, 1, 1, panelTintOpacity * 0.08)
        opacity: variant === "subtitle" ? 0.55 : 1.0
        antialiasing: true
    }

    Rectangle {
        anchors.fill: parent
        radius: parent.radius
        color: Qt.rgba(1, 1, 1, Math.min(0.08, reflectPower * 0.08))
        opacity: Math.min(1.0, 0.35 + distortion * 8.0)
        antialiasing: true
    }

    GlassHighlight {
        anchors.fill: parent
        radius: card.radius
        highlightOpacity: card.highlightOpacity
        topHighlightHeight: card.topHighlightHeight
        radialHighlightOpacity: card.radialHighlightOpacity
        z: 1
    }

    GlassEdge {
        anchors.fill: parent
        radius: card.radius
        edgeWidth: card.edgeWidth
        edgeOpacity: card.edgeOpacity
        edgeDarkening: card.edgeDarkening
        iridescenceOpacity: card.iridescenceOpacity
        rgbShift: card.rgbShift
        cyanEdgeOpacity: card.cyanEdgeOpacity
        magentaEdgeOpacity: card.magentaEdgeOpacity
        warmEdgeOpacity: card.warmEdgeOpacity
        z: 2
    }

    Behavior on glassOpacity { NumberAnimation { duration: card.animationMs; easing.type: Easing.OutCubic } }
    Behavior on panelTintOpacity { NumberAnimation { duration: card.animationMs; easing.type: Easing.OutCubic } }
    Behavior on borderOpacity { NumberAnimation { duration: card.animationMs; easing.type: Easing.OutCubic } }
    Behavior on highlightOpacity { NumberAnimation { duration: card.animationMs; easing.type: Easing.OutCubic } }
    Behavior on radialHighlightOpacity { NumberAnimation { duration: card.animationMs; easing.type: Easing.OutCubic } }
    Behavior on shadowOpacity { NumberAnimation { duration: card.animationMs; easing.type: Easing.OutCubic } }
    Behavior on iridescenceOpacity { NumberAnimation { duration: card.animationMs; easing.type: Easing.OutCubic } }
}
