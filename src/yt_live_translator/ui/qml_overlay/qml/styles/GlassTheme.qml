import QtQuick

QtObject {
    property bool glassEnabled: true
    property bool animationEnabled: true
    property bool shaderEdgeEnabled: false
    property color textPrimary: "#FFFFFF"
    property color textSecondary: "#D8D8D8"
    property real subtitleBackgroundOpacity: 0.58
    property real cardBackgroundOpacity: 0.46
    property real panelTintOpacity: 0.32
    property real edgeWidth: 2.0
    property real edgeOpacity: 0.36
    property real edgeDarkening: 0.08
    property real distortion: 0.018
    property real reflectPower: 0.28
    property real rgbShift: 0.012
    property real cyanEdgeOpacity: 0.22
    property real magentaEdgeOpacity: 0.18
    property real warmEdgeOpacity: 0.12
    property real borderOpacity: 0.36
    property real highlightOpacity: 0.30
    property real topHighlightHeight: 0.36
    property real radialHighlightOpacity: 0.18
    property real shadowOpacity: 0.30
    property int shadowRadius: 28
    property int shadowYOffset: 8
    property real iridescenceOpacity: 0.26
    property real iridescenceWidth: 2.0
    property real noiseOpacity: 0.018
    property int cornerRadius: 28
    property int cardCornerRadius: 30
    property int subtitleFadeMs: 140
    property int cardOpenMs: 180
    property int cardCloseMs: 130
    property int popoverOpenMs: 160
    property int popoverCloseMs: 120
    property real scaleFrom: 0.965
    property real scaleTo: 1.0
    property int slideOffsetPx: 12
    property int thumbMoveMs: 220
    property real thumbStretchScale: 1.10
    property real thumbCompressScale: 0.96
}
