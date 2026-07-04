import QtQuick

Item {
    id: button
    signal clicked()
    property bool open: false
    property bool hovered: false
    property bool pressed: false

    scale: pressed ? 0.94 : hovered ? 1.04 : 1.0

    Behavior on scale {
        NumberAnimation { duration: 110; easing.type: Easing.OutCubic }
    }

    GlassCard {
        anchors.centerIn: parent
        width: 54
        height: 54
        radius: 22
        glassOpacity: open ? 0.64 : 0.48
        iridescenceOpacity: open ? 0.25 : 0.08

        Canvas {
            z: 3
            anchors.centerIn: parent
            width: 28
            height: 28
            onPaint: {
                var ctx = getContext("2d")
                ctx.clearRect(0, 0, width, height)
                ctx.strokeStyle = "rgba(255,255,255,0.92)"
                ctx.lineWidth = 2.2
                ctx.lineCap = "round"
                for (var i = 0; i < 3; i++) {
                    var y = 7 + i * 7
                    ctx.beginPath()
                    ctx.moveTo(4, y)
                    ctx.lineTo(24, y)
                    ctx.stroke()
                    ctx.beginPath()
                    ctx.arc(i === 1 ? 17 : 11, y, 2.5, 0, Math.PI * 2)
                    ctx.fillStyle = "rgba(255,255,255,0.95)"
                    ctx.fill()
                }
            }
        }
    }

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        onEntered: button.hovered = true
        onExited: button.hovered = false
        onPressed: button.pressed = true
        onReleased: button.pressed = false
        onCanceled: button.pressed = false
        onClicked: button.clicked()
    }
}
