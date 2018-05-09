
var map;
var dataLayer = null;
var jsonFormat = new OpenLayers.Format.JSON();

function init() {
    map = new OpenLayers.Map('map');
    map.restrictedExtent = map.maxExtent;
    var coast = new OpenLayers.Layer.WMS(
	"Coastline",
	"http://labs.metacarta.com/wms/vmap0",
	{
	    layers: 'coastline_01', format: 'image/png', transparent: 'true'
	}				 
    );
    
    map.addLayer(coast);
    setLayer();
    map.zoomToMaxExtent();

}

function setLayer(layer) {
    if (dataLayer !== null) {
	map.removeLayer(dataLayer);
    }
    if (!layer) {
	dataLayer = new OpenLayers.Layer.WMS(
	    "Data Layer",
	    "http://labs.metacarta.com/wms/vmap0",
	    {
		layers: 'basic', format: 'image/png', transparent: 'false'
	    }				 
	);
    }
    else {
	dataLayer = new OpenLayers.Layer.WMS(
	    layer,
	    fcURL,
	    {
		layers: layer,
		format: 'image/png'
	    }
	);
	buildLayerPanel($('panel'), layer);
	
    }
    map.addLayer(dataLayer);

}

function setLayerDim(dimension, value) {
    var params = {};
    params[dimension] = value;
    dataLayer.mergeNewParams(params);
    //console.log('Set Layer Dim '+dimension+', '+value);
}

// Load the GetContext JSON response for a layer to get it's dimensions.
function getLayerDetails(layer) {
    var r = OpenLayers.Request.GET({
	url: fcURL,
	params: {
	    layers: layer,
	    request: 'GetContext', format: 'application/json',
	},
	async: false
    });
 
    //!TODO: should probably trap errors here.
   
    return jsonFormat.read(r.responseText);
}

// Populate a div with details about a layer
function buildLayerPanel(div, layer) {
    var details, title, abstract, dim, d, s, extent, x, opt;

    details = getLayerDetails(layer)[layer];

    title = '<div><b>Title: </b>'+details.title+'</div>';
    abstract = '<div><b>Abstract: </b>'+details.abstract+'</div>';
    div.innerHTML = title+abstract;

    for (d in details.dimensions) {
	dim = div.appendChild(document.createElement('div'));
	dim.innerHTML = '<b>'+d+': </b>';
	s = dim.appendChild(document.createElement('select'));
	s._dim = d;
	s.id='dimopt_'+d
	s.onchange = function() {
	    setLayerDim(this._dim, this.value);
	};
	extent = details.dimensions[d].extent;
	for (x=0; x<extent.length; x++) {
	    opt = s.appendChild(document.createElement('option'));
	    opt.value = extent[x];
	    opt.innerHTML = extent[x];
	}
	dim.appendChild(document.createTextNode(' '+details.dimensions[d].units));
	if (document.getElementById('wcsdownload') == null) {
		createDownloadButton(dim);	
		}	
    }
}


// call WCS with current map parameters (bbox, layer, crs, dimensions etc)
function callWCS() {
	console.log('making WCS request');
	console.log('layer name: ' +dataLayer.name);
	console.log('map extent: ' + map.getExtent());
	//TODO: read the dimopt_d select dropdowns - get values
	//convert into WCS request.
}

//Create a download button, set to invisible at first
function createDownloadButton(div) {
    button=div.appendChild(document.createElement('input'));
    button.type='submit';
    button.id='wcsdownload';
    button.value='Download (not working yet)';
    button.onclick= function() {
    	callWCS();
    };
}



