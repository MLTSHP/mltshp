/* JS for the tools page */

(function($) {
  
  $.fn.hint = function(text) {
    
    var default_text = text;
    var field = this;
    var original_color = $(this).css('color');
    
    var setDefault = function() {
      if ($(field).val() == '') {
        $(field).css('color', '#999').val(default_text);
      }
    };
    
    var resetStyles = function() {
      $(field).css('color', original_color);
    };
    
    var clearField = function() {
      $(field).val('');
    };
    
    setDefault();
    
    this.focus(function() {
      if ($(this).val() == default_text) {
        resetStyles();
        clearField();
      }
    }).blur(function() {
      setDefault();
    });
    
    // on submit, clear out the hint before submit.
    this.parents('form:first').submit(function() {
      if ($(field).val() == default_text) {
        clearField();
      }
    });
    
    return this;
  };
  
})(jQuery);


$(document).ready(function() {
  
  $('#description-field').hint('Write a description if you\'d like!');

});
