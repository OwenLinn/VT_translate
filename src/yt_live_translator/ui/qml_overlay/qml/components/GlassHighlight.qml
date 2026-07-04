import QtQuick

Item {
    id: highlight
    property real radius: 28
    property real highlightOpacity: 0.30
    property real topHighlightHeight: 0.36
    property real radialHighlightOpacity: 0.18

    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: parent.height * highlight.topHighlightHeight
        radius: highlight.radius
        gradient: Gradient {
            GradientStop { position: 0.0; color: Qt.rgba(1, 1, 1, highlight.highlightOpacity) }
            GradientStop { position: 0.42; color: Qt.rgba(1, 1, 1, highlight.highlightOpacity * 0.22) }
            GradientStop { position: 1.0; color: Qt.rgba(1, 1, 1, 0.0) }
        }
    }

    Rectangle {
        anchors.left: parent.left
        anchors.top: parent.top
        width: parent.width * 0.48
        height: parent.height * 0.72
        radius: highlight.radius
        gradient: Gradient {
            GradientStop { position: 0.0; color: Qt.rgba(1, 1, 1, highlight.radialHighlightOpacity) }
            GradientStop { position: 0.58; color: Qt.rgba(1, 1, 1, highlight.radialHighlightOpacity * 0.22) }
            GradientStop { position: 1.0; color: Qt.rgba(1, 1, 1, 0.0) }
        }
        opacity: 0.72
    }

    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: parent.height * 0.24
        radius: highlight.radius
        gradient: Gradient {
            GradientStop { position: 0.0; color: Qt.rgba(1, 1, 1, 0.0) }
            GradientStop { position: 1.0; color: Qt.rgba(1, 1, 1, highlight.radialHighlightOpacity * 0.42) }
        }
    }
}

