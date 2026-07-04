import QtQuick

Item {
    id: edge
    property real radius: 28
    property real edgeWidth: 2.0
    property real edgeOpacity: 0.36
    property real edgeDarkening: 0.08
    property real iridescenceOpacity: 0.26
    property real rgbShift: 0.012
    property real cyanEdgeOpacity: 0.22
    property real magentaEdgeOpacity: 0.18
    property real warmEdgeOpacity: 0.12

    Rectangle {
        anchors.fill: parent
        radius: edge.radius
        color: "transparent"
        border.width: Math.max(1, edge.edgeWidth)
        border.color: Qt.rgba(1, 1, 1, edge.edgeOpacity)
        antialiasing: true
    }

    Rectangle {
        anchors.fill: parent
        anchors.leftMargin: -edge.rgbShift * parent.width
        anchors.rightMargin: edge.rgbShift * parent.width
        radius: edge.radius
        color: "transparent"
        border.width: Math.max(1, edge.edgeWidth * 0.70)
        border.color: Qt.rgba(0.35, 0.95, 1.0, edge.cyanEdgeOpacity * edge.iridescenceOpacity)
        antialiasing: true
    }

    Rectangle {
        anchors.fill: parent
        anchors.leftMargin: edge.rgbShift * parent.width
        anchors.rightMargin: -edge.rgbShift * parent.width
        radius: edge.radius
        color: "transparent"
        border.width: Math.max(1, edge.edgeWidth * 0.70)
        border.color: Qt.rgba(1.0, 0.32, 0.86, edge.magentaEdgeOpacity * edge.iridescenceOpacity)
        antialiasing: true
    }

    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: Math.max(1, edge.edgeWidth)
        radius: edge.radius
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: Qt.rgba(0.35, 0.85, 1.0, 0.0) }
            GradientStop { position: 0.28; color: Qt.rgba(0.35, 0.90, 1.0, edge.cyanEdgeOpacity * edge.iridescenceOpacity) }
            GradientStop { position: 0.62; color: Qt.rgba(1.0, 1.0, 1.0, edge.edgeOpacity * 0.65) }
            GradientStop { position: 1.0; color: Qt.rgba(1.0, 0.78, 0.30, edge.warmEdgeOpacity * edge.iridescenceOpacity) }
        }
    }

    Rectangle {
        anchors.fill: parent
        radius: edge.radius
        color: Qt.rgba(0, 0, 0, edge.edgeDarkening)
        opacity: 0.35
        antialiasing: true
    }
}

