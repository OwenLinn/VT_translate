import QtQuick

Column {
    id: tuning
    property var bridge
    spacing: 6
    height: visible ? implicitHeight : 0
    clip: true

    Text {
        width: parent.width
        text: "Visual Tuning"
        color: "white"
        font.pixelSize: 14
        font.bold: true
    }

    GlassSlider {
        width: parent.width
        label: "Subtitle opacity"
        value: bridge ? bridge.subtitleOpacity : 1.0
        valueText: bridge ? Math.round(bridge.subtitleOpacity * 100) + "%" : ""
        onValueChangedByUser: if (bridge) bridge.setSubtitleOpacity(value)
    }

    GlassSlider {
        width: parent.width
        label: "Glass opacity"
        value: bridge ? bridge.glassOpacity : 0.58
        valueText: bridge ? Math.round(bridge.glassOpacity * 100) + "%" : ""
        onValueChangedByUser: if (bridge) bridge.setGlassOpacity(value)
    }

    GlassSlider {
        width: parent.width
        label: "Card opacity"
        value: bridge ? bridge.cardOpacity : 0.46
        valueText: bridge ? Math.round(bridge.cardOpacity * 100) + "%" : ""
        onValueChangedByUser: if (bridge) bridge.setCardOpacity(value)
    }

    GlassSlider {
        width: parent.width
        label: "Iridescence"
        value: bridge ? bridge.glassIridescence : 0.26
        valueText: bridge ? Math.round(bridge.glassIridescence * 100) + "%" : ""
        onValueChangedByUser: if (bridge) bridge.setGlassIridescence(value)
    }

    GlassSlider {
        width: parent.width
        label: "Iridescence width"
        value: bridge ? bridge.iridescenceWidth / 8.0 : 0.25
        valueText: bridge ? bridge.iridescenceWidth.toFixed(1) + "px" : ""
        onValueChangedByUser: if (bridge) bridge.setIridescenceWidth(value * 8.0)
    }

    GlassSlider {
        width: parent.width
        label: "Corner radius"
        value: bridge ? bridge.cornerRadius / 60.0 : 0.45
        valueText: bridge ? bridge.cornerRadius + "px" : ""
        onValueChangedByUser: if (bridge) bridge.setCornerRadius(Math.round(value * 60))
    }

    GlassSlider {
        width: parent.width
        label: "Shadow"
        value: bridge ? bridge.shadowOpacity : 0.3
        valueText: bridge ? Math.round(bridge.shadowOpacity * 100) + "%" : ""
        onValueChangedByUser: if (bridge) bridge.setShadowOpacity(value)
    }

    GlassSlider {
        width: parent.width
        label: "Highlight"
        value: bridge ? bridge.highlightOpacity : 0.3
        valueText: bridge ? Math.round(bridge.highlightOpacity * 100) + "%" : ""
        onValueChangedByUser: if (bridge) bridge.setHighlightOpacity(value)
    }

    GlassSlider {
        width: parent.width
        label: "Translation size"
        value: bridge ? bridge.translationFontSize / 72.0 : 0.42
        valueText: bridge ? bridge.translationFontSize + "px" : ""
        onValueChangedByUser: if (bridge) bridge.setTranslationFontSize(Math.round(value * 72))
    }

    GlassSlider {
        width: parent.width
        label: "Source size"
        value: bridge ? bridge.sourceFontSize / 48.0 : 0.38
        valueText: bridge ? bridge.sourceFontSize + "px" : ""
        onValueChangedByUser: if (bridge) bridge.setSourceFontSize(Math.round(value * 48))
    }

    GlassSlider {
        width: parent.width
        label: "Animation"
        value: bridge ? bridge.animationMs / 800.0 : 0.18
        valueText: bridge ? bridge.animationMs + "ms" : ""
        onValueChangedByUser: if (bridge) bridge.setAnimationMs(Math.round(value * 800))
    }

    PillButton {
        width: parent.width
        text: "Copy current parameters"
        onClicked: if (bridge) bridge.copyCurrentParameters()
    }
}
