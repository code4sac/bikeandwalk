/*
 * LEAFLET.FLOWMARKER
 * v0.1.0
 * Bill Leddy
 * stollen from Thomas Brüggemann
 */

/* FLOW ICON */
L.FlowIcon = L.Icon.extend({

	// OPTIONS
	options: {
		flowData: {},
		iconSize: new L.Point(75, 75),
		className: "leaflet-flow-icon",
		outboundColor: 'rgba(255,0,0,1)',
		inboundColor: 'rgba(128,128,128,.5)',
		northEastArrows: false // only draw arrows on north and east legs if true
	},

	// PROPERTIES
	ctx: null,

	// CREATE ICON
	// setup the icon and start drawing
	createIcon: function () {
		var e = document.createElement("canvas");
		this._setIconStyles(e, "icon");
		var s = this.options.iconSize;

		e.width = s.x;
		e.height = s.y;

		this.ctx = e.getContext("2d");
		this.drawCanvas(this.ctx, s.x, this.options.flowData,this.options.northEastArrows);

		return e;
	}
	,
	    drawCanvas: function(ctx,canvasWidth,flowData,northEastArrows){
			// draw a 4 legged traffic flow marker
            if(northEastArrows == undefined){ 
                northEastArrows = false; // draw arrows on all 4 directions
            }
			/*
				flowData: {
							"south":{"inbound":87, "outbound":59, "heading": 10},
							"west":{"inbound":66,"outbound":0, "heading": 10},
							"north":{"inbound":45,"outbound":80, "heading": 10},
							"east":{"outbound":25,"inbound":32, "heading": 10}
							}
				"inbound" and "outbound" determine the length of the arrow from center to edge of canvas.
				heading is the number of degrees to rotate the canvas so that arrow aligns with streets on map.
			*/
           var theCenter = canvasWidth/2; 
           mapOrder = ["north","east","south","west"]
           
           // just for testing...
           arrowColor = ['rgba(255,0,0,1)','rgba(0,255,0,1)','rgba(0,0,255,1)','rgba(0,0,0,1)']
           
           // determine the highest count for this location
           var maxCount = 0;
           for (var i = 0; i < 4; i++){
               var thisDir = flowData[mapOrder[i]];
              if (thisDir.inbound > maxCount) { maxCount = thisDir.inbound;}
              if (thisDir.outbound > maxCount) { maxCount = thisDir.outbound;}
           }
           
           // draw one arrow, then turn grid to the new heading and draw next
           var kind = "inbound";
           for (var j = 0; j < 2; j++){
               // Draw all the inbounds first so they are at the bottom of stack
               for (var i = 0; i < 4; i++){
                   this.options.outboundColor = arrowColor[i]; // testing...
                   var thisDir = flowData[mapOrder[i]];
                       /*
                         To rotate the lines, translate to the center of the box,
                         then rotate the grid to the desired angle.
                         Next, reset the grid to the starting point and draw as though
                         grid is in the normal orientation.
                       */
                      ctx.translate(theCenter, theCenter); // translate to canvas center 
                      if(i > 0){
                          // turn 90 deg
                          //ctx.rotate((Math.PI/180)*90)
                      }

                   if (thisDir != undefined){
                       // adjust heading so it point north
                       var streetAngle = i * 90; // default heading
                       if(thisDir.heading != undefined){ streetAngle = thisDir.heading };
                       
                       ctx.rotate((Math.PI/180)*streetAngle);
                       ctx.translate(-theCenter,-theCenter); // back to starting place
                       // draw something
                       if(kind == "inbound"){
                           var len = 0;
                           if(thisDir.inbound != undefined && maxCount > 0){ len = thisDir.inbound/maxCount}
                           this.drawInbound(ctx,len,theCenter);
                       } else {
                           var len = 0;
                           if(thisDir.outbound != undefined && maxCount > 0){ len = thisDir.outbound/maxCount}
                           var drawArrowhead = true;
                           if(northEastArrows && (mapOrder[i] == "south" ||  mapOrder[i] == "west")){
                               drawArrowhead = false;
                           }
                           this.drawOutbound(ctx,len,theCenter,drawArrowhead);
                       }
                       // restore normal orientation
                       ctx.translate(theCenter, theCenter); // translate to canvas center 
                       ctx.rotate((Math.PI/180)*(streetAngle * -1)); // reset street angle to 0
                       ctx.translate(-theCenter, -theCenter); // translate to canvas center 
                   } // end thisDir
               } // end for i
               kind = "outbound";
           } // end for j
		} // end drawCanvas
		,
	    drawInbound: function(ctx,pct,theCenter){
	        /*
	        Draw the incoming traffic indicator.
	        In this case, a triangle:
	        @param: ctx the canvas context
	        @param: pct fractional value for length of leg
	        */
            
	        ctx.beginPath();
	        ctx.fillStyle = this.options.inboundColor;

	        if(pct < 0){ pct = 0;}

	        var theWidth = 8; // half the width of triangle base

	        // all drawing is done as though oriented north
	        // coordinents are (x,y)
	        ctx.moveTo(theCenter,theCenter);
	        ctx.lineTo(theCenter+theWidth,theCenter+(theCenter*pct));
	        ctx.lineTo(theCenter-theWidth,theCenter+(theCenter*pct));
	        ctx.fill()
	    },

	    drawOutbound: function (ctx,pct,theCenter,drawArrowhead){
	        /*
	        Draw an arrow representing the outgoing traffic
	        */
	        if(drawArrowhead == undefined){ drawArrowhead = true};
	        var lineWidth = 5;
	        ctx.beginPath();
	        ctx.lineCap =  'round';
	        ctx.miterLimit = 10;
	        ctx.lineJoin = "miter";
	        ctx.lineWidth = lineWidth;
	        ctx.strokeStyle = this.options.outboundColor;

	        var arrowWidth = 8 * pct; // half the width of the arrow head

	        // all drawing is done as though oriented north
	        // coordinents are (x,y)
	        ctx.moveTo(theCenter,theCenter);
	        ctx.lineTo(theCenter,theCenter-(theCenter*pct)+(lineWidth/2))
	        if(drawArrowhead){
	            ctx.moveTo(theCenter-arrowWidth,theCenter-(theCenter*pct)+arrowWidth);
    	        ctx.lineTo(theCenter,theCenter-(theCenter*pct)+(lineWidth/2))
    	        ctx.lineTo(theCenter+arrowWidth,theCenter-(theCenter*pct)+arrowWidth);
            }
	        ctx.stroke();
	    },
	    
	    

});

L.FlowMarker = L.Marker.extend({
    setHeading: function(maker,heading){
        // an example of how to provide callable functions for a marker
        
    }    
});

L.flowMarker = function(pos, options, dataIn) {

	options.icon = new L.FlowIcon({ flowData: dataIn});

    return new L.FlowMarker(pos, options);
};

L.alignmentMarker = function(pos, options,northHeading,eastHeading) {
    // create a dummy marker used to set the alignment of arrows for location records
    if(northHeading == undefined){northHeading = 0;}
    northHeading = parseFloat(northHeading);
    if(eastHeading == undefined){eastHeading = 90}
    eastHeading = parseFloat(eastHeading);
    
    dataIn = {
			"south":{"inbound":0, "outbound":1, "heading": 180+northHeading},
			"west":{"inbound":0,"outbound":1, "heading": 180+eastHeading},
			"north":{"inbound":0,"outbound":1, "heading": northHeading},
			"east":{"inbound":0,"outbound":1, "heading": eastHeading}
            }
	options.icon = new L.FlowIcon({ flowData: dataIn, northEastArrows: true });

    return new L.FlowMarker(pos, options);
};