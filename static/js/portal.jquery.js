/*
 * Portal 0.2
 * 
 * Conceived by Andre Torrez (@torrez) in his dreams. 
 * 
 */

(function($) {
    
  var Portal = function(el, settings) {
    this.start_click_x = 0;
    this.start_click_y = 0;
    this.end_click_x = 0;
    this.end_click_y = 0;
    this.settings = settings;
    
    this.element = el;
    this.$element = $(el);
    this.ctx = this.element.getContext('2d');
    
    // calculate height width of drawable area.
    // make sure height & width attributes are set on
    // canvas element, otherwise we get deformed drawing.
    this.height = this.$element.height();
    this.width = this.$element.width();
    this.$element.attr('height', this.height);
    this.$element.attr('width', this.width);    
  };
  
  Portal.prototype.getEventPosition = function(e) {
    var left = 0;
    var top = 0;
    if (typeof e.touches != 'undefined' && typeof e.touches[0] != 'undefined') {
      left = e.touches[0].pageX - this.$element.offset().left;
      top = e.touches[0].pageY - this.$element.offset().top;      
    }
    else if (typeof e.changedTouches != 'undefined' && typeof e.changedTouches[0] != 'undefined') {
      left = e.changedTouches[0].pageX - this.$element.offset().left;
      top = e.changedTouches[0].pageY - this.$element.offset().top;      
    } else {
      left = e.pageX - this.$element.offset().left;
      top = e.pageY - this.$element.offset().top;
    }
    return {'left': left, 'top': top};
  };
  
  Portal.prototype.drawPortal = function(depressed) {          
    var width_x = Math.abs(this.start_click_x - this.end_click_x);
    var width_y = Math.abs(this.start_click_y - this.end_click_y);
    var reverse_x = (this.end_click_x < this.start_click_x) ? -1 : 1;
    var reverse_y = (this.end_click_y > this.start_click_y) ? 1 : -1;
    
    var x = this.start_click_x + (width_x / 2) * reverse_x;
    var y = this.start_click_y + (width_y / 2) * reverse_y;
    var radius = width_x / 2;
    
    this.clearCanvas();
    if (!depressed) {
      this.ctx.fillStyle = this.settings['button-side-color'];
      this.ctx.strokeStyle = this.settings['button-side-color'];
              
      for (var i = 0; i <= 10; i++) {
        this.ctx.beginPath();
        this.ctx.arc(x, y + i, radius, 0, Math.PI*2, true);
        this.ctx.fill();
      }
      
      this.ctx.beginPath();
      this.ctx.fillStyle = this.settings['button-top-color'];
      this.ctx.strokeStyle = this.settings['button-top-color'];
      this.ctx.arc(x, y, radius, 0, Math.PI*2, true);
      this.ctx.fill();
      
    } else {
      this.ctx.beginPath();
      this.ctx.fillStyle = this.settings['button-top-color'];
      this.ctx.strokeStyle = this.settings['button-top-color'];
      this.ctx.arc(x, y + 10, radius, 0, Math.PI*2, true);
      this.ctx.fill();
    }
  };
  
  Portal.prototype.clearCanvas = function() {
    this.ctx.clearRect(0, 0,this.width,this.height);
  };  
  
  Portal.prototype.pointInCircle = function(x, y) {
    return this.ctx.isPointInPath(x, y);
  };
    
  // Setup events.
  Portal.prototype.init = function() {
    var that = this;
    
    // Start Action
    this.$element.mousedown(function(e) {
      that.startAction(e);
    });
    this.element.addEventListener('touchstart', function(e) {
      that.startAction(e);
    }, false);
        
    // End Action
    this.element.addEventListener('touchend', function(e) {
      that.endAction(e);
    }, false);
    $(document).mouseup(function(e) {
      that.endAction(e);
    });
    
  };

  Portal.prototype.startAction = function(e) {
    var position = this.getEventPosition(e);
    if (this.pointInCircle(position.left, position.top)) {
      this.drawPortal(true);
      this.settings.callback();          
    } else {
      this.start_click_x = position.left;
      this.start_click_y = position.top;
    }
  };
  
  Portal.prototype.endAction = function(e) {
    var position = this.getEventPosition(e);
    if (this.pointInCircle(position.left, position.top)) {
      this.drawPortal();
    } else {
      this.end_click_x = position.left;
      this.end_click_y = position.top;
      this.drawPortal();
    }
  };

  $.fn.portal = function(options) {
    var defaults = {
      'button-top-color' : '#999',
      'button-side-color' : '#666',
      'callback' : (function() {})
    };
        
    if (options) {
      $.extend(defaults, options);
    }
    
    return this.each(function() {
      var portal = new Portal(this, defaults);
      portal.init();
    });
  };
  
})(jQuery);