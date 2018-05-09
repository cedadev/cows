<?xml version="1.0" encoding="utf-8"?>
<?python

import urlparse
import logging

logger = logging.getLogger('pywms.templates.GetCapabilities')

def strip_qs(url):
    t = urlparse.urlparse(url)
    return urlparse.urlunparse(list(t[:3])+['','',''])

def layerFolderName(indexes):
    """Turn a list of indexes into a layer name.

    """
    return "folder_%s" % '_'.join(str(x) for x in indexes)
?>



<WMS_Capabilities version="${version}" 
		  xmlns:py="http://purl.org/kid/ns#"
		  xmlns="http://www.opengis.net/wms"
		  xmlns:xlink="http://www.w3.org/1999/xlink/">

  <Layer py:def="layer(name)">
    <!--! <?python logger.info('calling layer(%s)' % name) ?> -->
    <Name>${name}</Name>
    <Title>${model.layers[name].title}</Title>
    <Abstract py:content="model.layers[name].abstract"/>
    <Dimension py:for="name, dim in model.layers[name].dimensions.items()"
	       name="${name}"
	       units="${dim.units}"
	       >${dim.extent}</Dimension>
  </Layer>

  <Layer py:def="layerFolder(lf, indexes, depth, topLevel=False)">
    <!--! <?python logger.info('calling layerFolder(%s, %s, %s)' % (lf, indexes, depth)) ?> -->
    <Name py:if="indexes" py:content="layerFolderName(indexes)"/>
    <Name py:if="not indexes">toplevel</Name>
    <Title py:content="lf.title"/>
    <Abstract py:content="lf.abstract"/>
    <!--! <CRS py:if="topLevel">CRS:84</CRS> -->
    <SRS py:if="topLevel">EPSG:4326</SRS>
    <BoundingBox py:if="topLevel" SRS="EPSG:4326"
		 minx="-180" miny="-90" maxx="180" maxy="90"/>
    <div py:if="depth != 0" py:for="i, item in enumerate(lf.contents)" py:strip="True">
      <Layer py:if="type(item) == str" py:replace="layer(item)"/>
      <Layer py:if="type(item) != str" py:replace="layerFolder(item, indexes + [i], depth-1)"/>
    </div>
  </Layer>

  <Service>
    <Name>WMS</Name>
    <Title>${model.title}</Title>
    <OnlineResource xlink:type="simple" xlink:href="${strip_qs(url)}"/>
  </Service>
  <Capability>
    <Request>
      <GetCapabilities>
        <Format>application/vnd.ogc.wms_xml</Format>
        <DCPType><HTTP><Get>
          <OnlineResource xlink:type="simple" xlink:href="${strip_qs(url)}"/>
        </Get></HTTP></DCPType>
      </GetCapabilities>
      <GetMap>
        <Format py:for="format in formats">${format}</Format>
        <DCPType><HTTP><Get>
          <OnlineResource xlink:type="simple" xlink:href="${strip_qs(url)}"/>
        </Get></HTTP></DCPType>
      </GetMap>
    </Request>
    <Exception>
      <Format>application/vnd.ogc.se_xml</Format>
    </Exception>
    <?python

    if not contextFolder:
        contextFolder = model.layerFolder

    ?>
    ${layerFolder(contextFolder, indexes, depth, topLevel=True)}
  </Capability>
</WMS_Capabilities>
