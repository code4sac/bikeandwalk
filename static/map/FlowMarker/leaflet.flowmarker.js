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
		inboundColor: 'rgba(128,128,128,.5)'
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
		this.drawCanvas(this.ctx, s.x, this.options.flowData);

		return e;
	}
	,
	    drawCanvas: function(ctx,canvasWidth,flowData){
			// draw a 4 legged traffic flow marker

			/*
				flowData: {
							"south":{"inbound":0.8, "outbound":0.8, "alignment": 10},
							"west":{"inbound":0.5,"outbound":0.5, "alignment": 10},
							"north":{"inbound":0.25,"outbound":0.15, "alignment": 10},
							"east":{"outbound":0.1,"inbound":0.2, "alignment": 10}
							}
				"inbound" and "outbound" determine the length of the arrow from center to edge of canvas.
				alignment is the number of degrees to rotate the canvas so that arrow aligns with streets on map.
			*/
				/*flowData= {
							"south":{"inbound":0.8, "outbound":0.8, "alignment": 10},
							"west":{"inbound":0.5,"outbound":0.5, "alignment": 10},
							"north":{"inbound":0.25,"outbound":0.15, "alignment": 10},
							"east":{"outbound":0.1,"inbound":0.2, "alignment": 10}
							}
				*/
           var theCenter = canvasWidth/2; 
           mapOrder = ["north","west","south","east"]

           // draw one arrow, then turn grid, 90° and draw next
           var kind = "inbound";
           for (var j = 0; j < 2; j++){
               // Draw all the inbounds first so they are at the bottom of stack
               for (var i = 0; i < 4; i++){
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
                          ctx.rotate((Math.PI/180)*90)
                      }

                   if (thisDir != undefined){
                       var streetAngle = 0;
                       if(thisDir.alignment != undefined){ streetAngle = thisDir.alignment };

                       ctx.rotate((Math.PI/180)*streetAngle);
                       ctx.translate(-theCenter,-theCenter); // back to starting place
                       // draw something
                       if(kind == "inbound"){
                           var len = 0;
                           if(thisDir.inbound != undefined){ len = thisDir.inbound}
                           this.drawInbound(ctx,len,theCenter);
                       } else {
                           var len = 0;
                           if(thisDir.outbound != undefined){ len = thisDir.outbound}
                           this.drawOutbound(ctx,len,theCenter);
                       }
                       ctx.translate(theCenter, theCenter); // translate to canvas center 
                       ctx.rotate((Math.PI/180)*(streetAngle * -1)); // reset street angle to 0
                       ctx.translate(-theCenter, -theCenter); // translate to canvas center 
                   } // end thisDir
               } // end for i
               // restore north orientation
               ctx.translate(theCenter, theCenter); // translate to canvas center 
               ctx.rotate((Math.PI/180)*90)
               ctx.translate(-theCenter,-theCenter); // back to starting place

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

	    drawOutbound: function (ctx,pct,theCenter){
	        /*
	        Draw an arrow representing the outgoing traffic
	        */
	        ctx.beginPath();
	        ctx.lineCap =  'round';
	        ctx.lineWidth = 5;
	        ctx.strokeStyle = this.options.outboundColor;

	        var arrowWidth = 8 * pct; // half the width of the arrow head

	        // all drawing is done as though oriented north
	        // coordinents are (x,y)
	        ctx.moveTo(theCenter,theCenter);
	        ctx.lineTo(theCenter,theCenter-(theCenter*pct))
	        ctx.moveTo(theCenter-arrowWidth,theCenter-(theCenter*pct)+arrowWidth);
	        ctx.lineTo(theCenter,theCenter-(theCenter*pct))
	        ctx.lineTo(theCenter+arrowWidth,theCenter-(theCenter*pct)+arrowWidth);
	        ctx.stroke();
	    },

});

L.FlowMarker = L.Marker.extend({
  	
});

L.flowMarker = function(pos, options, dataIn) {

	options.icon = new L.FlowIcon({ flowData: dataIn});

    return new L.FlowMarker(pos, options);
};
