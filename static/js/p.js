function getEmbed(){
   var e = window.frames["instacalc_bookmarklet_iframe"];
   return e;
}

function addCSS(url){
  var headID = document.getElementsByTagName("head")[0];
  var cssNode = document.createElement('link');
  cssNode.type = 'text/css';
  cssNode.rel = 'stylesheet';
  cssNode.href = url;
  cssNode.media = 'screen';
  headID.appendChild(cssNode);
}

/* Base64 encoding from http://ostermiller.org/calc/encode.html

License
This program is free software; you can redistribute it and/or modify it 
under the terms of the GNU General Public License as published by the 
Free Software Foundation; either version 2 of the License, or (at your 
option) any later version.
This program is distributed in the hope that it will be useful, but 
WITHOUT ANY WARRANTY; without even the implied warranty of 
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General 
Public License for more details.

*/
var END_OF_INPUT = -1;
var base64Chars = new Array(
    'A','B','C','D','E','F','G','H',
    'I','J','K','L','M','N','O','P',
    'Q','R','S','T','U','V','W','X',
    'Y','Z','a','b','c','d','e','f',
    'g','h','i','j','k','l','m','n',
    'o','p','q','r','s','t','u','v',
    'w','x','y','z','0','1','2','3',
    '4','5','6','7','8','9','+','/'
);

var reverseBase64Chars = new Array();
for (var i=0; i < base64Chars.length; i++){
    reverseBase64Chars[base64Chars[i]] = i;
}

var base64Str;
var base64Count;
function setBase64Str(str){
    base64Str = str;
    base64Count = 0;
}
function readBase64(){    
    if (!base64Str) return END_OF_INPUT;
    if (base64Count >= base64Str.length) return END_OF_INPUT;
    var c = base64Str.charCodeAt(base64Count) & 0xff;
    base64Count++;
    return c;
}

/* make string URL safe; remove padding =, replace "+" and "/" with "*" and "-" */
function encodeBase64ForURL(str){
   var str = encodeBase64(str).replace(/=/g, "").replace(/\+/g, "*").replace(/\//g, "-");
   str = str.replace(/\s/g, "");   /* Watch out! encodeBase64 breaks lines at 76 chars -- we don't want any whitespace */
   return str;
}

function keyPressHandler(e) {
      var kC  = (window.event) ?    // MSIE or Firefox?
                 event.keyCode : e.keyCode;
      var Esc = (window.event) ?   
                27 : e.DOM_VK_ESCAPE // MSIE : Firefox
      if(kC==Esc){
         // alert("Esc pressed");
         toggleItem("instacalc_bookmarklet");
      }
}


function toggleItem(id){
  var item = document.getElementById(id);
  if(item){
    if ( item.style.display == "none"){
      item.style.display = "";
    }
    else{
      item.style.display = "none";
    } 
  }
}

function showItem(id){
  try{
    var item = document.getElementById(id);
    if(item){
        item.style.display = "";
    }
  }
  catch(e){
  
  }
}

(function(){

  var iframe_url = "http://localhost:8000/tools/p?url=" + encodeURIComponent(document.location.href);

 
  var existing_iframe = document.getElementById('instacalc_bookmarklet_iframe');
  
  if (existing_iframe){
    showItem('instacalc_bookmarklet');
    return;
  }
  
  addCSS("http://localhost:8000/static/css/picker.css?x=" + (Math.random()));
 
  var div = document.createElement("div");
  div.id = "instacalc_bookmarklet";
  
  var str = "";
  str += "<table id='instacalc_bookmarklet_table' valign='top' width='570' cellspacing='0' cellpadding='0'><tr><td width ='550' height='80'>";
  str += "<iframe frameborder='0' scrolling='no' name='instacalc_bookmarklet_iframe' id='instacalc_bookmarklet_iframe' src='" + iframe_url + "' width='550px' height='75px' style='textalign:right; backgroundColor: white;'></iframe>";
  str += "</td><td onClick='toggleItem(\"instacalc_bookmarklet\");' style='background: #FFDDDD;' title='click to close window' valign='top' align='center' width='20px'>";
  str += "<a href='javascript:void(0);' style='width:100%; text-align: middle; color: #FF0000; font-family: Arial;'>x</a>";
  str += "</td></tr></table>";
  
  div.innerHTML = str;
  
  div.onkeypress = keyPressHandler;
  document.body.insertBefore(div, document.body.firstChild);
})()
