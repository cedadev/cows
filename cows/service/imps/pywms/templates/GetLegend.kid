<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:py="http://purl.org/kid/ns#"
>
<head>
</head>

<body>
<div class="WMSC_colourbar">
  <img src="${url}?REQUEST=GetColourbar&amp;LAYERS=${name}&amp;CMAP=${cmap}"/>
  <table class="WMSC_colourbarAnnotations">
    <tr>
      <td class="WMSC_colourbarMin">${'%.2g' % layer.minValue}</td>
      <td class="WMSC_colourbarMid">${'%.2g' % (layer.minValue + (layer.maxValue - layer.minValue) / 2)}</td>
      <td class="WMSC_colourbarMax">${'%.2g' % layer.maxValue}</td>
    </tr>
  </table>
</div>

<div class="WMSC_legendTitle">${layer.title} (${layer.units})</div>
</body>
</html>