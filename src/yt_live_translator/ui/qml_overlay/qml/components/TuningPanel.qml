import QtQuick

Column {
    id: tuning
    property var bridge
    spacing: 6
    height: visible ? implicitHeight : 0
    clip: true

    Text {
        width: parent.width
        text: "Material Tuning"
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
        label: "Panel tint"
        value: bridge ? bridge.panelTintOpacity : 0.32
        valueText: bridge ? Math.round(bridge.panelTintOpacity * 100) + "%" : ""
        onValueChangedByUser: if (bridge) bridge.setPanelTintOpacity(value)
    }

    GlassSlider {
        width: parent.width
        label: "Edge width"
        value: bridge ? bridge.edgeWidth / 12.0 : 0.16
        valueText: bridge ? bridge.edgeWidth.toFixed(1) + "px" : ""
        onValueChangedByUser: if (bridge) bridge.setEdgeWidth(value * 12.0)
    }

    GlassSlider {
        width: parent.width
        label: "Edge opacity"
        value: bridge ? bridge.edgeOpacity : 0.36
        valueText: bridge ? Math.round(bridge.edgeOpacity * 100) + "%" : ""
        onValueChangedByUser: if (bridge) bridge.setEdgeOpacity(value)
    }

    GlassSlider {
        width: parent.width
        label: "Edge darkening"
        value: bridge ? bridge.edgeDarkening / 0.5 : 0.16
        valueText: bridge ? bridge.edgeDarkening.toFixed(3) : ""
        onValueChangedByUser: if (bridge) bridge.setEdgeDarkening(value * 0.5)
    }

    GlassSlider {
        width: parent.width
        label: "Distortion"
        value: bridge ? bridge.distortion / 0.08 : 0.22
        valueText: bridge ? bridge.distortion.toFixed(3) : ""
        onValueChangedByUser: if (bridge) bridge.setDistortion(value * 0.08)
    }

    GlassSlider {
        width: parent.width
        label: "Reflect"
        value: bridge ? bridge.reflectPower : 0.28
        valueText: bridge ? Math.round(bridge.reflectPower * 100) + "%" : ""
        onValueChangedByUser: if (bridge) bridge.setReflectPower(value)
    }

    GlassSlider {
        width: parent.width
        label: "RGB shift"
        value: bridge ? bridge.rgbShift / 0.06 : 0.20
        valueText: bridge ? bridge.rgbShift.toFixed(3) : ""
        onValueChangedByUser: if (bridge) bridge.setRgbShift(value * 0.06)
    }

    GlassSlider {
        width: parent.width
        label: "Cyan edge"
        value: bridge ? bridge.cyanEdgeOpacity : 0.22
        valueText: bridge ? Math.round(bridge.cyanEdgeOpacity * 100) + "%" : ""
        onValueChangedByUser: if (bridge) bridge.setCyanEdgeOpacity(value)
    }

    GlassSlider {
        width: parent.width
        label: "Magenta edge"
        value: bridge ? bridge.magentaEdgeOpacity : 0.18
        valueText: bridge ? Math.round(bridge.magentaEdgeOpacity * 100) + "%" : ""
        onValueChangedByUser: if (bridge) bridge.setMagentaEdgeOpacity(value)
    }

    GlassSlider {
        width: parent.width
        label: "Warm edge"
        value: bridge ? bridge.warmEdgeOpacity : 0.12
        valueText: bridge ? Math.round(bridge.warmEdgeOpacity * 100) + "%" : ""
        onValueChangedByUser: if (bridge) bridge.setWarmEdgeOpacity(value)
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
        label: "Radius"
        value: bridge ? bridge.cornerRadius / 60.0 : 0.45
        valueText: bridge ? bridge.cornerRadius + "px" : ""
        onValueChangedByUser: if (bridge) bridge.setCornerRadius(Math.round(value * 60))
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
        label: "Radial highlight"
        value: bridge ? bridge.radialHighlightOpacity : 0.18
        valueText: bridge ? Math.round(bridge.radialHighlightOpacity * 100) + "%" : ""
        onValueChangedByUser: if (bridge) bridge.setRadialHighlightOpacity(value)
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
        label: "Translation size"
        value: bridge ? bridge.translationFontSize / 72.0 : 0.42
        valueText: bridge ? bridge.translationFontSize + "px" : ""
        onValueChangedByUser: if (bridge) bridge.setTranslationFontSize(Math.round(value * 72))
    }

    GlassSlider {
        width: parent.width
        label: "Animation"
        value: bridge ? bridge.animationMs / 800.0 : 0.18
        valueText: bridge ? bridge.animationMs + "ms" : ""
        onValueChangedByUser: if (bridge) bridge.setAnimationMs(Math.round(value * 800))
    }

    GlassSlider {
        width: parent.width
        label: "Thumb move"
        value: bridge ? bridge.thumbMoveMs / 800.0 : 0.28
        valueText: bridge ? bridge.thumbMoveMs + "ms" : ""
        onValueChangedByUser: if (bridge) bridge.setThumbMoveMs(Math.round(value * 800))
    }

    PillButton {
        width: parent.width
        text: "Copy current parameters"
        onClicked: if (bridge) bridge.copyCurrentParameters()
    }
}

