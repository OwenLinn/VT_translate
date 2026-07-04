import QtQuick

GlassCard {
    id: thumb
    property int selectedIndex: 0
    property int itemCount: 2
    property int moveMs: 220
    property real stretchScale: 1.10
    property real compressScale: 0.96
    property bool vertical: false

    glassOpacity: 0.34
    iridescenceOpacity: 0.32
    edgeOpacity: 0.38
    radius: height / 2

    x: vertical ? 0 : Math.max(0, selectedIndex) * parent.width / Math.max(1, itemCount)
    y: vertical ? Math.max(0, selectedIndex) * parent.height / Math.max(1, itemCount) : 0
    width: vertical ? parent.width : parent.width / Math.max(1, itemCount)
    height: vertical ? parent.height / Math.max(1, itemCount) : parent.height
    scale: 1.0

    SequentialAnimation on scale {
        id: pulse
        running: false
        NumberAnimation { to: thumb.stretchScale; duration: Math.max(40, thumb.moveMs * 0.32); easing.type: Easing.OutCubic }
        NumberAnimation { to: thumb.compressScale; duration: Math.max(40, thumb.moveMs * 0.28); easing.type: Easing.InOutCubic }
        NumberAnimation { to: 1.0; duration: Math.max(40, thumb.moveMs * 0.40); easing.type: Easing.OutCubic }
    }

    onSelectedIndexChanged: pulse.restart()

    Behavior on x { NumberAnimation { duration: thumb.moveMs; easing.type: Easing.OutCubic } }
    Behavior on y { NumberAnimation { duration: thumb.moveMs; easing.type: Easing.OutCubic } }
    Behavior on width { NumberAnimation { duration: thumb.moveMs; easing.type: Easing.OutCubic } }
    Behavior on height { NumberAnimation { duration: thumb.moveMs; easing.type: Easing.OutCubic } }
}

